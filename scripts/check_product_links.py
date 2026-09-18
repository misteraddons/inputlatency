#!/usr/bin/env python3
"""
Check that the product and source links in the explorer payload still resolve.

The catalog carries a buy link for most items, many of them Amazon affiliate
short links, and nothing has ever checked that they still lead somewhere. A dead
link on a monetised page costs money quietly.

This only reports. It never edits the payload or the spreadsheet.

Usage:
  python scripts/check_product_links.py                  # check every link
  python scripts/check_product_links.py --limit 20       # first 20, for a smoke test
  python scripts/check_product_links.py --delay 2        # slower, for rate limits
  python scripts/check_product_links.py --report out.csv # also write a CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = REPO_ROOT / "docs" / "data" / "latency.json"
# Vendors serve a different page, or none at all, to an obvious script.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def collect_links(payload: dict) -> dict[str, list[str]]:
    """Map each URL to the device names that use it."""
    links: dict[str, list[str]] = {}
    for item in payload.get("items") or []:
        for field in ("buyUrl", "sourceUrl"):
            url = str(item.get(field) or "").strip()
            if not url:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            links.setdefault(url, []).append(str(item.get("name") or ""))
    return links


def check_link(url: str, timeout: int) -> tuple[int | None, str, str]:
    """Return (status, final_url, note). A status of None means no response."""
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl(), ""
    except HTTPError as error:
        # 403 from a storefront usually means bot filtering, not a dead link.
        note = "blocked by the site, check by hand" if error.code in {403, 429} else ""
        return error.code, getattr(error, "url", url), note
    except URLError as error:
        return None, url, f"no response: {error.reason}"
    except (TimeoutError, OSError) as error:
        return None, url, f"no response: {error}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check explorer product links")
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0, help="check only the first N links")
    parser.add_argument("--report", type=Path, help="write every result to this CSV")
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    links = collect_links(payload)
    urls = sorted(links)
    if args.limit:
        urls = urls[: args.limit]

    print(f"Checking {len(urls)} unique links from {len(payload.get('items') or [])} items")
    rows = []
    problems = []
    for index, url in enumerate(urls, start=1):
        status, final_url, note = check_link(url, args.timeout)
        ok = status is not None and 200 <= status < 400
        rows.append(
            {
                "url": url,
                "status": status if status is not None else "",
                "final_url": final_url,
                "devices": "; ".join(sorted(set(links[url]))),
                "note": note,
            }
        )
        if not ok:
            problems.append(rows[-1])
            print(f"  [{index}/{len(urls)}] {status or 'no response'}  {url}  {note}".rstrip())
        if index < len(urls):
            time.sleep(args.delay)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["url", "status", "final_url", "devices", "note"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {args.report}")

    print(f"\n{len(urls) - len(problems)} of {len(urls)} links resolved")
    if problems:
        print("Links needing attention:")
        for row in problems:
            print(f"  {row['status'] or 'no response'}  {row['url']}  ({row['devices'][:60]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
