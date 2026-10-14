# Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Playwright MCP tools fail with `spawn UNKNOWN` / browser not found | MCP server can't launch the system Chrome | Use a Node Playwright script with the **bundled Chromium** (`npx playwright install chromium`), or the host's integrated browser tools |
| Edge/Chrome window closes right at the SSO/ADFS redirect (even non-headless) | Corporate policy / managed browser | Use bundled Chromium; if still failing, `loginInteractive` in a visible browser and let the user finish |
| Integrated-browser screenshot isn't 1920x1080 | Its viewport is host-controlled | Use Playwright with `viewport 1920x1080, deviceScaleFactor 1` and check with `check_manual.py` |
| Microsoft login "Next" button stays disabled after `fill()` | Page needs real key events | `locator.pressSequentially(text, {delay: 40})`, then wait for the button to be enabled |
| Password field selector hits a hidden field | Pages add off-screen `aria-hidden` prefill inputs | Use `input[type=password]:not([aria-hidden="true"])` and `:visible`, wait for the field before reading its rect |
| Role-based `getByRole('button')` doesn't find a button | Button isn't a real `<button>` | Use text locator `getByText(/Search/i)` or a `[title=…]` selector |
| Header text not found | Text is uppercase only via CSS `text-transform` | Case-insensitive regex locator |
| Dialog won't close with Escape | Custom modal | Click its close (X) button; else `page.goto(sameUrl)` |
| Screenshot shows "Loading…" | Captured too early | Wait for loader/spinner to disappear, then `networkidle`, then shot |
| Native `<select>` dropdown not visible in screenshot | OS-rendered popup | Describe options in text (read `option` elements); screenshot the closed control |
| Click on column header toggles sorting twice | Header toggles asc → desc → none | One click per state; verify the arrow icon before shot |
| Blur not applied to an `<input>` | Site CSS overrides filter | Use `mask` mode (Playwright `mask` option) or Pillow `regions` |
| Multi-line text replacement in a script silently does nothing | File has CRLF line endings | Use the editor/`edit` tool, or normalise EOL before replacing |
| Process exits silently with code 0 mid-login | Browser disconnected on redirect | Add `browser.on('disconnected')` logging; try bundled Chromium/headed |
| Numbers in text differ from the live app | Data changes | Don't hard-code counts, or say "for example" |
| Different record shown each run | Data order/volatile | Mask by selector, not by value; pick records by criteria, not position |
