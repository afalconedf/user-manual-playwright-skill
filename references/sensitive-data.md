# Sensitive data in screenshots

## Principle
A screenshot must be safe to send to a customer. Mask **by selector or text pattern**, never by literal value, because data changes between runs and the manual is regenerated.

## Decide what to mask
1. Build the list from `references/discovery.md` candidates.
2. Ask the user to confirm; ask about anything doubtful. When in doubt during a run, **mask first, ask after**, then adjust.
3. Store the decisions in `manual.profile.json` → `sensitive.selectors`, `sensitive.textPatterns`, `sensitive.regions`.

## Modes
| Mode | How | Use for |
|------|-----|---------|
| `blur` (default) | CSS `filter: blur(Npx)` (+ transparent text with shadow for inputs), N ≥ 8 | Names, company names, ids in tables and modals |
| `mask` | Playwright screenshot `mask` option → solid colour box | Very short or high-risk values (tax ids, IBAN, e-mails, user name/avatar, tokens) — short digit strings can be recovered from light blur |
| `regions` | Pillow on the final PNG (`scripts/blur_regions.py`) | Elements that resist CSS (embedded/ADFS-style login fields, canvas, iframes) |

Hints:
- A table: mask the whole **column** (`td:nth-child(n)`) rather than cell values; mask the same columns inside modals/detail tables.
- Free text: use `textPatterns` (regex) for e-mails, tax ids, IBAN, `\b\d{8,}\b`-like numbers; they wrap matching text nodes.
- `textPatterns` only wraps text nodes: it does not reach `<input>`/`<textarea>` values, `<option>` text, `title` tooltips, iframes or shadow DOM — cover those with `maskSelectors` (or `regions`).
- The logged-in user's name/e-mail in the header or profile menu is sensitive too.
- Login screens: show them, but mask the user/e-mail field and any prefilled value; never type the password before the screenshot.
- Re-apply masks right before each screenshot (modals and lazy tables add new nodes). `shot()` in `capture-lib.js` does this.

## Verify
- Run the capture, then **view at least the screenshots with tables/modals** and check there is no readable value.
- Run `python scripts/check_manual.py` (text-level leak check on the `.md`).
- If a new screen appears later in the manual, repeat the question "is anything here sensitive?".
- Never keep unmasked originals inside the repo; if the user wants them, keep outside (session `files/` folder) and say so.
