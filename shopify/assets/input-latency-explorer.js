const latencyState = {
  items: [],
  filtered: [],
  summary: null,
  sortDescending: false,
  xZoomLevel: 0,
  xPanRatio: 0.5,
  viewMode: "list",
  selectedItemId: "",
  selectedDisplayVariantId: "",
};

const latencyRefs = {
  searchInput: document.getElementById("latencySearchInput"),
  connectionSelect: document.getElementById("latencyConnectionSelect"),
  modeSelect: document.getElementById("latencyModeSelect"),
  adapterInputSelect: document.getElementById("latencyAdapterInputSelect"),
  faceButtonsSelect: document.getElementById("latencyFaceButtonsSelect"),
  homeButtonSelect: document.getElementById("latencyHomeButtonSelect"),
  categorySelect: document.getElementById("latencyCategorySelect"),
  saleStatusSelect: document.getElementById("latencySaleStatusSelect"),
  sourceStatusSelect: document.getElementById("latencySourceStatusSelect"),
  tierSelect: document.getElementById("latencyTierSelect"),
  sortSelect: document.getElementById("latencySortSelect"),
  sortDirectionToggle: document.getElementById("latencySortDirectionToggle"),
  heroStats: document.getElementById("latencyHeroStats"),
  recentPanel: document.getElementById("latencyRecentPanel"),
  recentSummary: document.getElementById("latencyRecentSummary"),
  recentList: document.getElementById("latencyRecentList"),
  statusBanner: document.getElementById("latencyStatusBanner"),
  grid: document.getElementById("latencyGrid"),
  cardTemplate: document.getElementById("latencyCardTemplate"),
  viewOptions: document.querySelectorAll("[data-latency-view-mode]"),
  xZoomControl: document.querySelector(".latency-zoom-control"),
  xZoomSlider: document.getElementById("latencyXZoomSlider"),
  xPanScrollbar: document.getElementById("latencyXPanScrollbar"),
  xPanTrack: document.getElementById("latencyXPanTrack"),
  xZoomLabel: document.getElementById("latencyXZoomLabel"),
  scatter: document.getElementById("latencyScatter"),
  tooltip: document.getElementById("latencyTooltip"),
};

const latencyNumberFormatter = new Intl.NumberFormat("en-US");
const latencyMsFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const latencyPercentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const latencyDateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
});
const latencyShortDateFormatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
});
const latencyTextCollator = new Intl.Collator("en-US", {
  numeric: true,
  sensitivity: "base",
});

const DEFAULT_LATENCY_DATA_URL = "./data/latency.json";
const LATENCY_TIER_ORDER = ["Diamond", "Platinum", "Gold", "Silver", "Bronze", "Copper", "Rust"];
const LATENCY_TIER_LABELS = {
  Diamond: "Diamond (0-1 ms)",
  Platinum: "Platinum (1-2 ms)",
  Gold: "Gold (2-5 ms)",
  Silver: "Silver (5-10 ms)",
  Bronze: "Bronze (10-16.67 ms)",
  Copper: "Copper (16.67-33.33 ms)",
  Rust: "Rust (33.33+ ms)",
};
const LATENCY_SALE_STATUS_ORDER = ["Actively sold", "Discontinued", "Unknown"];
const LATENCY_SOURCE_STATUS_ORDER = ["Open Source", "Closed Source"];
const LATENCY_CONNECTION_ORDER = ["Wired", "Wireless BT", "Wireless 2.4GHz", "Wireless"];
const LATENCY_TIER_ICON_LABELS = {
  Diamond: "Diamond tier",
  Platinum: "Platinum tier",
  Gold: "Gold tier",
  Silver: "Silver tier",
  Bronze: "Bronze tier",
  Copper: "Copper tier",
  Rust: "Rust tier",
};
const LATENCY_OUTPUT_MODE_ALIASES = new Map([
  ["pc", "DInput"],
  ["dinput", "DInput"],
  ["dinpit", "DInput"],
  ["directinput", "DInput"],
  ["direct input", "DInput"],
  ["xinput", "XInput"],
  ["xinpit", "XInput"],
  ["x-input", "XInput"],
  ["switch", "Switch"],
  ["switch 2", "Switch 2"],
  ["ps3", "PS3"],
  ["ps4", "PS4"],
  ["ps5", "PS5"],
  ["wii u", "Wii U"],
  ["xbox 360", "Xbox 360"],
  ["xbox one", "Xbox One"],
  ["xbox series x", "Xbox Series X"],
  ["android", "Android"],
  ["macos", "macOS"],
  ["mac", "macOS"],
  ["usb", "DInput"],
]);
const LATENCY_OUTPUT_MODE_ORDER = [
  "DInput",
  "XInput",
  "Switch",
  "Switch 2",
  "PS3",
  "PS4",
  "PS5",
  "Wii U",
  "Xbox 360",
  "Xbox One",
  "Xbox Series X",
  "Android",
  "macOS",
];
const LATENCY_ADAPTER_INPUT_EXCLUDED_TYPES = new Set([
  "Wired Controller",
  "Wireless Controller",
  "Controller",
  "Controller Adapter",
  "Controller Conversion",
  "Wired Arcade Stick",
  "Wireless Arcade Stick",
  "Arcade Stick",
  "Arcade Stick Encoder",
  "Joystick",
  "Joystick Encoder",
  "Supergun",
  "Unknown",
  "Uncategorized",
]);
const LATENCY_CONTROLLER_ATTRIBUTE_CATEGORIES = new Set(["Controller", "Arcade Stick"]);
const LATENCY_SVG_NS = "http://www.w3.org/2000/svg";
const LATENCY_LOG_X_TICKS = [0.5, 1, 2, 5, 10, 20, 50, 100, 200];
const LATENCY_X_ZOOM_MAX = 100;
const LATENCY_X_ZOOM_STEP = 0.04;
const LATENCY_X_ZOOM_MIN_LOG_RATIO = 0.04;
const LATENCY_POINT_BASE_RADIUS = 3.8;
const LATENCY_POINT_MAGNIFY_RANGE = 58;
const LATENCY_POINT_HIT_RADIUS = 22;
const LATENCY_POINT_LENS_RADIUS = 76;
const LATENCY_POINT_LENS_SCALE = 2.8;
const LATENCY_POINT_LENS_HORIZONTAL_SPLAY = 18;
const LATENCY_POINT_LENS_VERTICAL_LIFT = 30;
const LATENCY_POINT_LENS_MAX_OFFSET = 74;
let latencyScatterResizeFrame = 0;
let latencyActiveScatterPoint = null;
let latencyScatterLayout = null;
let latencyPanScrollbarSyncing = false;

function normalizeLatencyUrl(value) {
  return String(value || "").trim();
}

function normalizeLatencyCanonicalPath() {
  if (typeof window === "undefined" || !window.location || !window.history) return;
  const canonicalPath = "/pages/latency";
  if (window.location.pathname !== canonicalPath) return;
  const params = new URLSearchParams(window.location.search);
  if (params.get("view") !== "input-latency-explorer") return;
  if (params.has("preview_theme_id") || params.has("oseid")) return;
  const nextUrl = `${canonicalPath}${window.location.hash || ""}`;
  window.history.replaceState(window.history.state, document.title, nextUrl);
}

normalizeLatencyCanonicalPath();

function getConfiguredLatencyDataUrl() {
  const globalUrl = normalizeLatencyUrl(globalThis.MISTER_LATENCY_DATA_URL);
  if (globalUrl) return globalUrl;

  const appShell = document.querySelector(".input-latency-explorer-app");
  return normalizeLatencyUrl(appShell && appShell.dataset ? appShell.dataset.latencyUrl : "");
}

function getLatencyDataUrl() {
  return getConfiguredLatencyDataUrl() || DEFAULT_LATENCY_DATA_URL;
}

async function fetchLatencyPayload(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

function showLatencyStatus(message) {
  latencyRefs.statusBanner.textContent = message;
  latencyRefs.statusBanner.hidden = false;
}

function hideLatencyStatus() {
  latencyRefs.statusBanner.hidden = true;
  latencyRefs.statusBanner.textContent = "";
}

function formatLatencyMs(value) {
  return Number.isFinite(value) ? `${latencyMsFormatter.format(value)} ms` : "-";
}

function formatLatencyPercent(value) {
  return Number.isFinite(value) ? `${latencyPercentFormatter.format(value)}%` : "-";
}

function parseLatencyDate(value) {
  if (!value) return null;
  const text = String(value).trim();
  const isoDate = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (isoDate) {
    const [, year, month, day] = isoDate;
    return new Date(Number(year), Number(month) - 1, Number(day)).getTime();
  }
  const slashDate = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(text);
  if (slashDate) {
    const [, month, day, year] = slashDate;
    return new Date(Number(year), Number(month) - 1, Number(day)).getTime();
  }
  const timestamp = Date.parse(text);
  return Number.isNaN(timestamp) ? null : timestamp;
}

function getLatencyDateSortValue(item) {
  return parseLatencyDate(item.dateAddedSort || item.dateAdded);
}

function formatLatencyDateAdded(item) {
  const timestamp = getLatencyDateSortValue(item);
  if (timestamp !== null) return latencyShortDateFormatter.format(new Date(timestamp));
  return item.dateAdded || "-";
}

function getMostRecentLatencyItems(items, limit = 5) {
  return [...items]
    .map((item) => ({ item, timestamp: getLatencyDateSortValue(item) }))
    .filter((entry) => entry.timestamp !== null)
    .sort((left, right) => {
      const dateResult = right.timestamp - left.timestamp;
      if (dateResult !== 0) return dateResult;
      return latencyTextCollator.compare(left.item.name || "", right.item.name || "");
    })
    .slice(0, limit)
    .map((entry) => entry.item);
}

function createLatencyRecentItem(item) {
  const row = document.createElement("button");
  row.type = "button";
  row.className = `latency-recent-item tier-${sanitizeLatencyClass(item.averageTier)}`;
  row.dataset.recentItemId = item.id || "";
  row.dataset.recentDisplayVariantId = item.displayVariantId || "";
  row.setAttribute("aria-label", `Show details for ${item.name || "recent latency result"}`);

  const title = document.createElement("strong");
  title.className = "latency-recent-name";
  title.textContent = item.name || "Unknown controller";

  const meta = document.createElement("span");
  meta.className = "latency-recent-meta";
  meta.textContent = [formatLatencyDateAdded(item), buildLatencySubtitle(item)].filter(Boolean).join(" / ");

  const metrics = document.createElement("div");
  metrics.className = "latency-recent-metrics";

  const average = document.createElement("span");
  average.className = "latency-recent-ms";
  average.textContent = formatLatencyMs(item.averageMs);

  const tier = document.createElement("span");
  tier.className = "latency-recent-tier";
  tier.textContent = item.averageTier || "-";

  metrics.append(average, tier);
  row.append(title, meta, metrics);
  return row;
}

function renderLatencyRecentItems(items) {
  if (!latencyRefs.recentPanel || !latencyRefs.recentSummary || !latencyRefs.recentList) return;

  latencyRefs.recentList.innerHTML = "";
  if (!items.length) {
    latencyRefs.recentSummary.textContent = "No dated results";
    const empty = document.createElement("p");
    empty.className = "latency-recent-empty";
    empty.textContent = "No recently dated latency results are available.";
    latencyRefs.recentList.appendChild(empty);
    return;
  }

  latencyRefs.recentSummary.textContent = `${items.length} newest`;
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    fragment.appendChild(createLatencyRecentItem(item));
  }
  latencyRefs.recentList.appendChild(fragment);
}

function clearLatencyFilterControls() {
  latencyRefs.searchInput.value = "";
  latencyRefs.connectionSelect.value = "";
  latencyRefs.modeSelect.value = "";
  latencyRefs.adapterInputSelect.value = "";
  latencyRefs.faceButtonsSelect.value = "";
  latencyRefs.homeButtonSelect.value = "";
  latencyRefs.categorySelect.value = "";
  latencyRefs.saleStatusSelect.value = "";
  latencyRefs.sourceStatusSelect.value = "";
  latencyRefs.tierSelect.value = "";
}

function formatLatencyCount(value, singular, plural = `${singular}s`) {
  const label = value === 1 ? singular : plural;
  return `${latencyNumberFormatter.format(value)} ${label}`;
}

function isFiniteLatencyNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function clampLatencyValue(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function sanitizeLatencyClass(value) {
  return String(value || "unknown").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "unknown";
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((left, right) => latencyTextCollator.compare(left, right));
}

function uniqueSortedByOrder(values, orderValues) {
  const order = new Map(orderValues.map((value, index) => [value, index]));
  return Array.from(new Set(values.filter(Boolean))).sort((left, right) => {
    const leftOrder = order.has(left) ? order.get(left) : orderValues.length;
    const rightOrder = order.has(right) ? order.get(right) : orderValues.length;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return latencyTextCollator.compare(left, right);
  });
}

function getLatencyTierLabel(tier) {
  return LATENCY_TIER_LABELS[tier] || tier;
}

function getLatencyVariants(item) {
  return Array.isArray(item.modeVariants) && item.modeVariants.length ? item.modeVariants : [item];
}

function normalizeLatencyLabel(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function splitLatencyOutputModeText(value) {
  return normalizeLatencyLabel(value).split(/\s*[,;/]+\s*/).map(normalizeLatencyLabel).filter(Boolean);
}

function normalizeLatencyOutputMode(value) {
  const text = normalizeLatencyLabel(value);
  const key = text.toLowerCase();
  return LATENCY_OUTPUT_MODE_ALIASES.get(key) || text;
}

function sortLatencyOutputModes(values) {
  return uniqueSortedByOrder(values, LATENCY_OUTPUT_MODE_ORDER);
}

function getLatencyOutputModes(item) {
  return sortLatencyOutputModes(splitLatencyOutputModeText(item.outputMode).map(normalizeLatencyOutputMode));
}

function getLatencyTargetPlatform(item) {
  return getLatencyOutputModes(item)[0] || "";
}

function formatLatencyOutputModes(item) {
  const values = getLatencyOutputModes(item);
  return values.length ? values.join(", ") : "-";
}

function simplifyLatencyModeLabel(value) {
  let text = normalizeLatencyLabel(value);
  if (!text) return "";
  text = text.replace(/\s*\(via\b.*$/i, "");
  text = text.replace(/\s*\[.*?\]\s*$/g, "");
  text = text.replace(/^Wireless Wii Classic Receiver$/i, "Wii Classic Receiver");
  text = text.replace(/^Wiimote \/ Classic Controller Wireless Adapter$/i, "Wii Classic Adapter");
  text = text.replace(/^8Bitdo Wireless Bluetooth \(MacOS \/ Select \+ Right\)$/i, "Bluetooth");
  return text;
}

function getLatencyModeDisplay(item) {
  const simplified = simplifyLatencyModeLabel(item.modeDisplay || item.modeLabel || item.modeRaw || "");
  const outputModes = formatLatencyOutputModes(item);
  if (simplified === "USB" && outputModes === "DInput") return "USB";
  if (outputModes !== "-") return outputModes;
  return simplified;
}

function getLatencyConnectionModeSummary(item) {
  const labels = [];
  for (const variant of getLatencyVariants(item)) {
    const connection = getLatencyConnectionFilterValue(variant);
    let label = "";
    if (connection === "Wired") label = "USB";
    else if (connection === "Wireless BT") label = "BT";
    else if (connection === "Wireless 2.4GHz") label = "2.4GHz";
    else if (connection === "Wireless") label = "Wireless";
    if (label && !labels.includes(label)) labels.push(label);
  }
  if (!labels.includes("USB") || labels.length < 2) return "";
  if (labels.includes("BT") && labels.includes("2.4GHz")) return "USB + BT + 2.4GHz";
  if (labels.includes("BT")) return "USB + BT";
  if (labels.includes("2.4GHz")) return "USB + 2.4GHz";
  if (labels.includes("Wireless")) return "USB + Wireless";
  return ["USB", "BT", "2.4GHz", "Wireless"].filter((label) => labels.includes(label)).join(" + ");
}

function getLatencyListModeDisplay(item) {
  return getLatencyConnectionModeSummary(item) || getLatencyModeDisplay(item);
}

function getLatencyVariantModeDisplay(item) {
  const mode = getLatencyModeDisplay(item) || "-";
  const adapterInput = formatLatencyAdapterInputs(item);
  if (item.category === "Controller Adapter" && adapterInput !== "-") return `${adapterInput} / ${mode}`;
  return mode;
}

function getLatencyVariantSearchText(variant) {
  if (variant.searchText) return String(variant.searchText).toLowerCase();
  return [
    variant.name,
    variant.connection,
    variant.connectionKind,
    variant.wirelessConnection,
    variant.connectionTag,
    variant.modeRaw,
    variant.outputMode,
    formatLatencyOutputModes(variant),
    variant.modeLabel,
    variant.modeDisplay,
    formatLatencyAdapterInputs(variant),
    variant.rankMode,
    variant.averageTier,
    variant.category,
    variant.saleStatus,
    variant.sourceStatus,
    variant.isOpenSource ? "open source" : "",
  ].filter(Boolean).join(" ").toLowerCase();
}

function getLatencyDeviceTypes(item) {
  return Array.isArray(item.deviceTypes) ? item.deviceTypes : [];
}

function sortLatencyAdapterInputs(values) {
  return uniqueSorted(values);
}

function getLatencyAdapterInputs(item) {
  return sortLatencyAdapterInputs(getLatencyDeviceTypes(item)
    .map(normalizeLatencyLabel)
    .filter((value) => value && !LATENCY_ADAPTER_INPUT_EXCLUDED_TYPES.has(value)));
}

function formatLatencyAdapterInputs(item) {
  const values = getLatencyAdapterInputs(item);
  return values.length ? values.join(", ") : "-";
}

function formatLatencyWeight(item) {
  if (!isLatencyControllerAttributeCategory(item.category)) return "N/A";
  const value = normalizeLatencyLabel(item.weightOz);
  if (!value) return "N/A";
  return /\boz\b/i.test(value) ? value : `${value} oz`;
}

function isLatencyControllerAttributeCategory(category) {
  return LATENCY_CONTROLLER_ATTRIBUTE_CATEGORIES.has(normalizeLatencyLabel(category));
}

function getLatencyFaceButtons(item) {
  return normalizeLatencyLabel(item.faceButtons);
}

function getLatencyHomeButton(item) {
  return normalizeLatencyLabel(item.homeButton);
}

function getLatencySaleStatus(item) {
  return item.saleStatus || "Unknown";
}

function getLatencySourceStatus(item) {
  return item.sourceStatus || "Closed Source";
}

function getLatencyConnectionFilterValue(item) {
  const tag = normalizeLatencyLabel(item.connectionTag);
  if (tag && tag !== "Unknown") return tag;
  const kind = normalizeLatencyLabel(item.connectionKind);
  return kind && kind !== "Unknown" ? kind : "";
}

function fillLatencySelect(select, values, currentValue = "", getOptionLabel = (value) => value) {
  if (!select) return;
  const firstOption = select.querySelector("option");
  select.innerHTML = "";
  if (firstOption) {
    select.appendChild(firstOption);
  }
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = getOptionLabel(value);
    select.appendChild(option);
  }
  select.value = values.includes(currentValue) ? currentValue : "";
}

function syncLatencyAdapterInputAvailability() {
  if (!latencyRefs.adapterInputSelect || !latencyRefs.categorySelect) return;
  const enabled = latencyRefs.categorySelect.value === "Controller Adapter";
  latencyRefs.adapterInputSelect.disabled = !enabled;
  latencyRefs.adapterInputSelect.closest(".control-block")?.classList.toggle("is-disabled", !enabled);
  if (!enabled && latencyRefs.adapterInputSelect.value) latencyRefs.adapterInputSelect.value = "";
}

function syncLatencyControllerAttributeAvailability() {
  if (!latencyRefs.categorySelect || !latencyRefs.faceButtonsSelect || !latencyRefs.homeButtonSelect) return;
  const enabled = isLatencyControllerAttributeCategory(latencyRefs.categorySelect.value);
  latencyRefs.faceButtonsSelect.disabled = !enabled;
  latencyRefs.homeButtonSelect.disabled = !enabled;
  latencyRefs.faceButtonsSelect.closest(".control-block")?.classList.toggle("is-disabled", !enabled);
  latencyRefs.homeButtonSelect.closest(".control-block")?.classList.toggle("is-disabled", !enabled);
  if (!enabled && latencyRefs.faceButtonsSelect.value) latencyRefs.faceButtonsSelect.value = "";
  if (!enabled && latencyRefs.homeButtonSelect.value) latencyRefs.homeButtonSelect.value = "";
}

function populateLatencyControls(items) {
  fillLatencySelect(
    latencyRefs.categorySelect,
    uniqueSorted(items.map((item) => item.category)),
    latencyRefs.categorySelect.value,
  );
  fillLatencySelect(
    latencyRefs.faceButtonsSelect,
    uniqueSorted(items.flatMap((item) => getLatencyVariants(item)
      .filter((variant) => isLatencyControllerAttributeCategory(variant.category))
      .map(getLatencyFaceButtons))),
    latencyRefs.faceButtonsSelect?.value,
  );
  fillLatencySelect(
    latencyRefs.homeButtonSelect,
    uniqueSortedByOrder(
      items.flatMap((item) => getLatencyVariants(item)
        .filter((variant) => isLatencyControllerAttributeCategory(variant.category))
        .map(getLatencyHomeButton)),
      ["Yes", "No", "N/A"],
    ),
    latencyRefs.homeButtonSelect?.value,
  );
  fillLatencySelect(
    latencyRefs.adapterInputSelect,
    sortLatencyAdapterInputs(items.flatMap((item) => getLatencyVariants(item)
      .filter((variant) => variant.category === "Controller Adapter")
      .flatMap(getLatencyAdapterInputs))),
    latencyRefs.adapterInputSelect.value,
  );
  fillLatencySelect(
    latencyRefs.modeSelect,
    sortLatencyOutputModes(items.flatMap((item) => getLatencyVariants(item).flatMap(getLatencyOutputModes))),
    latencyRefs.modeSelect.value,
  );
  fillLatencySelect(
    latencyRefs.connectionSelect,
    uniqueSortedByOrder(
      items.flatMap((item) => getLatencyVariants(item).map(getLatencyConnectionFilterValue)),
      LATENCY_CONNECTION_ORDER,
    ),
    latencyRefs.connectionSelect.value,
  );
  fillLatencySelect(
    latencyRefs.saleStatusSelect,
    uniqueSortedByOrder([
      ...LATENCY_SALE_STATUS_ORDER,
      ...items.flatMap((item) => getLatencyVariants(item).map(getLatencySaleStatus)),
    ], LATENCY_SALE_STATUS_ORDER),
    latencyRefs.saleStatusSelect.value,
  );
  fillLatencySelect(
    latencyRefs.sourceStatusSelect,
    uniqueSortedByOrder([
      ...LATENCY_SOURCE_STATUS_ORDER,
      ...items.flatMap((item) => getLatencyVariants(item).map(getLatencySourceStatus)),
    ], LATENCY_SOURCE_STATUS_ORDER),
    latencyRefs.sourceStatusSelect.value,
  );
  fillLatencySelect(
    latencyRefs.tierSelect,
    LATENCY_TIER_ORDER.filter((tier) => items.some((item) => item.averageTier === tier)),
    latencyRefs.tierSelect.value,
    getLatencyTierLabel,
  );
  syncLatencyAdapterInputAvailability();
  syncLatencyControllerAttributeAvailability();
}

function buildLatencySubtitle(item) {
  const connection = item.connection || (item.connectionKind === "Unknown" ? "" : item.connectionKind);
  const category = item.category === "Uncategorized" ? "" : item.category;
  const parts = [
    category,
    connection,
    item.wirelessConnection && item.wirelessConnection !== "-" ? item.wirelessConnection : "",
    item.originalSystem,
  ].filter(Boolean);
  return parts.join(" / ");
}

function createLatencyTierIcon(tier) {
  const icon = document.createElement("i");
  icon.className = `latency-tier-icon tier-${sanitizeLatencyClass(tier)}`;
  icon.setAttribute("aria-hidden", "true");
  icon.title = LATENCY_TIER_ICON_LABELS[tier] || "Latency tier";
  return icon;
}

function createLatencyMetric(label, value, kind = "", icon = null) {
  const metric = document.createElement("div");
  metric.className = `latency-metric ${kind}`.trim();

  const valueNode = document.createElement("strong");
  if (icon) {
    valueNode.append(icon, document.createTextNode(value));
  } else {
    valueNode.textContent = value;
  }
  metric.appendChild(valueNode);

  const labelNode = document.createElement("span");
  labelNode.textContent = label;
  metric.appendChild(labelNode);

  return metric;
}

function createLatencyTag(label, options = {}) {
  const tag = options.href ? document.createElement("a") : options.filter ? document.createElement("button") : document.createElement("span");
  tag.className = `card-tag ${options.kind ? `tag-${options.kind}` : ""}`.trim();
  tag.textContent = label;
  if (options.href) {
    tag.href = options.href;
    tag.target = "_blank";
    tag.rel = "noreferrer noopener";
  } else {
    tag.type = "button";
    if (options.filter) {
      tag.dataset.filter = options.filter;
      tag.dataset.value = options.value || label;
    }
  }
  if (options.title) tag.title = options.title;
  return tag;
}

function buildLatencyTags(item) {
  const tags = [];
  if (Number.isFinite(item.modeVariantCount) && item.modeVariantCount > 1) {
    tags.push(createLatencyTag(`${latencyNumberFormatter.format(item.modeVariantCount)} modes`, {
      kind: "mode-count",
      title: "Measured modes available in the expanded details",
    }));
  }
  if (item.connectionTag) {
    tags.push(createLatencyTag(item.connectionTag, {
      kind: "connection",
      title: "Transport type",
    }));
  }
  if (item.isOpenSource) {
    tags.push(createLatencyTag("Open Source", {
      kind: "source-open",
      filter: "sourceStatus",
      value: "Open Source",
      title: "Open source firmware is available",
    }));
  }
  if (Number.isFinite(item.overallRank)) {
    tags.push(createLatencyTag(`#${latencyNumberFormatter.format(item.overallRank)} Overall`, {
      kind: "rank-overall",
      title: "Ranked by average latency across all results",
    }));
  }
  if (Number.isFinite(item.modeRank) && item.rankMode) {
    tags.push(createLatencyTag(`#${latencyNumberFormatter.format(item.modeRank)} ${item.rankMode}`, {
      kind: "rank-mode",
      title: `Ranked by average latency within all ${item.rankMode} results`,
    }));
  }
  return tags;
}

function createLatencyDetailItem(label, value, kind = "") {
  const item = document.createElement("div");
  item.className = `latency-detail-item ${kind}`.trim();

  const labelNode = document.createElement("span");
  labelNode.textContent = label;
  const valueNode = document.createElement("strong");
  valueNode.textContent = value;
  item.append(labelNode, valueNode);
  return item;
}

function createLatencyModeVariants(item) {
  const variants = getLatencyVariants(item);
  if (variants.length <= 1) return null;

  const panel = document.createElement("div");
  panel.className = "latency-mode-variants";

  const title = document.createElement("h3");
  title.textContent = "Measured modes";
  panel.appendChild(title);

  const rows = document.createElement("div");
  rows.className = "latency-mode-variant-grid";
  for (const variant of [...variants].sort((left, right) => (left.averageMs ?? Infinity) - (right.averageMs ?? Infinity))) {
    const row = document.createElement("div");
    row.className = "latency-mode-variant";
    if (variant.id === item.displayVariantId || (!item.displayVariantId && variant.id === item.id)) {
      row.classList.add("is-current");
    }

    const mode = document.createElement("strong");
    mode.textContent = getLatencyVariantModeDisplay(variant) || variant.name || "-";
    const average = document.createElement("span");
    average.textContent = formatLatencyMs(variant.averageMs);
    const tier = document.createElement("span");
    tier.textContent = variant.averageTier || "-";
    const source = document.createElement("span");
    const sourceParts = [
      variant.connectionTag || variant.connectionKind || variant.resultLabel || "",
    ].filter(Boolean);
    source.textContent = sourceParts.join(" / ") || "-";
    row.append(mode, average, tier, source);
    rows.appendChild(row);
  }
  panel.appendChild(rows);
  return panel;
}

function getLatencyDetailSource(item) {
  if (isFiniteLatencyNumber(item.adapterAverageMs)) return "Reflex Adapt adjusted";
  if (item.hasRawCapture) return "Raw capture";
  if (isFiniteLatencyNumber(item.observedSameFramePct)) return "Source export";
  return "Average-implied";
}

function buildLatencyDetailNote(item) {
  if (isFiniteLatencyNumber(item.adapterAverageMs) && isFiniteLatencyNumber(item.measuredAverageMs)) {
    const mode = item.adapterMode ? ` ${item.adapterMode}` : "";
    return `Average subtracts the ${formatLatencyMs(item.adapterAverageMs)} Reflex Adapt${mode} baseline from the ${formatLatencyMs(item.measuredAverageMs)} measured total. Same-frame is derived from the adjusted average for consistent comparison.`;
  }
  if (item.hasRawCapture) {
    return "Chart same-frame is derived from average latency for consistent comparison. Observed same-frame, 99th percentile, and sample count come from raw capture data.";
  }
  if (isFiniteLatencyNumber(item.observedSameFramePct)) {
    return "Chart same-frame is derived from average latency for consistent comparison. Source same-frame is retained separately when provided.";
  }
  return "Chart same-frame is derived from average latency. This row does not include separate observed same-frame or 99th percentile data.";
}

function renderLatencyCard(item) {
  const card = latencyRefs.cardTemplate.content.firstElementChild.cloneNode(true);
  card.classList.add(`tier-${sanitizeLatencyClass(item.averageTier)}`);
  card.classList.add(`result-${sanitizeLatencyClass(item.resultType)}`);
  card.classList.add("is-expandable");
  card.dataset.itemId = item.id || "";
  card.dataset.displayVariantId = item.displayVariantId || "";
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  card.setAttribute("aria-expanded", "false");
  if (latencyState.selectedItemId === item.id) {
    card.classList.add("is-selected");
    card.setAttribute("aria-current", "true");
  }

  const title = card.querySelector(".card-title");
  const buyUrl = normalizeLatencyUrl(item.buyUrl || item.link);
  if (buyUrl) {
    const titleLink = document.createElement("a");
    titleLink.className = "card-title-link";
    titleLink.href = buyUrl;
    titleLink.target = "_blank";
    titleLink.rel = "noreferrer noopener";
    titleLink.textContent = item.name;
    titleLink.title = "Open product page";
    title.appendChild(titleLink);
  } else {
    title.textContent = item.name;
  }

  const subtitle = card.querySelector(".card-subtitle");
  const subtitleText = buildLatencySubtitle(item);
  subtitle.textContent = subtitleText || " ";

  const metrics = card.querySelector(".latency-metrics");
  metrics.append(
    createLatencyMetric("Average", formatLatencyMs(item.averageMs), "metric-average"),
    createLatencyMetric("Tier", item.averageTier || "-", "metric-tier", createLatencyTierIcon(item.averageTier)),
    createLatencyMetric("Mode", getLatencyListModeDisplay(item) || "-", "metric-mode"),
  );

  const details = card.querySelector(".latency-detail-panel");
  const detailGrid = card.querySelector(".latency-detail-grid");
  const detailItems = [
    createLatencyDetailItem("99th", formatLatencyMs(item.p99Ms), "detail-p99"),
    createLatencyDetailItem("Same Frame from Avg", formatLatencyPercent(item.sameFramePct), "detail-modeled"),
    createLatencyDetailItem(
      item.hasRawCapture ? "Observed Same Frame" : "Source Same Frame",
      formatLatencyPercent(item.observedSameFramePct),
      item.hasRawCapture ? "detail-raw" : "detail-modeled",
    ),
    createLatencyDetailItem("Samples", item.sampleCount ? latencyNumberFormatter.format(item.sampleCount) : "-", "detail-samples"),
    createLatencyDetailItem("Stats Source", getLatencyDetailSource(item), item.hasRawCapture ? "detail-raw" : "detail-modeled"),
    createLatencyDetailItem("Date Added", formatLatencyDateAdded(item), "detail-date"),
    createLatencyDetailItem("Category", item.category || "-", "detail-category"),
    createLatencyDetailItem("Controller Adapter Input", formatLatencyAdapterInputs(item), "detail-adapter-input"),
    createLatencyDetailItem("Sale Status", getLatencySaleStatus(item), "detail-sale-status"),
    createLatencyDetailItem("Firmware", getLatencySourceStatus(item), "detail-source-status"),
    createLatencyDetailItem("Connection", item.connection || item.connectionKind || "-", "detail-connection"),
    createLatencyDetailItem("Input Mode", simplifyLatencyModeLabel(item.modeRaw || item.modeDisplay || item.modeLabel) || "-", "detail-mode"),
    createLatencyDetailItem("Output Mode", formatLatencyOutputModes(item), "detail-mode"),
    createLatencyDetailItem("Face Buttons", getLatencyFaceButtons(item) || "N/A", "detail-face-buttons"),
    createLatencyDetailItem("Home Button", getLatencyHomeButton(item) || "N/A", "detail-home-button"),
    createLatencyDetailItem("VID:PID", normalizeLatencyLabel(item.joystickId) || "N/A", "detail-vid-pid"),
    createLatencyDetailItem("Weight", formatLatencyWeight(item), "detail-weight"),
  ];
  if (isFiniteLatencyNumber(item.measuredAverageMs)) {
    detailItems.push(createLatencyDetailItem("Measured Total", formatLatencyMs(item.measuredAverageMs), "detail-raw"));
  }
  if (isFiniteLatencyNumber(item.adapterAverageMs)) {
    const adapterLabel = item.adapterMode ? `${formatLatencyMs(item.adapterAverageMs)} ${item.adapterMode}` : formatLatencyMs(item.adapterAverageMs);
    detailItems.push(createLatencyDetailItem("Adapter Baseline", adapterLabel, "detail-modeled"));
  }
  detailGrid.append(...detailItems);
  const modeVariantItem = latencyState.selectedItemId === item.id && latencyState.selectedDisplayVariantId
    ? { ...item, displayVariantId: latencyState.selectedDisplayVariantId }
    : item;
  const modeVariants = createLatencyModeVariants(modeVariantItem);
  if (modeVariants) {
    details.insertBefore(modeVariants, card.querySelector(".latency-detail-note"));
  }
  const note = card.querySelector(".latency-detail-note");
  note.textContent = buildLatencyDetailNote(item);
  const selected = latencyState.selectedItemId === item.id;
  details.hidden = !selected;
  if (selected) {
    card.classList.add("is-expanded");
    card.dataset.selectionExpanded = "true";
    card.setAttribute("aria-expanded", "true");
  }

  const tags = card.querySelector(".card-tags");
  for (const tag of buildLatencyTags(item)) {
    tags.appendChild(tag);
  }

  return card;
}

function renderLatencyItems(items) {
  latencyRefs.grid.innerHTML = "";
  latencyRefs.grid.classList.remove("view-list", "view-card");
  latencyRefs.grid.classList.add(latencyState.viewMode === "tiles" ? "view-card" : "view-list");
  if (latencyState.selectedItemId && !items.some((item) => item.id === latencyState.selectedItemId)) {
    latencyState.selectedItemId = "";
    latencyState.selectedDisplayVariantId = "";
    hideLatencyTooltip(true);
  }
  const displayItems = latencyState.selectedItemId
    ? items.filter((item) => item.id === latencyState.selectedItemId)
    : items;

  if (!displayItems.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No latency results match the selected filters.";
    latencyRefs.grid.appendChild(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const item of displayItems) {
    fragment.appendChild(renderLatencyCard(item));
  }
  latencyRefs.grid.appendChild(fragment);
}

function toggleLatencyCard(card, force) {
  const details = card.querySelector(".latency-detail-panel");
  if (!details) return;
  const nextExpanded = typeof force === "boolean" ? force : !card.classList.contains("is-expanded");
  card.classList.toggle("is-expanded", nextExpanded);
  card.setAttribute("aria-expanded", String(nextExpanded));
  details.hidden = !nextExpanded;
  if (!nextExpanded) delete card.dataset.selectionExpanded;
}

function createLatencySvgElement(name, attributes = {}) {
  const element = document.createElementNS(LATENCY_SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

function getLatencyStableAngle(value, fallback = 0) {
  const text = String(value || fallback);
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) >>> 0;
  }
  return ((hash % 360) / 180) * Math.PI;
}

function getLatencyPlotItems(items) {
  return items.filter((item) => {
    if (!isFiniteLatencyNumber(item.averageMs) || item.averageMs <= 0) return false;
    if (!isFiniteLatencyNumber(item.sameFramePct)) return false;
    return true;
  });
}

function getLatencyLogDomain(values) {
  const positiveValues = values.filter((value) => value > 0);
  const minValue = Math.min(...positiveValues);
  const maxValue = Math.max(...positiveValues);
  if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) return { min: 1, max: 10 };
  if (minValue === maxValue) {
    const logValue = Math.log10(minValue);
    return {
      min: Math.pow(10, logValue - 0.15),
      max: Math.pow(10, logValue + 0.15),
    };
  }
  return { min: minValue, max: maxValue };
}

function isLatencyTickNearValue(tick, value) {
  return Math.abs(Math.log10(tick) - Math.log10(value)) < 0.045;
}

function getLatencyLogTicks(domain) {
  const ticks = [domain.min];
  for (const tick of LATENCY_LOG_X_TICKS) {
    if (tick <= domain.min || tick >= domain.max) continue;
    if (isLatencyTickNearValue(tick, domain.min) || isLatencyTickNearValue(tick, domain.max)) continue;
    ticks.push(tick);
  }
  ticks.push(domain.max);
  return Array.from(new Set(ticks.map((tick) => Number(tick.toFixed(6))))).sort((left, right) => left - right);
}

function getLatencyVisibleLogRange(baseLogRange, zoomLevel = latencyState.xZoomLevel) {
  const boundedZoom = clampLatencyValue(Number(zoomLevel) || 0, 0, LATENCY_X_ZOOM_MAX);
  if (boundedZoom <= 0) return baseLogRange;
  const visibleRatio = 1 - (boundedZoom / LATENCY_X_ZOOM_MAX) * (1 - LATENCY_X_ZOOM_MIN_LOG_RATIO);
  return Math.max(baseLogRange * visibleRatio, 0.000001);
}

function getLatencyXDomain(plotItems, zoomLevel = latencyState.xZoomLevel, panRatio = latencyState.xPanRatio) {
  const baseDomain = getLatencyLogDomain(plotItems.map((item) => item.averageMs));
  const boundedZoom = clampLatencyValue(Number(zoomLevel) || 0, 0, LATENCY_X_ZOOM_MAX);
  if (boundedZoom <= 0) return baseDomain;

  const baseLogMin = Math.log10(baseDomain.min);
  const baseLogMax = Math.log10(baseDomain.max);
  const baseLogRange = Math.max(baseLogMax - baseLogMin, 0.000001);
  const visibleLogRange = getLatencyVisibleLogRange(baseLogRange, boundedZoom);
  const panSpan = Math.max(baseLogRange - visibleLogRange, 0);
  const nextLogMin = baseLogMin + panSpan * clampLatencyValue(Number(panRatio) || 0, 0, 1);
  const nextLogMax = nextLogMin + visibleLogRange;

  return {
    min: Math.pow(10, Math.max(nextLogMin, baseLogMin)),
    max: Math.pow(10, Math.min(nextLogMax, baseLogMax)),
  };
}

function getLatencyMedianAverage(plotItems) {
  const values = plotItems
    .map((item) => item.averageMs)
    .filter(isFiniteLatencyNumber)
    .sort((left, right) => left - right);
  if (!values.length) return null;
  const midpoint = Math.floor(values.length / 2);
  return values.length % 2 ? values[midpoint] : (values[midpoint - 1] + values[midpoint]) / 2;
}

function isLatencyItemInXDomain(item, xDomain) {
  return item.averageMs >= xDomain.min && item.averageMs <= xDomain.max;
}

function getLatencyXZoomLabel(visibleCount, allCount, xDomain, baseDomain) {
  const resultLabel = visibleCount === 1 ? "RESULT" : "RESULTS";
  const sameDomain = (
    !baseDomain
    || Math.abs(Math.log10(xDomain.min) - Math.log10(baseDomain.min)) < 0.0001
    && Math.abs(Math.log10(xDomain.max) - Math.log10(baseDomain.max)) < 0.0001
  );
  const windowLabel = sameDomain
    ? "All"
    : `${formatLatencyMs(xDomain.min)}-${formatLatencyMs(xDomain.max)}`;
  const countLabel = sameDomain
    ? allCount
    : visibleCount;
  return `${windowLabel} / ${latencyNumberFormatter.format(countLabel)} ${resultLabel}`;
}

function getLatencyScatterCursorRatio(event) {
  if (!latencyScatterLayout || !latencyScatterLayout.clientChartWidth) return 0.5;
  return clampLatencyValue(
    (event.clientX - latencyScatterLayout.clientChartLeft) / latencyScatterLayout.clientChartWidth,
    0,
    1,
  );
}

function getLatencyPanRatioForAnchor(plotItems, nextZoomLevel, anchorRatio) {
  const baseDomain = getLatencyLogDomain(plotItems.map((item) => item.averageMs));
  const currentDomain = getLatencyXDomain(plotItems);
  const baseLogMin = Math.log10(baseDomain.min);
  const baseLogMax = Math.log10(baseDomain.max);
  const baseLogRange = Math.max(baseLogMax - baseLogMin, 0.000001);
  const visibleLogRange = getLatencyVisibleLogRange(baseLogRange, nextZoomLevel);
  const panSpan = Math.max(baseLogRange - visibleLogRange, 0);
  if (panSpan <= 0.000001) return 0.5;

  const currentLogMin = Math.log10(currentDomain.min);
  const currentLogRange = Math.max(Math.log10(currentDomain.max) - currentLogMin, 0.000001);
  const anchorLog = currentLogMin + clampLatencyValue(anchorRatio, 0, 1) * currentLogRange;
  const desiredLogMin = anchorLog - clampLatencyValue(anchorRatio, 0, 1) * visibleLogRange;
  return clampLatencyValue((desiredLogMin - baseLogMin) / panSpan, 0, 1);
}

function setLatencyXPanRatio(value) {
  const nextRatio = clampLatencyValue(Number(value) || 0, 0, 1);
  if (Math.abs(nextRatio - latencyState.xPanRatio) < 0.001) return;
  latencyState.xPanRatio = nextRatio;
  renderLatencyScatter(latencyState.filtered);
}

function setLatencyXZoomLevel(value, anchorRatio = null) {
  const nextLevel = clampLatencyValue(Number(value) || 0, 0, LATENCY_X_ZOOM_MAX);
  const previousLevel = latencyState.xZoomLevel;
  const previousPan = latencyState.xPanRatio;
  if (anchorRatio !== null) {
    const plotItems = getLatencyPlotItems(latencyState.filtered);
    latencyState.xPanRatio = getLatencyPanRatioForAnchor(plotItems, nextLevel, anchorRatio);
  } else if (nextLevel <= 0) {
    latencyState.xPanRatio = 0.5;
  }
  if (Math.abs(nextLevel - previousLevel) < 0.01 && Math.abs(latencyState.xPanRatio - previousPan) < 0.001) return;
  latencyState.xZoomLevel = nextLevel;
  if (latencyRefs.xZoomSlider) latencyRefs.xZoomSlider.value = String(Math.round(nextLevel));
  renderLatencyScatter(latencyState.filtered);
}

function syncLatencyXZoomControl(visibleCount, allCount = visibleCount, xDomain = null, baseDomain = null) {
  const isZoomed = latencyState.xZoomLevel > 0.01;
  if (latencyRefs.xZoomControl) {
    latencyRefs.xZoomControl.classList.toggle("is-zoomed", isZoomed);
  }
  if (latencyRefs.xPanScrollbar) {
    latencyRefs.xPanScrollbar.classList.toggle("is-zoomed", isZoomed);
  }
  if (latencyRefs.xZoomSlider) {
    latencyRefs.xZoomSlider.min = "0";
    latencyRefs.xZoomSlider.max = String(LATENCY_X_ZOOM_MAX);
    latencyRefs.xZoomSlider.step = "1";
    latencyRefs.xZoomSlider.value = String(Math.round(latencyState.xZoomLevel));
  }
  syncLatencyPanScrollbar(isZoomed, xDomain, baseDomain);
  if (latencyRefs.xZoomLabel) {
    latencyRefs.xZoomLabel.textContent = xDomain
      ? getLatencyXZoomLabel(visibleCount, allCount, xDomain, baseDomain)
      : `All / ${latencyNumberFormatter.format(allCount)} ${allCount === 1 ? "RESULT" : "RESULTS"}`;
  }
}

function syncLatencyPanScrollbar(isZoomed, xDomain, baseDomain) {
  if (!latencyRefs.xPanScrollbar || !latencyRefs.xPanTrack) return;
  latencyRefs.xPanScrollbar.setAttribute("aria-disabled", isZoomed ? "false" : "true");
  if (!isZoomed || !xDomain || !baseDomain) {
    latencyRefs.xPanTrack.style.width = "100%";
    latencyPanScrollbarSyncing = true;
    latencyRefs.xPanScrollbar.scrollLeft = 0;
    latencyPanScrollbarSyncing = false;
    return;
  }

  const baseLogRange = Math.max(Math.log10(baseDomain.max) - Math.log10(baseDomain.min), 0.000001);
  const visibleLogRange = Math.max(Math.log10(xDomain.max) - Math.log10(xDomain.min), 0.000001);
  const trackWidthRatio = clampLatencyValue(baseLogRange / visibleLogRange, 1, 10);
  latencyRefs.xPanTrack.style.width = `${trackWidthRatio * 100}%`;

  requestAnimationFrame(() => {
    if (!latencyRefs.xPanScrollbar) return;
    const maxScroll = Math.max(latencyRefs.xPanScrollbar.scrollWidth - latencyRefs.xPanScrollbar.clientWidth, 0);
    latencyPanScrollbarSyncing = true;
    latencyRefs.xPanScrollbar.scrollLeft = maxScroll * clampLatencyValue(latencyState.xPanRatio, 0, 1);
    requestAnimationFrame(() => {
      latencyPanScrollbarSyncing = false;
    });
  });
}

function handleLatencyScatterWheel(event) {
  if (!latencyRefs.scatter || !latencyState.filtered.length) return;
  event.preventDefault();
  if (Math.abs(event.deltaX) > Math.abs(event.deltaY) && latencyState.xZoomLevel > 0) {
    setLatencyXPanRatio(latencyState.xPanRatio + clampLatencyValue(event.deltaX, -240, 240) / 900);
    return;
  }
  const delta = clampLatencyValue(event.deltaY, -240, 240);
  setLatencyXZoomLevel(latencyState.xZoomLevel - delta * LATENCY_X_ZOOM_STEP, getLatencyScatterCursorRatio(event));
}

function makeLatencyAxisTick(value, x1, y1, x2, y2, label, anchor = "middle") {
  const group = createLatencySvgElement("g", { class: "latency-axis-tick" });
  group.appendChild(createLatencySvgElement("line", { x1, y1, x2, y2 }));
  const text = createLatencySvgElement("text", { x: x2, y: y2 + 18, "text-anchor": anchor });
  text.textContent = label;
  group.appendChild(text);
  return group;
}

function renderLatencyScatter(items) {
  if (!latencyRefs.scatter) return;

  latencyActiveScatterPoint = null;
  if (!latencyState.selectedItemId) hideLatencyTooltip(true);
  latencyRefs.scatter.innerHTML = "";

  const allPlotItems = getLatencyPlotItems(items);
  const baseXDomain = getLatencyLogDomain(allPlotItems.map((item) => item.averageMs));
  const xDomain = getLatencyXDomain(allPlotItems);
  const plotItems = allPlotItems.filter((item) => isLatencyItemInXDomain(item, xDomain));
  if (latencyState.selectedItemId && !allPlotItems.some((item) => item.id === latencyState.selectedItemId)) {
    latencyState.selectedItemId = "";
    latencyState.selectedDisplayVariantId = "";
    hideLatencyTooltip(true);
  }
  syncLatencyXZoomControl(plotItems.length, allPlotItems.length, xDomain, baseXDomain);
  const height = 360;
  const renderedBox = latencyRefs.scatter.getBoundingClientRect();
  const renderedWidth = renderedBox.width || 760;
  const renderedHeight = renderedBox.height || height;
  const width = Math.max(520, Math.round(renderedWidth / Math.max(renderedHeight, 1) * height));
  latencyRefs.scatter.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const widePlot = width > 900;
  const padding = widePlot
    ? { top: 34, right: 72, bottom: 54, left: 112 }
    : { top: 34, right: 36, bottom: 54, left: 96 };
  const yLabelX = widePlot ? 24 : 18;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const bottom = padding.top + chartHeight;
  const clientScaleX = renderedBox.width / Math.max(width, 1);
  latencyScatterLayout = {
    clientChartLeft: renderedBox.left + padding.left * clientScaleX,
    clientChartWidth: chartWidth * clientScaleX,
  };
  latencyRefs.scatter.dataset.plotLeft = String(padding.left);
  latencyRefs.scatter.dataset.plotRight = String(padding.left + chartWidth);
  latencyRefs.scatter.dataset.plotTop = String(padding.top);
  latencyRefs.scatter.dataset.plotBottom = String(bottom);

  if (!plotItems.length) {
    const empty = createLatencySvgElement("text", {
      x: width / 2,
      y: height / 2,
      class: "latency-plot-empty",
      "text-anchor": "middle",
    });
    empty.textContent = "No chartable latency data in this filter.";
    latencyRefs.scatter.appendChild(empty);
    return;
  }

  const xLogMin = Math.log10(xDomain.min);
  const xLogRange = Math.max(Math.log10(xDomain.max) - xLogMin, 0.000001);
  const xScale = (value) => {
    const clamped = clampLatencyValue(value, xDomain.min, xDomain.max);
    return padding.left + ((Math.log10(clamped) - xLogMin) / xLogRange) * chartWidth;
  };
  const yScale = (value) => bottom - (clampLatencyValue(value, 0, 100) / 100) * chartHeight;

  const axisLayer = createLatencySvgElement("g", { class: "latency-axis-layer" });
  axisLayer.appendChild(createLatencySvgElement("line", { x1: padding.left, y1: bottom, x2: padding.left + chartWidth, y2: bottom }));
  axisLayer.appendChild(createLatencySvgElement("line", { x1: padding.left, y1: padding.top, x2: padding.left, y2: bottom }));

  for (const tick of getLatencyLogTicks(xDomain)) {
    const x = xScale(tick);
    axisLayer.appendChild(makeLatencyAxisTick(tick, x, bottom, x, bottom + 5, formatLatencyMs(tick)));
  }

  for (const tick of [0, 50, 100]) {
    const y = yScale(tick);
    const group = createLatencySvgElement("g", { class: "latency-axis-tick latency-axis-y-tick" });
    group.appendChild(createLatencySvgElement("line", { x1: padding.left - 5, y1: y, x2: padding.left + chartWidth, y2: y }));
    const text = createLatencySvgElement("text", { x: padding.left - 10, y: y + 4, "text-anchor": "end" });
    text.textContent = formatLatencyPercent(tick);
    group.appendChild(text);
    axisLayer.appendChild(group);
  }

  const medianAverage = getLatencyMedianAverage(allPlotItems);
  if (isFiniteLatencyNumber(medianAverage) && medianAverage >= xDomain.min && medianAverage <= xDomain.max) {
    const medianX = xScale(medianAverage);
    const medianGroup = createLatencySvgElement("g", { class: "latency-median-line" });
    medianGroup.appendChild(createLatencySvgElement("line", {
      x1: medianX,
      y1: padding.top,
      x2: medianX,
      y2: bottom,
    }));
    const medianLabel = createLatencySvgElement("text", {
      x: medianX + 6,
      y: padding.top + 13,
      "text-anchor": "start",
    });
    medianLabel.textContent = `Median ${formatLatencyMs(medianAverage)}`;
    medianGroup.appendChild(medianLabel);
    axisLayer.appendChild(medianGroup);
  }

  const xLabel = createLatencySvgElement("text", {
    x: padding.left + chartWidth / 2,
    y: height - 12,
    class: "latency-axis-label",
    "text-anchor": "middle",
  });
  xLabel.textContent = "Average latency, log scale";
  axisLayer.appendChild(xLabel);

  const yLabel = createLatencySvgElement("text", {
    x: yLabelX,
    y: padding.top + chartHeight / 2,
    class: "latency-axis-label latency-axis-y-label",
    "text-anchor": "middle",
    transform: `rotate(-90 ${yLabelX} ${padding.top + chartHeight / 2})`,
  });
  yLabel.textContent = "Same-frame probability";
  axisLayer.appendChild(yLabel);
  latencyRefs.scatter.appendChild(axisLayer);

  const hitLayer = createLatencySvgElement("g", { class: "latency-hit-layer" });
  const pointsLayer = createLatencySvgElement("g", { class: "latency-points-layer" });
  for (const item of plotItems) {
    const pointX = xScale(item.averageMs);
    const pointY = yScale(item.sameFramePct);
    const displayVariantId = item.displayVariantId || "";
    const hitArea = createLatencySvgElement("circle", {
      class: "latency-point-hitarea",
      cx: pointX,
      cy: pointY,
      r: LATENCY_POINT_HIT_RADIUS,
      "aria-hidden": "true",
      "data-item-id": item.id,
      "data-display-variant-id": displayVariantId,
      "data-base-cx": pointX.toFixed(2),
      "data-base-cy": pointY.toFixed(2),
    });
    const point = createLatencySvgElement("circle", {
      class: `latency-point tier-${sanitizeLatencyClass(item.averageTier)}`,
      cx: pointX,
      cy: pointY,
      r: LATENCY_POINT_BASE_RADIUS,
      tabindex: "0",
      role: "button",
      "aria-label": `${item.name}, ${formatLatencyMs(item.averageMs)} average`,
      "data-base-radius": LATENCY_POINT_BASE_RADIUS,
      "data-item-id": item.id,
      "data-display-variant-id": displayVariantId,
      "data-base-cx": pointX.toFixed(2),
      "data-base-cy": pointY.toFixed(2),
    });
    hitLayer.appendChild(hitArea);
    pointsLayer.appendChild(point);
  }
  latencyRefs.scatter.appendChild(hitLayer);
  latencyRefs.scatter.appendChild(pointsLayer);
  syncLatencyScatterSelection();
}

function getLatencyItemById(itemId) {
  return latencyState.filtered.find((item) => item.id === itemId) || latencyState.items.find((item) => item.id === itemId);
}

function isLatencySelectedItemId(itemId) {
  return Boolean(latencyState.selectedItemId && itemId === latencyState.selectedItemId);
}

function syncLatencyResultSelection(options = {}) {
  if (!latencyRefs.grid) return null;
  let selectedCard = null;
  for (const card of latencyRefs.grid.querySelectorAll(".latency-card")) {
    const selected = isLatencySelectedItemId(card.dataset.itemId);
    card.classList.toggle("is-selected", selected);
    if (selected) {
      card.setAttribute("aria-current", "true");
      selectedCard = card;
      if (!card.classList.contains("is-expanded")) {
        card.dataset.selectionExpanded = "true";
        toggleLatencyCard(card, true);
      }
    } else {
      card.removeAttribute("aria-current");
      if (card.dataset.selectionExpanded) {
        toggleLatencyCard(card, false);
        delete card.dataset.selectionExpanded;
      }
    }
  }
  if (selectedCard && options.scroll && typeof selectedCard.scrollIntoView === "function") {
    selectedCard.scrollIntoView({ block: "center", behavior: "smooth" });
  }
  return selectedCard;
}

function syncLatencyScatterSelection(event) {
  if (!latencyRefs.scatter) return null;
  let selectedPoint = null;
  for (const point of latencyRefs.scatter.querySelectorAll(".latency-point")) {
    const selected = isLatencySelectedItemId(point.dataset.itemId);
    point.classList.toggle("is-selected", selected);
    if (selected) {
      selectedPoint = point;
      point.classList.add("is-active", "is-selected");
      point.classList.remove("is-lensed");
      point.setAttribute("r", point.dataset.baseRadius || LATENCY_POINT_BASE_RADIUS);
      if (point.parentNode) point.parentNode.appendChild(point);
    } else if (!point.classList.contains("is-lensed")) {
      point.classList.remove("is-active", "is-selected");
      point.setAttribute("r", point.dataset.baseRadius || LATENCY_POINT_BASE_RADIUS);
    }
  }
  if (selectedPoint && event) showLatencyTooltip(event, selectedPoint);
  return selectedPoint;
}

function selectLatencyScatterPoint(point, event) {
  const item = getLatencyItemById(point.dataset.itemId);
  if (!item) return;
  latencyState.selectedItemId = item.id;
  latencyState.selectedDisplayVariantId = point.dataset.displayVariantId || item.displayVariantId || "";
  renderLatencyItems(latencyState.filtered);
  const selectedPoint = syncLatencyScatterSelection(event) || point;
  syncLatencyResultSelection({ scroll: true });
  showLatencyTooltip(event, selectedPoint);
}

function selectLatencyRecentItem(itemId, displayVariantId = "") {
  const item = getLatencyItemById(itemId);
  if (!item) return;
  clearLatencyFilterControls();
  applyLatencyFilters();
  latencyState.selectedItemId = item.id;
  latencyState.selectedDisplayVariantId = displayVariantId || item.displayVariantId || "";
  renderLatencyItems(latencyState.filtered);
  syncLatencyScatterSelection();
  syncLatencyResultSelection({ scroll: true });
  resetLatencyScatterMagnification();
  hideLatencyTooltip(true);
}

function clearLatencyScatterSelection() {
  if (!latencyState.selectedItemId && !latencyState.selectedDisplayVariantId) return;
  latencyState.selectedItemId = "";
  latencyState.selectedDisplayVariantId = "";
  latencyActiveScatterPoint = null;
  renderLatencyItems(latencyState.filtered);
  syncLatencyResultSelection();
  resetLatencyScatterMagnification();
  hideLatencyTooltip(true);
}

function setLatencyTooltipContent(item) {
  if (!latencyRefs.tooltip) return;
  latencyRefs.tooltip.innerHTML = "";
  const title = document.createElement("strong");
  title.textContent = item.name;
  const details = document.createElement("span");
  details.textContent = `${formatLatencyMs(item.averageMs)} average / ${formatLatencyPercent(item.sameFramePct)} same frame from average`;
  const meta = document.createElement("span");
  const metaParts = [
    item.connectionTag || "",
    getLatencyModeDisplay(item) || "",
    formatLatencyAdapterInputs(item) !== "-" ? formatLatencyAdapterInputs(item) : "",
    Number.isFinite(item.overallRank) ? `#${latencyNumberFormatter.format(item.overallRank)} Overall` : "",
    item.connectionKind && item.connectionKind !== "Unknown" ? item.connectionKind : "",
    item.hasRawCapture ? "Raw capture stats available" : "Modeled consistency details",
  ].filter(Boolean);
  meta.textContent = metaParts.join(" / ");
  latencyRefs.tooltip.append(title, details, meta);
}

function positionLatencyTooltip(event) {
  if (!latencyRefs.tooltip || !latencyRefs.scatter) return;
  const wrap = latencyRefs.scatter.closest(".latency-plot-wrap");
  if (!wrap) return;
  const bounds = wrap.getBoundingClientRect();
  latencyRefs.tooltip.hidden = false;
  const left = clampLatencyValue(event.clientX - bounds.left + 14, 8, bounds.width - latencyRefs.tooltip.offsetWidth - 8);
  const top = clampLatencyValue(event.clientY - bounds.top + 14, 8, bounds.height - latencyRefs.tooltip.offsetHeight - 8);
  latencyRefs.tooltip.style.left = `${left}px`;
  latencyRefs.tooltip.style.top = `${top}px`;
}

function showLatencyTooltip(event, point) {
  const item = getLatencyItemById(point.dataset.itemId);
  if (!item || !latencyRefs.tooltip) return;
  setLatencyTooltipContent(item);
  positionLatencyTooltip(event);
}

function hideLatencyTooltip(force = false) {
  if (!latencyRefs.tooltip) return;
  if (!force && latencyState.selectedItemId) return;
  latencyRefs.tooltip.hidden = true;
}

function getLatencySvgPointer(event) {
  if (!latencyRefs.scatter) return null;
  const matrix = latencyRefs.scatter.getScreenCTM();
  if (!matrix) return null;
  const point = latencyRefs.scatter.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(matrix.inverse());
}

function getLatencyPointBasePosition(point) {
  const x = Number(point.dataset.baseCx || point.getAttribute("cx"));
  const y = Number(point.dataset.baseCy || point.getAttribute("cy"));
  return { x, y };
}

function setLatencyPointDisplayPosition(point, x, y, hitAreas = null) {
  point.setAttribute("cx", x.toFixed(2));
  point.setAttribute("cy", y.toFixed(2));
  const hitArea = hitAreas
    ? hitAreas.get(point.dataset.itemId)
    : latencyRefs.scatter && latencyRefs.scatter.querySelector(`.latency-point-hitarea[data-item-id="${CSS.escape(point.dataset.itemId || "")}"]`);
  if (hitArea) {
    hitArea.setAttribute("cx", x.toFixed(2));
    hitArea.setAttribute("cy", y.toFixed(2));
  }
}

function resetLatencyPointDisplayPosition(point, hitAreas = null) {
  const base = getLatencyPointBasePosition(point);
  if (!Number.isFinite(base.x) || !Number.isFinite(base.y)) return;
  setLatencyPointDisplayPosition(point, base.x, base.y, hitAreas);
}

function getLatencyPointDistance(point, cursor) {
  const { x, y } = getLatencyPointBasePosition(point);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return Number.POSITIVE_INFINITY;
  return Math.hypot(cursor.x - x, cursor.y - y);
}

function getLatencyPlotBounds() {
  if (!latencyRefs.scatter || !latencyRefs.scatter.dataset) {
    return { left: 0, right: 0, top: 0, bottom: 0 };
  }
  return {
    left: Number(latencyRefs.scatter.dataset.plotLeft) || 0,
    right: Number(latencyRefs.scatter.dataset.plotRight) || 0,
    top: Number(latencyRefs.scatter.dataset.plotTop) || 0,
    bottom: Number(latencyRefs.scatter.dataset.plotBottom) || 0,
  };
}

function getLatencyLensPosition(point, cursor, bounds, peakLift = 0, isAnchor = false) {
  const base = getLatencyPointBasePosition(point);
  if (isAnchor) {
    return { x: base.x, y: base.y, strength: 1 };
  }
  const distance = Math.hypot(cursor.x - base.x, cursor.y - base.y);
  if (!Number.isFinite(distance) || distance > LATENCY_POINT_LENS_RADIUS) {
    return { x: base.x, y: base.y, strength: 0 };
  }

  const strength = clampLatencyValue(1 - distance / LATENCY_POINT_LENS_RADIUS, 0, 1);
  const eased = strength * strength * (3 - 2 * strength);
  const scale = 1 + (LATENCY_POINT_LENS_SCALE - 1) * eased;
  const angle = getLatencyStableAngle(`${point.dataset.itemId}|${point.dataset.displayVariantId}`);
  const xDistance = base.x - cursor.x;
  const side = Math.sign(xDistance) || (Math.cos(angle) >= 0 ? 1 : -1);
  let x = cursor.x + xDistance * scale
    + side * LATENCY_POINT_LENS_HORIZONTAL_SPLAY * eased
    + Math.cos(angle) * LATENCY_POINT_LENS_HORIZONTAL_SPLAY * 0.45 * eased;
  const arcProgress = clampLatencyValue((base.x - cursor.x + LATENCY_POINT_LENS_RADIUS) / (LATENCY_POINT_LENS_RADIUS * 2), 0, 1);
  const rainbowLift = peakLift * Math.sin(arcProgress * Math.PI);
  let y = base.y - rainbowLift;
  const offsetX = x - base.x;
  if (Math.abs(offsetX) > LATENCY_POINT_LENS_MAX_OFFSET) {
    x = base.x + Math.sign(offsetX) * LATENCY_POINT_LENS_MAX_OFFSET;
  }
  if (bounds.right > bounds.left) x = clampLatencyValue(x, bounds.left, bounds.right);
  if (bounds.bottom > bounds.top) y = clampLatencyValue(y, bounds.top, bounds.bottom);
  return { x, y, strength: eased };
}

function resetLatencyScatterMagnification() {
  latencyActiveScatterPoint = null;
  if (!latencyRefs.scatter) return;
  const hitAreas = new Map(Array.from(latencyRefs.scatter.querySelectorAll(".latency-point-hitarea")).map((hitArea) => [hitArea.dataset.itemId, hitArea]));
  for (const point of latencyRefs.scatter.querySelectorAll(".latency-point")) {
    resetLatencyPointDisplayPosition(point, hitAreas);
    point.setAttribute("r", point.dataset.baseRadius || LATENCY_POINT_BASE_RADIUS);
    if (isLatencySelectedItemId(point.dataset.itemId)) {
      point.classList.add("is-active", "is-selected");
      point.classList.remove("is-lensed");
    } else {
      point.classList.remove("is-lensed", "is-active", "is-selected");
    }
  }
  hideLatencyTooltip();
}

function activateLatencyScatterPoint(point, event) {
  if (!point) return;
  if (latencyActiveScatterPoint && latencyActiveScatterPoint !== point) {
    latencyActiveScatterPoint.classList.remove("is-active");
  }
  latencyActiveScatterPoint = point;
  point.classList.add("is-active");
  if (point.parentNode) point.parentNode.appendChild(point);
  showLatencyTooltip(event, point);
}

function updateLatencyScatterMagnification(event) {
  if (!latencyRefs.scatter) return;
  const cursor = getLatencySvgPointer(event);
  if (!cursor) return;
  const points = Array.from(latencyRefs.scatter.querySelectorAll(".latency-point"));
  const hitAreas = new Map(Array.from(latencyRefs.scatter.querySelectorAll(".latency-point-hitarea")).map((hitArea) => [hitArea.dataset.itemId, hitArea]));
  const bounds = getLatencyPlotBounds();
  let maxLensStrength = 0;
  let minLensBaseY = Number.POSITIVE_INFINITY;
  for (const point of points) {
    const distance = getLatencyPointDistance(point, cursor);
    if (!Number.isFinite(distance) || distance > LATENCY_POINT_LENS_RADIUS) continue;
    minLensBaseY = Math.min(minLensBaseY, getLatencyPointBasePosition(point).y);
    const strength = clampLatencyValue(1 - distance / LATENCY_POINT_LENS_RADIUS, 0, 1);
    maxLensStrength = Math.max(maxLensStrength, strength * strength * (3 - 2 * strength));
  }
  const requestedPeakLift = maxLensStrength * LATENCY_POINT_LENS_VERTICAL_LIFT;
  const peakLift = Math.min(requestedPeakLift, Math.max(0, minLensBaseY - bounds.top));
  let nearest = null;
  let nearestDistance = Number.POSITIVE_INFINITY;

  for (const point of points) {
    const distance = getLatencyPointDistance(point, cursor);
    if (distance < nearestDistance) {
      nearest = point;
      nearestDistance = distance;
    }
  }
  const anchorPoint = nearest && nearestDistance <= LATENCY_POINT_MAGNIFY_RANGE ? nearest : null;

  for (const point of points) {
    const lens = getLatencyLensPosition(point, cursor, bounds, peakLift, point === anchorPoint);
    setLatencyPointDisplayPosition(point, lens.x, lens.y, hitAreas);
    point.setAttribute("r", point.dataset.baseRadius || LATENCY_POINT_BASE_RADIUS);
    if (isLatencySelectedItemId(point.dataset.itemId)) {
      point.classList.add("is-active", "is-selected");
      point.classList.toggle("is-lensed", lens.strength > 0.03);
    } else {
      point.classList.toggle("is-lensed", lens.strength > 0.03);
      point.classList.remove("is-active", "is-selected");
    }
  }

  if (!anchorPoint) {
    latencyActiveScatterPoint = null;
    hideLatencyTooltip();
    return;
  }

  activateLatencyScatterPoint(anchorPoint, event);
}

function resetLatencyScatterMagnificationOutsideChart(event) {
  if ((!latencyActiveScatterPoint && !latencyState.selectedItemId) || !latencyRefs.scatter) return;
  if (!latencyRefs.scatter.contains(event.target)) resetLatencyScatterMagnification();
}

function getLatencyScatterClickPoint(event) {
  if (!event.target || typeof event.target.closest !== "function") return latencyActiveScatterPoint;
  const hitTarget = latencyActiveScatterPoint || event.target.closest(".latency-point") || event.target.closest(".latency-point-hitarea");
  if (!hitTarget || !latencyRefs.scatter) return null;
  const itemId = hitTarget.dataset.itemId;
  if (!itemId) return null;
  return latencyRefs.scatter.querySelector(`.latency-point[data-item-id="${CSS.escape(itemId)}"]`) || hitTarget;
}

function syncLatencyViewToggle() {
  Array.from(latencyRefs.viewOptions || []).forEach((button) => {
    const isActive = button.dataset.latencyViewMode === latencyState.viewMode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function scheduleLatencyScatterResize() {
  if (!latencyState.filtered.length || latencyScatterResizeFrame) return;
  latencyScatterResizeFrame = requestAnimationFrame(() => {
    latencyScatterResizeFrame = 0;
    renderLatencyScatter(latencyState.filtered);
  });
}

function latencySortValue(item, sortMode) {
  return item.averageMs ?? Number.POSITIVE_INFINITY;
}

function sortLatencyItems(items) {
  const sortMode = latencyRefs.sortSelect.value || "average";
  const sorted = [...items].sort((left, right) => {
    if (sortMode === "date-added") {
      const leftDate = getLatencyDateSortValue(left);
      const rightDate = getLatencyDateSortValue(right);
      if (leftDate === null && rightDate !== null) return 1;
      if (rightDate === null && leftDate !== null) return -1;
      if (leftDate !== null && rightDate !== null) {
        const dateResult = leftDate - rightDate;
        if (dateResult !== 0) return latencyState.sortDescending ? -dateResult : dateResult;
      }
      return latencyTextCollator.compare(left.name || "", right.name || "");
    }

    const leftValue = latencySortValue(left, sortMode);
    const rightValue = latencySortValue(right, sortMode);
    let result = 0;
    if (typeof leftValue === "string" || typeof rightValue === "string") {
      result = latencyTextCollator.compare(String(leftValue), String(rightValue));
    } else {
      result = leftValue - rightValue;
    }
    if (result === 0) {
      result = latencyTextCollator.compare(left.name || "", right.name || "");
    }
    return latencyState.sortDescending ? -result : result;
  });
  return sorted;
}

function compareLatencyRankItems(left, right) {
  const leftValue = left.averageMs ?? Number.POSITIVE_INFINITY;
  const rightValue = right.averageMs ?? Number.POSITIVE_INFINITY;
  const latencyResult = leftValue - rightValue;
  if (latencyResult !== 0) return latencyResult;
  return latencyTextCollator.compare(left.name || "", right.name || "");
}

function assignLatencyDisplayRanks(items) {
  for (const item of items) {
    item.overallRank = null;
    item.modeRank = null;
  }

  const ranked = [...items].filter((item) => isFiniteLatencyNumber(item.averageMs)).sort(compareLatencyRankItems);
  ranked.forEach((item, index) => {
    item.overallRank = index + 1;
  });

  const grouped = new Map();
  for (const item of ranked) {
    const rankMode = String(item.rankMode || "").trim();
    if (!rankMode) continue;
    if (!grouped.has(rankMode)) grouped.set(rankMode, []);
    grouped.get(rankMode).push(item);
  }

  for (const groupItems of grouped.values()) {
    groupItems.sort(compareLatencyRankItems).forEach((item, index) => {
      item.modeRank = index + 1;
    });
  }
}

function variantMatchesLatencyFilters(variant, connection, category, saleStatus, sourceStatus, tier, mode, adapterInput, faceButtons, homeButton) {
  if (connection && getLatencyConnectionFilterValue(variant) !== connection) return false;
  if (category && variant.category !== category) return false;
  if (saleStatus && getLatencySaleStatus(variant) !== saleStatus) return false;
  if (sourceStatus && getLatencySourceStatus(variant) !== sourceStatus) return false;
  if (tier && variant.averageTier !== tier) return false;
  if (mode && !getLatencyOutputModes(variant).includes(mode)) return false;
  if (adapterInput && (variant.category !== "Controller Adapter" || !getLatencyAdapterInputs(variant).includes(adapterInput))) return false;
  if (faceButtons && getLatencyFaceButtons(variant) !== faceButtons) return false;
  if (homeButton && getLatencyHomeButton(variant) !== homeButton) return false;
  return true;
}

function resolveLatencyDisplayItem(item, filters) {
  if (filters.query && !String(item.searchText || "").includes(filters.query)) return null;
  let candidates = getLatencyVariants(item)
    .filter((variant) => variantMatchesLatencyFilters(
      variant,
      filters.connection,
      filters.category,
      filters.saleStatus,
      filters.sourceStatus,
      filters.tier,
      filters.mode,
      filters.adapterInput,
      filters.faceButtons,
      filters.homeButton,
    ));
  if (filters.query) {
    const queryMatches = candidates.filter((variant) => getLatencyVariantSearchText(variant).includes(filters.query));
    if (queryMatches.length) candidates = queryMatches;
  }
  candidates = candidates
    .sort((left, right) => {
      const latencyResult = (left.averageMs ?? Infinity) - (right.averageMs ?? Infinity);
      if (latencyResult !== 0) return latencyResult;
      return latencyTextCollator.compare(left.name || "", right.name || "");
    });
  if (!candidates.length) return null;
  const selected = candidates[0];
  return {
    ...item,
    ...selected,
    id: item.id,
    name: item.name,
    deviceNorm: item.deviceNorm,
    searchText: item.searchText,
    controllerGroupKey: item.controllerGroupKey,
    modeVariants: item.modeVariants,
    modeVariantCount: item.modeVariantCount,
    displayVariantId: selected.id,
    rankMode: item.rankMode,
    overallRank: item.overallRank,
    modeRank: item.modeRank,
  };
}

function syncLatencySortDirectionToggle() {
  latencyRefs.sortDirectionToggle.textContent = latencyState.sortDescending ? "Descending" : "Ascending";
  latencyRefs.sortDirectionToggle.setAttribute("aria-pressed", String(latencyState.sortDescending));
  latencyRefs.sortDirectionToggle.title = latencyState.sortDescending
    ? "Switch to ascending sort"
    : "Switch to descending sort";
}

function updateLatencyMeta(items) {
}

function renderLatencyHeroStats(summary) {
  latencyRefs.heroStats.innerHTML = "";
  const generatedAt = latencyState.generatedAt ? latencyDateFormatter.format(new Date(latencyState.generatedAt)) : "Unknown";
  const stats = [
    { label: "Results", value: latencyNumberFormatter.format(summary.totalItems || 0), filter: "" },
    { label: "Best Average", value: formatLatencyMs(summary.bestAverageMs), filter: "" },
    { label: "Updated", value: generatedAt, filter: "" },
  ];

  for (const stat of stats) {
    const button = document.createElement("button");
    button.className = "hero-stat latency-hero-stat";
    button.type = "button";
    if (stat.filter) button.dataset.heroFilter = stat.filter;
    const value = document.createElement("strong");
    value.textContent = stat.value;
    const label = document.createElement("span");
    label.textContent = stat.label;
    button.append(value, label);
    latencyRefs.heroStats.appendChild(button);
  }
}

function applyLatencyFilters() {
  syncLatencyAdapterInputAvailability();
  syncLatencyControllerAttributeAvailability();
  if (latencyState.selectedItemId) {
    latencyState.selectedItemId = "";
    latencyState.selectedDisplayVariantId = "";
    hideLatencyTooltip(true);
  }
  const query = latencyRefs.searchInput.value.trim().toLowerCase();
  const filters = {
    query,
    connection: latencyRefs.connectionSelect.value,
    category: latencyRefs.categorySelect.value,
    saleStatus: latencyRefs.saleStatusSelect.value,
    sourceStatus: latencyRefs.sourceStatusSelect.value,
    tier: latencyRefs.tierSelect.value,
    mode: latencyRefs.modeSelect.value,
    adapterInput: latencyRefs.categorySelect.value === "Controller Adapter" ? latencyRefs.adapterInputSelect.value : "",
    faceButtons: isLatencyControllerAttributeCategory(latencyRefs.categorySelect.value) ? latencyRefs.faceButtonsSelect.value : "",
    homeButton: isLatencyControllerAttributeCategory(latencyRefs.categorySelect.value) ? latencyRefs.homeButtonSelect.value : "",
  };
  const filtered = latencyState.items
    .map((item) => resolveLatencyDisplayItem(item, filters))
    .filter(Boolean);
  latencyState.filtered = sortLatencyItems(filtered);
  updateLatencyMeta(latencyState.filtered);
  renderLatencyItems(latencyState.filtered);
  renderLatencyScatter(latencyState.filtered);
}

function applyLatencyQuickFilter(filter, value) {
  if (filter === "tier") {
    latencyRefs.tierSelect.value = value;
    applyLatencyFilters();
  } else if (filter === "saleStatus") {
    latencyRefs.saleStatusSelect.value = value;
    applyLatencyFilters();
  } else if (filter === "sourceStatus") {
    latencyRefs.sourceStatusSelect.value = value;
    applyLatencyFilters();
  } else if (filter === "search") {
    latencyRefs.searchInput.value = value;
    applyLatencyFilters();
  }
}

async function loadLatencyData() {
  try {
    const inlineData = globalThis.MISTER_LATENCY_DATA;
    const payload = inlineData && Array.isArray(inlineData.items)
      ? inlineData
      : await fetchLatencyPayload(getLatencyDataUrl());

    latencyState.items = Array.isArray(payload.items) ? payload.items : [];
    latencyState.summary = payload.summary || {};
    latencyState.generatedAt = payload.generatedAt || "";

    assignLatencyDisplayRanks(latencyState.items);
    populateLatencyControls(latencyState.items);
    renderLatencyHeroStats(latencyState.summary);
    renderLatencyRecentItems(getMostRecentLatencyItems(latencyState.items));
    hideLatencyStatus();
    applyLatencyFilters();
  } catch (error) {
    showLatencyStatus(`Could not load latency data: ${error.message}`);
  }
}

latencyRefs.searchInput.addEventListener("input", applyLatencyFilters);
latencyRefs.connectionSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.modeSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.adapterInputSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.faceButtonsSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.homeButtonSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.categorySelect.addEventListener("change", () => {
  syncLatencyAdapterInputAvailability();
  syncLatencyControllerAttributeAvailability();
  applyLatencyFilters();
});
latencyRefs.saleStatusSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.sourceStatusSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.tierSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.sortSelect.addEventListener("change", applyLatencyFilters);
latencyRefs.sortDirectionToggle.addEventListener("click", () => {
  latencyState.sortDescending = !latencyState.sortDescending;
  syncLatencySortDirectionToggle();
  applyLatencyFilters();
});
Array.from(latencyRefs.viewOptions || []).forEach((button) => {
  button.addEventListener("click", () => {
    const nextMode = button.dataset.latencyViewMode || "list";
    if (latencyState.viewMode === nextMode) return;
    latencyState.viewMode = nextMode;
    syncLatencyViewToggle();
    renderLatencyItems(latencyState.filtered);
  });
});
if (latencyRefs.recentList) {
  latencyRefs.recentList.addEventListener("click", (event) => {
    const target = event.target.closest("[data-recent-item-id]");
    if (!target || !latencyRefs.recentList.contains(target)) return;
    event.stopPropagation();
    selectLatencyRecentItem(target.dataset.recentItemId, target.dataset.recentDisplayVariantId || "");
  });
}
if (latencyRefs.xZoomSlider) {
  latencyRefs.xZoomSlider.addEventListener("input", () => {
    setLatencyXZoomLevel(Number.parseFloat(latencyRefs.xZoomSlider.value) || 0);
  });
}
if (latencyRefs.xPanScrollbar) {
  latencyRefs.xPanScrollbar.addEventListener("scroll", () => {
    if (latencyPanScrollbarSyncing || latencyState.xZoomLevel <= 0) return;
    const maxScroll = Math.max(latencyRefs.xPanScrollbar.scrollWidth - latencyRefs.xPanScrollbar.clientWidth, 0);
    if (maxScroll <= 0) return;
    setLatencyXPanRatio(latencyRefs.xPanScrollbar.scrollLeft / maxScroll);
  });
}
latencyRefs.grid.addEventListener("click", (event) => {
  const target = event.target.closest("[data-filter]");
  if (target) {
    applyLatencyQuickFilter(target.dataset.filter, target.dataset.value || target.textContent);
    return;
  }
  if (event.target.closest("a, button, input, select, textarea")) return;
  const card = event.target.closest(".latency-card.is-expandable");
  if (!card || !latencyRefs.grid.contains(card)) return;
  toggleLatencyCard(card);
});
latencyRefs.grid.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  if (event.target.closest("a, button, input, select, textarea")) return;
  const card = event.target.closest(".latency-card.is-expandable");
  if (!card || !latencyRefs.grid.contains(card)) return;
  event.preventDefault();
  toggleLatencyCard(card);
});
if (latencyRefs.scatter) {
  window.addEventListener("resize", scheduleLatencyScatterResize);
  document.addEventListener("pointermove", resetLatencyScatterMagnificationOutsideChart);
  latencyRefs.scatter.addEventListener("wheel", handleLatencyScatterWheel, { passive: false });
  latencyRefs.scatter.addEventListener("pointermove", updateLatencyScatterMagnification);
  latencyRefs.scatter.addEventListener("pointerleave", resetLatencyScatterMagnification);
  latencyRefs.scatter.addEventListener("mouseleave", resetLatencyScatterMagnification);
  latencyRefs.scatter.addEventListener("pointercancel", resetLatencyScatterMagnification);
  latencyRefs.scatter.addEventListener("focusin", (event) => {
    const point = event.target.closest(".latency-point");
    if (!point) return;
    resetLatencyScatterMagnification();
    point.setAttribute("r", point.dataset.baseRadius || LATENCY_POINT_BASE_RADIUS);
    point.classList.add("is-active");
    if (point.parentNode) point.parentNode.appendChild(point);
  });
  latencyRefs.scatter.addEventListener("focusout", (event) => {
    if (event.target.closest(".latency-point")) resetLatencyScatterMagnification();
  });
  latencyRefs.scatter.addEventListener("click", (event) => {
    const point = getLatencyScatterClickPoint(event);
    event.stopPropagation();
    if (point) {
      selectLatencyScatterPoint(point, event);
      return;
    }
    clearLatencyScatterSelection();
  });
  latencyRefs.scatter.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const point = event.target.closest(".latency-point");
    if (!point) return;
    event.preventDefault();
    selectLatencyScatterPoint(point, event);
  });
}
document.addEventListener("click", (event) => {
  if (!latencyState.selectedItemId) return;
  const target = event.target;
  if (target && typeof target.closest === "function") {
    if (target.closest(".latency-point, .latency-point-hitarea, .latency-card.is-selected, .latency-tooltip")) return;
  }
  clearLatencyScatterSelection();
});
latencyRefs.heroStats.addEventListener("click", (event) => {
  const target = event.target.closest("[data-hero-filter]");
  if (!target) return;
  latencyRefs.searchInput.value = target.dataset.heroFilter || "";
  applyLatencyFilters();
});

syncLatencySortDirectionToggle();
syncLatencyViewToggle();
syncLatencyXZoomControl(0);
showLatencyStatus("Loading latency data...");
loadLatencyData();
