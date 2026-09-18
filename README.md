# Input latency testing for MiSTer FPGA
The purpose of this setup is to measure the latency of a USB controller using an arduino, DE10-nano, and IO board to form a closed-loop feedback system. The arduino is soldered to a button on the controller under test, and is also connected to the IO board's user port. When executed, the code commands a virtual button press on the controller and measures the response from the input latency core. The button under test must be mapped explicitly in the NES core. Results are monitored using putty or similar to connect to the COM port of the Arduino.

* Test PCB
  * I made a hat for the DE10-nano. It replaces the IO board and has a spot for the arduino pro-micro, 2 pins for the controller, and connects to all the necessary DE10-nano pins for signals and power.

* Troubleshooting
  * If no response is registered, ensure the button is mapped in the core
    * If this does not fix it, try flipping the + and - leads from the arduino to the button. Some only trigger when wired backwards from normal.

## Input Latency Explorer

The public explorer is the Shopify section at https://misteraddons.com/pages/latency, built from the files under `shopify/`. `docs/latency.html` is a local preview of the same explorer; it loads the generated payload in `docs/data/latency.json` and the static assets in `docs/assets/`.

### Explorer files

- Explorer page: `docs/latency.html`
- Explorer assets: `docs/assets/`
- Explorer data: `docs/data/latency.json` and `docs/data/latency.js`
- Data generator: `scripts/build_latency_catalog.py`
- Browser behavior tests: `test_latency_explorer.js`
- Shopify export: `shopify/`

### Build the explorer data

```bash
python scripts/build_latency_catalog.py --no-private --sheet-csv results/latency_sheet_cache.csv
```

The generator reads this repo's public latency export from `results/latency_cleaned_export.csv` and augments product metadata from the verified sheet cache. A default build fetches the live Google Sheet and fails before writing output if that fetch fails. Use `--no-sheet-links` only for an intentional metadata-free build, and `--include-private` only for a private preview.

Run the complete verification set with:

```bash
python -m unittest test_latency_catalog.py test_update_prices.py
npm install
npx playwright install chromium
npm test
```

### Scheduled Amazon price updates

`.github/workflows/update-prices.yml` updates spreadsheet prices through Amazon's
Creators API. It maintains the `Price` column on the `Detailed Results` tab.
Configure these repository Actions secrets before running it:

- `AMAZON_CREATORS_CREDENTIAL_ID`
- `AMAZON_CREATORS_CREDENTIAL_SECRET`
- `AMAZON_CREATORS_CREDENTIAL_VERSION`
- `AMAZON_PARTNER_TAG`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

The workflow writes prices only when the service account can edit the `Price`
column. While that column is a protected range, the run still succeeds but logs
"Price column is protected" and writes nothing, which is the current state.

To enable writes:

1. Find the service account address. It ends in `.iam.gserviceaccount.com` and
   appears in the sheet's Share dialog, because the account already has access
   to read the sheet. It is also the `client_email` field of the
   `GOOGLE_SERVICE_ACCOUNT_JSON` secret.
2. In the sheet, open `Data` > `Protected sheets and ranges` and select the
   protection covering the `Price` column on `Detailed Results`.
3. Under `Set permissions` > `Restrict who can edit this range`, add that
   address, then save.
4. Re-run the workflow from the Actions tab. A working run logs
   `Updates: <n>, Protected cells skipped: 0`.

Prices are read from the Amazon Creators API, which returns a price only for
items that currently have an offer. The 2026-09-13 run resolved 100 unique
ASINs and got prices for 37 of them, so expect discontinued items to stay blank.

Prices reach the explorer only after the data is rebuilt: run `Rscript render.R`
(refreshes `results/latency_sheet_cache.csv`), rebuild the explorer data, then
upload the theme assets.

## R latency report

The older R report is generated from `rpubs/input.Rmd` into `docs/input.html`. It is a build output kept in the tree; GitHub Pages is not enabled for this repository, so nothing under `docs/` is served from `misteraddons.github.io`.

### Where the HTML lives

- Authoring template: `rpubs/input.Rmd`
- Build script: `render.R`
- Generated site page: `docs/input.html`
- Generated dependencies/assets: `docs/input_libs/`

Workflow:

1. Edit `rpubs/input.Rmd`
2. Run `Rscript render.R`
3. Commit `docs/input.html` (and `docs/input_libs/` updates when present)

### Build

```bash
Rscript render.R
```

### Data source behavior

- Primary source: live Google Sheet used by the project.
- Cache fallback: `results/latency_sheet_cache.csv`.
- During render, if live sheet fetch succeeds, the cache file is refreshed.
- If live fetch fails, render falls back to the cache so the report can still build offline.

### Build artifacts

- Main report: `docs/input.html`
- Report assets: `docs/input_libs/`
- UI: responsive layout with persistent light/dark theme toggle
- Derived exports:
  - `results/latency_cleaned_export.csv`
  - `results/raw_capture_unmatched.csv`
  - `results/database_without_raw_capture.csv`

### Publish the explorer to `misteraddons.com`

The live page is the `input-latency-explorer` Shopify section. To publish a new build:

1. Rebuild the data (see above) so `shopify/assets/input-latency-data.js` is current.
2. Bump `latency_asset_revision` (and `latency_css_revision` when the stylesheet changed) at the top of `shopify/sections/input-latency-explorer.liquid`.
3. Merge to `main`, then dispatch the `Publish Reflex Sites` workflow in the `mister_cores` repository, which runs `scripts/upload_shopify_theme_assets.py` from this repository's `main`. Running that script locally with `SHOPIFY_STORE_DOMAIN` and `SHOPIFY_ADMIN_API_ACCESS_TOKEN` set uploads the same files. The script always targets the published theme; `SHOPIFY_THEME_ID` is optional and only reported when it differs.

See `shopify/README.md` for the asset list.
