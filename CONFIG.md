# Tagging config reference

A config is a Python file loaded by `scripts/tag_engine.py`. It imports the
tree helpers from the engine:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                'path', 'to', 'scripts'))
from tag_engine import node, table, tr, th, F, M, MC, REST
```

(`examples/sunflower/config.py` is a complete working example.)

## Required names

### `TITLE: str`
Document title, written to XMP `dc:title` and docinfo. Shown in the window
title bar because the engine also sets `DisplayDocTitle`.

### `BANDS: dict[int, list]`
Per page (0-based), a list of bands:

```python
BANDS = {0: [ (ymin, ymax, [(xlimit, key), ..., (None, key)]), ... ]}
```

Every text op (and `Do` op) gets a position from the same interpreter as
`scripts/opdump.py`: `y` = distance from page top at the line origin
(baseline), `x` = line-start x. The first band with `ymin <= y < ymax` wins;
inside it, the first rule with `x < xlimit` (or the final `(None, key)`
catch-all) gives the element key.

- `key` is an element key (below), `'ART'` (artifact), or `None`
  ("nothing expected here" — the engine errors if content shows up, which is
  what you want while iterating).
- Bands are checked in list order; keep them non-overlapping.
- Any op not matched by any band is a hard error naming page/y/x/text.

**Element keys** encode their structure type as the prefix before the first
`_`: `H1`, `H2_company`, `P_privacy`, `TH_apr`, `TD_apr`, `Span_x`,
`Figure_logo`, `Caption_t1`… Allowed types: H1–H6, P, TH, TD, Span, Caption,
Figure, L, LI, Lbl, LBody, BlockQuote, Note, Code, Quote, Reference, Formula,
Index, TOC, TOCI, Sect, Div, Art, Part. One element may collect many runs
from anywhere on **one** page; the engine orders them by line, then x.

### `TREE: list`
The document's children in reading order. Builders:

- `node(key, *kids, **attrs)` — kids are `M`, `REST`, `MC(i)`, `F(name)`, or
  nested nodes.
  - `M` — all of this element's MCIDs (reading order). Safe default.
  - `MC(i)` — the i-th MCID only (after reading-order sort); for interleaving
    fields between specific runs, e.g.
    `node('P_choose', MC(0), F('Check Box 8'), MC(1), F('Check Box 9'), MC(2))`.
  - `REST` — every not-yet-consumed MCID; use when a line unexpectedly splits
    into extra runs (tab spans, text-object boundaries).
  - `F('fully qualified field name')` — wraps that widget in a `Form` element
    with an OBJR. Every widget must appear exactly once across the TREE.
- `table(key, *rows)`, `tr(key, *cells)`,
  `th(key, scope, colspan=None, rowspan=None)` — scope is `'Row'`,
  `'Column'`, or `'Both'`. Give banner rows that span the table
  `colspan=<n>` so row widths stay regular.

Field names are the fully qualified AcroForm names (`parent.kid`); for
merged field+widget dictionaries that's just `/T`. `inspect_pdf.py` prints
them exactly as the engine expects.

### `TU: dict[str, str]`
Accessible name for **every** widget, keyed by the same names. Missing
entries are a hard error listing the names.

## Optional names

- `LANG = 'en-US'` — written to the catalog only if it has no `/Lang`.
- `PDFUA = True` — write `pdfuaid:part = 1` to XMP. Set `False` until the
  output actually validates.
- `REMOVE_CIDSET = True` — strip `/CIDSet` from embedded CID font
  descriptors (they're optional, routinely incomplete, and fail PDF/UA rule
  7.21.4.2; removal never affects rendering).
- `ARTIFACT_TEXT(pageno, y, x, font) -> bool` — force specific text ops to
  artifact before band lookup (e.g. dingbat glyphs duplicating widget
  checkboxes). Scope rules per page: font names are reused with different
  meanings across pages.
- `ACTUALTEXT(pageno, y, x, font, label) -> str | None` — wrap a single text
  op in its own `Span` MCID (owned by `label`'s element) carrying ActualText,
  e.g. return `'☐'` for a print-only checkbox glyph whose ToUnicode is
  wrong.
- `ALT: dict[key, str]` — alt text for each `Figure_*` key (required per
  Figure).
- `SKIP_NON_WIDGET_ANNOTS = False` — the engine refuses pages with
  non-widget annotations (e.g. Links, which would need `Link` elements);
  set True only if you've handled them some other way.

## What the engine guarantees / checks

- Visuals untouched: it only inserts `BDC/EMC` (never rendered) and rebuilds
  the content stream losslessly. Confirm with `verify.py` (zero-pixel diff).
- Marked content properly nested w.r.t. `BT/ET`; existing marked-content
  spans (e.g. InDesign tab `ActualText` spans) are preserved and absorbed
  into the surrounding element.
- Hard errors: unclassified ops, unbalanced pairs, elements spanning pages,
  MCIDs not consumed by the TREE, elements with content missing from TREE,
  fields missing TU, fields referenced twice or never, unknown structure
  types, heading-level jumps (warning).
