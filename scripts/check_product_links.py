#!/usr/bin/env python3
"""
Check that the product and source links in the explorer payload still resolve.

The catalog carries a buy link for most items, many of them Amazon affiliate
short links, and nothing has ever checked that they still lead somewhere. A dead
link on a monetised page costs money quietly.

Read the result carefully. Amazon answers 404 from amzn.to when it is
throttling, which looks exactly like a deleted link: a first sweep at one second
spacing reported eight live links as dead, and every one of them resolved on
later runs. Failures are retried once, short-link and storefront hosts are
called out as needing a human, and nothing here is proof that a link is gone
until you have opened it yourself.

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
# These hosts answer with a plausible-looking error when they throttle, so a
# failure from them says nothing about whether the link still works.
UNRELIABLE_HOSTS = ("amzn.to", "a.co", "amazon.com", "amazon.ca", "amazon.co.uk")
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


def host_is_unreliable(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == name or host.endswith("." + name) for name in UNRELIABLE_HOSTS)


def request_once(url: str, timeout: int) -> tuple[int | None, str, str]:
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


def is_ok(status: int | None) -> bool:
    return status is not None and 200 <= status < 400


def check_link(url: str, timeout: int, retry_delay: float = 6.0) -> tuple[int | None, str, str]:
    """Return (status, final_url, note). A status of None means no response.

    Amazon's short-link service answers 404 when it is throttling, which is
    indistinguishable from a deleted link, so a failure is always retried once
    after a longer pause. Without this, a one second sweep reported six live
    links as dead.
    """
    status, final_url, note = request_once(url, timeout)
    if is_ok(status):
        return status, final_url, note
    time.sleep(retry_delay)
    retry_status, retry_final, retry_note = request_once(url, timeout)
    if is_ok(retry_status):
        return retry_status, retry_final, "failed once, resolved on retry"
    if host_is_unreliable(url):
        return retry_status, retry_final, "this host throttles with an error status, verify by hand"
    return retry_status, retry_final, retry_note or note


def main() -> int:
    parser = argparse.ArgumentParser(description="Check explorer product links")
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0, help="check only the first N links")
    parser.add_argument("--retry-delay", type=float, default=6.0, help="pause before retrying a failure")
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
        status, final_url, note = check_link(url, args.timeout, args.retry_delay)
        ok = is_ok(status)
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
        print("Links to open by hand before changing anything:")
        for row in problems:
            print(f"  {row['status'] or 'no response'}  {row['url']}  ({row['devices'][:60]})")
        print(
            "None of the above is proof that a link is dead. Storefronts and Amazon "
            "short links return errors when they throttle, so open each one before "
            "editing the spreadsheet."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
