# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

USB controller input latency measurements for MiSTer FPGA, in two halves:

1. A hardware test rig (Arduino Pro Micro + DE10-nano + custom hat) that measures button-to-detection latency in milliseconds and writes CSV captures.
2. A publishing pipeline that turns the results spreadsheet and captures into the Input Latency Explorer at https://misteraddons.com/pages/latency.

## Hardware Rig

- Arduino Pro Micro triggers button presses on the controller under test and measures the response via an interrupt.
- DE10-nano runs `test_core/NES_Lag_Tester.rbf`, which raises a User I/O pin when the USB press is detected.
- `pcb/InputLatencyTester.zip` holds Gerbers for the hat that replaces the IO board.
- Serial output at 115200 baud, CSV rows of `read, delay` (delay in ms).

Firmware timing parameters in `arduino/MiSTer_USB_Latency_Test_Lemonici/*.ino`:
- `delayPress = 16`: ms between button state toggles
- `maxExtraDelayPress = 200`: ms to keep waiting for a slow controller before starting the next press
- Pin 5: button trigger (pulls LOW); Pin 2: MiSTer response (interrupt, FALLING edge)

Compile check without hardware:
```
arduino-cli compile --fqbn arduino:avr:leonardo arduino/MiSTer_USB_Latency_Test_Lemonici
```

`docs/internal/firmware-timeout-test.md` holds the unrun hardware test plan for
the slow-controller timeout fix.

## Data Pipeline

```
Google Sheet  --(Rscript render.R)-->  results/latency_sheet_cache.csv
captures/*.csv                          results/latency_cleaned_export.csv
                                        results/raw_capture_unmatched.csv
                                        docs/input.html (legacy R report)
        |
        v  scripts/build_latency_catalog.py --no-private --sheet-csv results/latency_sheet_cache.csv
docs/data/latency.json, docs/data/latency.js, shopify/assets/input-latency-data.js
        |
        v  scripts/upload_shopify_theme_assets.py
Shopify theme section input-latency-explorer  ->  misteraddons.com/pages/latency
```

- Source sheet: https://docs.google.com/spreadsheets/d/1KlRObr3Be4zLch7Zyqg6qCJzGuhyGmXaOIUrpfncXIM/
- The R render matches capture files to sheet `Device` names by normalized name (`normalize_capture_name` in `rpubs/input.Rmd`). Captures that do not match are listed in `results/raw_capture_unmatched.csv` and contribute no sample count or percentile data.
- Capture filenames may carry a VID/PID suffix or a `-<samples>-<date>` run suffix; both are stripped before matching. Other spelling differences need an entry in `capture_name_aliases`.
- GitHub Pages is not enabled for this repository. Everything under `docs/` is build output or a local preview; the live page loads its data inline from the theme asset.
- Publishing runs from the `mister_cores` repository: its `Publish Reflex Sites` workflow (manual dispatch) checks out this repo's `main` and runs `scripts/upload_shopify_theme_assets.py`. The script uploads sources unchanged; Shopify's CDN serves them minified.

## Commands

R report (needs R 4.5 and pandoc; paths below are this machine's):
```
Sys.setenv(RSTUDIO_PANDOC='C:/Users/Robot/AppData/Local/Pandoc')
"C:\Program Files\R\R-4.5.2\bin\Rscript.exe" render.R
```

Explorer data and tests:
```
python scripts/build_latency_catalog.py --no-private --sheet-csv results/latency_sheet_cache.csv
python -m unittest test_latency_catalog.py test_update_prices.py
npm test          # node unit tests + Playwright smoke test of docs/latency.html
```

Publishing: bump `latency_asset_revision` (and `latency_css_revision` when the stylesheet changed) in `shopify/sections/input-latency-explorer.liquid`, merge to `main`, then dispatch `Publish Reflex Sites` in `mister_cores`, or run `scripts/upload_shopify_theme_assets.py` locally with `SHOPIFY_STORE_DOMAIN` and `SHOPIFY_ADMIN_API_ACCESS_TOKEN` set. The script uploads to the published theme, not to a configured `SHOPIFY_THEME_ID`. Uploading is a release action; do not run it as a side effect of a build.

## Price Updates

`.github/workflows/update-prices.yml` runs `scripts/update_prices.py` weekly. It fills the sheet's `Price` column from the Amazon Creators API and needs the service account to be an editor of that column; while the column is protected, the run succeeds but writes nothing. Prices only reach the site after a render, a data rebuild and an upload.

## Key Files

- `rpubs/input.Rmd`, `render.R`: R report and capture matching
- `scripts/build_latency_catalog.py`: explorer payload builder (name cleanup, classification, ranking)
- `scripts/upload_shopify_theme_assets.py`: theme upload
- `shopify/`: liquid section, page templates, generated assets
- `docs/assets/latency.js` and `shopify/assets/input-latency-explorer.js`: identical explorer script
- `captures/`: raw CSV captures, one file per device and mode
