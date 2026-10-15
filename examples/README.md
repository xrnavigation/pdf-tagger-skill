# Examples

Two small, fully self-contained examples. Each directory has:

- `make_pdf.py` — regenerates the untagged `input.pdf` (committed, so you
  don't need reportlab or the fonts to try the engine)
- `config.py` — the tagging config for that document
- `NOTES.md` — what the example demonstrates

Run one:

```sh
cd examples/report        # or examples/form
python ../../scripts/tag_engine.py config.py input.pdf tagged.pdf
python ../../scripts/verify.py input.pdf tagged.pdf
python ../../scripts/readback.py tagged.pdf
```

Expected: `verify.py` ends with `ALL CHECKS PASSED` (including a zero-pixel
render diff), and `verapdf --flavour ua1 tagged.pdf` reports PASS.

If you edit a `make_pdf.py`, regenerate `input.pdf` and re-derive the
config's band coordinates from `python ../../scripts/opdump.py input.pdf` —
the numbers are document-specific by design.

- **report/** — headings, paragraphs, and a real data table with `TH` column
  headers; the table's grid rules become artifacts; text objects live inside
  `q/Q` graphics states (platypus output).
- **form/** — an AcroForm: `Form` structure elements with OBJR for every
  widget, `/TU` accessible names, and reading-order interleaving (text field
  after its label, checkbox before its label).
