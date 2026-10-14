# LEARNINGS

Self-improvement log. **Read at the start of every run; update at the end.** Entries are generic: no project names, URLs, credentials or customer data. Format: *symptom → cause → fix*. Merge duplicates, drop obsolete entries, promote stable lessons into `SKILL.md`/scripts (with the user's approval).

## Browser & login
- Playwright MCP server fails with `spawn UNKNOWN` → cannot launch system Chrome → use a Node script with bundled Chromium (`npx playwright install chromium`) or the host's integrated browser.
- System Edge/Chrome exit exactly at a federated-SSO (ADFS) redirect → managed-browser policy → bundled Chromium worked.
- SSO "Next" button disabled after `fill()` → needs key events → `pressSequentially`, wait until enabled.
- Password locator picked an off-screen `aria-hidden` field → exclude `[aria-hidden=true]`, wait for the visible field.
- Never keep passwords in scripts/files; pass through session env var in the same command, or let the user type in a visible browser.
- "Stay signed in?" and password-change prompts: dismiss ("No"/skip) unless the user says otherwise.

## Capture
- Default/integrated viewports are not 1080p (e.g. 1452x958, 1141x747) → always `viewport 1920x1080, DPR 1` and validate PNG size.
- Capture before the page finishes loading → wait for loaders/network idle.
- Dialogs: Escape often fails → use the close button, else `goto` same URL.
- Headers uppercased by CSS → match with case-insensitive regex.
- Native `<select>` popups can't be screenshotted → document options as text.
- Sorting header cycles asc → desc → none; count clicks.
- Volatile data (row counts, which record appears) → mask by selector, avoid hard-coded numbers.
- CSS `filter: blur` ignored on some inputs → use Playwright `mask` or Pillow region blur.
- Short numeric strings are recoverable from light blur → use solid mask for IDs/tax codes.

## Writing
- Verify every UI label/operator/URL claim against the live DOM; remove or ask about the rest (a previous draft wrongly claimed the URL changes after filtering).
- Source code/DB views/config in the workspace are the best source for "what is this field and where does it come from".
- If the user doesn't answer a sensitive-data question, stay conservative: mask and record the open decision.

## Tooling
- Multi-line string replacement in PowerShell fails silently on CRLF files → use the editor tool.
- DOCX: keep `.md` as source of truth; regenerate rather than editing the DOCX.
