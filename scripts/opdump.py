#!/usr/bin/env python3
"""Per-operator dump of a PDF's content streams with the same position
computation the tagging engine uses. Classification bands (BANDS in the
config) must be derived from THESE y/x values.

y is distance from the page top at the text-line origin (baseline); x is the
line-start x and goes stale for subsequent ops on the same line (glyph
advances are not tracked) — fine for band boundaries, just don't trust x for
the 2nd+ run on a line.

Usage: python opdump.py INPUT.pdf
"""
import sys

import pikepdf

def mat_mul(a, b):
    return (a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3],
            a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3],
            a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5])

ID6 = (1, 0, 0, 1, 0, 0)
pdf = pikepdf.open(sys.argv[1])
for pno, page in enumerate(pdf.pages):
    H = float(page.mediabox[3])
    insts = pikepdf.parse_content_stream(page)
    ctm = ID6; stack = []; tm = ID6; tlm = ID6; tl = 0.0
    font = None; size = 0.0
    print(f'===== PAGE {pno+1} =====')
    for i, inst in enumerate(insts):
        op = str(inst.operator); o = inst.operands
        if op == 'q': stack.append(ctm)
        elif op == 'Q': ctm = stack.pop() if stack else ID6
        elif op == 'cm': ctm = mat_mul(tuple(float(x) for x in o), ctm)
        elif op == 'BT': tm = tlm = ID6
        elif op == 'Tf': font = str(o[0]); size = float(o[1])
        elif op == 'Tm': tm = tlm = tuple(float(x) for x in o)
        elif op == 'Td':
            tlm = mat_mul((1,0,0,1,float(o[0]),float(o[1])), tlm); tm = tlm
        elif op == 'TD':
            tl = -float(o[1])
            tlm = mat_mul((1,0,0,1,float(o[0]),float(o[1])), tlm); tm = tlm
        elif op == 'TL': tl = float(o[0])
        elif op == 'T*':
            tlm = mat_mul((1,0,0,1,0,-tl), tlm); tm = tlm

        if op in ('Tj', 'TJ', "'", '"'):
            m = mat_mul(tm, ctm)
            x, y = m[4], H - m[5]
            parts = []
            try:
                if op == 'TJ':
                    for e in o[0]:
                        if isinstance(e, pikepdf.String):
                            parts.append(bytes(e).decode('latin-1', 'replace'))
                else:
                    parts.append(bytes(o[-1]).decode('latin-1', 'replace'))
            except Exception as ex:
                parts.append(f'<?{ex}>')
            txt = ''.join(parts).replace('\n', '\\n')
            print(f'[{i:4}] y={y:7.1f} x={x:7.1f} {font} {size:g} {op} |{txt[:90]}|')
        elif op == 'Do':
            x, y = ctm[4], H - ctm[5]
            print(f'[{i:4}] y={y:7.1f} x={x:7.1f} Do {o[0]}')
        elif op in ('BDC', 'BMC', 'EMC', 'MP', 'DP'):
            print(f'[{i:4}] {op} ' + ' '.join(str(x) for x in o)[:90])
