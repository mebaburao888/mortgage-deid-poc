const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
  const htmlPath = path.resolve(__dirname, 'mortgage-deid-architecture.html');
  const pdfPath = path.resolve(__dirname, 'mortgage-deid-architecture.pdf');

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  const html = fs.readFileSync(htmlPath, 'utf8');
  await page.setContent(html, { waitUntil: 'networkidle0' });

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
    printBackground: true,
  });

  await browser.close();
  console.log('PDF saved to:', pdfPath);
})();
