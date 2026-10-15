"""Tagging config for examples/report/input.pdf (see make_pdf.py).

Demonstrates: headings, paragraphs, a real data table with column headers
(grid rules become artifacts automatically), and text objects living inside
q/Q graphics states (platypus output).

The y/x numbers come from `opdump.py input.pdf` — regenerate them if you
change make_pdf.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from tag_engine import node, table, tr, th, F, M, MC, REST

TITLE = 'Community Garden Annual Report'
LANG = 'en-US'
PDFUA = True

BANDS = {
 0: [
    (80, 110,  [(None, 'H1')]),
    (110, 165, [(None, 'P_intro')]),
    (165, 190, [(None, 'H2_harvest')]),
    (190, 228, [(None, 'P_harvest')]),
    # table: columns split at x=320 and x=400
    (230, 248, [(320, 'TH_crop'), (400, 'TH_beds'), (None, 'TH_yield')]),
    (248, 266, [(320, 'TD_r1c1'), (400, 'TD_r1c2'), (None, 'TD_r1c3')]),
    (266, 284, [(320, 'TD_r2c1'), (400, 'TD_r2c2'), (None, 'TD_r2c3')]),
    (284, 302, [(320, 'TD_r3c1'), (400, 'TD_r3c2'), (None, 'TD_r3c3')]),
    (310, 335, [(None, 'H2_plans')]),
    (335, 375, [(None, 'P_plans')]),
    (378, 400, [(None, 'P_footer')]),
 ],
}

TU = {}   # no form fields in this document

TREE = [
 node('H1', M),
 node('P_intro', M),
 node('H2_harvest', M),
 node('P_harvest', M),
 table('Table_harvest',
       tr('TR_h', th('TH_crop', 'Column'), th('TH_beds', 'Column'),
          th('TH_yield', 'Column')),
       tr('TR_1', node('TD_r1c1', M), node('TD_r1c2', M), node('TD_r1c3', M)),
       tr('TR_2', node('TD_r2c1', M), node('TD_r2c2', M), node('TD_r2c3', M)),
       tr('TR_3', node('TD_r3c1', M), node('TD_r3c2', M), node('TD_r3c3', M))),
 node('H2_plans', M),
 node('P_plans', M),
 node('P_footer', M),
]
