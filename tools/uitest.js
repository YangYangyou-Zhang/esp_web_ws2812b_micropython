#!/usr/bin/env node
/* Headless UI checks + screenshots against the desktop simulator.
 *   npm install --no-save puppeteer-core
 *   python tools/sim.py
 *   node tools/uitest.js
 */
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');

const ROOT = path.join(__dirname, '..');
const EDGE = process.env.EDGE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const URL = process.env.URL || 'http://127.0.0.1:8000/';
const PREFIX = process.env.PREFIX || '';
const OUT = path.join(ROOT, 'docs', 'screenshots');
fs.mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: [
      '--no-sandbox', '--disable-gpu', '--no-proxy-server',
      '--proxy-bypass-list=*', '--force-device-scale-factor=1', '--hide-scrollbars'
    ]
  });
  const errors = [];

  async function open(w, h, mobile) {
    const page = await browser.newPage();
    await page.setViewport({
      width: w, height: h, deviceScaleFactor: mobile ? 2 : 1,
      isMobile: mobile, hasTouch: mobile
    });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    page.on('requestfailed', (r) => errors.push('requestfailed: ' + r.url() + ' ' +
      (r.failure() && r.failure().errorText)));
    await page.goto(URL, { waitUntil: 'networkidle0', timeout: 30000 });
    await page.waitForFunction(
      () => document.querySelector('#connDot').classList.contains('online'),
      { timeout: 15000 });
    await sleep(500);
    return page;
  }

  async function overflow(page, tag) {
    const v = await page.evaluate(() => ({
      sw: document.documentElement.scrollWidth, iw: window.innerWidth
    }));
    console.log('layout', tag, 'scrollWidth=' + v.sw, 'innerWidth=' + v.iw,
      v.sw > v.iw + 1 ? 'OVERFLOW' : 'ok');
    if (v.sw > v.iw + 1) errors.push('horizontal overflow: ' + tag);
  }

  async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, PREFIX + name + '.png') });
    console.log('shot', PREFIX + name);
  }

  let page = await open(390, 844, true);
  await overflow(page, 'mobile-control');
  await shot(page, 'mobile-control');

  await page.click('.tab[data-page="styles"]');
  await sleep(500);
  await shot(page, 'mobile-styles');

  await page.click('.effect-card[data-id="fire"]');
  await sleep(800);
  await shot(page, 'mobile-fire');

  await page.click('.tab[data-page="control"]');
  await sleep(300);
  await page.click('#currentColor');
  await sleep(400);
  await shot(page, 'mobile-picker');
  await page.keyboard.press('Escape');

  await page.click('.tab[data-page="settings"]');
  await sleep(500);
  await shot(page, 'mobile-settings');
  await page.evaluate(() => document.querySelector('.project-block').scrollIntoView({ block: 'center' }));
  await sleep(300);
  await shot(page, 'mobile-project');
  console.log('project links', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.project-links a')).map((a) => [a.textContent, a.href]))));
  console.log('project meta', await page.evaluate(() =>
    document.querySelector('.project-meta').textContent.replace(/\s+/g, ' ').trim()));
  await page.close();

  page = await open(1440, 900, false);
  await overflow(page, 'desktop-control');
  await shot(page, 'desktop-control');

  await page.click('.tab[data-page="styles"]');
  await sleep(500);
  await shot(page, 'desktop-styles');

  await page.click('.effect-card[data-id="gradient"]');
  await sleep(800);
  await shot(page, 'desktop-params');

  await page.click('.tab[data-page="settings"]');
  await sleep(400);
  await page.evaluate(() => document.querySelector('.project-block').scrollIntoView({ block: 'center' }));
  await sleep(300);
  await shot(page, 'desktop-project');
  await page.close();

  console.log('errors:', errors.length ? errors : 'none');
  await browser.close();
  if (errors.length) process.exitCode = 1;
})().catch((e) => { console.error(e); process.exit(1); });
