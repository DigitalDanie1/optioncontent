import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browser = await chromium.launch();
try {
  const page = await browser.newPage({viewport: {width: 2880, height: 1620}, deviceScaleFactor: 1});
  for (const lang of ['ko', 'en']) {
    await page.goto(pathToFileURL(path.join(root, `scripts/weekly-${lang}-W42.html`)).href);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(img => img.decode()));
    });
    await page.screenshot({path: path.join(root, `assets/images/weekly-options-W42-${lang}.png`)});
    console.log(`Rendered ${lang}: 2880 × 1620`);
  }
} finally { await browser.close(); }
