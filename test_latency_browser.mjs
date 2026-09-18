import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";


const repoRoot = fileURLToPath(new URL(".", import.meta.url));
const expectedItemCount = JSON.parse(
  await readFile(resolve(repoRoot, "docs/data/latency.json"), "utf8"),
).summary.totalItems;
const contentTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
]);

function startStaticServer() {
  const server = createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url || "/", "http://127.0.0.1").pathname);
      const relativePath = pathname === "/" ? "docs/latency.html" : pathname.replace(/^\/+/, "");
      const absolutePath = resolve(repoRoot, relativePath);
      if (!absolutePath.startsWith(`${resolve(repoRoot)}${sep}`)) {
        response.writeHead(403).end("Forbidden");
        return;
      }
      const body = await readFile(absolutePath);
      response.writeHead(200, { "Content-Type": contentTypes.get(extname(absolutePath)) || "application/octet-stream" });
      response.end(body);
    } catch (error) {
      response.writeHead(error && error.code === "ENOENT" ? 404 : 500).end("Not found");
    }
  });
  return new Promise((accept, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => accept(server));
  });
}

function parseRank(text) {
  return Number(/#(\d+)/.exec(text || "")?.[1] || 0);
}

async function assertTitlesFit(page) {
  const clipped = await page.locator(".latency-grid.view-list .card-title").evaluateAll((titles) => titles
    .filter((title) => title.scrollHeight > title.clientHeight + 1)
    .map((title) => ({ text: title.textContent.trim(), clientHeight: title.clientHeight, scrollHeight: title.scrollHeight })));
  assert.deepEqual(clipped, [], `Clipped list titles: ${JSON.stringify(clipped)}`);
}

async function assertRankBounds(page) {
  const cardCount = await page.locator(".latency-card").count();
  const ranks = await page.locator(".tag-rank-overall").allTextContents();
  const maxRank = Math.max(...ranks.map(parseRank));
  assert.equal(cardCount, expectedItemCount);
  assert.ok(maxRank <= cardCount, `Maximum overall rank ${maxRank} exceeds ${cardCount} consolidated results`);
}

async function assertLightMedianContrast(page) {
  await page.getByRole("button", { name: "Light", exact: true }).click();
  const medianLine = page.locator(".latency-median-line line");
  await medianLine.waitFor({ state: "attached" });
  const style = await medianLine.evaluate((line) => ({
    stroke: getComputedStyle(line).stroke,
    strokeWidth: getComputedStyle(line).strokeWidth,
  }));
  assert.equal(style.stroke, "rgb(80, 0, 220)");
  assert.ok(parseFloat(style.strokeWidth) >= 1.75, `Median stroke is only ${style.strokeWidth}`);
  await page.getByRole("button", { name: "Dark", exact: true }).click();
}

async function assertThemeToggleContrast(page) {
  const darkButton = page.getByRole("button", { name: "Dark", exact: true });
  const lightButton = page.getByRole("button", { name: "Light", exact: true });

  await darkButton.click();
  assert.equal(await lightButton.evaluate((button) => getComputedStyle(button).color), "rgb(197, 186, 255)");
  await lightButton.click();
  assert.equal(await darkButton.evaluate((button) => getComputedStyle(button).color), "rgb(73, 63, 88)");
  await darkButton.click();
}

async function assertShopifyIsolation(page) {
  const styles = await page.evaluate(() => {
    const outside = document.createElement("div");
    const range = document.createElement("input");
    range.type = "range";
    outside.appendChild(range);
    document.documentElement.appendChild(outside);
    const result = {
      rootColorScheme: getComputedStyle(document.documentElement).colorScheme,
      rootPageBg: getComputedStyle(document.documentElement).getPropertyValue("--page-bg").trim(),
      rangeAccent: getComputedStyle(range).accentColor,
    };
    outside.remove();
    return result;
  });
  assert.equal(styles.rootColorScheme, "normal");
  assert.equal(styles.rootPageBg, "");
  assert.notEqual(styles.rangeAccent, "rgb(239, 255, 26)");
}

async function assertLightInteractionContrast(page) {
  await page.getByRole("button", { name: "Light", exact: true }).click();
  const searchInput = page.locator("#latencySearchInput");
  await searchInput.focus();
  assert.equal(
    await searchInput.evaluate((input) => getComputedStyle(input).outlineColor),
    "rgb(80, 0, 220)",
  );

  const selectedPoint = page.locator(".latency-point").first();
  await selectedPoint.evaluate((point) => point.classList.add("is-selected"));
  await page.waitForTimeout(180);
  const selectedStyle = await selectedPoint.evaluate((point) => ({
    stroke: getComputedStyle(point).stroke,
    token: getComputedStyle(point).getPropertyValue("--plot-selection").trim(),
  }));
  assert.equal(selectedStyle.token, "#5000dc", JSON.stringify(selectedStyle));
  assert.equal(selectedStyle.stroke, "rgb(80, 0, 220)", JSON.stringify(selectedStyle));
  await selectedPoint.evaluate((point) => point.classList.remove("is-selected"));
  await page.getByRole("button", { name: "Dark", exact: true }).click();
}

async function assertExternalProductLinksAvoidRestockMatcher(page) {
  const externalLink = page
    .locator('.card-title-link[href*="newwavetoys.com"]')
    .first();
  const href = await externalLink.getAttribute("href");
  assert.match(href, /^https:\/\/newwavetoys\.com\/%70roducts\//);
  assert.doesNotMatch(href, /\/products\//);
}

async function applyShopifyStyles(page) {
  await page.evaluate(async () => {
    for (const link of document.querySelectorAll('link[rel="stylesheet"]')) {
      if (/assets\/(reflex|mister-explorer|input-latency)\.css/.test(link.getAttribute("href") || "")) {
        link.remove();
      }
    }
    document.body.classList.add("input-latency-explorer-app");
    const storefrontButtonStyle = document.createElement("style");
    storefrontButtonStyle.textContent = "button { color: #242424; }";
    document.head.appendChild(storefrontButtonStyle);
    const loadStyle = (href) => new Promise((accept, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.onload = accept;
      link.onerror = reject;
      document.head.appendChild(link);
    });
    await loadStyle("/shopify/assets/input-latency-explorer.css");
  });
}

const server = await startStaticServer();
const address = server.address();
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const pageErrors = [];
page.on("pageerror", (error) => pageErrors.push(error.message));

try {
  await page.goto(`http://127.0.0.1:${address.port}/docs/latency.html`, { waitUntil: "networkidle" });
  await page.locator(".latency-card").first().waitFor();
  await page.evaluate(() => document.fonts.ready);

  await assertRankBounds(page);
  await assertTitlesFit(page);
  await assertThemeToggleContrast(page);
  await assertLightMedianContrast(page);

  const adaptCard = page.locator(".latency-card").filter({ has: page.locator(".card-title", { hasText: /^Reflex - Adapt$/ }) }).first();
  const initialAdaptRank = parseRank(await adaptCard.locator(".tag-rank-overall").textContent());
  await page.locator("#latencyCategorySelect").selectOption({ label: "Controller Adapter" });
  await page.locator("#latencyAdapterInputSelect").selectOption({ label: "N64 Controller" });
  const filteredAdaptCard = page.locator(".latency-card").filter({ has: page.locator(".card-title", { hasText: /^Reflex - Adapt$/ }) }).first();
  assert.equal(parseRank(await filteredAdaptCard.locator(".tag-rank-overall").textContent()), initialAdaptRank);

  await page.locator(".latency-recent-item").first().click();
  await page.locator(".latency-card.is-selected .latency-detail-panel:not([hidden])").waitFor();
  assert.equal(await page.locator(".latency-card").count(), 1);

  await page.locator("#latencySearchInput").fill("Reflex - Adapt");
  const detailsCard = page.locator(".latency-card").filter({ has: page.locator(".card-title", { hasText: /^Reflex - Adapt$/ }) }).first();
  await detailsCard.focus();
  await page.keyboard.press("Enter");
  await detailsCard.locator(".latency-mode-variant").first().waitFor();
  const fontSizes = await detailsCard.evaluate((card) => ({
    detail: getComputedStyle(card.querySelector(".latency-detail-item strong")).fontSize,
    mode: getComputedStyle(card.querySelector(".latency-mode-variant strong")).fontSize,
  }));
  assert.equal(fontSizes.detail, fontSizes.mode);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#latencySearchInput").fill("");
  await assertTitlesFit(page);
  assert.deepEqual(pageErrors, []);

  const shopifyPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const shopifyPageErrors = [];
  shopifyPage.on("pageerror", (error) => shopifyPageErrors.push(error.message));
  await shopifyPage.goto(`http://127.0.0.1:${address.port}/docs/latency.html`, { waitUntil: "networkidle" });
  await shopifyPage.locator(".latency-card").first().waitFor();
  await applyShopifyStyles(shopifyPage);
  await shopifyPage.evaluate(() => document.fonts.ready);
  await assertRankBounds(shopifyPage);
  await assertTitlesFit(shopifyPage);
  await assertShopifyIsolation(shopifyPage);
  await assertThemeToggleContrast(shopifyPage);
  await assertLightMedianContrast(shopifyPage);
  await assertLightInteractionContrast(shopifyPage);
  await assertExternalProductLinksAvoidRestockMatcher(shopifyPage);
  await shopifyPage.setViewportSize({ width: 390, height: 844 });
  await assertTitlesFit(shopifyPage);
  assert.deepEqual(shopifyPageErrors, []);
} finally {
  await browser.close();
  await new Promise((accept) => server.close(accept));
}

console.log("Browser smoke checks passed");
