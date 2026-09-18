#!/usr/bin/env node
// Check that the published explorer actually renders what this repo built.
//
// Two publishes in September 2026 succeeded while uploading to a Shopify theme
// nobody could see, and nothing noticed. This loads the live page in Chromium
// and fails loudly when the page is empty, stale, or throwing from our assets.
//
// Usage:
//   node scripts/verify_published_explorer.mjs
//   node scripts/verify_published_explorer.mjs --url https://example.com/pages/latency
//   node scripts/verify_published_explorer.mjs --skip-freshness

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DEFAULT_URL = "https://misteraddons.com/pages/latency";

function readFlag(name, fallback = null) {
  const index = process.argv.indexOf(`--${name}`);
  if (index === -1) return fallback;
  const value = process.argv[index + 1];
  return value && !value.startsWith("--") ? value : true;
}

const url = readFlag("url", DEFAULT_URL);
const skipFreshness = readFlag("skip-freshness", false) === true;
const failures = [];
const note = (message) => console.log(`  ${message}`);

// Third-party theme apps throw on this storefront; only our own assets matter.
const OUR_ASSETS = /input-latency|latency\.js/i;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
const ourErrors = [];
page.on("pageerror", (error) => {
  const stack = String(error.stack || error);
  if (OUR_ASSETS.test(stack)) ourErrors.push(String(error.message).slice(0, 160));
});
page.on("console", (message) => {
  if (message.type() !== "error") return;
  const location = message.location()?.url || "";
  if (OUR_ASSETS.test(location)) ourErrors.push(message.text().slice(0, 160));
});

console.log(`Verifying ${url}`);
try {
  await page.goto(url, { waitUntil: "networkidle", timeout: 90000 });
  await page.locator(".latency-card").first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(1500);
} catch (error) {
  failures.push(`the page never rendered a result card: ${String(error.message).split("\n")[0]}`);
}

const state = await page.evaluate(() => {
  const grid = document.getElementById("latencyGrid");
  const banner = document.getElementById("latencyStatusBanner");
  return {
    cards: grid ? grid.querySelectorAll(".latency-card").length : 0,
    bannerHeight: banner ? Math.round(banner.getBoundingClientRect().height) : 0,
    bannerText: banner ? banner.textContent.trim() : "",
    generatedAt: globalThis.MISTER_LATENCY_DATA?.generatedAt ?? null,
    itemCount: globalThis.MISTER_LATENCY_DATA?.items?.length ?? null,
  };
});

note(`cards rendered: ${state.cards}`);
note(`payload items: ${state.itemCount}`);
note(`payload built: ${state.generatedAt}`);

if (!state.cards) failures.push("no result cards rendered");
if (state.bannerHeight > 0) failures.push(`the status banner is visible: "${state.bannerText}"`);
if (state.itemCount && state.cards && state.cards !== state.itemCount) {
  failures.push(`rendered ${state.cards} cards for ${state.itemCount} payload items`);
}

if (!skipFreshness) {
  const localPath = path.join(repoRoot, "docs", "data", "latency.json");
  const local = JSON.parse(fs.readFileSync(localPath, "utf8"));
  note(`local payload built: ${local.generatedAt}`);
  if (local.generatedAt !== state.generatedAt) {
    failures.push(`the live payload was built ${state.generatedAt} but this checkout holds ${local.generatedAt}; publish again or pull`);
  }
  if (local.items.length !== state.itemCount) {
    failures.push(`the live payload holds ${state.itemCount} items and this checkout holds ${local.items.length}`);
  }
}

if (ourErrors.length) failures.push(`the explorer assets threw: ${ourErrors.join(" | ")}`);

await browser.close();

if (failures.length) {
  console.error("\nFAILED");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
console.log("\nPublished explorer looks correct.");
