// Renders anya-og.html to assets/images/anya-og.png (1200x630). Run: node assets/og/render.js
// Google Fonts requests are fetched via curl so they go through the environment proxy.
const { execFileSync, execSync } = require('child_process');
const { chromium } = require(execSync('npm root -g').toString().trim() + '/playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.route(/fonts\.(googleapis|gstatic)\.com/, async (route) => {
    const url = route.request().url();
    const body = execFileSync('curl', ['-sS', '-A', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36', url]);
    const ct = url.includes('googleapis') ? 'text/css' : 'font/woff2';
    await route.fulfill({ status: 200, body, headers: { 'content-type': ct, 'access-control-allow-origin': '*' } });
  });
  await p.goto(`file://${__dirname}/anya-og.html`, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  console.log(await p.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight).join(', ')));
  await p.screenshot({ path: `${__dirname}/../images/anya-og.png` });
  await b.close();
})();
