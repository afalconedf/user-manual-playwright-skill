---
name: user-manual-playwright
description: Use when asked to write, update or refresh an end-user manual, user guide or "manuale utente"/"guida utente" for a web application, with screenshots of the UI (sensitive data masked), documentation of what each role sees, and conversion to DOCX from a corporate template. Uses Playwright to drive the app.
---

# user-manual-playwright

Produce a **user manual** for a web application: a Markdown file plus screenshots in a `docs` folder, later converted to **DOCX**. Works on any project; nothing project-specific lives in this skill.

## Hard rules (never break)

1. **Resolution 1920x1080, deviceScaleFactor 1** for every screenshot. Verify it (`python <skill-dir>/scripts/check_manual.py`).
2. **Sensitive data is never visible** in a screenshot (blur or mask). If unsure whether a field is sensitive, **ask the user which** — do not guess, do not skip.
3. **Never write credentials** (passwords, tokens, cookies) in any repo file, log, manual or chat summary. Credentials go only to the browser login form, typed by the user. Auth state files live in `.manual-auth/` (git-ignored).
4. **Ask when in doubt.** Ask the user (`AskUserQuestion` in Claude Code, `ask_user` in Copilot); batch independent questions (up to 4 per call, with choices) instead of one per turn.
5. **Do not invent.** Every button, label, operator and value in the manual must be seen in the live UI/DOM or in the source code. Anything unverified is either removed or asked about.

## Workflow

### 0. Prepare
- Read `LEARNINGS.md` first.
- Check tools: `node -v`, `python --version`. Copy `scripts/` to a work folder **outside the repo docs** (e.g. `%TEMP%\manual-work` or the session `files/` folder) and run `npm install` + `npx playwright install chromium` there. Run the Node capture from that work folder (`.manual-auth/` is created there). Prefer the **bundled Chromium** (it worked where Edge/Chrome and the Playwright MCP server failed — see `references/troubleshooting.md`).
- If a `docs/<manual>/manual.profile.json` already exists, load it (URLs, roles, selectors to mask, template) and ask only what is missing or changed. Otherwise start from `templates/manual.profile.json`.
- Prefer light models for mechanical steps — see [references/cost-policy.md](references/cost-policy.md).

### 1. Discovery questionnaire (ask, don't assume)
Follow [references/discovery.md](references/discovery.md). In short, ask, batching independent questions (up to 4 per call):
1. Application **base URL** and which area/feature(s) the manual covers.
2. **Audience** and language (default: the language of the user's request).
3. **Login method** (SSO/Azure/ADFS/MFA/local form) and **which users/roles** may be used. Ask the user to type the password themselves in a visible browser. Prefer dedicated test users.
4. **Roles that might see different interfaces** (menus, buttons, columns, data scope). Ask for one user per role.
5. **Sensitive data**: show the list of candidate fields you found and ask which to blur/mask; ask about doubtful ones.
6. **Output**: docs folder and manual name (default `docs/<manual-name>/manual.md` + `images/`), and the **DOCX template** (see step 6).
7. Existing manual to update, or new?

Persist the answers (no secrets) in `docs/<manual>/manual.profile.json`.

### 2. Role discovery
Follow [references/discovery.md](references/discovery.md#role-discovery). For each role: log in (separate `storageState` in `.manual-auth/<role>.json`), capture the navigation menu, available pages, buttons and table columns as text, and **diff** against the other roles. If roles differ, ask the user whether each difference must be documented, then:
- add a **"Visibility by role"** matrix to the manual;
- mark role-specific parts with a callout like `> **Role: <name> only**`;
- take extra screenshots only where the screen is materially different (name them `NN-<slug>--<role>.png`).

If roles do not differ, say so in the manual's introduction and capture once.

### 3. Capture screenshots
Use `scripts/capture-lib.js` (viewport 1920x1080, DPR 1, blur/mask helpers, resolution check) via a small project script based on `scripts/capture.example.js`.
- Name images `NN-<slug>.png` in `docs/<manual>/images/`; login screen first (mask the user field).
- Apply masks **by selector/pattern, not by value** (data changes between runs). Re-apply right before each screenshot; wait for loaders ("Loading…", spinners) to disappear first.
- Modals/dialogs: close with their close button (Escape often does nothing); if stuck, `goto` the same URL.
- Read/inspect only: never submit forms, delete, export or save data unless the user explicitly agreed. Do not hard-code numbers such as row counts in the text (they change).
- Details and blur modes: [references/sensitive-data.md](references/sensitive-data.md).

### 4. Write the manual (`manual.md`)
Start from `templates/manual.template.md`. Keep one H1 (title), H2 per chapter, H3 per task. For every screen: purpose, numbered steps, screenshot, **field table** (field · what it represents · where the data comes from · notes). Take field meaning/source from the workspace source (views, config, code) when available; otherwise ask the user — nothing "inferred" stays in the final text.
Include: login chapter, screen overview, role matrix (if relevant), FAQ/troubleshooting, glossary, document version/date.

### 5. Validate
Run `python <skill-dir>/scripts/check_manual.py docs/<manual>/manual.md`: image links exist, every PNG is 1920x1080, no e-mails/credential patterns in the text. Then view 2–3 representative screenshots to confirm masks are effective. Fix and re-run.

### 6. DOCX conversion
Follow [references/docx-conversion.md](references/docx-conversion.md). The `.md` is the source of truth. **Ask the user for the base DOCX/DOTX template** (corporate styles, header/footer, cover). Order of preference:
1. A Copilot/agent docx capability if available in the host (give it the `.md`, the `images/` folder and the template, and ask it to rebuild the structure with the template's styles).
2. `python <skill-dir>/scripts/md_to_docx.py manual.md --template template.docx -o manual.docx` (needs `pip install -r <skill-dir>/scripts/requirements.txt`).
3. `pandoc manual.md -o manual.docx --reference-doc=template.docx` if pandoc exists.

No template available → ask whether to proceed with a neutral default; styles can be swapped later.

### 7. Self-improve (every run)
At the end, review what went wrong or was slow. Append **generic, project-independent** lessons to `LEARNINGS.md` (symptom → cause → fix; no names, URLs, credentials or customer data). Before saving `LEARNINGS.md`, run `rg -n -i "password|token|@|https?://" LEARNINGS.md` (or grep) and remove any hit that is project data. If the skill folder is read-only or a shared install, propose the lesson to the user instead of writing. If a lesson changes how the skill should work, propose the edit to `SKILL.md`/scripts to the user and apply it when approved. Keep `LEARNINGS.md` short: merge duplicates, delete obsolete items.

### 8. Clean up
Delete temp files/snapshots and `.manual-auth/` (saved sessions = credentials) unless the user asks to keep it for a later run. Make sure `.manual-auth/` and `node_modules/` are git-ignored and that `git status` shows only the manual folder (and the profile). Do not commit unless asked.

## Files

| Path | Purpose |
|------|---------|
| `references/discovery.md` | Questionnaire + role discovery procedure |
| `references/sensitive-data.md` | What to mask, blur vs mask, verification |
| `references/docx-conversion.md` | MD → DOCX options and template rules |
| `references/troubleshooting.md` | Login/browser/capture problems and fixes |
| `references/cost-policy.md` | Light-model rules for mechanical steps |
| `scripts/capture-lib.js` | Playwright helpers (1080p, login, masking, shot) |
| `scripts/capture.example.js` | Starting point for a project capture script |
| `scripts/blur_regions.py` | Post-hoc blur/fill of rectangles on a PNG (Pillow) |
| `scripts/check_manual.py` | Validates links, resolution, leaked secrets |
| `scripts/md_to_docx.py` | MD → DOCX using a template (python-docx) |
| `templates/manual.template.md` | Manual skeleton |
| `templates/manual.profile.json` | Per-project profile (no secrets) |
| `LEARNINGS.md` | Accumulated lessons (self-improvement log) |
