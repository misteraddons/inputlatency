#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
SHOPIFY_ROOT = REPO_ROOT / "shopify"
DEFAULT_API_VERSION = "2024-01"


def get_liquid_revision(shopify_root: Path, variable_name: str, fallback: str | None = None) -> str:
    section_path = shopify_root / "sections" / "input-latency-explorer.liquid"
    content = section_path.read_text(encoding="utf-8")
    match = re.search(r"{%\s*assign\s+" + re.escape(variable_name) + r"\s*=\s*'([^']+)'\s*%}", content)
    if match:
        return match.group(1)
    if fallback is not None:
        return fallback
    raise SystemExit(f"Could not find {variable_name} in {section_path}")


def default_asset_uploads(shopify_root: Path) -> tuple[tuple[str, str], ...]:
    asset_revision = get_liquid_revision(shopify_root, "latency_asset_revision")
    css_revision = get_liquid_revision(shopify_root, "latency_css_revision", asset_revision)
    return (
        ("assets/reflex.css", "assets/reflex.css"),
        ("assets/input-latency-data.js", "assets/input-latency-data.js"),
        (f"assets/input-latency-data-{asset_revision}.js", "assets/input-latency-data.js"),
        ("assets/input-latency-explorer.css", "assets/input-latency-explorer.css"),
        (
            f"assets/input-latency-explorer-{css_revision}.css",
            f"assets/input-latency-explorer-{css_revision}.css",
        ),
        ("assets/input-latency-explorer.js", "assets/input-latency-explorer.js"),
        (
            f"assets/input-latency-explorer-{asset_revision}.js",
            f"assets/input-latency-explorer-{asset_revision}.js",
        ),
        ("sections/input-latency-explorer.liquid", "sections/input-latency-explorer.liquid"),
        ("templates/page.input-latency-explorer.json", "templates/page.input-latency-explorer.json"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload Input Latency Explorer assets to a Shopify theme")
    parser.add_argument("--shop", default=os.environ.get("SHOPIFY_STORE_DOMAIN", ""))
    parser.add_argument("--theme-id", default=os.environ.get("SHOPIFY_THEME_ID", ""))
    parser.add_argument("--access-token", default=os.environ.get("SHOPIFY_ADMIN_API_ACCESS_TOKEN", ""))
    parser.add_argument("--api-version", default=os.environ.get("SHOPIFY_API_VERSION", DEFAULT_API_VERSION))
    parser.add_argument("--shopify-root", type=Path, default=SHOPIFY_ROOT)
    return parser.parse_args()


def shop_domain(value: str) -> str:
    value = str(value or "").strip().removeprefix("https://").removeprefix("http://").strip("/")
    if not value:
        raise SystemExit("Missing Shopify store domain. Set SHOPIFY_STORE_DOMAIN, for example mister-fpga.myshopify.com.")
    return value


def api_request(method: str, base_url: str, token: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {
        "Accept": "application/json",
        "X-Shopify-Access-Token": token,
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {path} failed: HTTP {exc.code} {body[:1000]}") from exc


def main() -> int:
    args = parse_args()
    domain = shop_domain(args.shop)
    if not args.theme_id:
        raise SystemExit("Missing Shopify theme id. Set SHOPIFY_THEME_ID.")
    if not args.access_token:
        raise SystemExit("Missing Shopify Admin API token. Set SHOPIFY_ADMIN_API_ACCESS_TOKEN.")

    base_url = f"https://{domain}/admin/api/{args.api_version}"
    api_request("GET", base_url, args.access_token, f"/themes/{args.theme_id}.json")

    for key, source in default_asset_uploads(args.shopify_root):
        source_path = args.shopify_root / source
        value = source_path.read_text(encoding="utf-8")
        api_request(
            "PUT",
            base_url,
            args.access_token,
            f"/themes/{args.theme_id}/assets.json",
            {"asset": {"key": key, "value": value}},
        )
        print(f"Uploaded {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
