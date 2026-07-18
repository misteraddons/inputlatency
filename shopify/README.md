# Shopify Input Latency Explorer

This folder contains the Shopify theme pieces for the Input Latency Explorer.

Files:

- `sections/input-latency-explorer.liquid`
- `templates/page.input-latency-explorer.json`
- generated assets in `assets/`

To rebuild the latency data from this repo:

```powershell
python scripts/build_latency_catalog.py --no-private --sheet-csv results/latency_sheet_cache.csv
```

That writes:

- `docs/data/latency.json`
- `docs/data/latency.js`
- `shopify/assets/input-latency-data.js`

For Shopify, copy these assets into the theme. The upload script publishes the
unversioned JavaScript assets to both the normal and revisioned Shopify asset
names, so revisioned JavaScript files are not stored in this repository:

- `shopify/assets/input-latency-data.js`
- `shopify/assets/input-latency-explorer.css`
- the revisioned `shopify/assets/input-latency-explorer-<revision>.css` referenced by the section
- `shopify/assets/input-latency-explorer.js`
- `shopify/assets/reflex.css`
- `shopify/sections/input-latency-explorer.liquid`
- `shopify/templates/page.input-latency-explorer.json`
- `shopify/templates/page.latency.json`
