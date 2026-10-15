#!/usr/bin/env python3
"""Verify a tagged PDF against its untagged original.

Checks: pixel-identical rendering (with annotations drawn), every content op
tagged or artifact, marked-content nesting vs BT/ET, contiguous MCIDs,
ParentTree consistency, widget TU/StructParent/OBJR backlinks, font embedding
and ToUnicode, title metadata, DisplayDocTitle, Lang.

Exit code 0 only if every check passes.

Usage: python verify.py ORIGINAL.pdf TAGGED.pdf
"""
import sys
import tempfile

import pikepdf
from pikepdf import Name

ORIG, TAGGED = sys.argv[1], sys.argv[2]
fails = []

def check(cond, msg):
    print(('  OK  : ' if cond else '  FAIL: ') + msg)
    if not cond:
        fails.append(msg)

# --------------------------------------------------------- 1. render diff
import pypdfium2 as pdfium
from PIL import Image, ImageChops

print('== render diff ==')
with tempfile.TemporaryDirectory() as td:
    paths = {}
    for label, path in (('orig', ORIG), ('tagged', TAGGED)):
        doc = pdfium.PdfDocument(path)
        paths[label] = []
        for p in range(len(doc)):
            png = f'{td}/{label}_p{p}.png'
            doc[p].render(scale=2.5, draw_annots=True).to_pil().save(png)
            paths[label].append(png)
        doc.close()
    check(len(paths['orig']) == len(paths['tagged']), 'same page count')
    for p, (pa, pb) in enumerate(zip(paths['orig'], paths['tagged'])):
        a, b = Image.open(pa), Image.open(pb)
        same = a.size == b.size
        maxd = -1
        if same:
            diff = ImageChops.difference(a.convert('RGB'), b.convert('RGB'))
            maxd = max(e[1] for e in diff.getextrema())
        check(same and maxd == 0,
              f'page {p+1} pixel-identical (max channel diff {maxd})')

# --------------------------------------------------- 2. content coverage
pdf = pikepdf.open(TAGGED)
print('== content stream coverage ==')
TEXT_SHOW = {'Tj', 'TJ', "'", '"'}
PAINT = {'S','s','f','F','f*','B','B*','b','b*','sh','Do','EI'}
for pageno, page in enumerate(pdf.pages):
    stack = []          # (kind, opened_inside_bt)
    in_bt = False
    naked = bad_nest = 0
    mcids = []
    for inst in pikepdf.parse_content_stream(page):
        op = str(inst.operator); o = inst.operands
        if op in ('BDC', 'BMC'):
            kind = 'other'
            if str(o[0]) == '/Artifact':
                kind = 'ART'
            elif (len(o) > 1 and isinstance(o[1], pikepdf.Dictionary)
                  and '/MCID' in o[1]):
                kind = 'MCID'
                mcids.append(int(o[1]['/MCID']))
            stack.append((kind, in_bt))
        elif op == 'EMC':
            if not stack:
                bad_nest += 1
            elif stack.pop()[1] != in_bt:
                bad_nest += 1
        elif op == 'BT':
            in_bt = True
        elif op == 'ET':
            bad_nest += sum(1 for _, inside in stack if inside)
            in_bt = False
        elif op in TEXT_SHOW or op in PAINT:
            if not any(k in ('ART', 'MCID') for k, _ in stack):
                naked += 1
    check(not stack, f'page {pageno+1} balanced marked content')
    check(bad_nest == 0, f'page {pageno+1} BT/ET nesting clean')
    check(naked == 0,
          f'page {pageno+1} all content tagged or artifact ({naked} naked)')
    check(sorted(mcids) == list(range(len(mcids))),
          f'page {pageno+1} MCIDs contiguous 0..{len(mcids)-1}')
    check(int(page.get('/StructParents', -1)) == pageno,
          f'page {pageno+1} StructParents == {pageno}')
    check(page.get('/Tabs') == Name('/S'), f'page {pageno+1} Tabs /S')

# --------------------------------------------------------- 3. struct tree
print('== structure tree ==')
root = pdf.Root
check('/StructTreeRoot' in root, 'StructTreeRoot present')
check(bool(root.MarkInfo.Marked), 'MarkInfo/Marked true')
sr = root.StructTreeRoot
ptree = {int(k): v for k, v in zip(sr.ParentTree.Nums[::2],
                                   sr.ParentTree.Nums[1::2])}
page_of = {p.obj.objgen: i for i, p in enumerate(pdf.pages)}

mcid_owner = {}
def walk(el, parent):
    if el.get('/P').objgen != parent.objgen:
        fails.append(f'parent pointer mismatch in {el.get("/S")}')
    k = el.get('/K')
    if k is None:
        return
    items = k if isinstance(k, pikepdf.Array) else [k]
    for item in items:
        if isinstance(item, int):
            mcid_owner[(page_of[el.Pg.objgen], int(item))] = el
        elif hasattr(item, 'keys'):
            if item.get('/Type') == Name('/OBJR'):
                continue
            walk(item, el)

doc_el = sr.K[0]
check(str(doc_el.S) == '/Document', 'root element is Document')
if doc_el.get('/P').objgen != sr.objgen:
    fails.append('Document parent != StructTreeRoot')
print(f'  Document children: {len(doc_el.K)}')
for kid in doc_el.K:
    walk(kid, doc_el)

for pno in range(len(pdf.pages)):
    arr = ptree[pno]
    n = len(arr)
    owned = sum(1 for m in range(n) if (pno, m) in mcid_owner)
    check(owned == n, f'page {pno+1}: all {n} ParentTree MCIDs in tree')
    agree = all(arr[m].objgen == mcid_owner[(pno, m)].objgen
                for m in range(n) if (pno, m) in mcid_owner)
    check(agree, f'page {pno+1}: ParentTree matches tree owners')

# ------------------------------------------------------------- 4. widgets
print('== widgets ==')
n = tu = sp = objr_ok = 0
for page in pdf.pages:
    for a in page.get('/Annots', []):
        if a.get('/Subtype') != Name('/Widget'):
            continue
        n += 1
        if '/TU' in a:
            tu += 1
        spv = a.get('/StructParent')
        if spv is not None and int(spv) in ptree:
            sp += 1
            form = ptree[int(spv)]
            if str(form.S) == '/Form':
                k = form.K
                o = k[0] if isinstance(k, pikepdf.Array) else k
                if (o.get('/Type') == Name('/OBJR')
                        and o.Obj.objgen == a.objgen):
                    objr_ok += 1
check(tu == n, f'all {n} widgets have /TU ({tu})')
check(sp == n, f'all widgets have StructParent in ParentTree ({sp})')
check(objr_ok == n, f'all OBJR backlinks correct ({objr_ok})')

# --------------------------------------------------------------- 5. fonts
# Only fonts that are active at a text-show op matter: unused Resources
# entries and never-rendering selections (e.g. reportlab's default
# "BT /F1 12 Tf ET") are harmless, and veraPDF ignores them too.
print('== fonts ==')
for pageno, page in enumerate(pdf.pages):
    used = set()
    cur = None
    fstack = []
    for inst in pikepdf.parse_content_stream(page):
        op = str(inst.operator)
        if op == 'Tf':
            cur = str(inst.operands[0])
        elif op == 'q':
            fstack.append(cur)
        elif op == 'Q':
            cur = fstack.pop() if fstack else cur
        elif op in TEXT_SHOW and cur is not None:
            used.add(cur)
    for fname, f in page.Resources.get('/Font', {}).items():
        if str(fname) not in used:
            continue
        sub = str(f.get('/Subtype'))
        desc = (f.DescendantFonts[0].FontDescriptor if sub == '/Type0'
                else f.get('/FontDescriptor'))
        emb = desc is not None and any(
            k in desc for k in ('/FontFile', '/FontFile2', '/FontFile3'))
        tounicode = '/ToUnicode' in f
        std = str(f.get('/Encoding', '')) in ('/WinAnsiEncoding',
                                              '/MacRomanEncoding')
        check(emb, f'p{pageno+1} {fname} ({sub}) embedded')
        check(tounicode or std, f'p{pageno+1} {fname} Unicode-mappable')

# ------------------------------------------------------------ 6. metadata
print('== metadata ==')
with pdf.open_metadata() as meta:
    check(meta.get('dc:title') is not None,
          f"dc:title = {meta.get('dc:title')!r}")
    print(f"  info: pdfuaid:part = {meta.get('pdfuaid:part')!r}")
check(bool(root.ViewerPreferences.DisplayDocTitle), 'DisplayDocTitle true')
check(str(root.get('/Lang', '')) != '', f"Lang = {root.get('/Lang')}")

print()
print('RESULT:', 'ALL CHECKS PASSED' if not fails else f'{len(fails)} FAILURES')
sys.exit(1 if fails else 0)
