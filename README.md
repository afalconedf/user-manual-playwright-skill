# user-manual-playwright

Agent skill (GitHub Copilot / Claude-style `SKILL.md`) that writes **end-user manuals** for any web application using Playwright, for teams that support customers.

- 1920×1080 screenshots, sensitive data **blurred/masked** (asks which data when unsure)
- Asks for URL, users and roles; detects whether roles see different interfaces and documents it
- Output: `docs/<manual>/manual.md` + `images/`, then converted to **DOCX** from a template
- Designed for **light models** to save credits
- **Self-improving**: lessons go to [LEARNINGS.md](skills/user-manual-playwright/LEARNINGS.md); project-agnostic (per-project data lives in `manual.profile.json`)

(IT) Skill per redigere manuali utente di applicazioni web con Playwright: screenshot 1920×1080, dati sensibili sfocati, domande su URL/utenti/ruoli, manuale in `.md` + immagini convertito in DOCX da template.

## Install as plugin (VS Code)

**Claude Code** (extension or terminal):

```
/plugin marketplace add afalconedf/user-manual-playwright-skill
/plugin install user-manual-playwright@user-manual-playwright
```

**GitHub Copilot in VS Code** (agent plugins): add the repo to the `chat.plugins.marketplaces` setting, then install it from the Extensions view (`@agentPlugins`).

Local test without publishing: `/plugin marketplace add <path-to-this-repo>`.

## Install as plain skill

Copy `skills/user-manual-playwright/` into the project (or user) skills location:

| Where | Path |
|-------|------|
| Project (Copilot) | `.github/skills/user-manual-playwright/` |
| Personal (Copilot) | `~/.copilot/skills/user-manual-playwright/` |
| Claude-style | `.claude/skills/user-manual-playwright/` |

Then ask the agent e.g. *"Write the user manual for <URL>, use the user-manual-playwright skill"*.

Requirements: Node 18+, Python 3.9+, `pip install -r scripts/requirements.txt`, `npm install && npx playwright install chromium` in the scripts folder (copied to a work dir).

## Suggested `.gitignore` in projects using it

```
.manual-auth/
node_modules/
```

## Layout

See the table in [SKILL.md](skills/user-manual-playwright/SKILL.md#files).
