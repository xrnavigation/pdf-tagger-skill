# Worked example: Sunflower Bank Visa Business Card Credit Application

Source: the bank's public fillable application form, `Sunflower Bank Business
CC App 02.2026.pdf` (2 pages, InDesign 20.5 output, 95 merged field+widget
AcroForm fields, completely untagged). The PDF itself is not redistributed
here; `config.py` is the complete tagging config that was applied to it.

Result: zero-pixel render diff against the original; veraPDF reports
**PDF/UA-1 compliant**.

## Decisions worth copying

- **H1** = the two-line product title (12pt bold runs + a 7pt `®`); **H2** =
  the eight 10pt-bold section headings. But the 10pt-bold row labels inside
  the "Interest Rates" disclosure box are **TH cells, not headings** — same
  font, different role. Classify by layout, not by size.
- The two credit-card **"Schumer boxes"** are genuine 2-column tables →
  `Table/TR/TH/TD`, left column `Scope=Row`, full-width banner rows
  (`Fees`, `Transaction Fees`, …) as `TH` with `ColSpan=2`
  (`Scope=Column` for the table title row, `Both` for group banners).
- The **fillable grids** (company info, cardholders, trade references) are
  *not* tagged as tables: label line as `P`, fields right after, with
  group-prefixed `/TU` names ("Cardholder 2: last name"). The original
  field names were unusable ("Check Box 7" → "Business type: Other"; row 2's
  credit-limit field is literally named `1 Bus CC Credit 1` in the source —
  its TU says "Cardholder 2: credit limit").
- **Page-1 ZapfDingbats squares** sit under real widget checkboxes →
  artifacts (`ARTIFACT_TEXT`). The same ZapfDingbats squares on **page 2's
  Customer Diligence questions have no widgets** — they're real content, but
  their ToUnicode maps the box glyph to the letter "r", so each gets an
  ActualText override of `☐` (U+2610).
- InDesign emitted `Span` marked-content pairs with `ActualText` tab
  characters between labels; the engine preserves them nested inside the
  owning element's MCID.
- The embedded CID fonts carried incomplete `/CIDSet` streams — the single
  veraPDF failure on the first pass. `REMOVE_CIDSET = True` fixed it
  (CIDSet is optional metadata; removal cannot affect rendering).
- Left undone on purpose: the three Customer Diligence yes/no questions have
  no interactive fields in the original. Adding checkboxes would change the
  form's behavior, so it was offered to the owner rather than done.
