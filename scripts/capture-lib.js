'use strict';
// Playwright helpers for user-manual capture: 1920x1080, DPR 1, masking, login, UI inventory.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const VIEWPORT = { width: 1920, height: 1080 };
const STYLE_ID = '__manual_mask_style';

async function launch({ headless = true, storageState, executablePath, locale } = {}) {
  const browser = await chromium.launch({ headless, executablePath });
  browser.on('disconnected', () => console.error('[browser] disconnected'));
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: 1,
    locale,
    storageState: storageState && fs.existsSync(storageState) ? storageState : undefined,
  });
  const page = await context.newPage();
  return { browser, context, page };
}

// Visible browser: the user types credentials/MFA; we wait for the post-login URL and save the session.
async function loginInteractive(page, context, { startUrl, successUrl, stateFile, timeoutMs = 300000 }) {
  await page.goto(startUrl);
  console.error('[login] complete the login in the browser window...');
  await page.waitForURL(successUrl, { timeout: timeoutMs });
  await page.waitForLoadState('networkidle').catch(() => {});
  if (stateFile) {
    fs.mkdirSync(path.dirname(stateFile), { recursive: true });
    await context.storageState({ path: stateFile });
  }
}

// Types like a human (needed by pages whose buttons stay disabled after fill()); skips hidden prefill fields.
async function typeIn(page, selector, text) {
  const field = page.locator(`${selector}:not([aria-hidden="true"]):visible`).first();
  await field.waitFor({ state: 'visible', timeout: 30000 });
  await field.click();
  await field.pressSequentially(text, { delay: 40 });
}

async function waitIdle(page, { loaders = ['.spinner', '.loading', '[aria-busy="true"]'], timeout = 30000 } = {}) {
  for (const sel of loaders) {
    await page.locator(sel).first().waitFor({ state: 'hidden', timeout }).catch(() => {});
  }
  await page.getByText(/^(loading|caricamento)/i).first().waitFor({ state: 'hidden', timeout }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout }).catch(() => {});
}

// sensitive = { selectors: [], textPatterns: [], blurPx: 8, maskSelectors: [] }
// selectors -> CSS blur; maskSelectors -> solid box applied by screenshot({mask}); textPatterns -> regex over text nodes (blurred)
async function applyMasks(page, sensitive = {}) {
  const { selectors = [], textPatterns = [], blurPx = 8 } = sensitive;
  await page.evaluate(({ selectors, textPatterns, blurPx, STYLE_ID }) => {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement('style');
      style.id = STYLE_ID;
      document.head.appendChild(style);
    }
    style.textContent =
      `[data-manual-mask]{filter:blur(${blurPx}px)!important;user-select:none!important}` +
      `input[data-manual-mask],textarea[data-manual-mask]{color:transparent!important;text-shadow:0 0 ${blurPx}px rgba(0,0,0,.7)!important}`;
    for (const sel of selectors) {
      document.querySelectorAll(sel).forEach((el) => el.setAttribute('data-manual-mask', '1'));
    }
    if (textPatterns.length) {
      const res = textPatterns.map((p) => new RegExp(p, 'g'));
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const parent = node.parentElement;
        if (!parent || parent.closest('[data-manual-mask],script,style')) continue;
        for (const re of res) {
          re.lastIndex = 0;
          if (!re.test(node.nodeValue)) continue;
          re.lastIndex = 0;
          const frag = document.createDocumentFragment();
          let last = 0, m;
          const text = node.nodeValue;
          while ((m = re.exec(text))) {
            if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
            const span = document.createElement('span');
            span.setAttribute('data-manual-mask', '1');
            span.textContent = m[0];
            frag.appendChild(span);
            last = m.index + m[0].length;
            if (m[0].length === 0) re.lastIndex++;
          }
          if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
          node.replaceWith(frag);
          break;
        }
      }
    }
  }, { selectors, textPatterns, blurPx, STYLE_ID });
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) };
}

// Waits, re-applies masks, screenshots at 1920x1080 and verifies the size.
async function shot(page, outDir, name, { sensitive = {}, fullPage = false, clip } = {}) {
  fs.mkdirSync(outDir, { recursive: true });
  await waitIdle(page);
  await applyMasks(page, sensitive);
  const mask = (sensitive.maskSelectors || []).map((s) => page.locator(s));
  const file = path.join(outDir, name.endsWith('.png') ? name : `${name}.png`);
  await page.screenshot({ path: file, fullPage, clip, mask, maskColor: '#444444' });
  const { width, height } = pngSize(file);
  if (!fullPage && !clip && (width !== VIEWPORT.width || height !== VIEWPORT.height)) {
    throw new Error(`${file} is ${width}x${height}, expected 1920x1080`);
  }
  return file;
}

// Text inventory of the current page: used for role discovery/diff. Contains no values from data rows.
async function collectUiInventory(page) {
  return page.evaluate(() => {
    const txt = (el) => (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '').trim().replace(/\s+/g, ' ');
    const uniq = (a) => [...new Set(a.filter(Boolean))].sort();
    return {
      url: location.pathname,
      title: document.title,
      menu: uniq([...document.querySelectorAll('nav a, [role=navigation] a, .navbar a, .sidebar a, [role=menuitem]')].map(txt)),
      buttons: uniq([...document.querySelectorAll('button, [role=button], input[type=submit]')].map(txt)),
      tableHeaders: uniq([...document.querySelectorAll('th, [role=columnheader]')].map(txt)),
      formLabels: uniq([...document.querySelectorAll('label')].map(txt)),
    };
  });
}

module.exports = { VIEWPORT, launch, loginInteractive, typeIn, waitIdle, applyMasks, shot, collectUiInventory, pngSize };
