# Input latency testing for MiSTer FPGA
The purpose of this setup is to measure the latency of a USB controller using an arduino, DE10-nano, and IO board to form a closed-loop feedback system. The arduino is soldered to a button on the controller under test, and is also connected to the IO board's user port. When executed, the code commands a virtual button press on the controller and measures the response from the input latency core. The button under test must be mapped explicitly in the NES core. Results are monitored using putty or similar to connect to the COM port of the Arduino.

* Test PCB
  * I made a hat for the DE10-nano. It replaces the IO board and has a spot for the arduino pro-micro, 2 pins for the controller, and connects to all the necessary DE10-nano pins for signals and power.

* Troubleshooting
  * If no response is registered, ensure the button is mapped in the core
    * If this does not fix it, try flipping the + and - leads from the arduino to the button. Some only trigger when wired backwards from normal.

## Input Latency Explorer

The current interactive explorer is published from `docs/latency.html`. It uses the generated payload in `docs/data/latency.json` and the static assets in `docs/assets/`.

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

## R latency report

The older R report is generated from `rpubs/input.Rmd` and published from `docs/input.html`.

### Where the HTML lives

- Authoring template: `rpubs/input.Rmd`
- Build script: `render.R`
- Generated site page: `docs/input.html`
- Generated dependencies/assets: `docs/input_libs/`

Workflow:

1. Edit `rpubs/input.Rmd`
2. Run `Rscript render.R`
3. Commit and push `docs/input.html` (and `docs/input_libs/` updates when present)
4. GitHub Pages serves the content from the `docs/` folder on the default branch

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

### Publish to `misteraddons.com`

Recommended setup is a subdomain (for example: `inputlatency.misteraddons.com`) pointed to this repo's GitHub Pages site.

1. In GitHub repo settings, open Pages and set source to default branch + `/docs`.
2. Set custom domain to `inputlatency.misteraddons.com`.
3. Add `docs/CNAME` with one line:
   - `inputlatency.misteraddons.com`
4. In DNS for `misteraddons.com`, create:
   - `CNAME` record: `inputlatency` -> `misteraddons.github.io`
5. After DNS propagates, enable HTTPS in GitHub Pages.
