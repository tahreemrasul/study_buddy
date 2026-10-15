const { chromium } = require(process.argv[2] + "/node_modules/playwright-core");
(async () => {
  const b = await chromium.launch({ channel: "chrome" });
  const p = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1.5 });
  await p.goto("file://" + __dirname + "/diagrams.html", { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready);
  for (const s of await p.$$("section")) {
    const id = await s.getAttribute("id");
    await s.screenshot({ path: `${__dirname}/../images/${id}.png` });
    console.log(id);
  }
  await b.close();
})();
