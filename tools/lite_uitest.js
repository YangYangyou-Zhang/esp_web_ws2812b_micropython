#!/usr/bin/env node
/* Headless checks for the ESP8266 lite UI.
 *   python tools/sim_lite.py
 *   node tools/lite_uitest.js
 */
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer-core');

const EDGE = process.env.EDGE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const URL = process.env.URL || 'http://127.0.0.1:8002/';
const OUT = path.join(__dirname, '..', 'docs', 'screenshots');
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--no-proxy-server', '--proxy-bypass-list=*',
      '--force-device-scale-factor=1', '--hide-scrollbars']
  });
  const errors = [];

  async function open(w, h, mobile) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h, deviceScaleFactor: mobile ? 2 : 1,
      isMobile: mobile, hasTouch: mobile });
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    page.on('requestfailed', (r) => errors.push('requestfailed: ' + r.url()));
    await page.goto(URL, { waitUntil: 'networkidle0', timeout: 30000 });
    await page.waitForFunction(() => document.querySelector('#dot').classList.contains('on'),
      { timeout: 15000 });
    await sleep(400);
    return page;
  }
  async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, 'lite-' + name + '.png') });
    console.log('shot lite-' + name);
  }
  async function overflow(page, tag) {
    const v = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth }));
    console.log('layout', tag, v.sw, v.iw, v.sw > v.iw + 1 ? 'OVERFLOW' : 'ok');
    if (v.sw > v.iw + 1) errors.push('overflow ' + tag);
  }
  async function state(page) {
    return page.evaluate(async () => (await fetch('/api/state', { cache: 'no-store' })).json());
  }

  let page = await open(390, 844, true);
  await overflow(page, 'mobile');
  const s1 = await state(page);
  console.log('state', JSON.stringify(s1));
  await shot(page, 'mobile');

  await page.click('.fx[data-id="breath"]');
  await sleep(700);
  await shot(page, 'mobile-breath');
  console.log('after apply', JSON.stringify(await state(page)));

  await page.click('#currentColor');
  await sleep(300);
  await shot(page, 'mobile-picker');
  await page.click('#cancel');

  await page.click('details.card summary');
  await sleep(300);
  await shot(page, 'mobile-settings');
  await page.evaluate(() => document.querySelector('.footer').scrollIntoView({ block: 'center' }));
  await sleep(300);
  await shot(page, 'mobile-footer');
  console.log('footer links', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.footer a')).map((a) => [a.textContent, a.href]))));
  await page.close();

  page = await open(1200, 900, false);
  await overflow(page, 'desktop');
  await shot(page, 'desktop');
  await page.close();

  console.log('errors:', errors.length ? errors : 'none');
  await browser.close();
  if (errors.length) process.exitCode = 1;
})().catch((e) => { console.error(e); process.exit(1); });
