#!/usr/bin/env python3
"""Visual text lines with font names and sizes (via pdfplumber).
Use this to understand the document's visual hierarchy before writing
classification bands — but derive the bands themselves from opdump.py,
whose coordinates match the tagging engine exactly.

Usage: python textdump.py INPUT.pdf
"""
import sys
from collections import Counter

import pdfplumber

with pdfplumber.open(sys.argv[1]) as pdf:
    for p in pdf.pages:
        print(f'=== PAGE {p.page_number} ({p.width}x{p.height}) ===')
        fonts = Counter((ch['fontname'], round(ch['size'], 1))
                        for ch in p.chars)
        print('font/size usage:', fonts.most_common(20))
        words = p.extract_words(extra_attrs=['size', 'fontname'])
        lines = {}
        for w in words:
            lines.setdefault(round(w['top'], 0), []).append(w)
        for top in sorted(lines):
            ws = sorted(lines[top], key=lambda w: w['x0'])
            szs = sorted({round(w['size'], 1) for w in ws})
            fns = sorted({w['fontname'].split('+')[-1] for w in ws})
            text = ' '.join(w['text'] for w in ws)
            print(f'  y={top:7.1f} sz={szs} {fns} | {text[:150]}')
