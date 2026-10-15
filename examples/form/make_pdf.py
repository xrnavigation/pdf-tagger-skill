#!/usr/bin/env python3
"""Generate the untagged example form (examples/form/input.pdf).

A one-page sign-up form: reportlab draws the static text (embedded TTF),
then pikepdf adds an AcroForm with four text fields and two checkboxes whose
appearance streams are pure vector paths (no fonts), keeping the file clean
for PDF/UA font checks.

Usage: python make_pdf.py [out.pdf]
"""
import io
import os
import sys

import pikepdf
from pikepdf import Array, Dictionary, Name, String
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

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
W, H = letter


def at(y_top):               # top-based y -> PDF baseline y
    return H - y_top

buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=letter)
c.setFont('Bold', 16); c.drawString(72, at(80), 'Volunteer Sign-Up')
c.setFont('Body', 10)
c.drawString(72, at(108), 'Join the community garden for the coming season.')
c.drawString(72, at(122), 'We will only use your details to coordinate shifts.')
c.drawString(72, at(160), 'Full name')
c.drawString(72, at(210), 'Email')
c.drawString(72, at(260), 'Phone')
c.setFont('Bold', 13); c.drawString(72, at(320), 'Preferences')
c.setFont('Body', 10)
c.drawString(92, at(352), 'Subscribe to the monthly newsletter')
c.drawString(92, at(380), 'I agree to the garden rules')
c.drawString(72, at(420), 'Preferred day for shifts')
c.setFont('Body', 8)
c.drawString(72, at(470), 'Return this form to the shed mailbox, or hand it '
                          'to any committee member.')
c.save()
pdf = pikepdf.open(buf)
page = pdf.pages[0]


def ap_stream(w, h, extra=b''):
    xo = pdf.make_stream(b'0 G 0.75 w 0.4 0.4 %.1f %.1f re S\n' %
                         (w - 0.8, h - 0.8) + extra)
    xo[Name('/Type')] = Name('/XObject')
    xo[Name('/Subtype')] = Name('/Form')
    xo[Name('/BBox')] = Array([0, 0, w, h])
    xo[Name('/Resources')] = Dictionary()
    return xo


def rect(x0, ytop, x1, ybot):
    return Array([x0, H - ybot, x1, H - ytop])


fields = []

def textfield(name, x0, ytop, x1, ybot):
    w, h = x1 - x0, ybot - ytop
    f = pdf.make_indirect(Dictionary(
        Type=Name('/Annot'), Subtype=Name('/Widget'), FT=Name('/Tx'),
        T=String(name), V=String(''), F=4, Rect=rect(x0, ytop, x1, ybot),
        DA=String('/Helv 10 Tf 0 g'),
        AP=Dictionary(N=ap_stream(w, h))))
    page[Name('/Annots')] = Array(
        list(page.get('/Annots', [])) + [f])
    fields.append(f)

def checkbox(name, x0, ytop):
    s = 12.0
    off = ap_stream(s, s)
    yes = ap_stream(s, s, b'1.2 w 2.5 2.5 m 9.5 9.5 l S 2.5 9.5 m 9.5 2.5 l S\n')
    f = pdf.make_indirect(Dictionary(
        Type=Name('/Annot'), Subtype=Name('/Widget'), FT=Name('/Btn'),
        T=String(name), V=Name('/Off'), AS=Name('/Off'), F=4,
        Rect=rect(x0, ytop, x0 + s, ytop + s),
        AP=Dictionary(N=Dictionary(Off=off, Yes=yes))))
    page[Name('/Annots')] = Array(list(page.get('/Annots', [])) + [f])
    fields.append(f)


textfield('name', 72, 168, 320, 186)
textfield('email', 72, 218, 320, 236)
textfield('phone', 72, 268, 320, 286)
checkbox('newsletter', 72, 342)
checkbox('rules', 72, 370)
textfield('day', 72, 428, 320, 446)

helv = pdf.make_indirect(Dictionary(
    Type=Name('/Font'), Subtype=Name('/Type1'),
    BaseFont=Name('/Helvetica'), Encoding=Name('/WinAnsiEncoding')))
pdf.Root[Name('/AcroForm')] = pdf.make_indirect(Dictionary(
    Fields=Array(fields), DA=String('/Helv 0 Tf 0 g'),
    DR=Dictionary(Font=Dictionary(Helv=helv))))

pdf.save(out)
print('wrote', out)
