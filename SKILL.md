---
name: pdf-tagger
description: Tag an existing PDF for accessibility (PDF/UA-1, Section 508, WCAG) while keeping it pixel-identical to the original. Use when asked to "tag a PDF", "make a PDF accessible", "remediate a PDF", "add accessibility tags / a structure tree", "make a PDF screen-reader friendly", "add tooltips to PDF form fields", or to make a PDF "508 compliant" / "PDF/UA compliant". Builds headings, paragraphs, tables, artifacts, and Form elements with accessible names for every field; sets title/language metadata; verifies output renders pixel-identically and passes veraPDF PDF/UA validation.
---

# PDF accessibility tagging

Add a full logical structure tree to an untagged PDF **without changing a
single rendered pixel**. The deliverable is a new file next to the original
(never overwrite the original without being asked).

All scripts live in `scripts/` relative to this skill. They need Python 3.11+
with `pikepdf`, `pdfplumber`, `pypdfium2`, `Pillow`
(`pip install -r requirements.txt`). A worked example (2-page bank form,
95 fields, two disclosure tables → veraPDF PDF/UA-1 PASS) is in
`examples/sunflower/config.py` — skim it before writing your first config.

## How it works

`scripts/tag_engine.py` is a generic engine. You author one **per-document
config** (a Python file, format in `CONFIG.md`) that supplies the three things
that are always document-specific:

1. **BANDS** — y/x coordinate rules that classify every text operation into a
   named element (`H1`, `H2_company`, `P_privacy`, `TH_apr`, `TD_apr`, …).
2. **TREE** — the structure tree in reading order, interleaving each form
   field (`F('field name')`) after its visible label.
3. **TU** — an accessible name for every form field.

The engine wraps every content op in marked content (MCIDs or `/Artifact`),
builds the structure tree + ParentTree, sets `/TU`, `/Tabs /S`, MarkInfo,
title, `DisplayDocTitle`, `Lang`, strips broken `/CIDSet`s, and claims
PDF/UA-1 in XMP. It fails loudly (with page/y/x/text) on anything
unclassified, so you iterate on the config until it runs clean.

## Workflow

### 1. Inspect — before deciding anything

```
python scripts/inspect_pdf.py in.pdf     # pages, tags?, fields+rects, op histogram
python scripts/textdump.py in.pdf        # visual lines with fonts/sizes
python scripts/opdump.py in.pdf > ops.txt  # per-op y/x — the band coordinates
```

**Probe the real file before encoding heuristics.** Do not assume
"10pt bold = heading": in the example document, 10pt bold is used both for
section headings (H2) and for table row headers (TH) inside a disclosure box.
Classify from the actual layout, item by item. Bands must come from
`opdump.py` values (engine-identical math), not from pdfplumber's `top`.

If the PDF is scanned (no text ops), stop: it needs OCR first, not tagging.
If it already has a StructTreeRoot, ask before replacing it.

### 2. Author the config

Read `CONFIG.md` for the format. Judgment calls that recur:

- **Headings**: one H1 (the document title); sections H2; never skip levels.
- **Real tables vs. form grids**: tag genuine static tables (e.g. credit-card
  "Schumer boxes") as `Table/TR/TH/TD` with `Scope` (and `ColSpan` for banner
  rows). Fillable label-over-field grids read better as flow: label line as
  `P`, then the fields — the `/TU` names carry the semantics. A malformed
  table is worse than none.
- **TU naming**: prefix group context so fields are unambiguous out of
  context: "Cardholder 2: last name", "Trade reference 3: account number".
  Fix misleading generic names ("Check Box 7" → "Business type: Other").
- **Printed checkbox glyphs** (ZapfDingbats etc.) that duplicate an
  interactive widget → artifact (`ARTIFACT_TEXT` hook). Watch out: the same
  font name can be a dingbat on one page and body text on another.
- **Print-only checkboxes** (no widget) are content; if their ToUnicode is
  garbage (e.g. maps to "r"), override with `ACTUALTEXT` returning "☐".
- **Standalone underscore runs** under a field are decorative → artifact or
  leave as content; underscores inside longer label strings stay.
- **Reading order** is yours to choose where columns interleave; pick what a
  human would read aloud. Within an element the engine auto-sorts runs by
  line/x.

### 3. Tag and iterate

```
python scripts/tag_engine.py config.py in.pdf out.pdf
```

Errors are designed for iteration: `UNCLASSIFIED op page N y=.. x=..` →
add/fix a band; `unowned MCIDs` → an element produced more runs than your
`MC(i)` spec, use `REST` or `M`; missing `TU` entries are listed by name.

### 4. Verify — all three, every time

```
python scripts/verify.py in.pdf out.pdf    # must end ALL CHECKS PASSED
python scripts/readback.py out.pdf         # eyeball reading order, headings,
                                           # table cells, field names
```

`verify.py` renders both files at 2.5× with annotations and requires **zero**
pixel difference, plus full structural audit (coverage, nesting, ParentTree,
OBJR backlinks, fonts, metadata). `readback.py` is the screen-reader's-eye
view: read it top to bottom and fix anything that sounds wrong.

If veraPDF is available (Java tool, https://verapdf.org), run
`verapdf --flavour ua1 out.pdf` — target: PASS. Only ship the `pdfuaid:part`
claim (config `PDFUA = True`) when it passes or you've audited equivalent
rules yourself.

### 5. Deliver

Save as `<original name> (tagged).pdf` beside the original and report: what
was tagged, judgment calls made, verification results, and anything left
undone (e.g. questions that have no interactive fields — adding fields
changes the form, so offer it, don't do it unasked).

## Engine limitations (fail loudly, handle manually)

- Link annotations (needs `Link` elements) — engine refuses unless
  `SKIP_NON_WIDGET_ANNOTS = True`.
- Inline images (`BI`), page `/Rotate`, text inside Form XObjects.
- Image XObjects are supported via `Figure_*` band keys + `ALT` map
  (`Do` ops classify by position like text; decorative images → `'ART'`).
- Lists (`L/LI`) aren't auto-built; numbered paragraphs as `P` are acceptable.
