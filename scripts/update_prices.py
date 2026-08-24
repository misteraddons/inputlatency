#!/usr/bin/env python3
"""
Update prices in the MiSTer Controller Latency Google Sheet.

Reads Amazon URLs from the spreadsheet, queries the Amazon Creators API
for current prices, and updates the Price column.

Requirements:
  pip install gspread google-auth

Environment variables:
  GOOGLE_SERVICE_ACCOUNT_JSON - key file path or service account JSON document
  AMAZON_CREATORS_CREDENTIAL_ID      - Creators API credential ID
  AMAZON_CREATORS_CREDENTIAL_SECRET  - Creators API credential secret
  AMAZON_CREATORS_CREDENTIAL_VERSION - Creators API credential version
  AMAZON_PARTNER_TAG          - Amazon Associates partner tag
  AMAZON_MARKETPLACE          - Marketplace domain (default: www.amazon.com)

Usage:
  python scripts/update_prices.py             # Update prices in the sheet
  python scripts/update_prices.py --dry-run   # Preview without writing
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SPREADSHEET_ID = "1KlRObr3Be4zLch7Zyqg6qCJzGuhyGmXaOIUrpfncXIM"
SHEET_NAME = "Sheet1"
CREATORS_API_URL = "https://creatorsapi.amazon/catalog/v1/getItems"
CREATORS_TOKEN_ENDPOINTS = {
    "3.1": "https://api.amazon.com/auth/o2/token",
    "3.2": "https://api.amazon.co.uk/auth/o2/token",
    "3.3": "https://api.amazon.co.jp/auth/o2/token",
}
DEFAULT_MARKETPLACE = "www.amazon.com"
CREATORS_PRICE_RESOURCES = (
    "offersV2.listings.price",
    "offersV2.listings.isBuyBoxWinner",
)


def extract_asin(url: str) -> str | None:
    """Extract Amazon ASIN from a URL."""
    if not url:
        return None
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/ASIN/([A-Z0-9]{10})",
        r"amazon\.[^/]+/([A-Z0-9]{10})(?:[/?]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def expand_product_url(url: str) -> str:
    """Follow an Amazon short link and return its destination URL."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; inputlatency-price-updater/1.0)"}
    request = Request(url, headers=headers, method="HEAD")
    try:
        with urlopen(request, timeout=15) as response:
            return response.geturl()
    except HTTPError:
        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=15) as response:
            return response.geturl()


def resolve_asin(url: str, expand_url: Callable[[str], str] = expand_product_url) -> str | None:
    asin = extract_asin(url)
    if asin:
        return asin

    host = urlparse(url).netloc.lower().split(":", 1)[0]
    if host not in {"amzn.to", "www.amzn.to", "a.co", "www.a.co"}:
        return None
    return extract_asin(expand_url(url))


def row_product_url(row: list[str], amazon_col: int | None, link_col: int | None) -> str:
    for column in (amazon_col, link_col):
        if column is None or column >= len(row):
            continue
        value = row[column].strip()
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
    return ""


def collect_row_asins(
    all_values: list[list[str]],
    amazon_col: int | None,
    link_col: int | None,
    resolve: Callable[[str], str | None] = resolve_asin,
) -> dict[int, str]:
    row_asins: dict[int, str] = {}
    resolved_urls: dict[str, str | None] = {}
    for row_idx, row in enumerate(all_values[1:], start=2):
        url = row_product_url(row, amazon_col, link_col)
        if not url:
            continue
        if url not in resolved_urls:
            try:
                resolved_urls[url] = resolve(url)
            except OSError as error:
                log.warning("Could not resolve product URL %s: %s", url, error)
                resolved_urls[url] = None
        asin = resolved_urls[url]
        if asin:
            row_asins[row_idx] = asin
    return row_asins


def get_sheet_client():
    """Authenticate and return a gspread client."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not creds_path:
        log.error("GOOGLE_SERVICE_ACCOUNT_JSON not set")
        sys.exit(1)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    if os.path.isfile(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    else:
        creds_info = json.loads(creds_path)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)

    return gspread.authorize(creds)


def creators_token_endpoint(version: str) -> str:
    normalized = str(version or "").strip().lower().removeprefix("v")
    endpoint = CREATORS_TOKEN_ENDPOINTS.get(normalized)
    if not endpoint:
        supported = ", ".join(sorted(CREATORS_TOKEN_ENDPOINTS))
        raise RuntimeError(f"Unsupported Creators API credential version {version!r}; expected {supported}")
    return endpoint


def post_json(
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
    opener: Callable = urlopen,
) -> dict:
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with opener(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Amazon request failed with HTTP {error.code}: {detail}") from error
    except (URLError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Amazon request failed: {error}") from error


def fetch_creators_access_token(
    credential_id: str,
    credential_secret: str,
    credential_version: str,
    request_json: Callable = post_json,
) -> str:
    response = request_json(
        creators_token_endpoint(credential_version),
        {
            "grant_type": "client_credentials",
            "client_id": credential_id,
            "client_secret": credential_secret,
            "scope": "creatorsapi::default",
        },
    )
    token = str(response.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Amazon Creators API token response did not include access_token")
    return token


def extract_creators_prices(response: dict) -> dict[str, float]:
    result = response.get("itemsResult") or response.get("itemResults") or {}
    prices: dict[str, float] = {}
    for item in result.get("items") or []:
        asin = str(item.get("asin") or "").strip().upper()
        listings = (item.get("offersV2") or {}).get("listings") or []
        if not asin or not listings:
            continue
        listing = next((value for value in listings if value.get("isBuyBoxWinner") is True), listings[0])
        amount = ((listing.get("price") or {}).get("money") or {}).get("amount")
        if isinstance(amount, (int, float)) and not isinstance(amount, bool):
            prices[asin] = float(amount)
    return prices


def fetch_prices_creators(
    asins: list[str],
    token_fetcher: Callable = fetch_creators_access_token,
    request_json: Callable = post_json,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, float]:
    """Query Amazon Creators API for prices. Returns {asin: price}."""
    credential_id = os.environ.get("AMAZON_CREATORS_CREDENTIAL_ID", "").strip()
    credential_secret = os.environ.get("AMAZON_CREATORS_CREDENTIAL_SECRET", "").strip()
    credential_version = os.environ.get("AMAZON_CREATORS_CREDENTIAL_VERSION", "").strip()
    partner_tag = os.environ.get("AMAZON_PARTNER_TAG", "").strip()
    marketplace = os.environ.get("AMAZON_MARKETPLACE", DEFAULT_MARKETPLACE).strip() or DEFAULT_MARKETPLACE
    required = {
        "AMAZON_CREATORS_CREDENTIAL_ID": credential_id,
        "AMAZON_CREATORS_CREDENTIAL_SECRET": credential_secret,
        "AMAZON_CREATORS_CREDENTIAL_VERSION": credential_version,
        "AMAZON_PARTNER_TAG": partner_tag,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Amazon Creators API credentials are not configured: {', '.join(missing)}")

    access_token = token_fetcher(credential_id, credential_secret, credential_version)
    prices: dict[str, float] = {}
    failed_batches = 0
    for batch_start in range(0, len(asins), 10):
        batch = asins[batch_start : batch_start + 10]
        try:
            response = request_json(
                CREATORS_API_URL,
                {
                    "itemIds": batch,
                    "itemIdType": "ASIN",
                    "marketplace": marketplace,
                    "partnerTag": partner_tag,
                    "resources": list(CREATORS_PRICE_RESOURCES),
                },
                {
                    "Authorization": f"Bearer {access_token}",
                    "x-marketplace": marketplace,
                },
            )
            prices.update(extract_creators_prices(response))
        except RuntimeError as error:
            log.error("Creators API error for batch %s: %s", batch, error)
            failed_batches += 1

        if batch_start + 10 < len(asins):
            sleep(1)

    batch_count = (len(asins) + 9) // 10
    if batch_count and failed_batches == batch_count:
        raise RuntimeError("Every Amazon Creators API request failed")
    return prices


def main():
    parser = argparse.ArgumentParser(description="Update prices in the latency spreadsheet")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    log.info("Connecting to Google Sheets...")
    gc = get_sheet_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)

    all_values = worksheet.get_all_values()
    if not all_values:
        log.error("Sheet is empty")
        sys.exit(1)

    header = all_values[0]

    # Find relevant columns
    def find_col(name: str) -> int | None:
        for i, h in enumerate(header):
            if h.strip().lower() == name.strip().lower():
                return i
        return None

    amazon_col = find_col("Amazon")
    link_col = find_col("Link")
    price_col = find_col("Price")

    if price_col is None:
        log.error("No 'Price' column found in the spreadsheet header")
        sys.exit(1)

    if amazon_col is None and link_col is None:
        log.error("Neither 'Amazon' nor 'Link' column found")
        sys.exit(1)

    log.info("Using per-row URLs from Amazon and Link columns; Price column is %d", price_col)

    # Collect ASINs
    row_asins = collect_row_asins(all_values, amazon_col, link_col)

    unique_asins = sorted(set(row_asins.values()))
    log.info("Found %d rows with Amazon ASINs (%d unique)", len(row_asins), len(unique_asins))

    if not unique_asins:
        raise RuntimeError("No Amazon ASINs could be resolved from the spreadsheet URLs")

    # Fetch prices
    prices = fetch_prices_creators(unique_asins)
    log.info("Fetched prices for %d / %d ASINs", len(prices), len(unique_asins))
    if not prices:
        raise RuntimeError("Amazon Creators API returned no prices")

    # Apply updates
    updates = 0
    stale = 0
    for row_idx, asin in sorted(row_asins.items()):
        if asin in prices:
            new_price = f"${prices[asin]:.2f}"
            current_price = all_values[row_idx - 1][price_col] if price_col < len(all_values[row_idx - 1]) else ""
            if current_price != new_price:
                if args.dry_run:
                    device = all_values[row_idx - 1][2] if len(all_values[row_idx - 1]) > 2 else f"row {row_idx}"
                    log.info("[DRY RUN] Row %d (%s): %s -> %s", row_idx, device, current_price or "(empty)", new_price)
                else:
                    # gspread uses 1-indexed columns
                    worksheet.update_cell(row_idx, price_col + 1, new_price)
                    time.sleep(0.5)  # Rate limit Sheets API
                updates += 1
        else:
            stale += 1

    log.info("Updates: %d, No price available: %d", updates, stale)
    if args.dry_run:
        log.info("Dry run complete — no changes written")
    else:
        log.info("Price update complete")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        log.error("%s", error)
        raise SystemExit(1) from error
