const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");

const explorerSource = fs.readFileSync("docs/assets/latency.js", "utf8");
const explorerStyles = fs.readFileSync("docs/assets/input-latency.css", "utf8");
const shopifyStyles = fs.readFileSync("shopify/assets/input-latency-explorer.css", "utf8");
const reflexStyles = fs.readFileSync("docs/assets/reflex.css", "utf8");
const explorerMarkup = fs.readFileSync("docs/latency.html", "utf8");
const shopifyMarkup = fs.readFileSync("shopify/sections/input-latency-explorer.liquid", "utf8");
const explorerAssets = `${explorerSource}\n${explorerStyles}`;

test("latency map dot click pins selection instead of filtering search", () => {
  assert.match(explorerSource, /selectedItemId/);
  assert.match(explorerSource, /function selectLatencyScatterPoint/);
  assert.match(explorerSource, /function clearLatencyScatterSelection/);
  assert.doesNotMatch(explorerSource, /latencyRefs\.searchInput\.value\s*=\s*item\.name/);
});

test("latency map selection links points to expandable result cards", () => {
  assert.match(explorerSource, /card\.dataset\.itemId\s*=\s*item\.id/);
  assert.match(explorerSource, /data-display-variant-id/);
  assert.match(explorerAssets, /\.latency-card\.is-selected/);
  assert.match(explorerAssets, /\.latency-point\.is-selected/);
});

test("latency map dot click narrows and expands the list without a separate selected-result pane", () => {
  assert.doesNotMatch(explorerMarkup, /id="latencySelectedResult"/);
  assert.doesNotMatch(shopifyMarkup, /id="latencySelectedResult"/);
  assert.doesNotMatch(explorerSource, /selectedResult:\s*document\.getElementById\("latencySelectedResult"\)/);
  assert.doesNotMatch(explorerSource, /function renderLatencySelectedResult/);
  assert.doesNotMatch(explorerSource, /renderLatencySelectedResult\(item\)/);
  assert.match(explorerSource, /renderLatencyItems\(latencyState\.filtered\)/);
  assert.match(explorerSource, /items\.filter\(\(item\) => item\.id === latencyState\.selectedItemId\)/);
});

test("latency map click accepts the currently lensed point as the target", () => {
  assert.match(explorerSource, /function getLatencyScatterClickPoint/);
  assert.match(explorerSource, /const hitTarget = latencyActiveScatterPoint\s*\|\|\s*event\.target\.closest\("\.latency-point"\)\s*\|\|\s*event\.target\.closest\("\.latency-point-hitarea"\)/);
});

test("latency map points expose larger invisible click targets", () => {
  assert.match(explorerSource, /LATENCY_POINT_HIT_RADIUS/);
  assert.match(explorerSource, /class:\s*"latency-point-hitarea"/);
  assert.match(explorerAssets, /\.latency-point-hitarea/);
});

test("latency map hover lens separates dense points without changing dot size", () => {
  assert.doesNotMatch(explorerSource, /LATENCY_POINT_MAGNIFIED_RADIUS/);
  assert.match(explorerSource, /const LATENCY_POINT_MAGNIFY_RANGE = 58;/);
  assert.match(explorerSource, /const LATENCY_POINT_HIT_RADIUS = 22;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_RADIUS = 76;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_SCALE = 2\.8;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_HORIZONTAL_SPLAY = 18;/);
  assert.match(explorerSource, /const LATENCY_POINT_LENS_VERTICAL_LIFT = 30;/);
  assert.match(explorerSource, /function getLatencyLensPosition/);
  assert.match(explorerSource, /function getLatencyLensPosition\(point, cursor, bounds, peakLift = 0, isAnchor = false\)/);
  assert.match(explorerSource, /if \(isAnchor\) \{\s*return \{ x: base\.x, y: base\.y, strength: 1 \};\s*\}/);
  assert.match(explorerSource, /const arcProgress = clampLatencyValue\(\(base\.x - cursor\.x \+ LATENCY_POINT_LENS_RADIUS\) \/ \(LATENCY_POINT_LENS_RADIUS \* 2\), 0, 1\)/);
  assert.match(explorerSource, /const rainbowLift = peakLift \* Math\.sin\(arcProgress \* Math\.PI\)/);
  assert.match(explorerSource, /let y = base\.y - rainbowLift/);
  assert.match(explorerSource, /const requestedPeakLift = maxLensStrength \* LATENCY_POINT_LENS_VERTICAL_LIFT/);
  assert.match(explorerSource, /const peakLift = Math\.min\(requestedPeakLift, Math\.max\(0, minLensBaseY - bounds\.top\)\)/);
  assert.match(explorerSource, /const anchorPoint = nearest && nearestDistance <= LATENCY_POINT_MAGNIFY_RANGE \? nearest : null/);
  assert.match(explorerSource, /getLatencyLensPosition\(point, cursor, bounds, peakLift, point === anchorPoint\)/);
  assert.match(explorerSource, /setLatencyPointDisplayPosition\(point, lens\.x, lens\.y, hitAreas\)/);
  assert.match(explorerSource, /point\.setAttribute\("r", point\.dataset\.baseRadius \|\| LATENCY_POINT_BASE_RADIUS\)/);
  assert.doesNotMatch(explorerSource, /Math\.sin\(angle\)/);
  assert.doesNotMatch(explorerSource, /cursor\.y \+ \(base\.y - cursor\.y\) \* scale/);
});

test("latency map keeps exact base coordinates at rest and explains cursor lens", () => {
  assert.doesNotMatch(explorerSource, /LATENCY_POINT_SPREAD/);
  assert.doesNotMatch(explorerSource, /function getLatencySpreadPositions/);
  assert.match(explorerSource, /"data-base-cx": pointX\.toFixed\(2\)/);
  assert.match(explorerSource, /"data-base-cy": pointY\.toFixed\(2\)/);
  assert.doesNotMatch(explorerMarkup, /Dots spread slightly when results overlap\./);
  assert.doesNotMatch(shopifyMarkup, /Dots spread slightly when results overlap\./);
  assert.match(explorerMarkup, /Hovering over dense areas fans points horizontally and lifts them in a tapered arc for selection\./);
  assert.match(shopifyMarkup, /Hovering over dense areas fans points horizontally and lifts them in a tapered arc for selection\./);
});

test("latency explorer filters are ordered and consistently titled", () => {
  for (const markup of [explorerMarkup, shopifyMarkup]) {
    assert.match(markup, /Input Latency Explorer/);
    assert.match(markup, /recorded on MiSTer FPGA, but applicable to devices that poll USB at 1 ms/);
    assert.match(markup, /Amazon product links on this page are affiliate links\./);
    assert.match(markup, /Face Buttons/);
    assert.match(markup, /Home Button/);
    assert.match(markup, /Controller Adapter Input/);
    assert.match(markup, /Latency Tier \(Average\)/);
    assert.match(markup, /<select id="latencyAdapterInputSelect" disabled>/);
    assert.match(markup, /<select id="latencyFaceButtonsSelect" disabled>/);
    assert.match(markup, /<select id="latencyHomeButtonSelect" disabled>/);
    assert.doesNotMatch(markup, /Result source/);
    assert.doesNotMatch(markup, /data-result-type/);
    assert.doesNotMatch(markup, /latencyDeviceTypeSelect/);
    assert.doesNotMatch(markup, /class="catalog-meta latency-meta"/);
    assert.doesNotMatch(markup, /published and unreleased/i);

    const labels = [
      "Search",
      "Category",
      "Face Buttons",
      "Home Button",
      "Controller Adapter Input",
      "Output Mode",
      "Connection",
      "Latency Tier (Average)",
      "Sale Status",
      "Firmware",
      "Sort",
    ];
    const positions = labels.map((label) => markup.indexOf(`>${label}</label>`));
    assert.equal(positions.every((position) => position >= 0), true);
    assert.deepEqual([...positions].sort((left, right) => left - right), positions);
    assert.doesNotMatch(markup, />Source<\/label>/);
    assert.match(markup, />All firmware<\/option>/);
  }
});

test("latency explorer includes a collapsed testing methodology blurb below the hero header", () => {
  for (const markup of [explorerMarkup, shopifyMarkup]) {
    assert.match(markup, /<div class="hero-stats latency-hero-stats" id="latencyHeroStats"><\/div>\s*<details class="latency-methodology">/);
    assert.match(markup, /<summary>Testing Methodology<\/summary>/);
    assert.match(markup, /ATMega 32u4/i);
    assert.match(markup, /custom MiSTer NES core/i);
    assert.match(markup, /User I\/O pin/i);
    assert.match(markup, /CSV captures are summarized with R/i);
    assert.match(markup, /1 ms USB polling/i);
  }
  assert.match(explorerStyles, /\.latency-methodology/);
  assert.match(explorerStyles, /\.latency-methodology summary/);
  assert.match(explorerStyles, /\.latency-methodology-body/);
});

test("latency explorer normalizes forced view URLs back to the canonical latency page", () => {
  assert.match(explorerSource, /function normalizeLatencyCanonicalPath/);
  assert.match(explorerSource, /params\.get\("view"\) !== "input-latency-explorer"/);
  assert.match(explorerSource, /window\.history\.replaceState\(window\.history\.state, document\.title, nextUrl\)/);
  assert.match(explorerSource, /normalizeLatencyCanonicalPath\(\);/);
});

test("latency explorer leaves most recent 5 pane expanded between hero and filters", () => {
  for (const markup of [explorerMarkup, shopifyMarkup]) {
    const heroPosition = markup.indexOf('<section class="hero">');
    const recentPosition = markup.indexOf('<details class="latency-recent-panel" id="latencyRecentPanel" open>');
    const filtersPosition = markup.indexOf('<section class="controls-panel latency-controls">');

    assert.notEqual(heroPosition, -1);
    assert.notEqual(recentPosition, -1);
    assert.notEqual(filtersPosition, -1);
    assert.equal(heroPosition < recentPosition && recentPosition < filtersPosition, true);
    assert.match(markup, /<summary>\s*<span>Most Recent 5<\/span>\s*<strong id="latencyRecentSummary">Loading<\/strong>\s*<\/summary>/);
    assert.match(markup, /<div class="latency-recent-list" id="latencyRecentList"><\/div>/);
  }

  assert.match(explorerSource, /recentPanel:\s*document\.getElementById\("latencyRecentPanel"\)/);
  assert.match(explorerSource, /function getMostRecentLatencyItems\(items, limit = 5\)/);
  assert.match(explorerSource, /function renderLatencyRecentItems\(items\)/);
  assert.match(explorerSource, /getMostRecentLatencyItems\(latencyState\.items\)/);
  assert.match(explorerSource, /function selectLatencyRecentItem\(itemId, displayVariantId = ""\)/);
  assert.match(explorerSource, /data-recent-item-id/);
  assert.match(explorerSource, /latencyRefs\.recentList\.addEventListener\("click"/);
  assert.match(explorerSource, /event\.stopPropagation\(\);[\s\S]*selectLatencyRecentItem\(target\.dataset\.recentItemId/);
  assert.match(explorerSource, /syncLatencyResultSelection\(\{ scroll: true \}\)/);
  assert.match(explorerStyles, /\.latency-recent-panel/);
  assert.match(explorerStyles, /\.latency-recent-list/);
  assert.match(explorerStyles, /\.latency-recent-item/);
});

test("list and recent card titles are not clipped on descenders", () => {
  const titleRule = /\.latency-grid\.view-list \.latency-card \.card-title \{(?<body>[\s\S]*?)\n\}/.exec(explorerStyles)?.groups?.body || "";
  const linkRule = /\.latency-grid\.view-list \.latency-card \.card-title-link \{(?<body>[\s\S]*?)\n\}/.exec(explorerStyles)?.groups?.body || "";
  const recentNameRule = /\.latency-recent-name \{(?<body>[\s\S]*?)\n\}/.exec(explorerStyles)?.groups?.body || "";

  assert.match(titleRule, /display:\s*block/);
  assert.match(titleRule, /white-space:\s*normal/);
  assert.match(titleRule, /overflow:\s*visible/);
  assert.match(titleRule, /line-height:\s*1\.5/);
  assert.match(titleRule, /padding-top:\s*2px/);
  assert.match(titleRule, /padding-bottom:\s*7px/);
  assert.doesNotMatch(titleRule, /-webkit-line-clamp/);
  assert.doesNotMatch(titleRule, /display:\s*-webkit-box/);

  assert.match(linkRule, /display:\s*inline/);
  assert.match(linkRule, /overflow:\s*visible/);
  assert.match(linkRule, /text-overflow:\s*clip/);
  assert.match(linkRule, /line-height:\s*inherit/);
  assert.doesNotMatch(linkRule, /display:\s*inline-block/);

  assert.match(recentNameRule, /display:\s*block/);
  assert.match(recentNameRule, /overflow:\s*visible/);
  assert.match(recentNameRule, /line-height:\s*1\.5/);
  assert.match(recentNameRule, /padding-top:\s*2px/);
  assert.match(recentNameRule, /padding-bottom:\s*7px/);
  assert.doesNotMatch(recentNameRule, /max-height/);
  assert.doesNotMatch(recentNameRule, /-webkit-line-clamp/);
});

test("open source firmware is labeled as open source in filters, tags, and details", () => {
  assert.match(explorerSource, /LATENCY_SOURCE_STATUS_ORDER = \["Open Source", "Closed Source"\]/);
  assert.match(explorerSource, /createLatencyTag\("Open Source"/);
  assert.match(explorerSource, /value:\s*"Open Source"/);
  assert.match(explorerSource, /createLatencyDetailItem\("Firmware", getLatencySourceStatus\(item\)/);
  assert.doesNotMatch(explorerSource, /Open Source Firmware/);
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

test("latency window labels use result counts instead of point shorthand", () => {
  assert.match(explorerSource, /RESULTS/);
  assert.doesNotMatch(explorerSource, /\bpts\b/i);
});

test("latency map has tier guide, smooth mouse-wheel horizontal zoom, and filtered median line", () => {
  assert.match(explorerMarkup, /latencyPlotTierGuide/);
  assert.match(shopifyMarkup, /latencyPlotTierGuide/);
  assert.match(explorerMarkup, /latency-zoom-header/);
  assert.match(shopifyMarkup, /latency-zoom-header/);
  assert.match(explorerMarkup, /max="100"/);
  assert.match(explorerMarkup, /id="latencyXPanScrollbar"/);
  assert.match(shopifyMarkup, /id="latencyXPanScrollbar"/);
  assert.match(explorerMarkup, /id="latencyXPanTrack"/);
  assert.match(explorerMarkup, /class="latency-tooltip" id="latencyTooltip" hidden><\/div>\s*<\/div>\s*<div id="latencyXPanScrollbar"[\s\S]*<p class="latency-plot-note">Each point is an input device\./);
  assert.match(shopifyMarkup, /class="latency-tooltip" id="latencyTooltip" hidden><\/div>\s*<\/div>\s*<div id="latencyXPanScrollbar"[\s\S]*<p class="latency-plot-note">Each point is an input device\./);
  assert.match(explorerSource, /function handleLatencyScatterWheel/);
  assert.match(explorerSource, /latencyRefs\.scatter\.addEventListener\("wheel", handleLatencyScatterWheel/);
  assert.match(explorerSource, /LATENCY_X_ZOOM_MAX = 100/);
  assert.match(explorerSource, /LATENCY_X_ZOOM_MIN_LOG_RATIO = 0\.04/);
  assert.match(explorerSource, /function getLatencyScatterCursorRatio/);
  assert.match(explorerSource, /event\.clientX - latencyScatterLayout\.clientChartLeft/);
  assert.match(explorerSource, /setLatencyXZoomLevel\(latencyState\.xZoomLevel - delta \* LATENCY_X_ZOOM_STEP, getLatencyScatterCursorRatio\(event\)\)/);
  assert.match(explorerSource, /function setLatencyXPanRatio/);
  assert.match(explorerSource, /latencyRefs\.xPanScrollbar\.addEventListener\("scroll"/);
  assert.match(explorerSource, /latencyRefs\.xPanScrollbar\.scrollLeft \/ maxScroll/);
  assert.match(explorerSource, /latencyRefs\.xPanScrollbar\.classList\.toggle\("is-zoomed", isZoomed\)/);
  assert.match(explorerStyles, /\.latency-pan-scrollbar\.is-zoomed/);
  assert.match(explorerStyles, /overflow-x:\s*auto/);
  assert.match(explorerStyles, /\.latency-pan-scrollbar \{[\s\S]*width:\s*100%/);
  assert.match(explorerStyles, /\.latency-pan-scrollbar \{[\s\S]*margin:\s*8px 0 0/);
  assert.doesNotMatch(explorerStyles, /\.latency-pan-scrollbar \{[\s\S]*calc\(100% \+ 36px\)/);
  assert.doesNotMatch(explorerSource, /LATENCY_X_ZOOM_WINDOWS/);
  assert.doesNotMatch(explorerSource, /xZoomIndex/);
  assert.match(explorerSource, /function getLatencyMedianAverage/);
  assert.match(explorerSource, /const medianAverage = getLatencyMedianAverage\(allPlotItems\)/);
  assert.match(explorerSource, /latency-median-line/);
  assert.match(explorerSource, /Median/);
});

test("latency median line uses a high-contrast light-theme color", () => {
  for (const styles of [explorerStyles, shopifyStyles]) {
    assert.match(styles, /--latency-median-color:\s*rgba\(230, 255, 30, 0\.62\)/);
    assert.match(styles, /--latency-median-color:\s*#5000dc/);
    assert.match(styles, /stroke:\s*var\(--latency-median-color\)/);
    assert.match(styles, /stroke-width:\s*1\.75/);
  }
});

test("theme toggle text overrides storefront button colors", () => {
  for (const styles of [reflexStyles, shopifyStyles]) {
    assert.match(styles, /\.rx-theme-toggle button\s*\{[^}]*color:\s*var\(--muted\)/s);
    assert.match(styles, /\.rx-theme-toggle button\[aria-pressed="true"\]\s*\{[^}]*color:\s*#1c1430/s);
    assert.doesNotMatch(styles, /:where\(\.rx-theme-toggle button/);
  }
});

test("Shopify uses one fully scoped CSS bundle", () => {
  assert.doesNotMatch(shopifyMarkup, /['"]reflex\.css['"]/);
  assert.doesNotMatch(shopifyStyles, /@import\s+url\(["']?reflex\.css/);
  assert.match(shopifyStyles, /\.input-latency-explorer-app\s*\{[^}]*--brand-primary:\s*#5000dc/s);
});

test("hero title pane shows updated next to best average", () => {
  assert.match(explorerSource, /label:\s*"Best Average"/);
  assert.match(explorerSource, /label:\s*"Updated"/);
  assert.doesNotMatch(explorerSource, /label:\s*"Best average"/);
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
  assert.match(explorerSource, /variantMatchesLatencyFilters\(variant, connection/);
});

test("list mode summarizes controllers tested over usb plus wireless transports", () => {
  assert.match(explorerSource, /function getLatencyConnectionModeSummary/);
  assert.match(explorerSource, /USB \+ BT/);
  assert.match(explorerSource, /USB \+ 2\.4GHz/);
  assert.match(explorerSource, /createLatencyMetric\("Mode", getLatencyListModeDisplay\(item\) \|\| "-", "metric-mode"\)/);
});

test("rank badges use catalog-global ranks instead of filtered result ranks", () => {
  assert.match(explorerSource, /assignLatencyDisplayRanks\(latencyState\.items\)/);
  assert.doesNotMatch(explorerSource, /assignLatencyDisplayRanks\(filtered\)/);
  assert.match(explorerSource, /overallRank:\s*item\.overallRank/);
  assert.match(explorerSource, /modeRank:\s*item\.modeRank/);
  assert.doesNotMatch(explorerSource, /overallRank:\s*selected\.overallRank/);
  assert.doesNotMatch(explorerSource, /modeRank:\s*selected\.modeRank/);
  assert.match(explorerSource, /title:\s*"Ranked by average latency across all results"/);
  assert.match(explorerSource, /title:\s*`Ranked by average latency within all \$\{item\.rankMode\} results`/);
});

test("tile cards are compact enough for dense browsing", () => {
  assert.match(explorerStyles, /contain-intrinsic-size:\s*2[0-5]\dpx/);
  assert.match(explorerStyles, /height:\s*2[0-5]\dpx/);
});

test("tile cards reserve the subtitle line and show category before connection", () => {
  assert.match(explorerSource, /const parts = \[\s*category,/);
  assert.match(explorerSource, /subtitle\.textContent = subtitleText \|\| " "/);
  assert.doesNotMatch(explorerSource, /subtitle\.hidden = true/);
  assert.match(explorerStyles, /\.latency-grid\.view-card \.latency-card \.card-subtitle \{[\s\S]*min-height:/);
});

test("latency tiers have compact cartoon icon hooks", () => {
  assert.match(explorerSource, /LATENCY_TIER_ICON_LABELS/);
  assert.match(explorerSource, /function createLatencyTierIcon/);
  assert.match(explorerSource, /createLatencyMetric\("Tier", item\.averageTier \|\| "-", "metric-tier", createLatencyTierIcon\(item\.averageTier\)\)/);
  assert.match(explorerStyles, /\.latency-tier-icon/);
  for (const tier of ["diamond", "platinum", "gold", "silver", "bronze", "copper", "rust"]) {
    assert.match(explorerStyles, new RegExp(`\\.latency-tier-icon\\.tier-${tier}`));
  }
  assert.match(explorerStyles, /\.latency-tier-icon\.tier-gold[\s\S]*clip-path:\s*polygon/);
  assert.match(explorerStyles, /\.latency-tier-icon\.tier-bronze[\s\S]*clip-path:\s*polygon/);
  assert.match(explorerStyles, /\.latency-tier-icon\.tier-diamond[\s\S]*clip-path:\s*polygon\(22% 8%, 78% 8%, 98% 36%, 50% 98%, 2% 36%\)/);
  assert.match(explorerStyles, /\.latency-tier-icon\.tier-copper[\s\S]*border-radius:\s*50%/);
  assert.match(explorerStyles, /\.latency-tier-icon\.tier-rust[\s\S]*border-radius:\s*0/);
  assert.doesNotMatch(explorerStyles, /\.latency-tier-icon\.tier-gold[\s\S]{0,120}border-radius:\s*50%/);
});

test("hero affiliate disclosure matches adjacent hero link text size", () => {
  assert.match(explorerStyles, /\.hero-linkline\.latency-affiliate-note \{[\s\S]*font-size:\s*0\.98rem/);
  assert.doesNotMatch(explorerStyles, /\.latency-affiliate-note \{[^}]*font-size:\s*0\.82rem/);
});

test("rank badges and title links align consistently", () => {
  assert.match(explorerSource, /`#\$\{latencyNumberFormatter\.format\(item\.overallRank\)\} Overall`/);
  assert.doesNotMatch(explorerSource, /#\$\{latencyNumberFormatter\.format\(item\.overallRank\)\} overall/);
  assert.match(explorerStyles, /\.latency-grid\.view-list \.latency-title-row \.card-tags \{[\s\S]*margin-left:\s*auto/);
  assert.match(explorerStyles, /\.card-title-link \{[\s\S]*width:\s*fit-content/);
});

test("list metrics stay compact enough for long title tag rows", () => {
  assert.match(explorerStyles, /\.latency-grid\.view-list \.latency-card \.card-frame \{[\s\S]*grid-template-columns:\s*minmax\(320px,\s*1fr\) minmax\(340px,\s*390px\)/);
  assert.match(explorerStyles, /\.latency-grid\.view-list \.latency-card \.latency-metrics \{[\s\S]*grid-template-columns:\s*96px 118px minmax\(110px,\s*1fr\)/);
  assert.match(explorerStyles, /\.latency-grid\.view-list \.latency-card \.latency-metrics \{[\s\S]*width:\s*min\(100%,\s*390px\)/);
});
