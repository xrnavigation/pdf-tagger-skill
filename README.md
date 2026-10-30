# pdf-tagger-skill

An [Agent Skills](https://agentskills.io) package for Claude Code, Codex, and Antigravity,
for
tagging existing PDFs for accessibility (PDF/UA-1 / Section 508 / WCAG)
**without changing a single rendered pixel**.

Untagged PDFs are unreadable structure-wise to screen readers: no headings,
no reading order, no table semantics, form fields with no accessible names.
This skill gives an agent a repeatable, verifiable remediation workflow:

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

Two self-contained examples ship with committed inputs, generators, and
configs: `examples/report/` (headings plus a data table with column headers)
and `examples/form/` (an AcroForm with named, tooltipped fields). Both tag to
a zero-pixel diff and validate as **PDF/UA-1 compliant in
[veraPDF](https://verapdf.org)**. The engine was developed against a
real-world two-page banking application form — 95 AcroForm fields, two
disclosure tables, printed checkbox dingbats — with the same results.

## Install

The repository root is the `pdf-tagger` skill. Install the entire repository so
`scripts/`, `CONFIG.md`, requirements, and examples remain beside `SKILL.md`.
It is not a plugin marketplace.

### Claude Code

```sh
git clone https://github.com/xrnavigation/pdf-tagger-skill ~/.claude/skills/pdf-tagger
python -m pip install -r ~/.claude/skills/pdf-tagger/requirements.txt
```

Invoke `/pdf-tagger`, or ask Claude Code to "tag <file>.pdf for accessibility". Claude reads
`SKILL.md` and drives the scripts; the human-facing docs are:

- `SKILL.md` — the workflow and the judgment calls (headings vs. table
  headers, real tables vs. form grids, dingbats, naming fields…)
- `CONFIG.md` — the config file format for the engine
- `examples/sunflower/` — a complete, annotated config

### Codex and Antigravity

Use the same clone and dependency-installation commands above, replacing both
installation paths with your host's destination:

| Host | User-wide destination |
| --- | --- |
| Codex | `~/.agents/skills/pdf-tagger` |
| Antigravity App and IDE | `~/.gemini/config/skills/pdf-tagger` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/pdf-tagger` |

For project scope, use `.agents/skills/pdf-tagger` with Codex or Antigravity,
or `.claude/skills/pdf-tagger` with Claude Code. In PowerShell, use `$HOME`
when a program does not expand `~`. Install dependencies in the Python
environment the agent will actually run. Do not overwrite an existing install.

Ask Codex to use `$pdf-tagger`; invoke `/pdf-tagger` in Antigravity. Confirm
the host discovers the skill before starting a PDF task. These are direct skill
installations; the workflow was not executed on each host during this documentation update.

Sources: [Claude skills](https://code.claude.com/docs/en/skills),
[Codex skill discovery](https://learn.chatgpt.com/docs/build-skills), and
[Antigravity skill locations](https://antigravity.google/docs/skills).

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
