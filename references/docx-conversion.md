# Markdown → DOCX

The `.md` (in `docs/<manual>/`, with `images/` next to it) is the source of truth; the `.docx` is regenerated from it. Never edit the `.docx` by hand without back-porting changes to the `.md`.

## 1. Get a template
Ask the user: *"Do you have a base DOCX/DOTX template (cover page, header/footer, styles) I should start from?"*
- Yes → copy it next to the manual (e.g. `docs/<manual>/template.docx`) and record the path in `manual.profile.json`.
- No → ask whether a neutral default is acceptable, or whether they can supply one. Do not invent corporate branding.

Template conventions understood by `md_to_docx.py`:
- Styles used: `Title`, `Heading 1–4`, `Normal`/`Body Text`, `List Bullet`, `List Number`, `Quote` (blockquotes/callouts), `Table Grid` (or any table style given with `--table-style`), `Caption`.
- Missing styles fall back to `Normal`.
- Placeholders replaced in body, headers and footers: `{{TITLE}}`, `{{VERSION}}`, `{{DATE}}`, `{{AUTHOR}}`.
- A paragraph containing only `{{CONTENT}}` marks where the manual body is inserted. Without it, the template body is kept (cover) and the content is appended at the end.

## 2. Convert (in order of preference)
1. **Copilot/agent docx capability** (if the host exposes a docx skill/agent): give it the `.md`, `images/` and the template; ask it to keep the template's styles, header/footer, numbering, to insert images at full text width, and to keep tables as Word tables. Use a light model.
2. **Script**: 
   ```
   pip install -r scripts/requirements.txt
   python scripts/md_to_docx.py docs/<manual>/manual.md --template docs/<manual>/template.docx -o docs/<manual>/manual.docx --title "…" --version 1.0 --toc
   ```
3. **Pandoc** (if installed): `pandoc manual.md -o manual.docx --reference-doc=template.docx --resource-path=.`

## 3. Check the result
- Open/inspect: heading levels, numbered steps, tables, every image present and not wider than the text area, no raw Markdown symbols left, page header/footer from the template.
- Update the TOC field (Word: right-click → Update field) — tell the user, since fields refresh only inside Word.
- Report limits honestly (e.g. nested lists flattened).
