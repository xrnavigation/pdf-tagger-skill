#!/usr/bin/env python3
"""Generate the untagged example report (examples/report/input.pdf).

A one-page report with a title, two sections, and a bordered data table —
built with reportlab/platypus, so text objects sit inside q/Q graphics
states and the table rules are plain path artifacts. Fonts are embedded
(a PDF/UA requirement), so point --font/--bold at any TTF pair if the
defaults aren't on your system.

Usage: python make_pdf.py [out.pdf]
"""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)

CANDIDATES = {
    'Body': ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             '/mnt/c/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arial.ttf',
             '/Library/Fonts/Arial.ttf'],
    'Bold': ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             '/mnt/c/Windows/Fonts/arialbd.ttf',
             'C:/Windows/Fonts/arialbd.ttf', '/Library/Fonts/Arial Bold.ttf'],
}
for name, paths in CANDIDATES.items():
    path = next((p for p in paths if os.path.exists(p)), None)
    if path is None:
        raise SystemExit(f'no TTF found for {name}; edit CANDIDATES')
    pdfmetrics.registerFont(TTFont(name, path))

out = sys.argv[1] if len(sys.argv) > 1 else 'input.pdf'
doc = SimpleDocTemplate(out, pagesize=letter,
                        leftMargin=inch, rightMargin=inch,
                        topMargin=inch, bottomMargin=inch)
h1 = ParagraphStyle('h1', fontName='Bold', fontSize=18, leading=22,
                    spaceAfter=10)
h2 = ParagraphStyle('h2', fontName='Bold', fontSize=13, leading=16,
                    spaceBefore=14, spaceAfter=6)
body = ParagraphStyle('body', fontName='Body', fontSize=10, leading=14,
                      spaceAfter=6)
small = ParagraphStyle('small', fontName='Body', fontSize=8, leading=10,
                       spaceBefore=18)

tbl = Table(
    [['Crop', 'Beds', 'Yield (kg)'],
     ['Tomatoes', '4', '118'],
     ['Carrots', '2', '40'],
     ['Kale', '3', '31']],
    colWidths=[2.2 * inch, 1.1 * inch, 1.4 * inch])
tbl.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, 0), 'Bold'),
    ('FONTNAME', (0, 1), (-1, -1), 'Body'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
]))

doc.build([
    Paragraph('Community Garden Annual Report', h1),
    Paragraph('The garden completed its third season with twelve active '
              'beds and a volunteer roster of twenty-two members. This '
              'report summarizes the harvest and the plans agreed at the '
              'October meeting.', body),
    Paragraph('Harvest Summary', h2),
    Paragraph('Three crops accounted for most of the season\u2019s output. '
              'Totals below are weighed at collection and rounded to the '
              'nearest kilogram.', body),
    Spacer(1, 4),
    tbl,
    Paragraph('Plans for Next Season', h2),
    Paragraph('The committee voted to add two raised beds, trial a shared '
              'compost rota, and move the tool shed closer to the water '
              'point before planting resumes in March.', body),
    Paragraph('Prepared by the volunteer committee. Questions to the '
              'noticeboard, please.', small),
])
print('wrote', out)
