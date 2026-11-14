const latencyState = {
  items: [],
  filtered: [],
  summary: null,
  sortDescending: false,
  xZoomLevel: 0,
  xPanRatio: 0.5,
  page: "latencyPageRanking",
  selectedItemId: "",
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
  moreFiltersCount: document.getElementById("latencyMoreCount"),
  menu: document.getElementById("latencyMenu"),
  identCount: document.getElementById("latencyIdentCount"),
  identBest: document.getElementById("latencyIdentBest"),
  identMedian: document.getElementById("latencyIdentMedian"),
  identUpdated: document.getElementById("latencyIdentUpdated"),
  count: document.getElementById("latencyCount"),
  rows: document.getElementById("latencyRows"),
  statusBanner: document.getElementById("latencyStatusBanner"),
  recentMeta: document.getElementById("latencyRecentMeta"),
  recentRows: document.getElementById("latencyRecentRows"),
  best: document.getElementById("latencyBest"),
  methodBest: document.getElementById("latencyMethodBest"),
  methodRaw: document.getElementById("latencyMethodRaw"),
  mapMeta: document.getElementById("latencyMapMeta"),
  readout: document.getElementById("latencyReadout"),
  tiers: document.getElementById("latencyTiers"),
  xZoomSlider: document.getElementById("latencyXZoomSlider"),
  xZoomLabel: document.getElementById("latencyXZoomLabel"),
  xPanScrollbar: document.getElementById("latencyXPanScrollbar"),
  xPanTrack: document.getElementById("latencyXPanTrack"),
  scatter: document.getElementById("latencyScatter"),
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
const LATENCY_TIER_RANGES = {
  Diamond: "0-1 ms",
  Platinum: "1-2 ms",
  Gold: "2-5 ms",
  Silver: "5-10 ms",
  Bronze: "10-16.67 ms",
  Copper: "16.67-33.33 ms",
  Rust: "33.33+ ms",
};
// Upper bound of each tier but the last, in ms. Copper and Rust are past one 60 Hz frame.
const LATENCY_TIER_BOUNDS = [1, 2, 5, 10, 16.67, 33.33];
const LATENCY_LATE_TIERS = new Set(["Copper", "Rust"]);
const LATENCY_SALE_STATUS_ORDER = ["Actively sold", "Discontinued", "Unknown"];
const LATENCY_SOURCE_STATUS_ORDER = ["Open Source", "Closed Source"];
const LATENCY_CONNECTION_ORDER = ["Wired", "Wireless BT", "Wireless 2.4GHz", "Wireless"];
const LATENCY_CONNECTION_SHORT = {
  Wired: "Wired",
  "Wireless BT": "BT",
  "Wireless 2.4GHz": "2.4G",
  Wireless: "Wireless",
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
const LATENCY_LOG_X_TICKS = [0.5, 1, 2, 5, 10, 20, 50, 100, 200];
const LATENCY_X_ZOOM_MAX = 100;
const LATENCY_X_ZOOM_STEP = 0.04;
const LATENCY_X_ZOOM_MIN_LOG_RATIO = 0.04;
const LATENCY_X_DOMAIN_PAD_RATIO = 0.04;
const LATENCY_MARK_SIZE = 4;
const LATENCY_POINT_MAGNIFY_RANGE = 58;
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

function normalizeExternalProductUrl(value) {
  const normalized = normalizeLatencyUrl(value);
  if (!normalized || typeof window === "undefined" || !window.location) return normalized;

  try {
    const url = new URL(normalized, window.location.href);
    if (url.origin !== window.location.origin && url.pathname.startsWith("/products/")) {
      // ReStock treats every literal /products/ link as a same-store product, even on another origin.
      url.pathname = url.pathname.replace(/^\/products\//, "/%70roducts/");
    }
    return url.href;
  } catch (error) {
    return normalized;
  }
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

function showLatencyStatus(message, isError = false) {
  latencyRefs.statusBanner.textContent = message;
  latencyRefs.statusBanner.classList.toggle("svc-danger", isError);
  latencyRefs.statusBanner.hidden = false;
}

function hideLatencyStatus() {
  latencyRefs.statusBanner.hidden = true;
  latencyRefs.statusBanner.textContent = "";
}

function escapeLatencyHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character]));
}

function formatLatencyMs(value) {
  return Number.isFinite(value) ? `${latencyMsFormatter.format(value)} ms` : "-";
}

function formatLatencyMsValue(value) {
  return Number.isFinite(value) ? latencyMsFormatter.format(value) : "-";
}

function formatLatencyPercent(value) {
  return Number.isFinite(value) ? `${latencyPercentFormatter.format(value)}%` : "-";
}

function formatLatencyTick(value) {
  const digits = value < 1 ? 2 : value < 10 ? 1 : 0;
  return String(Number(value.toFixed(digits)));
}

function padLatencyDatePart(value) {
  return String(value).padStart(2, "0");
}

function formatLatencyIsoDate(timestamp) {
  const date = new Date(timestamp);
  return `${date.getFullYear()}-${padLatencyDatePart(date.getMonth() + 1)}-${padLatencyDatePart(date.getDate())}`;
}

function formatLatencyTimestamp(value) {
  const timestamp = Date.parse(value || "");
  if (Number.isNaN(timestamp)) return "Unknown";
  const date = new Date(timestamp);
  return `${formatLatencyIsoDate(timestamp)} ${padLatencyDatePart(date.getHours())}:${padLatencyDatePart(date.getMinutes())}`;
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
  if (timestamp !== null) return formatLatencyIsoDate(timestamp);
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

function isFiniteLatencyNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function clampLatencyValue(value, min, max) {
  return Math.min(Math.max(value, min), max);
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

function isLatencyLateTier(tier) {
  return LATENCY_LATE_TIERS.has(tier);
}

function getLatencyTierForMs(value) {
  const index = LATENCY_TIER_BOUNDS.findIndex((bound) => value <= bound);
  return LATENCY_TIER_ORDER[index < 0 ? LATENCY_TIER_ORDER.length - 1 : index];
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

function getLatencyConnectionShort(item) {
  const value = getLatencyConnectionFilterValue(item);
  return LATENCY_CONNECTION_SHORT[value] || value || "-";
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
  if (!enabled && latencyRefs.adapterInputSelect.value) latencyRefs.adapterInputSelect.value = "";
}

function syncLatencyControllerAttributeAvailability() {
  if (!latencyRefs.categorySelect || !latencyRefs.faceButtonsSelect || !latencyRefs.homeButtonSelect) return;
  const enabled = isLatencyControllerAttributeCategory(latencyRefs.categorySelect.value);
  latencyRefs.faceButtonsSelect.disabled = !enabled;
  latencyRefs.homeButtonSelect.disabled = !enabled;
  if (!enabled && latencyRefs.faceButtonsSelect.value) latencyRefs.faceButtonsSelect.value = "";
  if (!enabled && latencyRefs.homeButtonSelect.value) latencyRefs.homeButtonSelect.value = "";
}

function syncLatencyMoreFiltersCount() {
  if (!latencyRefs.moreFiltersCount) return;
  const active = [
    latencyRefs.faceButtonsSelect,
    latencyRefs.homeButtonSelect,
    latencyRefs.adapterInputSelect,
    latencyRefs.modeSelect,
    latencyRefs.sourceStatusSelect,
  ].filter((select) => select && select.value).length;
  latencyRefs.moreFiltersCount.textContent = active ? ` (${active} set)` : "";
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

const EMPTY_LATENCY_DETAIL_VALUES = new Set(["", "-", "--", "N/A", "n/a"]);

function isEmptyLatencyDetailValue(value) {
  return value === null || value === undefined || EMPTY_LATENCY_DETAIL_VALUES.has(String(value).trim());
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
    return "Same frame (from avg) is derived from average latency for consistent comparison. Observed same-frame, 99th percentile, and sample count come from raw capture data.";
  }
  if (isFiniteLatencyNumber(item.observedSameFramePct)) {
    return "Same frame (from avg) is derived from average latency for consistent comparison. Source same-frame is retained separately when provided.";
  }
  return "Same frame (from avg) is derived from average latency. This row does not include separate observed same-frame or 99th percentile data.";
}

function formatLatencyMinMax(item) {
  if (!isFiniteLatencyNumber(item.minMs) || !isFiniteLatencyNumber(item.maxMs)) return "-";
  return `${formatLatencyMsValue(item.minMs)} / ${formatLatencyMs(item.maxMs)}`;
}

function getLatencyDetailFields(item) {
  // Fields with nothing to report are left out rather than printed as N/A,
  // which keeps the leader lines to the values that actually carry data.
  const fields = [
    ["Same frame (from avg)", formatLatencyPercent(item.sameFramePct)],
    [item.hasRawCapture ? "Same frame (observed)" : "Same frame (source)", formatLatencyPercent(item.observedSameFramePct)],
    ["99th percentile", formatLatencyMs(item.p99Ms)],
    ["Std deviation", formatLatencyMs(item.sdMs)],
    ["Min / max", formatLatencyMinMax(item)],
    ["Samples", item.sampleCount ? latencyNumberFormatter.format(item.sampleCount) : "-"],
    ["Stats source", getLatencyDetailSource(item)],
    ["Added", formatLatencyDateAdded(item)],
    ["Category", item.category || "-"],
    ["Adapter input", formatLatencyAdapterInputs(item)],
    ["Connection", item.connection || item.connectionKind || "-"],
    ["Input mode", simplifyLatencyModeLabel(item.modeRaw || item.modeDisplay || item.modeLabel) || "-"],
    ["Output mode", formatLatencyOutputModes(item)],
    ["Face buttons", getLatencyFaceButtons(item) || "N/A"],
    ["Home button", getLatencyHomeButton(item) || "N/A"],
    ["Sale status", getLatencySaleStatus(item)],
    ["Firmware", getLatencySourceStatus(item)],
    ["VID:PID", normalizeLatencyLabel(item.joystickId) || "N/A"],
    ["Weight", formatLatencyWeight(item)],
  ];
  if (isFiniteLatencyNumber(item.measuredAverageMs)) {
    fields.push(["Measured total", formatLatencyMs(item.measuredAverageMs)]);
  }
  if (isFiniteLatencyNumber(item.adapterAverageMs)) {
    const adapterLabel = item.adapterMode ? `${formatLatencyMs(item.adapterAverageMs)} ${item.adapterMode}` : formatLatencyMs(item.adapterAverageMs);
    fields.push(["Adapter baseline", adapterLabel]);
  }
  return fields.filter(([, value]) => !isEmptyLatencyDetailValue(value));
}

function renderLatencyLead(label, valueHtml, valueClass = "") {
  return `<div class="svc-lead"><span class="svc-label">${escapeLatencyHtml(label)}</span><span class="svc-value ${valueClass}">${valueHtml}</span></div>`;
}

function getLatencyMeterRatio(value) {
  // Fixed 0.5-50 ms log scale, so bars compare across filters.
  if (!isFiniteLatencyNumber(value) || value <= 0) return 0;
  return clampLatencyValue((Math.log10(value) - Math.log10(0.5)) / 2, 0, 1);
}

function getLatencyProductLinks(item) {
  const links = [];
  const buyUrl = normalizeExternalProductUrl(item.buyUrl);
  const sourceUrl = normalizeExternalProductUrl(item.sourceUrl);
  if (/^https?:\/\//i.test(buyUrl)) links.push({ label: "Buy", href: buyUrl, title: "Open product page" });
  if (/^https?:\/\//i.test(sourceUrl) && sourceUrl !== buyUrl) links.push({ label: "Source", href: sourceUrl, title: "Open source page" });
  return links;
}

function renderLatencyModeVariants(item) {
  const variants = getLatencyVariants(item);
  if (variants.length <= 1) return "";
  const rows = [...variants]
    .sort((left, right) => (left.averageMs ?? Infinity) - (right.averageMs ?? Infinity))
    .map((variant) => {
      const current = variant.id === item.displayVariantId;
      const value = [
        formatLatencyMs(variant.averageMs),
        variant.averageTier || "-",
        variant.connectionTag || variant.connectionKind || variant.resultLabel || "",
      ].filter(Boolean).join(" · ");
      const late = isLatencyLateTier(variant.averageTier) ? " svc-danger" : "";
      return renderLatencyLead(getLatencyVariantModeDisplay(variant) || variant.name || "-", escapeLatencyHtml(value), `${current ? "svc-changed" : ""}${late}`);
    });
  return `<h3 class="svc-sub">Measured modes</h3><div class="svc-leaders latency-modes">${rows.join("")}</div>`;
}

function renderLatencyDetail(item) {
  const leads = getLatencyDetailFields(item).map(([label, value]) => renderLatencyLead(label, escapeLatencyHtml(value))).join("");
  const links = getLatencyProductLinks(item)
    .map((link, index) => `<a class="latency-action svc-sm${index === 0 ? " svc-primary" : ""}" href="${escapeLatencyHtml(link.href)}" target="_blank" rel="noreferrer noopener" title="${escapeLatencyHtml(link.title)}">${escapeLatencyHtml(link.label)}</a>`)
    .join("");
  return `<tr class="svc-detail" data-detail-for="${escapeLatencyHtml(item.id)}"><td colspan="7">`
    + `<div class="svc-leaders svc-leaders-cols">${leads}</div>`
    + renderLatencyModeVariants(item)
    + `<p class="latency-note">${escapeLatencyHtml(buildLatencyDetailNote(item))}</p>`
    + (links ? `<div class="svc-row">${links}</div>` : "")
    + "</td></tr>";
}

function renderLatencyRow(item, open) {
  const late = isLatencyLateTier(item.averageTier);
  const danger = late ? " svc-danger" : "";
  const rank = Number.isFinite(item.overallRank) ? latencyNumberFormatter.format(item.overallRank) : "-";
  const modeRank = Number.isFinite(item.modeRank) && item.rankMode
    ? `<span title="${escapeLatencyHtml(`Ranked by average latency within all ${item.rankMode} results`)}">#${latencyNumberFormatter.format(item.modeRank)} ${escapeLatencyHtml(item.rankMode)}</span>`
    : "-";
  const meter = (getLatencyMeterRatio(item.averageMs) * 100).toFixed(1);
  return `<tr class="latency-row js-row" tabindex="0" aria-expanded="${open}" data-item-id="${escapeLatencyHtml(item.id)}">`
    + `<td class="svc-num svc-muted" title="Ranked by average latency across all results">${rank}</td>`
    + `<td class="svc-name">${escapeLatencyHtml(item.name)}</td>`
    + `<td class="svc-num${danger}">${formatLatencyMsValue(item.averageMs)}</td>`
    + `<td class="svc-hide-sm"><span class="svc-meter" aria-hidden="true"><i class="${late ? "svc-danger" : ""}" style="width:${meter}%"></i></span></td>`
    + `<td class="latency-tier${danger}">${escapeLatencyHtml(item.averageTier || "-")}</td>`
    + `<td class="svc-hide-md svc-muted">${escapeLatencyHtml(getLatencyConnectionShort(item))}</td>`
    + `<td class="svc-hide-md svc-muted">${modeRank}</td>`
    + "</tr>";
}

function renderLatencyItems(items) {
  if (latencyState.selectedItemId && !items.some((item) => item.id === latencyState.selectedItemId)) {
    latencyState.selectedItemId = "";
  }
  latencyRefs.count.textContent = `${latencyNumberFormatter.format(items.length)} of ${latencyNumberFormatter.format(latencyState.items.length)}`;
  if (!items.length) {
    latencyRefs.rows.innerHTML = '<tr><td colspan="7" class="svc-muted latency-empty">No devices match. Clear the search or a filter.</td></tr>';
    return;
  }
  latencyRefs.rows.innerHTML = items.map((item) => {
    const open = item.id === latencyState.selectedItemId;
    return renderLatencyRow(item, open) + (open ? renderLatencyDetail(item) : "");
  }).join("");
}

function getLatencyRowElement(itemId) {
  return latencyRefs.rows.querySelector(`tr.js-row[data-item-id="${CSS.escape(itemId || "")}"]`);
}

function focusLatencyRow(itemId, options = {}) {
  const row = getLatencyRowElement(itemId);
  if (!row) return;
  row.focus({ preventScroll: true });
  if (options.scroll && typeof row.scrollIntoView === "function") {
    row.scrollIntoView({ block: "center", behavior: "smooth" });
  }
}

function toggleLatencyRow(itemId) {
  latencyState.selectedItemId = latencyState.selectedItemId === itemId ? "" : itemId;
  renderLatencyItems(latencyState.filtered);
  syncLatencyScatterSelection();
  focusLatencyRow(itemId);
}

function openLatencyItem(itemId, options = {}) {
  if (!latencyState.filtered.some((item) => item.id === itemId)) return;
  latencyState.selectedItemId = itemId;
  renderLatencyItems(latencyState.filtered);
  syncLatencyScatterSelection();
  showLatencyPage("latencyPageRanking");
  focusLatencyRow(itemId, { scroll: options.scroll !== false });
}

function selectLatencyRecentItem(itemId) {
  if (!latencyState.items.some((item) => item.id === itemId)) return;
  clearLatencyFilterControls();
  applyLatencyFilters();
  openLatencyItem(itemId);
}

function renderLatencyRecentItems(items) {
  if (!latencyRefs.recentRows) return;
  latencyRefs.recentMeta.textContent = items.length ? `${items.length} newest` : "No dated results";
  if (!items.length) {
    latencyRefs.recentRows.innerHTML = '<tr><td colspan="5" class="svc-muted">No recently dated latency results are available.</td></tr>';
    return;
  }
  latencyRefs.recentRows.innerHTML = items.map((item) => {
    const danger = isLatencyLateTier(item.averageTier) ? " svc-danger" : "";
    return `<tr class="latency-jump" tabindex="0" data-recent-item-id="${escapeLatencyHtml(item.id)}" title="Open in Ranking">`
      + `<td class="svc-muted">${escapeLatencyHtml(formatLatencyDateAdded(item))}</td>`
      + `<td class="svc-name">${escapeLatencyHtml(item.name)}</td>`
      + `<td class="svc-num${danger}">${formatLatencyMsValue(item.averageMs)}</td>`
      + `<td class="latency-tier${danger}">${escapeLatencyHtml(item.averageTier || "-")}</td>`
      + `<td class="svc-hide-md svc-muted">${escapeLatencyHtml(getLatencyConnectionShort(item))}</td>`
      + "</tr>";
  }).join("");
}

function renderLatencyBestByCategory(items) {
  if (!latencyRefs.best) return;
  const groups = new Map();
  for (const item of items) {
    const category = item.category && item.category !== "Uncategorized" ? item.category : "Other";
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category).push(item);
  }
  latencyRefs.best.innerHTML = [...groups.entries()]
    .sort((left, right) => right[1].length - left[1].length || latencyTextCollator.compare(left[0], right[0]))
    .map(([category, groupItems]) => {
      const best = [...groupItems].sort(compareLatencyRankItems)[0];
      const danger = isLatencyLateTier(best.averageTier) ? "svc-danger" : "";
      return renderLatencyLead(`${category} (${groupItems.length})`, `${escapeLatencyHtml(best.name)} &middot; ${escapeLatencyHtml(formatLatencyMs(best.averageMs))}`, danger);
    })
    .join("");
}

function renderLatencyTierCounts(items) {
  if (!latencyRefs.tiers) return;
  const counts = new Map();
  for (const item of items) counts.set(item.averageTier, (counts.get(item.averageTier) || 0) + 1);
  latencyRefs.tiers.innerHTML = LATENCY_TIER_ORDER
    .map((tier) => renderLatencyLead(`${tier} ${LATENCY_TIER_RANGES[tier]}`, latencyNumberFormatter.format(counts.get(tier) || 0), isLatencyLateTier(tier) ? "svc-danger" : ""))
    .join("");
}

function renderLatencyIdent(summary) {
  const total = summary.totalItems || latencyState.items.length;
  latencyRefs.identCount.textContent = `${latencyNumberFormatter.format(total)} ${total === 1 ? "result" : "results"}`;
  latencyRefs.identBest.textContent = formatLatencyMs(summary.bestAverageMs);
  latencyRefs.identMedian.textContent = formatLatencyMs(summary.medianAverageMs);
  latencyRefs.identUpdated.textContent = formatLatencyTimestamp(latencyState.generatedAt);
  if (latencyRefs.methodBest) latencyRefs.methodBest.textContent = formatLatencyMs(summary.bestAverageMs);
  if (latencyRefs.methodRaw) {
    const raw = Number.isFinite(summary.rawCaptureItems)
      ? summary.rawCaptureItems
      : latencyState.items.filter((item) => item.hasRawCapture).length;
    const share = total ? (raw / total) * 100 : 0;
    latencyRefs.methodRaw.textContent = `${latencyNumberFormatter.format(raw)} of ${latencyNumberFormatter.format(total)} (${latencyPercentFormatter.format(share)}%)`;
  }
}

function getLatencyMenuTabs() {
  return latencyRefs.menu ? Array.from(latencyRefs.menu.querySelectorAll('[role="tab"]')) : [];
}

function showLatencyPage(pageId) {
  const tabs = getLatencyMenuTabs();
  if (!tabs.some((tab) => tab.dataset.page === pageId)) return;
  latencyState.page = pageId;
  for (const tab of tabs) {
    const selected = tab.dataset.page === pageId;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    const page = document.getElementById(tab.dataset.page);
    if (page) page.hidden = !selected;
  }
  // The map is sized from its rendered box, which is empty while its page is hidden.
  if (pageId === "latencyPageMap") renderLatencyScatter(latencyState.filtered);
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
  // A small margin keeps the fastest and slowest marks off the frame.
  const pad = (Math.log10(maxValue) - Math.log10(minValue)) * LATENCY_X_DOMAIN_PAD_RATIO;
  return {
    min: Math.pow(10, Math.log10(minValue) - pad),
    max: Math.pow(10, Math.log10(maxValue) + pad),
  };
}

function getLatencyLogTicks(domain) {
  const ticks = LATENCY_LOG_X_TICKS.filter((tick) => tick >= domain.min && tick <= domain.max);
  if (ticks.length >= 2) return ticks;
  return Array.from(new Set([domain.min, ...ticks, domain.max])).sort((left, right) => left - right);
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

function isLatencyFullXDomain(xDomain, baseDomain) {
  return !baseDomain || (
    Math.abs(Math.log10(xDomain.min) - Math.log10(baseDomain.min)) < 0.0001
    && Math.abs(Math.log10(xDomain.max) - Math.log10(baseDomain.max)) < 0.0001
  );
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
  const fullDomain = !xDomain || isLatencyFullXDomain(xDomain, baseDomain);
  const isZoomed = latencyState.xZoomLevel > 0.01 && !fullDomain;
  if (latencyRefs.xPanScrollbar) {
    latencyRefs.xPanScrollbar.classList.toggle("is-zoomed", isZoomed);
  }
  if (latencyRefs.xZoomSlider) {
    latencyRefs.xZoomSlider.max = String(LATENCY_X_ZOOM_MAX);
    latencyRefs.xZoomSlider.value = String(Math.round(latencyState.xZoomLevel));
  }
  syncLatencyPanScrollbar(isZoomed, xDomain, baseDomain);
  if (latencyRefs.xZoomLabel) {
    latencyRefs.xZoomLabel.textContent = fullDomain
      ? "All"
      : `${formatLatencyTick(xDomain.min)}-${formatLatencyTick(xDomain.max)} ms`;
  }
  if (latencyRefs.mapMeta) {
    const total = latencyState.items.length;
    const count = latencyNumberFormatter.format;
    latencyRefs.mapMeta.textContent = fullDomain
      ? `${allCount === total ? count(allCount) : `${count(allCount)} of ${count(total)}`} ${allCount === 1 ? "device" : "devices"}`
      : `${count(visibleCount)} of ${count(allCount)} in window`;
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

function renderLatencyScatter(items) {
  const svg = latencyRefs.scatter;
  if (!svg) return;

  latencyActiveScatterPoint = null;
  const allPlotItems = getLatencyPlotItems(items);
  const baseXDomain = getLatencyLogDomain(allPlotItems.map((item) => item.averageMs));
  const xDomain = getLatencyXDomain(allPlotItems);
  const plotItems = allPlotItems.filter((item) => isLatencyItemInXDomain(item, xDomain));
  syncLatencyXZoomControl(plotItems.length, allPlotItems.length, xDomain, baseXDomain);

  // One viewBox unit per CSS pixel keeps 11 px labels and 4 px marks true to size.
  const width = Math.round(svg.clientWidth);
  const height = Math.round(svg.clientHeight);
  if (!width || !height) {
    latencyScatterLayout = null;
    return;
  }
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const padding = { top: 22, right: 14, bottom: 40, left: 46 };
  const chartWidth = Math.max(width - padding.left - padding.right, 10);
  const bottom = height - padding.bottom;
  const chartHeight = Math.max(bottom - padding.top, 10);
  const box = svg.getBoundingClientRect();
  const clientScale = box.width / Math.max(width + svg.clientLeft * 2, 1);
  latencyScatterLayout = {
    clientChartLeft: box.left + (svg.clientLeft + padding.left) * clientScale,
    clientChartWidth: chartWidth * clientScale,
  };
  svg.dataset.plotLeft = String(padding.left);
  svg.dataset.plotRight = String(padding.left + chartWidth);
  svg.dataset.plotTop = String(padding.top);
  svg.dataset.plotBottom = String(bottom);

  if (!plotItems.length) {
    svg.innerHTML = `<text class="svc-axis-text" x="${width / 2}" y="${height / 2}" text-anchor="middle">No chartable latency data in this filter.</text>`;
    return;
  }

  const xLogMin = Math.log10(xDomain.min);
  const xLogRange = Math.max(Math.log10(xDomain.max) - xLogMin, 0.000001);
  const xScale = (value) => padding.left + ((Math.log10(clampLatencyValue(value, xDomain.min, xDomain.max)) - xLogMin) / xLogRange) * chartWidth;
  const yScale = (value) => bottom - (clampLatencyValue(value, 0, 100) / 100) * chartHeight;
  const right = padding.left + chartWidth;
  let markup = "";

  for (const percent of [0, 25, 50, 75, 100]) {
    const y = yScale(percent).toFixed(1);
    markup += `<line class="svc-grid-line" x1="${padding.left}" x2="${right}" y1="${y}" y2="${y}"/>`;
    markup += `<text class="svc-axis-text" x="${padding.left - 8}" y="${Number(y) + 4}" text-anchor="end">${percent}%</text>`;
  }

  const bounds = LATENCY_TIER_BOUNDS.filter((bound) => bound > xDomain.min && bound < xDomain.max);
  for (const bound of bounds) {
    const x = xScale(bound).toFixed(1);
    markup += `<line class="svc-guide-line" x1="${x}" x2="${x}" y1="${padding.top}" y2="${bottom}"/>`;
  }
  const edges = [xDomain.min, ...bounds, xDomain.max];
  for (let index = 0; index < edges.length - 1; index += 1) {
    const left = xScale(edges[index]);
    const bandRight = xScale(edges[index + 1]);
    if (bandRight - left < 32) continue;
    const tier = getLatencyTierForMs(Math.sqrt(edges[index] * edges[index + 1]));
    markup += `<text class="svc-axis-text" x="${((left + bandRight) / 2).toFixed(1)}" y="${padding.top - 7}" text-anchor="middle">${tier.slice(0, 4).toUpperCase()}</text>`;
  }

  let lastTickX = -Infinity;
  for (const tick of getLatencyLogTicks(xDomain)) {
    const x = xScale(tick);
    if (x - lastTickX < 28) continue;
    lastTickX = x;
    markup += `<text class="svc-axis-text" x="${x.toFixed(1)}" y="${bottom + 16}" text-anchor="middle">${formatLatencyTick(tick)}</text>`;
  }
  markup += `<text class="svc-axis-text" x="${(padding.left + chartWidth / 2).toFixed(1)}" y="${height - 6}" text-anchor="middle">AVERAGE MS, LOG SCALE</text>`;

  const medianAverage = getLatencyMedianAverage(allPlotItems);
  if (isFiniteLatencyNumber(medianAverage) && medianAverage >= xDomain.min && medianAverage <= xDomain.max) {
    const medianX = xScale(medianAverage);
    const labelOnLeft = medianX > right - 120;
    markup += `<g class="latency-median"><line class="svc-ref-line" x1="${medianX.toFixed(1)}" x2="${medianX.toFixed(1)}" y1="${padding.top}" y2="${bottom}"/>`;
    markup += `<text class="svc-ref-label" x="${(medianX + (labelOnLeft ? -6 : 6)).toFixed(1)}" y="${padding.top + 14}" text-anchor="${labelOnLeft ? "end" : "start"}">MEDIAN ${escapeLatencyHtml(formatLatencyMs(medianAverage).toUpperCase())}</text></g>`;
  }
  markup += `<line class="svc-cursor latency-cursor" x1="0" x2="0" y1="${padding.top}" y2="${bottom}" visibility="hidden"/>`;

  const half = LATENCY_MARK_SIZE / 2;
  const marks = plotItems.map((item) => {
    const pointX = xScale(item.averageMs);
    const pointY = yScale(item.sameFramePct);
    const late = isLatencyLateTier(item.averageTier) ? " svc-mark-danger" : "";
    return `<rect class="svc-mark latency-mark${late}" data-item-id="${escapeLatencyHtml(item.id)}"`
      + ` data-base-cx="${pointX.toFixed(2)}" data-base-cy="${pointY.toFixed(2)}"`
      + ` x="${(pointX - half).toFixed(2)}" y="${(pointY - half).toFixed(2)}" width="${LATENCY_MARK_SIZE}" height="${LATENCY_MARK_SIZE}"/>`;
  });
  markup += `<g class="latency-marks">${marks.join("")}</g>`;
  svg.innerHTML = markup;
  syncLatencyScatterSelection();
  resetLatencyReadout();
}

function getLatencyItemById(itemId) {
  return latencyState.filtered.find((item) => item.id === itemId) || latencyState.items.find((item) => item.id === itemId);
}

function getLatencyScatterPoints() {
  return latencyRefs.scatter ? Array.from(latencyRefs.scatter.querySelectorAll(".latency-mark")) : [];
}

function syncLatencyScatterSelection() {
  let selectedPoint = null;
  for (const point of getLatencyScatterPoints()) {
    const selected = Boolean(latencyState.selectedItemId) && point.dataset.itemId === latencyState.selectedItemId;
    point.classList.toggle("svc-on", selected || point === latencyActiveScatterPoint);
    if (selected) selectedPoint = point;
  }
  if (selectedPoint && selectedPoint.parentNode) selectedPoint.parentNode.appendChild(selectedPoint);
  return selectedPoint;
}

function describeLatencyItem(item) {
  return [
    item.name,
    formatLatencyMs(item.averageMs),
    `${formatLatencyPercent(item.sameFramePct)} same frame`,
    item.averageTier || "",
    getLatencyConnectionShort(item),
  ].filter((part) => part && part !== "-").join(" · ");
}

function resetLatencyReadout() {
  if (!latencyRefs.readout) return;
  const selected = latencyState.selectedItemId ? getLatencyItemById(latencyState.selectedItemId) : null;
  latencyRefs.readout.textContent = selected ? describeLatencyItem(selected) : "Point at a device";
}

function setLatencyCursor(x) {
  const cursor = latencyRefs.scatter && latencyRefs.scatter.querySelector(".latency-cursor");
  if (!cursor) return;
  if (x === null) {
    cursor.setAttribute("visibility", "hidden");
    return;
  }
  cursor.setAttribute("x1", x.toFixed(2));
  cursor.setAttribute("x2", x.toFixed(2));
  cursor.setAttribute("visibility", "visible");
}

function selectLatencyScatterPoint(point) {
  const item = point && getLatencyItemById(point.dataset.itemId);
  if (!item) return;
  resetLatencyScatterMagnification();
  openLatencyItem(item.id);
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
  return { x: Number(point.dataset.baseCx), y: Number(point.dataset.baseCy) };
}

function setLatencyPointDisplayPosition(point, x, y) {
  const half = LATENCY_MARK_SIZE / 2;
  point.setAttribute("x", (x - half).toFixed(2));
  point.setAttribute("y", (y - half).toFixed(2));
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
  const angle = getLatencyStableAngle(point.dataset.itemId);
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
  for (const point of getLatencyScatterPoints()) {
    const base = getLatencyPointBasePosition(point);
    if (Number.isFinite(base.x) && Number.isFinite(base.y)) setLatencyPointDisplayPosition(point, base.x, base.y);
  }
  syncLatencyScatterSelection();
  setLatencyCursor(null);
  resetLatencyReadout();
}

function activateLatencyScatterPoint(point) {
  latencyActiveScatterPoint = point;
  syncLatencyScatterSelection();
  point.classList.add("svc-on");
  if (point.parentNode) point.parentNode.appendChild(point);
  setLatencyCursor(getLatencyPointBasePosition(point).x);
  const item = getLatencyItemById(point.dataset.itemId);
  if (item && latencyRefs.readout) latencyRefs.readout.textContent = describeLatencyItem(item);
}

function updateLatencyScatterMagnification(event) {
  const cursor = getLatencySvgPointer(event);
  if (!cursor) return;
  const points = getLatencyScatterPoints();
  const bounds = getLatencyPlotBounds();
  let maxLensStrength = 0;
  let minLensBaseY = Number.POSITIVE_INFINITY;
  let nearest = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  for (const point of points) {
    const distance = getLatencyPointDistance(point, cursor);
    if (distance < nearestDistance) {
      nearest = point;
      nearestDistance = distance;
    }
    if (!Number.isFinite(distance) || distance > LATENCY_POINT_LENS_RADIUS) continue;
    minLensBaseY = Math.min(minLensBaseY, getLatencyPointBasePosition(point).y);
    const strength = clampLatencyValue(1 - distance / LATENCY_POINT_LENS_RADIUS, 0, 1);
    maxLensStrength = Math.max(maxLensStrength, strength * strength * (3 - 2 * strength));
  }
  const requestedPeakLift = maxLensStrength * LATENCY_POINT_LENS_VERTICAL_LIFT;
  const peakLift = Math.min(requestedPeakLift, Math.max(0, minLensBaseY - bounds.top));
  const anchorPoint = nearest && nearestDistance <= LATENCY_POINT_MAGNIFY_RANGE ? nearest : null;

  for (const point of points) {
    const lens = getLatencyLensPosition(point, cursor, bounds, peakLift, point === anchorPoint);
    setLatencyPointDisplayPosition(point, lens.x, lens.y);
  }

  if (!anchorPoint) {
    latencyActiveScatterPoint = null;
    syncLatencyScatterSelection();
    setLatencyCursor(null);
    resetLatencyReadout();
    return;
  }
  activateLatencyScatterPoint(anchorPoint);
}

function scheduleLatencyScatterResize() {
  if (latencyState.page !== "latencyPageMap" || latencyScatterResizeFrame) return;
  latencyScatterResizeFrame = requestAnimationFrame(() => {
    latencyScatterResizeFrame = 0;
    renderLatencyScatter(latencyState.filtered);
  });
}

function latencySortValue(item, sortMode) {
  if (sortMode === "name") return item.name || "";
  if (sortMode === "same-frame") return item.sameFramePct ?? Number.NEGATIVE_INFINITY;
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
  latencyRefs.sortDirectionToggle.innerHTML = latencyState.sortDescending ? "Desc &#9662;" : "Asc &#9652;";
  latencyRefs.sortDirectionToggle.title = latencyState.sortDescending
    ? "Switch to ascending sort"
    : "Switch to descending sort";
}

function applyLatencyFilters() {
  syncLatencyAdapterInputAvailability();
  syncLatencyControllerAttributeAvailability();
  syncLatencyMoreFiltersCount();
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
  renderLatencyItems(latencyState.filtered);
  renderLatencyTierCounts(latencyState.filtered);
  renderLatencyScatter(latencyState.filtered);
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
    renderLatencyIdent(latencyState.summary);
    renderLatencyRecentItems(getMostRecentLatencyItems(latencyState.items));
    renderLatencyBestByCategory(latencyState.items);
    // The fastest device opens on arrival so the leader lines show what a row holds.
    const fastest = latencyState.items.find((item) => item.overallRank === 1);
    latencyState.selectedItemId = fastest ? fastest.id : "";
    hideLatencyStatus();
    applyLatencyFilters();
  } catch (error) {
    latencyRefs.identCount.textContent = "No data";
    showLatencyStatus(`Could not load latency data: ${error.message}`, true);
  }
}

function isLatencyTextEntry(element) {
  return Boolean(element && element.closest && element.closest("input, select, textarea, [contenteditable]"));
}

for (const select of [
  latencyRefs.connectionSelect,
  latencyRefs.modeSelect,
  latencyRefs.adapterInputSelect,
  latencyRefs.faceButtonsSelect,
  latencyRefs.homeButtonSelect,
  latencyRefs.categorySelect,
  latencyRefs.saleStatusSelect,
  latencyRefs.sourceStatusSelect,
  latencyRefs.tierSelect,
  latencyRefs.sortSelect,
]) {
  select.addEventListener("change", applyLatencyFilters);
}
latencyRefs.searchInput.addEventListener("input", applyLatencyFilters);
latencyRefs.sortDirectionToggle.addEventListener("click", () => {
  latencyState.sortDescending = !latencyState.sortDescending;
  syncLatencySortDirectionToggle();
  applyLatencyFilters();
});

latencyRefs.menu.addEventListener("click", (event) => {
  const tab = event.target.closest('[role="tab"]');
  if (tab) showLatencyPage(tab.dataset.page);
});
latencyRefs.menu.addEventListener("keydown", (event) => {
  const step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[event.key];
  if (!step) return;
  const tabs = getLatencyMenuTabs();
  const index = tabs.indexOf(document.activeElement);
  if (index < 0) return;
  event.preventDefault();
  const next = tabs[(index + step + tabs.length) % tabs.length];
  next.focus();
  showLatencyPage(next.dataset.page);
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || isLatencyTextEntry(document.activeElement)) return;
  event.preventDefault();
  showLatencyPage("latencyPageRanking");
  latencyRefs.searchInput.focus();
});

latencyRefs.rows.addEventListener("click", (event) => {
  if (event.target.closest("a, button, input, select, textarea")) return;
  const row = event.target.closest("tr.js-row");
  if (row) toggleLatencyRow(row.dataset.itemId);
});
latencyRefs.rows.addEventListener("keydown", (event) => {
  if ((event.key !== "Enter" && event.key !== " ") || !event.target.matches("tr.js-row")) return;
  event.preventDefault();
  toggleLatencyRow(event.target.dataset.itemId);
});
latencyRefs.recentRows.addEventListener("click", (event) => {
  const row = event.target.closest("[data-recent-item-id]");
  if (row) selectLatencyRecentItem(row.dataset.recentItemId);
});
latencyRefs.recentRows.addEventListener("keydown", (event) => {
  if ((event.key !== "Enter" && event.key !== " ") || !event.target.matches("[data-recent-item-id]")) return;
  event.preventDefault();
  selectLatencyRecentItem(event.target.dataset.recentItemId);
});

latencyRefs.xZoomSlider.addEventListener("input", () => {
  setLatencyXZoomLevel(Number.parseFloat(latencyRefs.xZoomSlider.value) || 0);
});
latencyRefs.xPanScrollbar.addEventListener("scroll", () => {
  if (latencyPanScrollbarSyncing || latencyState.xZoomLevel <= 0) return;
  const maxScroll = Math.max(latencyRefs.xPanScrollbar.scrollWidth - latencyRefs.xPanScrollbar.clientWidth, 0);
  if (maxScroll <= 0) return;
  setLatencyXPanRatio(latencyRefs.xPanScrollbar.scrollLeft / maxScroll);
});
window.addEventListener("resize", scheduleLatencyScatterResize);
latencyRefs.scatter.addEventListener("wheel", handleLatencyScatterWheel, { passive: false });
latencyRefs.scatter.addEventListener("pointermove", updateLatencyScatterMagnification);
// A tap sends no pointermove first, so pick the nearest mark on pointerdown too.
latencyRefs.scatter.addEventListener("pointerdown", updateLatencyScatterMagnification);
latencyRefs.scatter.addEventListener("pointerleave", resetLatencyScatterMagnification);
latencyRefs.scatter.addEventListener("pointercancel", resetLatencyScatterMagnification);
latencyRefs.scatter.addEventListener("click", () => {
  if (latencyActiveScatterPoint) selectLatencyScatterPoint(latencyActiveScatterPoint);
});

syncLatencySortDirectionToggle();
syncLatencyXZoomControl(0);
showLatencyStatus("Loading latency data...");
loadLatencyData();
