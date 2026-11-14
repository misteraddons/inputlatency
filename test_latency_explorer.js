const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");

const explorerSource = fs.readFileSync("docs/assets/latency.js", "utf8");
const explorerStyles = fs.readFileSync("docs/assets/input-latency.css", "utf8");
const serviceMenuStyles = fs.readFileSync("docs/assets/service-menu.css", "utf8");
const shopifyStyles = fs.readFileSync("shopify/assets/input-latency-explorer.css", "utf8");
const explorerMarkup = fs.readFileSync("docs/latency.html", "utf8");
const shopifyMarkup = fs.readFileSync("shopify/sections/input-latency-explorer.liquid", "utf8");
const bothMarkups = [explorerMarkup, shopifyMarkup];

function between(markup, start, end) {
  const from = markup.indexOf(start);
  const to = markup.indexOf(end, from);
  assert.notEqual(from, -1, `missing ${start}`);
  assert.notEqual(to, -1, `missing ${end}`);
  return markup.slice(from, to);
}

test("the docs and Shopify copies of the explorer stay in step", () => {
  // These drifted once: a pull request changed the docs copy only, and every
  // existing test still passed.
  const shopifySource = fs.readFileSync("shopify/assets/input-latency-explorer.js", "utf8");
  assert.equal(
    shopifySource,
    explorerSource,
    "shopify/assets/input-latency-explorer.js must be a byte-for-byte copy of docs/assets/latency.js",
  );

  // Everything from the first page to the key hints is the same markup on both sides.
  const pages = (markup) => between(markup, '<section class="svc-page" id="latencyPageRanking"', "</footer>");
  assert.equal(pages(shopifyMarkup), pages(explorerMarkup));
  for (const marker of [/class="svc latency-svc"/, /id="latencyMenu"/, /id="latencyThemeToggle"/, /class="svc-ident"/]) {
    assert.match(explorerMarkup, marker);
    assert.match(shopifyMarkup, marker);
  }
});

test("the page follows the service-menu layout: ident line, menu and pages", () => {
  for (const markup of bothMarkups) {
    // The hero, stat tiles, pill tags and card grid are gone.
    for (const retired of [/class="hero"/, /hero-stats/, /latencyCardTemplate/, /latencyGrid/, /card-tags/, /segmented-toggle/]) {
      assert.doesNotMatch(markup, retired);
    }
    assert.match(markup, /<div class="svc-wordmark"><h1>Latency<\/h1><span>Input latency explorer<\/span><\/div>/);
    assert.match(markup, /<span>Amazon links are affiliate links<\/span>/);

    const menu = between(markup, 'id="latencyMenu"', "</nav>");
    const labels = [...menu.matchAll(/role="tab"[^>]*>([^<]+)<\/button>/g)].map((match) => match[1]);
    assert.deepEqual(labels, ["Ranking", "Latency Map", "Recent", "Best by Category", "Methodology"]);
    for (const page of ["latencyPageRanking", "latencyPageMap", "latencyPageRecent", "latencyPageBest", "latencyPageMethod"]) {
      assert.match(markup, new RegExp(`<section class="svc-page" id="${page}" role="tabpanel"`));
    }
    // Only the first page shows before the script runs.
    assert.doesNotMatch(markup, /id="latencyPageRanking" role="tabpanel" aria-labelledby="latencyTabRanking" hidden/);
  }
  assert.match(explorerSource, /function showLatencyPage\(pageId\)/);
  assert.match(explorerSource, /ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1/);
});

test("the docs page loads the service-menu layer before the latency adapter", () => {
  const order = ["assets/reflex.css", "assets/mister-explorer.css", "assets/service-menu.css", "assets/input-latency.css"]
    .map((href) => explorerMarkup.indexOf(href));
  assert.equal(order.every((position) => position >= 0), true);
  assert.deepEqual([...order].sort((left, right) => left - right), order);
  assert.match(serviceMenuStyles, /\.svc-table tr\[aria-expanded\]/);
});

test("ranking filters keep every option, with the rarer ones folded under More filters", () => {
  for (const markup of bothMarkups) {
    const primary = between(markup, '<div class="svc-filters">', "</div>");
    const primaryIds = [...primary.matchAll(/<select id="(\w+)"/g)].map((match) => match[1]);
    assert.deepEqual(primaryIds, ["latencyCategorySelect", "latencyConnectionSelect", "latencyTierSelect", "latencySaleStatusSelect"]);

    const more = between(markup, '<details class="svc-advanced" id="latencyMoreFilters">', "</details>");
    const moreIds = [...more.matchAll(/<select id="(\w+)"/g)].map((match) => match[1]);
    assert.deepEqual(moreIds, [
      "latencyFaceButtonsSelect",
      "latencyHomeButtonSelect",
      "latencyAdapterInputSelect",
      "latencyModeSelect",
      "latencySourceStatusSelect",
    ]);
    assert.match(markup, /<select id="latencyAdapterInputSelect" disabled>/);
    assert.match(markup, /<select id="latencyFaceButtonsSelect" disabled>/);
    assert.match(markup, /<select id="latencyHomeButtonSelect" disabled>/);
    assert.match(markup, />All firmware<\/option>/);
    assert.match(markup, /<input id="latencySearchInput" type="search"/);

    const sorts = [...between(markup, '<select id="latencySortSelect"', "</select>").matchAll(/value="([\w-]+)"/g)].map((match) => match[1]);
    assert.deepEqual(sorts, ["average", "same-frame", "name", "date-added"]);
    assert.match(markup, /id="latencySortDirectionToggle"/);
  }
  assert.match(explorerSource, /function syncLatencyMoreFiltersCount/);
});

test("ranking rows are a dense table that opens into leader lines", () => {
  for (const markup of bothMarkups) {
    const header = between(markup, '<table class="svc-table" id="latencyTable">', "</thead>");
    const columns = [...header.matchAll(/<th[^>]*>([^<]+)<\/th>/g)].map((match) => match[1]);
    assert.deepEqual(columns, ["#", "Device", "Avg ms", "Log scale", "Tier", "Link", "Category rank"]);
  }
  assert.match(explorerSource, /class="latency-row js-row" tabindex="0" aria-expanded="\$\{open\}"/);
  assert.match(explorerSource, /return renderLatencyRow\(item, open\) \+ \(open \? renderLatencyDetail\(item\) : ""\)/);
  assert.match(explorerSource, /<tr class="svc-detail"[^`]*<td colspan="7">/);
  assert.match(explorerSource, /<div class="svc-leaders svc-leaders-cols">\$\{leads\}<\/div>/);
  assert.match(explorerSource, /<h3 class="svc-sub">Measured modes<\/h3>/);
  // The fastest device opens on arrival, as in the approved preview.
  assert.match(explorerSource, /latencyState\.selectedItemId = fastest \? fastest\.id : ""/);
});

test("tiers are words, and Copper and Rust read in the warning colour", () => {
  assert.doesNotMatch(explorerSource, /LATENCY_TIER_ICON_LABELS|createLatencyTierIcon|latency-tier-icon/);
  assert.doesNotMatch(explorerSource, /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u);
  assert.match(explorerSource, /const LATENCY_LATE_TIERS = new Set\(\["Copper", "Rust"\]\)/);
  assert.match(explorerSource, /<td class="latency-tier\$\{danger\}">/);
  assert.match(explorerSource, /svc-mark-danger/);
  assert.match(explorerStyles, /\.latency-svc \.latency-tier \{\s*text-transform: uppercase;/);
});

test("the theme toggle keeps the shared reflex-theme value and shows it as midnight", () => {
  for (const markup of bothMarkups) {
    assert.match(markup, /localStorage\.getItem\(["']reflex-theme["']\)/);
    assert.match(markup, /activeTheme === ["']lab["'] \? ["']midnight-light["'] : ["']midnight["']/);
    assert.match(markup, /localStorage\.setItem\(storageKey, activeTheme\)/);
    assert.match(markup, /data-reflex-theme-option="lab">Light<\/button>/);
  }
  // Shopify themes the section, never the storefront's document root.
  assert.doesNotMatch(shopifyMarkup, /document\.documentElement/);
  assert.match(shopifyMarkup, /data-reflex-theme-scope data-reflex-theme="midnight"/);
});

test("methodology keeps the measurement description and its links", () => {
  for (const markup of bothMarkups) {
    const page = between(markup, 'id="latencyPageMethod"', "</section>");
    assert.match(page, /ATmega32U4/);
    assert.match(page, /custom MiSTer NES core/i);
    assert.match(page, /User I\/O pin/);
    assert.match(page, /CSV captures are summarized in R/);
    assert.match(page, /1 ms USB polling/);
    assert.match(page, /apply to any device that polls USB at 1 ms/);
    assert.match(page, /test_core\/NES_Lag_Tester\.rbf/);
    assert.match(page, /github\.com\/misteraddons\/inputlatency"/);
    assert.match(page, /docs\.google\.com\/spreadsheets/);
    assert.match(page, /id="latencyMethodRaw"/);
  }
});

test("latency explorer normalizes forced view URLs back to the canonical latency page", () => {
  assert.match(explorerSource, /function normalizeLatencyCanonicalPath/);
  assert.match(explorerSource, /params\.get\("view"\) !== "input-latency-explorer"/);
  assert.match(explorerSource, /window\.history\.replaceState\(window\.history\.state, document\.title, nextUrl\)/);
  assert.match(explorerSource, /normalizeLatencyCanonicalPath\(\);/);
});

test("recent and map selections open the device in Ranking", () => {
  assert.match(explorerSource, /function getMostRecentLatencyItems\(items, limit = 5\)/);
  assert.match(explorerSource, /renderLatencyRecentItems\(getMostRecentLatencyItems\(latencyState\.items\)\)/);
  assert.match(explorerSource, /function selectLatencyRecentItem\(itemId\) \{[\s\S]*?clearLatencyFilterControls\(\);[\s\S]*?openLatencyItem\(itemId\);/);
  assert.match(explorerSource, /data-recent-item-id/);
  assert.match(explorerSource, /function openLatencyItem\(itemId, options = \{\}\) \{[\s\S]*?showLatencyPage\("latencyPageRanking"\);/);
  assert.match(explorerSource, /function selectLatencyScatterPoint\(point\) \{[\s\S]*?openLatencyItem\(item\.id\);/);
  assert.match(explorerSource, /if \(latencyActiveScatterPoint\) selectLatencyScatterPoint\(latencyActiveScatterPoint\)/);
});

test("open source firmware is labeled as open source in filters and details", () => {
  assert.match(explorerSource, /LATENCY_SOURCE_STATUS_ORDER = \["Open Source", "Closed Source"\]/);
  assert.match(explorerSource, /\["Firmware", getLatencySourceStatus\(item\)\]/);
  // Detail fields are built as tuples so empty ones can be filtered out.
  assert.match(explorerSource, /function isEmptyLatencyDetailValue/);
  assert.match(explorerSource, /\.filter\(\(\[, value\]\) => !isEmptyLatencyDetailValue\(value\)\)/);
  assert.doesNotMatch(explorerSource, /Open Source Firmware/);
});

test("product links use verified product or source URLs", () => {
  assert.match(explorerSource, /const buyUrl = normalizeExternalProductUrl\(item\.buyUrl\)/);
  assert.match(explorerSource, /const sourceUrl = normalizeExternalProductUrl\(item\.sourceUrl\)/);
  assert.match(explorerSource, /\/\^https\?:\\\/\\\/\/i\.test\(buyUrl\)/);
  assert.doesNotMatch(explorerSource, /item\.buyUrl \|\| item\.link/);
});

test("external Shopify product links avoid the ReStock same-store matcher", () => {
  assert.match(explorerSource, /function normalizeExternalProductUrl\(value\)/);
  assert.match(explorerSource, /url\.origin !== window\.location\.origin/);
  assert.match(explorerSource, /"\/%70roducts\/"/);
});

test("controller adapter input filter is only active for controller adapters", () => {
  assert.match(explorerSource, /function syncLatencyAdapterInputAvailability/);
  assert.match(explorerSource, /latencyRefs\.categorySelect\.value === "Controller Adapter"/);
  assert.match(explorerSource, /latencyRefs\.adapterInputSelect\.disabled = !enabled/);
  assert.match(explorerSource, /adapterInput:\s*latencyRefs\.categorySelect\.value === "Controller Adapter"\s*\?\s*latencyRefs\.adapterInputSelect\.value\s*:\s*""/);
});

test("face and home button filters are only active for controllers and arcade sticks", () => {
  assert.match(explorerSource, /function syncLatencyControllerAttributeAvailability/);
  assert.match(explorerSource, /new Set\(\["Controller", "Arcade Stick"\]\)/);
  assert.match(explorerSource, /latencyRefs\.faceButtonsSelect\.disabled = !enabled/);
  assert.match(explorerSource, /latencyRefs\.homeButtonSelect\.disabled = !enabled/);
  assert.match(explorerSource, /faceButtons:\s*isLatencyControllerAttributeCategory\(latencyRefs\.categorySelect\.value\)\s*\?\s*latencyRefs\.faceButtonsSelect\.value\s*:\s*""/);
  assert.match(explorerSource, /homeButton:\s*isLatencyControllerAttributeCategory\(latencyRefs\.categorySelect\.value\)\s*\?\s*latencyRefs\.homeButtonSelect\.value\s*:\s*""/);
});

test("controller adapter input options sort alphabetically", () => {
  assert.match(explorerSource, /function sortLatencyAdapterInputs\(values\) {\s*return uniqueSorted\(values\);\s*}/);
});

test("output mode filters normalize aliases and split comma-separated modes", () => {
  assert.match(explorerSource, /LATENCY_OUTPUT_MODE_ALIASES/);
  assert.match(explorerSource, /function splitLatencyOutputModeText/);
  assert.match(explorerSource, /function getLatencyOutputModes/);
  assert.match(explorerSource, /"pc",\s*"DInput"/i);
  assert.match(explorerSource, /"usb",\s*"DInput"/i);
  assert.match(explorerSource, /"dinput",\s*"DInput"/i);
  assert.match(explorerSource, /"xinput",\s*"XInput"/i);
  assert.match(explorerSource, /splitLatencyOutputModeText\(value\)/);
  assert.doesNotMatch(explorerSource, /\["console",\s*"Console"\]/i);
  assert.doesNotMatch(explorerSource, /LATENCY_OUTPUT_MODE_ORDER[\s\S]*"Console"/);
});

test("connection filters distinguish wired, bluetooth, and 2.4 ghz wireless", () => {
  assert.match(explorerSource, /Wireless BT/);
  assert.match(explorerSource, /Wireless 2\.4GHz/);
  assert.match(explorerSource, /function getLatencyConnectionFilterValue/);
  assert.match(explorerSource, /variantMatchesLatencyFilters\(\s*variant,\s*filters\.connection/);
});

test("rank columns use catalog-global ranks instead of filtered result ranks", () => {
  assert.match(explorerSource, /assignLatencyDisplayRanks\(latencyState\.items\)/);
  assert.doesNotMatch(explorerSource, /assignLatencyDisplayRanks\(filtered\)/);
  assert.match(explorerSource, /overallRank:\s*item\.overallRank/);
  assert.match(explorerSource, /modeRank:\s*item\.modeRank/);
  assert.match(explorerSource, /Ranked by average latency across all results/);
  assert.match(explorerSource, /Ranked by average latency within all \$\{item\.rankMode\} results/);
});

test("latency map hover lens separates dense points without changing mark size", () => {
  assert.match(explorerSource, /const LATENCY_MARK_SIZE = 4;/);
  assert.match(explorerSource, /const LATENCY_POINT_MAGNIFY_RANGE = 58;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_RADIUS = 76;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_SCALE = 2\.8;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_HORIZONTAL_SPLAY = 18;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_VERTICAL_LIFT = 30;/);
  assert.match(explorerSource, /function getLatencyLensPosition\(point, cursor, bounds, peakLift = 0, isAnchor = false\)/);
  assert.match(explorerSource, /if \(isAnchor\) \{\s*return \{ x: base\.x, y: base\.y, strength: 1 \};\s*\}/);
  assert.match(explorerSource, /const rainbowLift = peakLift \* Math\.sin\(arcProgress \* Math\.PI\)/);
  assert.match(explorerSource, /const anchorPoint = nearest && nearestDistance <= LATENCY_POINT_MAGNIFY_RANGE \? nearest : null/);
  assert.match(explorerSource, /setLatencyPointDisplayPosition\(point, lens\.x, lens\.y\)/);
  // Hovering names the device in the readout line instead of a floating tooltip.
  assert.match(explorerSource, /latencyRefs\.readout\.textContent = describeLatencyItem\(item\)/);
  assert.doesNotMatch(explorerSource, /latencyTooltip/);
  for (const markup of bothMarkups) {
    assert.match(markup, /<div class="svc-readout" id="latencyReadout" aria-live="polite">Point at a device<\/div>/);
  }
});

test("latency map draws with the layer's chart classes", () => {
  for (const className of ["svc-grid-line", "svc-guide-line", "svc-axis-text", "svc-ref-line", "svc-ref-label", "svc-cursor", "svc-mark"]) {
    assert.match(explorerSource, new RegExp(`class="${className}`));
  }
  assert.match(explorerSource, /AVERAGE MS, LOG SCALE/);
  assert.match(explorerSource, /MEDIAN \$\{/);
  assert.match(explorerSource, /const medianAverage = getLatencyMedianAverage\(allPlotItems\)/);
  assert.match(explorerSource, /LATENCY_TIER_BOUNDS = \[1, 2, 5, 10, 16\.67, 33\.33\]/);
});

test("latency map keeps mouse-wheel zoom, the window slider and the pan bar", () => {
  for (const markup of bothMarkups) {
    assert.match(markup, /id="latencyXZoomSlider" class="svc-range" type="range" min="0" max="100"/);
    assert.match(markup, /id="latencyXPanScrollbar" class="latency-pan"/);
    assert.match(markup, /id="latencyXPanTrack" class="latency-pan-fill"/);
  }
  assert.match(explorerSource, /function handleLatencyScatterWheel/);
  assert.match(explorerSource, /latencyRefs\.scatter\.addEventListener\("wheel", handleLatencyScatterWheel, \{ passive: false \}\)/);
  assert.match(explorerSource, /LATENCY_X_ZOOM_MAX = 100/);
  assert.match(explorerSource, /LATENCY_X_ZOOM_MIN_LOG_RATIO = 0\.04/);
  assert.match(explorerSource, /event\.clientX - latencyScatterLayout\.clientChartLeft/);
  assert.match(explorerSource, /setLatencyXZoomLevel\(latencyState\.xZoomLevel - delta \* LATENCY_X_ZOOM_STEP, getLatencyScatterCursorRatio\(event\)\)/);
  assert.match(explorerSource, /latencyRefs\.xPanScrollbar\.scrollLeft \/ maxScroll/);
  assert.match(explorerSource, /latencyRefs\.xPanScrollbar\.classList\.toggle\("is-zoomed", isZoomed\)/);
  assert.match(explorerStyles, /\.latency-svc \.latency-pan:not\(\.is-zoomed\) \{\s*display: none;/);
});

test("Shopify uses one fully scoped CSS bundle that carries the service-menu layer", () => {
  assert.doesNotMatch(shopifyMarkup, /['"]reflex\.css['"]/);
  assert.doesNotMatch(shopifyMarkup, /['"]service-menu\.css['"]/);
  assert.doesNotMatch(shopifyStyles, /@import\s+url\(["']?reflex\.css/);
  assert.match(shopifyStyles, /\.input-latency-explorer-app\s*\{[^}]*--brand-primary:\s*#5000dc/s);
  assert.match(shopifyStyles, /\.input-latency-explorer-app:where\(\[data-reflex-theme="midnight"\]\) \.svc/);
  // The page rules come after the layer so they can refine it.
  const layer = shopifyStyles.search(/\.input-latency-explorer-app \.svc\s*\{/);
  const pageRules = shopifyStyles.search(/\.input-latency-explorer-app \.latency-svc \.latency-action\s*\{/);
  assert.ok(layer > 0, "the scoped service-menu layer is missing");
  assert.ok(pageRules > layer, "the latency page rules must follow the service-menu layer");
});
