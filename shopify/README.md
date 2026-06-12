# Shopify Input Latency Explorer

This folder contains the Shopify theme pieces for the Input Latency Explorer.

Files:

- `sections/input-latency-explorer.liquid`
- `templates/page.input-latency-explorer.json`
- generated assets in `assets/`

To rebuild the latency data from this repo:

```powershell
python scripts/build_latency_catalog.py
```

That writes:

- `docs/data/latency.json`
- `docs/data/latency.js`

For Shopify, copy these assets into the theme:

- `shopify/assets/input-latency-data.js`
- `shopify/assets/input-latency-data-20260609-1704.js`
- `shopify/assets/input-latency-explorer.css`
- `shopify/assets/input-latency-explorer-20260609-1704.css`
- `shopify/assets/input-latency-explorer.js`
- `shopify/assets/input-latency-explorer-20260609-1704.js`
- `shopify/assets/reflex.css`
- `shopify/sections/input-latency-explorer.liquid`
- `shopify/templates/page.input-latency-explorer.json`
