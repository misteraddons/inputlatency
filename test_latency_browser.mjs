import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";


const repoRoot = fileURLToPath(new URL(".", import.meta.url));
const latencyPayload = JSON.parse(await readFile(resolve(repoRoot, "docs/data/latency.json"), "utf8"));
const expectedItemCount = latencyPayload.summary.totalItems;
const plotItemCount = latencyPayload.items
  .filter((item) => Number.isFinite(item.averageMs) && item.averageMs > 0 && Number.isFinite(item.sameFramePct)).length;
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
  return Number(/(\d+)/.exec(text || "")?.[1] || 0);
}

async function waitForRows(page) {
  await page.locator("#latencyRows tr.js-row").first().waitFor();
}

async function assertRankBounds(page) {
  const rowCount = await page.locator("#latencyRows tr.js-row").count();
  const ranks = await page.locator("#latencyRows tr.js-row td:first-child").allTextContents();
  const maxRank = Math.max(...ranks.map(parseRank));
  assert.equal(rowCount, expectedItemCount);
  assert.ok(maxRank <= rowCount, `Maximum overall rank ${maxRank} exceeds ${rowCount} consolidated results`);
  assert.equal(await page.locator("#latencyCount").textContent(), `${expectedItemCount} of ${expectedItemCount}`);
}

async function assertNoPageScroll(page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  assert.ok(overflow <= 0, `The page scrolls sideways by ${overflow}px`);
}

async function screenColor(page) {
  return page.locator(".svc-screen").evaluate((screen) => getComputedStyle(screen).backgroundColor);
}

async function assertThemeToggle(page) {
  const toggle = page.locator("#latencyThemeToggle");
  assert.equal(await toggle.textContent(), "Light");
  assert.equal(await screenColor(page), "rgb(26, 6, 64)");
  assert.equal(await toggle.evaluate((button) => getComputedStyle(button).color), "rgb(223, 255, 0)");

  await toggle.click();
  assert.equal(await toggle.textContent(), "Dark");
  assert.equal(await screenColor(page), "rgb(223, 255, 0)");
  assert.equal(await page.evaluate(() => localStorage.getItem("reflex-theme")), "lab");
  assert.equal(await page.locator("[data-reflex-theme-scope]").first().getAttribute("data-reflex-theme"), "midnight-light");

  await toggle.click();
  assert.equal(await toggle.textContent(), "Light");
  assert.equal(await screenColor(page), "rgb(26, 6, 64)");
  assert.equal(await page.evaluate(() => localStorage.getItem("reflex-theme")), "dark");
}

async function assertTierWords(page) {
  const tiers = await page.locator("#latencyRows .latency-tier").allTextContents();
  assert.deepEqual([...new Set(tiers)].sort(), ["Bronze", "Copper", "Diamond", "Gold", "Platinum", "Rust", "Silver"]);
  const colours = await page.evaluate(() => {
    const colourOf = (tier) => {
      const cell = [...document.querySelectorAll("#latencyRows .latency-tier")].find((node) => node.textContent === tier);
      return getComputedStyle(cell).color;
    };
    return { gold: colourOf("Gold"), copper: colourOf("Copper"), rust: colourOf("Rust"), shown: getComputedStyle(document.querySelector("#latencyRows .latency-tier")).textTransform };
  });
  assert.equal(colours.shown, "uppercase");
  assert.notEqual(colours.copper, colours.gold);
  assert.equal(colours.rust, colours.copper);
}

async function openRowByName(page, name) {
  await page.locator("#latencySearchInput").fill(name);
  const row = page.locator("#latencyRows tr.js-row").filter({ has: page.locator(".svc-name", { hasText: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`) }) }).first();
  if (await row.getAttribute("aria-expanded") !== "true") {
    await row.focus();
    await page.keyboard.press("Enter");
  }
  await page.locator("#latencyRows tr.svc-detail").first().waitFor();
  return row;
}

async function assertExternalProductLinksAvoidRestockMatcher(page) {
  await openRowByName(page, "New Wave Toys (Replicade) - Street Fighter II Mini Fight Stick");
  const href = await page.locator("#latencyRows tr.svc-detail a.latency-action", { hasText: "Buy" }).getAttribute("href");
  assert.match(href, /^https:\/\/newwavetoys\.com\/%70roducts\//);
  assert.doesNotMatch(href, /\/products\//);
  await page.locator("#latencySearchInput").fill("");
}

async function assertFiltersKeepGlobalRanks(page) {
  const rankOf = async (name) => parseRank(await page.locator("#latencyRows tr.js-row").filter({ has: page.locator(".svc-name", { hasText: new RegExp(`^${name}$`) }) }).first().locator("td").first().textContent());
  const initialAdaptRank = await rankOf("Reflex - Adapt");
  await page.locator("#latencyCategorySelect").selectOption({ label: "Controller Adapter" });
  await page.locator("#latencyMoreFilters > summary").click();
  await page.locator("#latencyAdapterInputSelect").selectOption({ label: "N64 Controller" });
  assert.equal(await rankOf("Reflex - Adapt"), initialAdaptRank);
  assert.match(await page.locator("#latencyMoreCount").textContent(), /1 set/);
  assert.equal(await page.locator("#latencyFaceButtonsSelect").isDisabled(), true);
  await page.locator("#latencyCategorySelect").selectOption({ value: "" });
  assert.equal(await page.locator("#latencyAdapterInputSelect").isDisabled(), true);
  await page.locator("#latencyMoreFilters > summary").click();
}

async function assertSorting(page) {
  const firstName = () => page.locator("#latencyRows tr.js-row .svc-name").first().textContent();
  await page.locator("#latencySortSelect").selectOption("name");
  const ascending = await firstName();
  await page.locator("#latencySortDirectionToggle").click();
  const descending = await firstName();
  assert.ok(ascending.localeCompare(descending) < 0, `${ascending} should sort before ${descending}`);
  assert.match(await page.locator("#latencySortDirectionToggle").textContent(), /Desc/);
  await page.locator("#latencySortDirectionToggle").click();
  await page.locator("#latencySortSelect").selectOption("average");
}

async function assertRecentOpensRanking(page) {
  await page.getByRole("tab", { name: "Recent" }).click();
  const recent = page.locator("#latencyRecentRows tr").first();
  const name = await recent.locator(".svc-name").textContent();
  await recent.click();
  assert.equal(await page.locator("#latencyPageRanking").isVisible(), true);
  assert.equal(await page.locator('#latencyRows tr.js-row[aria-expanded="true"] .svc-name').textContent(), name);
  assert.equal(await page.locator("#latencyRows tr.js-row").count(), expectedItemCount);
}

async function assertRowOpensLeaderLines(page) {
  const row = await openRowByName(page, "Reflex - Adapt");
  assert.equal(await row.getAttribute("aria-expanded"), "true");
  const detail = page.locator("#latencyRows tr.svc-detail");
  assert.ok(await detail.locator(".svc-lead").count() >= 6);
  await detail.locator("h3", { hasText: "Measured modes" }).waitFor();
  await row.focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator("#latencyRows tr.svc-detail").count(), 0);
  await page.locator("#latencySearchInput").fill("");
}

async function assertMapHoverAndClick(page) {
  await page.getByRole("tab", { name: "Latency Map" }).click();
  const marks = page.locator("#latencyScatter .latency-mark");
  await marks.first().waitFor({ state: "attached" });
  assert.equal(await marks.count(), plotItemCount);
  assert.ok(await page.locator("#latencyScatter .svc-mark-danger").count() > 0);
  await page.locator("#latencyScatter .latency-median .svc-ref-label").waitFor({ state: "attached" });

  // Point at the slowest device, which sits alone at the right of the map.
  const target = await page.evaluate(() => {
    const points = [...document.querySelectorAll("#latencyScatter .latency-mark")];
    const point = points.reduce((best, next) => (Number(next.dataset.baseCx) > Number(best.dataset.baseCx) ? next : best));
    const matrix = point.ownerSVGElement.getScreenCTM();
    return {
      id: point.dataset.itemId,
      x: matrix.e + Number(point.dataset.baseCx) * matrix.a,
      y: matrix.f + Number(point.dataset.baseCy) * matrix.d,
    };
  });
  const expected = latencyPayload.items.find((item) => item.id === target.id);
  await page.mouse.move(target.x, target.y);
  assert.match(await page.locator("#latencyReadout").textContent(), new RegExp(`^${expected.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} `));
  await page.mouse.click(target.x, target.y);
  assert.equal(await page.locator("#latencyPageRanking").isVisible(), true);
  assert.equal(await page.locator('#latencyRows tr.js-row[aria-expanded="true"] .svc-name').textContent(), expected.name);
  assert.equal(await page.evaluate(() => document.activeElement.matches('tr.js-row[aria-expanded="true"]')), true);
}

async function applyShopifyStyles(page) {
  await page.evaluate(async () => {
    for (const link of document.querySelectorAll('link[rel="stylesheet"]')) {
      if (/assets\/(reflex|mister-explorer|service-menu|input-latency)\.css/.test(link.getAttribute("href") || "")) {
        link.remove();
      }
    }
    document.body.classList.add("input-latency-explorer-app");
    const storefrontButtonStyle = document.createElement("style");
    storefrontButtonStyle.textContent = "button { color: #242424; } a { color: #242424; }";
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

async function assertShopifyIsolation(page) {
  const styles = await page.evaluate(() => {
    const outside = document.createElement("div");
    const range = document.createElement("input");
    const table = document.createElement("table");
    range.type = "range";
    outside.append(range, table);
    document.documentElement.appendChild(outside);
    const result = {
      rootColorScheme: getComputedStyle(document.documentElement).colorScheme,
      rootPageBg: getComputedStyle(document.documentElement).getPropertyValue("--page-bg").trim(),
      rootSvcInk: getComputedStyle(document.documentElement).getPropertyValue("--svc-ink").trim(),
      rangeAccent: getComputedStyle(range).accentColor,
      tableCollapse: getComputedStyle(table).borderCollapse,
    };
    outside.remove();
    return result;
  });
  assert.equal(styles.rootColorScheme, "normal");
  assert.equal(styles.rootPageBg, "");
  assert.equal(styles.rootSvcInk, "");
  assert.notEqual(styles.rangeAccent, "rgb(239, 255, 26)");
  assert.equal(styles.tableCollapse, "separate");
}

const server = await startStaticServer();
const address = server.address();
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const pageErrors = [];
page.on("pageerror", (error) => pageErrors.push(error.message));

try {
  await page.goto(`http://127.0.0.1:${address.port}/docs/latency.html`, { waitUntil: "networkidle" });
  await waitForRows(page);
  await page.evaluate(() => document.fonts.ready);

  await assertRankBounds(page);
  assert.equal(await page.locator('#latencyRows tr.js-row[aria-expanded="true"] td').first().textContent(), "1");
  await assertThemeToggle(page);
  await assertTierWords(page);
  await assertFiltersKeepGlobalRanks(page);
  await assertSorting(page);
  await assertRowOpensLeaderLines(page);
  await assertRecentOpensRanking(page);
  await assertMapHoverAndClick(page);

  await page.setViewportSize({ width: 375, height: 812 });
  await assertNoPageScroll(page);
  await page.getByRole("tab", { name: "Latency Map" }).click();
  await assertNoPageScroll(page);
  await page.getByRole("tab", { name: "Ranking" }).click();
  assert.deepEqual(pageErrors, []);

  const shopifyPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const shopifyPageErrors = [];
  shopifyPage.on("pageerror", (error) => shopifyPageErrors.push(error.message));
  await shopifyPage.goto(`http://127.0.0.1:${address.port}/docs/latency.html`, { waitUntil: "networkidle" });
  await waitForRows(shopifyPage);
  await applyShopifyStyles(shopifyPage);
  await shopifyPage.evaluate(() => document.fonts.ready);
  await assertRankBounds(shopifyPage);
  await assertShopifyIsolation(shopifyPage);
  await assertThemeToggle(shopifyPage);
  await assertTierWords(shopifyPage);
  await assertExternalProductLinksAvoidRestockMatcher(shopifyPage);
  await assertMapHoverAndClick(shopifyPage);
  await shopifyPage.setViewportSize({ width: 375, height: 812 });
  await assertNoPageScroll(shopifyPage);
  assert.deepEqual(shopifyPageErrors, []);
} finally {
  await browser.close();
  await new Promise((accept) => server.close(accept));
}

console.log("Browser smoke checks passed");
