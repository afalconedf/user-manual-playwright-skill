# Cost policy (light models)

Most of the work is mechanical (navigate, click, screenshot, convert). Keep credits low:

- Run discovery, capture, link checking and DOCX conversion with the **cheapest model that can use tools** (small/"mini"/"haiku"-class). If the host lets you pick a model for sub-agents (`task` agents, background agents), pick the light one **only when the user has allowed it**; otherwise just stay on the current model.
- Use a stronger model only for: resolving real ambiguity, writing the explanatory text of complex fields, final review.
- Save tokens: prefer DOM/snapshot queries over viewing images; view at most a few key screenshots per run (e.g. one per section) and rely on `check_manual.py` for the rest; never paste full DOM dumps into context — save them to a temp file and `grep` them.
- Do the scripted capture in **one Node run**, not one tool call per click.
