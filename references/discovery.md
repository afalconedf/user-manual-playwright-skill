# Discovery

Ask with `ask_user`, **one question at a time**, choices when possible. Skip what `manual.profile.json` already answers. Never ask the user to paste a password in chat if they can type it in the browser.

## Questionnaire

| # | Question | Notes |
|---|----------|-------|
| 1 | Base URL of the application (and any start page)? | Test/UAT preferred over production |
| 2 | Which area/feature/report must the manual cover? | If unsure, crawl the menu and offer a list |
| 3 | Audience and manual language? | e.g. customer-facing support team, key users |
| 4 | How do users log in? | local form / Azure AD / ADFS / other SSO; MFA? password-change prompts? |
| 5 | Which user(s) may I use, and which role does each have? | One per role; dedicated test users; never store passwords |
| 6 | Do different roles see different screens (menus, buttons, columns, data)? | If "don't know" → run role discovery |
| 7 | Which data is sensitive? | Present detected candidates (see below) and ask |
| 8 | Docs folder / manual name? DOCX template? | default `docs/<manual-name>/` |
| 9 | May I run actions that change data (save, export, delete)? | Default: **no** |

### Credentials handling
Preferred order:
1. **Visible browser, user types credentials** (`loginInteractive` in `capture-lib.js`), session stored in `.manual-auth/<role>.json`.
2. Session-only env vars (`MANUAL_USER`, `MANUAL_PWD`) set in the same shell command that runs the script and removed afterwards. Never echo them, never log them, never put them in a file.
3. If the user already pasted credentials in chat: use them only in the login form, never repeat them in files or summaries, and suggest rotating them.

If login asks for a password change or "stay signed in?": ask the user; default is to dismiss/skip and answer "No".

## Role discovery

Goal: know if different users/roles see different interfaces, and whether that must be traced in the manual.

1. For each role/user given: log in with its own `storageState`.
2. Extract, as text (not screenshots): navigation menu entries, page titles reachable from the menu, toolbar/button labels on the main pages, table column headers, filter fields, and any "access denied"/hidden sections. Helper: `collectUiInventory(page)` in `capture-lib.js` → JSON per role in the work folder.
3. Diff the inventories (`diff` or a small script). Classify differences: **menu/page visibility**, **actions (buttons)**, **columns/fields**, **data scope** (different row counts or filters).
4. Present the diff to the user and ask: *which differences must be documented, and for which audience?*
5. Outcome in the manual:
   - identical → one sentence in the introduction ("the interface is the same for all roles");
   - different → "Visibility by role" matrix (rows = functions/fields, columns = roles, ✔/✖), role callouts in the text, role-specific screenshots only where the screen really differs.
6. Record roles in `manual.profile.json` (role name, description, auth state file name — no passwords).

If only one user is available, state clearly in the manual which role the screenshots were taken with, and ask whether other roles exist and should be covered later.

## Sensitive-data candidates
Scan the inventory for: person names, e-mails, phones, tax/VAT/fiscal codes, IBAN, addresses, third-party company names (customers/suppliers), internal IDs, order/invoice/contract numbers, amounts/prices if confidential, tokens or URLs with tokens, the logged-in user's name/avatar/e-mail in headers, dates of birth. Ask the user to confirm the list; unknown → ask.
