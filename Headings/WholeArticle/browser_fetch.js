#!/usr/bin/env node

// Use a real browser when protected sites refuse simpler HTTP fetching.
const fs = require("fs");
const { chromium } = require("playwright");

async function launchBrowser() {
  const launchAttempts = [
    () => chromium.launch({ headless: true }),
    () => chromium.launch({ channel: "chrome", headless: true }),
    () =>
      chromium.launch({
        executablePath:
          "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        headless: true,
      }),
    () =>
      chromium.launch({
        executablePath:
          "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        headless: true,
      }),
    () =>
      chromium.launch({
        executablePath: "/Applications/Chromium.app/Contents/MacOS/Chromium",
        headless: true,
      }),
  ];

  let lastError;
  for (const attempt of launchAttempts) {
    try {
      const browser = await attempt();
      return browser;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}

async function main() {
  const url = process.argv[2];

  if (!url) {
    console.error("Missing URL argument.");
    process.exit(1);
  }

  const browser = await launchBrowser();

  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    viewport: { width: 1440, height: 2000 },
  });

  const page = await context.newPage();

  try {
    await page.goto(url, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForTimeout(3000);

    const html = await page.content();
    const finalUrl = page.url();

    process.stdout.write(
      JSON.stringify({
        html,
        finalUrl,
      })
    );
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  const chromeInstalled = fs.existsSync(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  );

  if (message.includes("Executable doesn't exist") && !chromeInstalled) {
    console.error(
      "No usable browser found. Either install Google Chrome locally or run: npx playwright install chromium"
    );
  } else if (message.includes("Executable doesn't exist")) {
    console.error(
      "Playwright could not find its bundled browser, but it should be able to use local Chrome. Make sure Google Chrome is installed in /Applications."
    );
  } else {
    console.error(message);
  }
  process.exit(1);
});
