#!/usr/bin/env python3
"""Overview of a PDF before tagging: pages, existing tags, metadata,
AcroForm fields, annotations (with positions), images, operator histogram.

Usage: python inspect_pdf.py INPUT.pdf
"""
import sys
from collections import Counter

import pikepdf
from pikepdf import Name

pdf = pikepdf.open(sys.argv[1])
root = pdf.Root
print('pages:', len(pdf.pages))
print('has StructTreeRoot:', '/StructTreeRoot' in root)
print('has MarkInfo:', '/MarkInfo' in root)
print('Lang:', root.get('/Lang'))
print('ViewerPreferences:', root.get('/ViewerPreferences'))
print('has AcroForm:', '/AcroForm' in root)
docinfo = pdf.docinfo if pdf.docinfo else {}
print('docinfo:', {str(k): str(v) for k, v in docinfo.items()})

for pno, page in enumerate(pdf.pages):
    mb = [float(v) for v in page.mediabox]
    res = page.get('/Resources', {})
    xobjs = res.get('/XObject', {})
    imgs = [str(k) for k, v in xobjs.items()
            if v.get('/Subtype') == Name('/Image')] if xobjs else []
    forms = [str(k) for k, v in xobjs.items()
             if v.get('/Subtype') == Name('/Form')] if xobjs else []
    ops = Counter(str(i.operator) for i in pikepdf.parse_content_stream(page))
    annots = page.get('/Annots')
    print(f'--- page {pno+1}: mediabox={mb} rotate={page.get("/Rotate", 0)} '
          f'tabs={page.get("/Tabs")} annots={len(annots) if annots is not None else 0}')
    print(f'    images={imgs} form-xobjects={forms}')
    print(f'    ops: {dict(ops)}')
    if annots is None:
        continue
    items = []
    for a in annots:
        sub = str(a.get('/Subtype'))
        ft = str(a.get('/FT', ''))
        names = []
        cur = a
        while cur is not None:
            t = cur.get('/T')
            if t is not None:
                names.insert(0, str(t))
            cur = cur.get('/Parent')
        rect = [round(float(x), 1) for x in a.get('/Rect', [0, 0, 0, 0])]
        top = round(mb[3] - rect[3], 1)
        states = None
        ap = a.get('/AP')
        if ap is not None and '/N' in ap and isinstance(ap['/N'], pikepdf.Dictionary):
            states = [str(k) for k in ap['/N'].keys()]
        items.append((top, rect[0], sub, ft, '.'.join(names), rect,
                      str(a.get('/TU', '')), states))
    for it in sorted(items):
        print(f'    top={it[0]:7.1f} x={it[1]:7.1f} {it[2]:8} FT={it[3]:5} '
              f"T='{it[4]}' rect={it[5]} TU='{it[6]}' states={it[7]}")
