#!/usr/bin/env python3
"""Print a tagged PDF's logical structure in reading order, roughly as
assistive technology walks it: element types, their text (via MCIDs), table
attributes, and form fields' accessible names.

Note: text is extracted with pdfplumber, which ignores marked-content
ActualText — an ActualText override shows the original glyphs here even
though conforming AT reads the override.

Usage: python readback.py TAGGED.pdf
"""
import sys

import pdfplumber
import pikepdf
from pikepdf import Name

TAGGED = sys.argv[1]

mcid_text = {}
with pdfplumber.open(TAGGED) as pl:
    for pno, page in enumerate(pl.pages):
        for ch in page.chars:
            m = ch.get('mcid')
            if m is not None:
                mcid_text.setdefault((pno, m), []).append(ch['text'])
mcid_text = {k: ''.join(v) for k, v in mcid_text.items()}

pdf = pikepdf.open(TAGGED)
page_of = {p.obj.objgen: i for i, p in enumerate(pdf.pages)}

def text_of(el):
    out = []
    k = el.get('/K')
    if k is None:
        return ''
    items = k if isinstance(k, pikepdf.Array) else [k]
    for item in items:
        if isinstance(item, int):
            out.append(mcid_text.get((page_of[el.Pg.objgen], int(item)), ''))
        elif hasattr(item, 'keys'):
            if item.get('/Type') == Name('/OBJR'):
                tu = item.Obj.get('/TU')
                kind = ('checkbox/button' if str(item.Obj.get('/FT')) == '/Btn'
                        else 'field')
                out.append(f'<<{kind}: {tu}>>')
            else:
                out.append(text_of(item))
    return ' '.join(x for x in out if x)

def walk(el, depth):
    s = str(el.S)[1:]
    if s in ('Table', 'TR', 'L', 'LI', 'Sect', 'Div', 'Part', 'Art'):
        print('  ' * depth + f'[{s}]')
        k = el.get('/K')
        items = k if isinstance(k, pikepdf.Array) else [k]
        for kid in items:
            if hasattr(kid, 'keys') and kid.get('/Type') != Name('/OBJR'):
                walk(kid, depth + 1)
        return
    attrs = ''
    a = el.get('/A')
    if a is not None:
        sc, cs = a.get('/Scope'), a.get('/ColSpan')
        attrs = (f" (Scope={str(sc)[1:] if sc else '-'}"
                 f"{', ColSpan=' + str(cs) if cs else ''})")
    alt = el.get('/Alt')
    if alt is not None:
        attrs += f' Alt="{alt}"'
    print('  ' * depth + f'[{s}]{attrs} {text_of(el)[:170]}')

doc = pdf.Root.StructTreeRoot.K[0]
print(f'[Document] ({len(doc.K)} children)')
for kid in doc.K:
    walk(kid, 1)
