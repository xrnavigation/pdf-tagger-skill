"""Tagging config for examples/form/input.pdf (see make_pdf.py).

Demonstrates: Form elements with OBJR for every widget, /TU accessible names,
interleaving fields with their visible labels in reading order (checkbox
before its label, text field after its label).

The y/x numbers come from `opdump.py input.pdf` — regenerate them if you
change make_pdf.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from tag_engine import node, table, tr, th, F, M, MC, REST

TITLE = 'Community Garden Volunteer Sign-Up'
LANG = 'en-US'
PDFUA = True

BANDS = {
 0: [
    (70, 95,   [(None, 'H1')]),
    (100, 135, [(None, 'P_intro')]),
    (150, 170, [(None, 'P_name')]),
    (200, 220, [(None, 'P_email')]),
    (250, 270, [(None, 'P_phone')]),
    (310, 332, [(None, 'H2_prefs')]),
    (340, 365, [(None, 'P_news')]),
    (368, 392, [(None, 'P_rules')]),
    (410, 432, [(None, 'P_day')]),
    (460, 480, [(None, 'P_footer')]),
 ],
}

TU = {
    'name': 'Full name',
    'email': 'Email address',
    'phone': 'Phone number',
    'newsletter': 'Subscribe to the monthly newsletter',
    'rules': 'I agree to the garden rules',
    'day': 'Preferred day for shifts',
}

TREE = [
 node('H1', M),
 node('P_intro', M),
 node('P_name', M, F('name')),        # label text, then its field
 node('P_email', M, F('email')),
 node('P_phone', M, F('phone')),
 node('H2_prefs', M),
 node('P_news', F('newsletter'), M),  # checkbox before its label
 node('P_rules', F('rules'), M),
 node('P_day', M, F('day')),
 node('P_footer', M),
]
