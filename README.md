# pdf-tagger-skill

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) for
tagging existing PDFs for accessibility (PDF/UA-1 / Section 508 / WCAG)
**without changing a single rendered pixel**.

Untagged PDFs are unreadable structure-wise to screen readers: no headings,
no reading order, no table semantics, form fields with no accessible names.
This skill gives Claude a repeatable, verifiable remediation workflow:

- inspection scripts that map a document's text operations, fonts, and form
  fields with exact coordinates;
- a generic tagging engine (`scripts/tag_engine.py`) driven by a small
  per-document config: coordinate bands that classify content, a structure
  tree in reading order, and an accessible name for every field;
- verification that the output renders **pixel-identically** to the input
  (2.5× raster diff, annotations drawn) and is structurally sound (full
  marked-content coverage, ParentTree/OBJR consistency, fonts, metadata);
- a reading-order "readback" that prints the document the way assistive
  technology walks it.

The worked example (`examples/sunflower/`) tags a 2-page bank credit-card
application — 95 AcroForm fields, two disclosure tables, printed checkbox
dingbats — and the result validates as **PDF/UA-1 compliant in
[veraPDF](https://verapdf.org)** with a zero-pixel diff.

## Install

```sh
git clone https://github.com/xrnavigation/pdf-tagger-skill ~/.claude/skills/pdf-tagger
pip install -r ~/.claude/skills/pdf-tagger/requirements.txt
```

Then ask Claude Code to "tag <file>.pdf for accessibility". Claude reads
`SKILL.md` and drives the scripts; the human-facing docs are:

- `SKILL.md` — the workflow and the judgment calls (headings vs. table
  headers, real tables vs. form grids, dingbats, naming fields…)
- `CONFIG.md` — the config file format for the engine
- `examples/sunflower/` — a complete, annotated config

## Requirements

Python 3.11+ with `pikepdf`, `pdfplumber`, `pypdfium2`, `Pillow`.
Optional but recommended: [veraPDF](https://verapdf.org) (Java) for an
independent PDF/UA validation pass.

## Scope and limitations

Born-digital PDFs with text content. Scanned documents need OCR first.
Not yet handled by the engine (it fails loudly rather than guessing):
link annotations, inline images, rotated pages, text inside Form XObjects.
Image XObjects are supported as `Figure` elements with alt text, or as
artifacts when decorative.

## License

MIT — see [LICENSE](LICENSE).
