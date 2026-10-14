'use strict';
// Example project capture script. Copy to the work folder and adapt; do not commit credentials.
// Usage:  node capture.example.js docs/<manual>/manual.profile.json <role>
const fs = require('fs');
const path = require('path');
const lib = require('./capture-lib');

// Saved session still valid? Loads the app and checks the logged-in marker (selector, else URL).
async function isLoggedIn(page, profile) {
  await page.goto(profile.baseUrl);
  await page.waitForLoadState('load');
  if (!profile.loginSuccessSelector) return new RegExp(profile.loginSuccessUrl).test(page.url());
  return page.locator(profile.loginSuccessSelector).first()
    .waitFor({ state: 'visible', timeout: 15000 }).then(() => true, () => false);
}

(async () => {
  const profile = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const role = process.argv[3] || profile.roles[0].name;
  const roleCfg = profile.roles.find((r) => r.name === role);
  const stateFile = path.resolve('.manual-auth', `${roleCfg.authState || role}.json`);
  const outDir = path.resolve(path.dirname(process.argv[2]), 'images');
  const sensitive = profile.sensitive;

  let interactive = !fs.existsSync(stateFile);
  let { browser, context, page } = await lib.launch({ headless: !interactive, storageState: stateFile });
  try {
    if (!interactive && !(await isLoggedIn(page, profile))) {
      console.error('[login] saved session expired, logging in again');
      fs.rmSync(stateFile);
      await browser.close();
      interactive = true;
      ({ browser, context, page } = await lib.launch({ headless: false }));
    }
    if (interactive) {
      // login screen: capture first (user field masked), then let the user log in
      await page.goto(profile.baseUrl);
      await lib.shot(page, outDir, '00-login', { sensitive });
      await lib.loginInteractive(page, context, {
        startUrl: profile.baseUrl,
        successUrl: new RegExp(profile.loginSuccessUrl),
        successSelector: profile.loginSuccessSelector,
        stateFile,
      });
    }

    for (const [i, step] of profile.steps.entries()) {
      await page.goto(new URL(step.path, profile.baseUrl).href);
      for (const a of step.actions || []) {
        // read-only interactions only: open panels, apply filters, open details
        if (a.click) await page.locator(a.click).first().click();
        if (a.text) await page.getByText(new RegExp(a.text, 'i')).first().click();
      }
      const name = `${String(i + 1).padStart(2, '0')}-${step.slug}${role === profile.roles[0].name ? '' : `--${role}`}`;
      await lib.shot(page, outDir, name, { sensitive });
    }
    console.log(JSON.stringify(await lib.collectUiInventory(page), null, 2));
  } finally {
    await browser.close();
  }
})().catch((e) => { console.error(e); process.exit(1); });
