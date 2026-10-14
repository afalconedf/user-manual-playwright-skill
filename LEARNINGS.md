# LEARNINGS

Self-improvement log. **Read at the start of every run; update at the end.** Entries are generic: no project names, URLs, credentials or customer data. Format: *symptom → cause → fix*. Merge duplicates, drop obsolete entries, promote stable lessons into `SKILL.md`/scripts (with the user's approval). Lessons are promoted to `references/troubleshooting.md` once stable.

## Browser & login
- Never keep passwords in scripts/files; let the user type them in a visible browser.
- "Stay signed in?" and password-change prompts: dismiss ("No"/skip) unless the user says otherwise.

## Capture
- Short numeric strings are recoverable from light blur → use solid mask for IDs/tax codes.

## Writing
- Verify every UI label/operator/URL claim against the live DOM; remove or ask about the rest (a previous draft wrongly claimed the URL changes after filtering).
- Source code/DB views/config in the workspace are the best source for "what is this field and where does it come from".
- If the user doesn't answer a sensitive-data question, stay conservative: mask and record the open decision.

## Tooling
- DOCX: keep `.md` as source of truth; regenerate rather than editing the DOCX.
