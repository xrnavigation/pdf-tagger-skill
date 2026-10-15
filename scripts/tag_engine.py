#!/usr/bin/env python3
"""Generic PDF accessibility-tagging engine.

Reads an untagged PDF plus a per-document Python config (see CONFIG.md) and
writes a tagged PDF that renders pixel-identically to the input:

  * wraps every text/path operation in marked content (MCIDs or /Artifact)
  * builds a full structure tree (headings, paragraphs, tables, figures,
    Form elements with OBJR references for every widget annotation)
  * sets /TU accessible names on all form fields
  * writes ParentTree, MarkInfo, /Tabs /S, language, title metadata,
    DisplayDocTitle, and (optionally) the PDF/UA-1 identifier
  * optionally strips incomplete /CIDSet streams (PDF/UA rule 7.21.4.2)

Usage:
    python tag_engine.py CONFIG.py INPUT.pdf OUTPUT.pdf

The config imports helpers from this module:
    from tag_engine import node, table, tr, th, F, M, MC, REST
"""
import importlib.util
import sys

import pikepdf
from pikepdf import Name, Dictionary, Array, Operator, String

# --------------------------------------------------------------- kid helpers
M = ('MCIDS',)                      # all of this element's MCIDs, reading order
REST = ('REST',)                    # every MCID not yet consumed by MC(i)
def F(name): return ('FORM', name)  # a form field by (fully qualified) name
def MC(i): return ('MCID', i)       # the i-th MCID (after reading-order sort)

def node(key, *kids, **attrs):
    """Structure element. S type = key prefix before first '_'
    (H1/H2/.../P/TH/TD/Span/Caption/Figure/L/LI/Lbl/LBody/BlockQuote/Note)."""
    return {'key': key, 'S': key.split('_')[0], 'kids': list(kids),
            'attrs': attrs}

def table(key, *rows):
    return {'key': key, 'S': 'Table', 'kids': list(rows), 'attrs': {}}

def tr(key, *cells):
    return {'key': key, 'S': 'TR', 'kids': list(cells), 'attrs': {}}

def th(key, scope, colspan=None, rowspan=None):
    """Table header cell. scope: 'Row' | 'Column' | 'Both'."""
    a = {'Scope': scope}
    if colspan: a['ColSpan'] = colspan
    if rowspan: a['RowSpan'] = rowspan
    return node(key, M, **a)

STD_TYPES = {'H1','H2','H3','H4','H5','H6','P','TH','TD','Span','Caption',
             'Figure','L','LI','Lbl','LBody','BlockQuote','Note','Code',
             'Quote','Reference','Formula','Index','TOC','TOCI','Sect','Div',
             'Art','Part'}

# ------------------------------------------------------------- interpreter
def mat_mul(a, b):
    return (a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3],
            a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3],
            a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5])

ID6 = (1, 0, 0, 1, 0, 0)
TEXT_SHOW = {'Tj', 'TJ', "'", '"'}
PATH_ART = {'m','l','c','v','y','re','h','W','W*','n',
            'S','s','f','F','f*','B','B*','b','b*','sh'}
POSITIONED = TEXT_SHOW | {'Do'}


def load_config(path):
    spec = importlib.util.spec_from_file_location('tagconfig', path)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    return cfg


def op_text(inst):
    """Best-effort raw text of a show op, for diagnostics only."""
    try:
        op = str(inst.operator)
        if op == 'Tj':
            return bytes(inst.operands[0]).decode('latin-1', 'replace')
        if op == 'TJ':
            return ''.join(bytes(e).decode('latin-1', 'replace')
                           for e in inst.operands[0]
                           if isinstance(e, pikepdf.String))
    except Exception:
        pass
    return ''


def run(cfg, src, out):
    pdf = pikepdf.open(src)
    npages = len(pdf.pages)

    bands = cfg.BANDS
    artifact_text = getattr(cfg, 'ARTIFACT_TEXT', None)
    actualtext = getattr(cfg, 'ACTUALTEXT', None)
    alt_map = getattr(cfg, 'ALT', {})
    skip_nonwidget = getattr(cfg, 'SKIP_NON_WIDGET_ANNOTS', False)

    def classify(pageno, y, x, font, inst):
        if artifact_text and artifact_text(pageno, y, x, font):
            return 'ART'
        for ymin, ymax, rules in bands.get(pageno, []):
            if ymin <= y < ymax:
                for xlim, key in rules:
                    if xlim is None or x < xlim:
                        if key is None:
                            break
                        return key
        raise SystemExit(
            f"UNCLASSIFIED op page {pageno+1} y={y:.1f} x={x:.1f} "
            f"font={font} text={op_text(inst)[:60]!r}\n"
            f"Add or adjust a band in BANDS[{pageno}].")

    elem_mcids = {}                       # key -> [{page,mcid,y,x}, ...]
    page_mcid_elem = [[] for _ in range(npages)]

    for pageno, page in enumerate(pdf.pages):
        mb = [float(v) for v in page.mediabox]
        if int(page.get('/Rotate', 0)) % 360 != 0:
            raise SystemExit(f"page {pageno+1} has /Rotate; not supported")
        H = mb[3]
        insts = list(pikepdf.parse_content_stream(page))

        # ---- pass 1: position + label per instruction -------------------
        special = {}      # inst index -> ActualText string
        ctm = ID6; stack = []; tm = ID6; tlm = ID6; tl = 0.0; font = None
        labels = [None] * len(insts)
        pos = [None] * len(insts)
        qdepth = 0
        for i, inst in enumerate(insts):
            op = str(inst.operator); o = inst.operands
            if op == 'q': stack.append(ctm); qdepth += 1
            elif op == 'Q': ctm = stack.pop() if stack else ID6; qdepth -= 1
            elif op == 'cm': ctm = mat_mul(tuple(float(x) for x in o), ctm)
            elif op == 'BT':
                tm = tlm = ID6
            elif op == 'Tf': font = str(o[0])
            elif op == 'Tm': tm = tlm = tuple(float(x) for x in o)
            elif op == 'Td':
                tlm = mat_mul((1,0,0,1,float(o[0]),float(o[1])), tlm); tm = tlm
            elif op == 'TD':
                tl = -float(o[1])
                tlm = mat_mul((1,0,0,1,float(o[0]),float(o[1])), tlm); tm = tlm
            elif op == 'TL': tl = float(o[0])
            elif op == 'T*':
                tlm = mat_mul((1,0,0,1,0,-tl), tlm); tm = tlm
            elif op in ('BI', 'ID', 'EI'):
                raise SystemExit("inline images not supported by this engine")

            if op in TEXT_SHOW:
                m = mat_mul(tm, ctm)
                x, y = m[4], H - m[5]
                pos[i] = (y, x)
                labels[i] = classify(pageno, y, x, font, inst)
                if actualtext and labels[i] != 'ART':
                    at = actualtext(pageno, y, x, font, labels[i])
                    if at is not None:
                        special[i] = at
            elif op == 'Do':
                x, y = ctm[4], H - ctm[5]
                pos[i] = (y, x)
                labels[i] = classify(pageno, y, x, None, inst)
            elif op in PATH_ART:
                labels[i] = 'ART'

        # ---- pre-existing marked-content pairs inherit one label --------
        pairs = []; bstack = []
        for i, inst in enumerate(insts):
            op = str(inst.operator)
            if op in ('BDC', 'BMC'):
                bstack.append(i)
            elif op == 'EMC':
                pairs.append((bstack.pop(), i))
        if bstack:
            raise SystemExit(f"page {pageno+1}: unbalanced existing BDC/EMC")
        for start, end in pairs:
            plabel = None
            for j in range(start + 1, end):          # first real content
                if labels[j] not in (None, 'ART'):
                    plabel = labels[j]; break
            if plabel is None:
                for j in range(start + 1, end):      # else any artifact
                    if labels[j] is not None:
                        plabel = labels[j]; break
            if plabel is None:
                for j in range(start - 1, -1, -1):   # else previous label
                    if labels[j] is not None:
                        plabel = labels[j]; break
            for j in range(start, end + 1):
                labels[j] = plabel

        # ---- pass 2: rewrite stream with BDC/EMC ------------------------
        outops = []
        st = {'open': None, 'inner': 0, 'in_bt': False,
              'next_mcid': 0, 'entry': None}

        def close_region():
            if st['open'] is not None:
                outops.append(([], Operator('EMC')))
                st['open'] = None

        def register(key, y, x):
            entry = {'page': pageno, 'mcid': st['next_mcid'], 'y': y, 'x': x}
            elem_mcids.setdefault(key, []).append(entry)
            page_mcid_elem[pageno].append(key)
            st['next_mcid'] += 1
            return entry

        def open_region(key, y, x):
            if key == 'ART':
                outops.append(([Name('/Artifact'),
                                Dictionary(Type=Name('/Layout'))],
                               Operator('BDC')))
                st['entry'] = None
            else:
                tag = key.split('_')[0]
                outops.append(([Name('/' + tag),
                                Dictionary(MCID=st['next_mcid'])],
                               Operator('BDC')))
                entry = register(key, y, x)
                st['entry'] = entry if y is None else None
            st['open'] = key

        for i, inst in enumerate(insts):
            op = str(inst.operator)
            lab = labels[i]
            if op == 'BT':
                close_region(); st['in_bt'] = True
                outops.append(inst); continue
            if op == 'ET':
                close_region(); st['in_bt'] = False
                outops.append(inst); continue
            if op in ('q', 'Q'):
                # keep marked content properly nested inside q/Q pairs
                if st['inner'] == 0:
                    close_region()
                outops.append(inst); continue
            if op in ('BDC', 'BMC'):
                if st['inner'] == 0 and lab is not None and lab != st['open']:
                    close_region()
                    open_region(lab, None, None)
                st['inner'] += 1
                outops.append(inst); continue
            if op == 'EMC':
                st['inner'] -= 1
                outops.append(inst); continue
            if i in special:
                assert st['inner'] == 0, "ActualText override inside existing pair"
                close_region()
                y, x = pos[i]
                outops.append(([Name('/Span'),
                                Dictionary(MCID=st['next_mcid'],
                                           ActualText=String(special[i]))],
                               Operator('BDC')))
                register(lab, y, x)
                outops.append(inst)
                outops.append(([], Operator('EMC')))
                continue
            if st['inner'] == 0 and lab is not None and lab != st['open']:
                close_region()
                p = pos[i] or (None, None)
                open_region(lab, p[0], p[1])
            outops.append(inst)
            if st['entry'] is not None and pos[i] is not None:
                st['entry']['y'], st['entry']['x'] = pos[i]
                st['entry'] = None
        close_region()

        page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(outops))
        page[Name('/StructParents')] = pageno
        page[Name('/Tabs')] = Name('/S')

    # reading order inside each element: by line (4pt buckets), then x
    for key, lst in elem_mcids.items():
        lst.sort(key=lambda r: (round(r['y'] / 4), r['x'])
                 if r['y'] is not None else (10**9, 10**9))

    # ------------------------------------------------------------ widgets
    widgets = {}   # fq name -> (annot, pageno)
    for pageno, page in enumerate(pdf.pages):
        for a in page.get('/Annots', []):
            if a.get('/Subtype') != Name('/Widget'):
                if skip_nonwidget:
                    continue
                raise SystemExit(
                    f"page {pageno+1} has a non-widget annotation "
                    f"({a.get('/Subtype')}); tag it manually (e.g. Link) or "
                    "set SKIP_NON_WIDGET_ANNOTS = True in the config")
            names = []; cur = a
            while cur is not None:
                t = cur.get('/T')
                if t is not None:
                    names.insert(0, str(t))
                cur = cur.get('/Parent')
            fq = '.'.join(names) or f'page{pageno+1}-unnamed'
            base, n = fq, 2
            while fq in widgets:
                fq = f'{base}#{n}'; n += 1
            widgets[fq] = (a, pageno)

    missing_tu = [t for t in widgets if t not in cfg.TU]
    if missing_tu:
        raise SystemExit('fields without a TU entry:\n  ' +
                         '\n  '.join(missing_tu))
    for t, (a, _) in widgets.items():
        a[Name('/TU')] = String(cfg.TU[t])

    # ------------------------------------------------------- structure tree
    pagerefs = [p.obj for p in pdf.pages]
    struct_root = pdf.make_indirect(Dictionary(Type=Name('/StructTreeRoot')))
    doc_elem = pdf.make_indirect(Dictionary(
        Type=Name('/StructElem'), S=Name('/Document'), P=struct_root))

    page_parent_arrays = [[None] * len(page_mcid_elem[p]) for p in range(npages)]
    annot_parents = []
    next_key = [npages]
    used_forms = set()
    used_mcids = set()

    def build(spec, parent):
        stype = spec['S']
        if stype not in STD_TYPES and stype not in ('Table', 'TR'):
            raise SystemExit(f"element key {spec['key']!r}: unknown structure "
                             f"type {stype!r}")
        el = pdf.make_indirect(Dictionary(
            Type=Name('/StructElem'), S=Name('/' + stype), P=parent))
        a = spec['attrs']
        if a:
            attr = Dictionary(O=Name('/Table'))
            if 'Scope' in a: attr[Name('/Scope')] = Name('/' + a['Scope'])
            if 'ColSpan' in a: attr[Name('/ColSpan')] = a['ColSpan']
            if 'RowSpan' in a: attr[Name('/RowSpan')] = a['RowSpan']
            el[Name('/A')] = attr
        if stype == 'Figure':
            alt = alt_map.get(spec['key'])
            if not alt:
                raise SystemExit(f"Figure {spec['key']!r} needs an ALT entry")
            el[Name('/Alt')] = String(alt)
        kids = []
        key = spec['key']
        mlist = elem_mcids.get(key, [])
        pageno = mlist[0]['page'] if mlist else None
        for k in spec['kids']:
            if isinstance(k, dict):
                kids.append(build(k, el))
                continue
            if k[0] in ('MCIDS', 'MCID', 'REST'):
                if k[0] == 'MCID':
                    entries = [mlist[k[1]]]
                else:
                    entries = [e for e in mlist
                               if (e['page'], e['mcid']) not in used_mcids]
                for e in entries:
                    assert (e['page'], e['mcid']) not in used_mcids
                    used_mcids.add((e['page'], e['mcid']))
                    kids.append(e['mcid'])
                    page_parent_arrays[e['page']][e['mcid']] = el
            elif k[0] == 'FORM':
                if k[1] not in widgets:
                    raise SystemExit(f"TREE references unknown field {k[1]!r}")
                if k[1] in used_forms:
                    raise SystemExit(f"field {k[1]!r} referenced twice in TREE")
                used_forms.add(k[1])
                annot, apage = widgets[k[1]]
                form = pdf.make_indirect(Dictionary(
                    Type=Name('/StructElem'), S=Name('/Form'), P=el,
                    Pg=pagerefs[apage]))
                form[Name('/K')] = Array([Dictionary(
                    Type=Name('/OBJR'), Obj=annot, Pg=pagerefs[apage])])
                kk = next_key[0]; next_key[0] += 1
                annot[Name('/StructParent')] = kk
                annot_parents.append((kk, form))
                kids.append(form)
                if pageno is None:
                    pageno = apage
        if mlist and len({e['page'] for e in mlist}) > 1:
            raise SystemExit(f"element {key!r} spans multiple pages; split it")
        if pageno is not None:
            el[Name('/Pg')] = pagerefs[pageno]
        el[Name('/K')] = Array(kids)
        return el

    doc_elem[Name('/K')] = Array([build(spec, doc_elem) for spec in cfg.TREE])

    # ------------------------------------------------------------- checks
    spec_keys = set()
    def walk_spec(s):
        spec_keys.add(s['key'])
        for k in s['kids']:
            if isinstance(k, dict):
                walk_spec(k)
    for s in cfg.TREE:
        walk_spec(s)
    unplaced = set(elem_mcids) - spec_keys
    if unplaced:
        raise SystemExit(f"elements with content but not in TREE: {unplaced}")

    bad = []
    for pno, arr in enumerate(page_parent_arrays):
        for mc, v in enumerate(arr):
            if v is None:
                k = page_mcid_elem[pno][mc]
                bad.append((pno + 1, mc, k,
                            [(e['mcid'], e['y'], e['x'])
                             for e in elem_mcids[k]]))
    if bad:
        for b in bad:
            print('UNOWNED MCID:', b, file=sys.stderr)
        raise SystemExit(
            "some MCIDs were not consumed — an element produced more runs "
            "than its MC(i) spec expects; use REST or M")

    unused = set(widgets) - used_forms
    if unused:
        raise SystemExit(f"widgets never placed in TREE: {unused}")

    # heading sequence sanity (warn only)
    levels = [int(s['key'][1]) for s in cfg.TREE
              if s['S'] in ('H1','H2','H3','H4','H5','H6')]
    prev = 0
    for lv in levels:
        if lv > prev + 1:
            print(f"WARNING: heading level jump H{prev} -> H{lv}",
                  file=sys.stderr)
        prev = lv

    # --------------------------------------------------------- parent tree
    nums = []
    for pno, arr in enumerate(page_parent_arrays):
        nums += [pno, pdf.make_indirect(Array(arr))]
    for kk, form in sorted(annot_parents):
        nums += [kk, form]
    struct_root[Name('/ParentTree')] = pdf.make_indirect(
        Dictionary(Nums=Array(nums)))
    struct_root[Name('/ParentTreeNextKey')] = next_key[0]
    struct_root[Name('/K')] = Array([doc_elem])
    pdf.Root[Name('/StructTreeRoot')] = struct_root
    pdf.Root[Name('/MarkInfo')] = Dictionary(Marked=True)

    # -------------------------------------------- fonts / metadata / prefs
    if getattr(cfg, 'REMOVE_CIDSET', True):
        removed = 0
        for page in pdf.pages:
            for f in page.Resources.get('/Font', {}).values():
                if f.get('/Subtype') == Name('/Type0'):
                    desc = f.DescendantFonts[0].get('/FontDescriptor')
                    if desc is not None and '/CIDSet' in desc:
                        del desc[Name('/CIDSet')]
                        removed += 1
        if removed:
            print(f'removed {removed} incomplete /CIDSet entries')

    if '/Lang' not in pdf.Root:
        pdf.Root[Name('/Lang')] = String(getattr(cfg, 'LANG', 'en-US'))
    vp = pdf.Root.get('/ViewerPreferences')
    if vp is None:
        pdf.Root[Name('/ViewerPreferences')] = Dictionary(DisplayDocTitle=True)
    else:
        vp[Name('/DisplayDocTitle')] = True

    with pdf.open_metadata(set_pikepdf_as_editor=False,
                           update_docinfo=True) as meta:
        meta['dc:title'] = cfg.TITLE
        if getattr(cfg, 'PDFUA', True):
            meta['pdfuaid:part'] = '1'

    pdf.save(out)
    print('saved', out)
    for pno in range(npages):
        print(f'  page {pno+1}: {len(page_mcid_elem[pno])} MCIDs')
    print(f'  elements: {len(elem_mcids)}  forms: {len(used_forms)}')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    run(load_config(sys.argv[1]), sys.argv[2], sys.argv[3])
