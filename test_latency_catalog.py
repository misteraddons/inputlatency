import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

import build_latency_catalog as latency  # noqa: E402
import upload_shopify_theme_assets as shopify_upload  # noqa: E402


class LatencyCatalogTests(unittest.TestCase):
    def write_csv(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

    def test_shopify_upload_uses_unversioned_javascript_for_revisioned_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            shopify_root = Path(temp_dir)
            section = shopify_root / "sections" / "input-latency-explorer.liquid"
            section.parent.mkdir(parents=True)
            section.write_text(
                "{% assign latency_asset_revision = '20260718-1548' %}\n"
                "{% assign latency_css_revision = '20260727-1558' %}\n",
                encoding="utf-8",
            )

            uploads = dict(shopify_upload.default_asset_uploads(shopify_root))

        self.assertEqual(
            uploads["assets/input-latency-data-20260718-1548.js"],
            "assets/input-latency-data.js",
        )
        self.assertEqual(
            uploads["assets/input-latency-explorer-20260718-1548.js"],
            "assets/input-latency-explorer.js",
        )

    def private_header(self):
        return [
            "", "Device", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "Number of Samples", "Same Frame Probability", "Average", "Maximum", "Minimum", "Standard Deviation",
            "Valid Results", "Joystick ID", "Notes", "Tester", "Date Added", "Category", "Original Controller System",
            "Face Buttons", "Weight (oz)", "'Feel (0-10)'", "Feel Notes", "99%", "Average Tier", "99% Tier", "Result Type",
        ]

    def private_row(self, device, average, *, category="", joystick_id="", p99="3.0", result_type="unreleased"):
        row = [""] * len(self.private_header())
        row[latency.PRIVATE_COLUMNS["device"]] = device
        row[latency.PRIVATE_COLUMNS["sample_count"]] = "2000"
        row[latency.PRIVATE_COLUMNS["same_frame"]] = "0.90"
        row[latency.PRIVATE_COLUMNS["average"]] = str(average)
        row[latency.PRIVATE_COLUMNS["maximum"]] = "3.5"
        row[latency.PRIVATE_COLUMNS["minimum"]] = "0.5"
        row[latency.PRIVATE_COLUMNS["sd"]] = "0.3"
        row[latency.PRIVATE_COLUMNS["valid"]] = "YES"
        row[latency.PRIVATE_COLUMNS["joystick_id"]] = joystick_id
        row[latency.PRIVATE_COLUMNS["category"]] = category
        row[latency.PRIVATE_COLUMNS["p99"]] = p99
        row[latency.PRIVATE_COLUMNS["average_tier"]] = "Stale"
        row[latency.PRIVATE_COLUMNS["p99_tier"]] = "Stale"
        row[latency.PRIVATE_COLUMNS["result_type"]] = result_type
        return row

    def test_latency_tiers_use_frame_boundary_cutoffs(self):
        one_frame_ms = latency.SAME_FRAME_WINDOW_MS
        two_frames_ms = latency.SAME_FRAME_WINDOW_MS * 2

        self.assertEqual(latency.tier_for_average(10.001), "Bronze")
        self.assertEqual(latency.tier_for_average(one_frame_ms), "Bronze")
        self.assertEqual(latency.tier_for_average(one_frame_ms + 0.001), "Copper")
        self.assertEqual(latency.tier_for_average(two_frames_ms), "Copper")
        self.assertEqual(latency.tier_for_average(two_frames_ms + 0.001), "Rust")
        self.assertEqual(latency.tier_for_p99(16.0), "Bronze")
        self.assertEqual(latency.tier_for_p99(25.0), "Copper")

    def test_product_urls_require_http_and_exclude_placeholders_and_source_links(self):
        self.assertTrue(latency.is_product_or_buy_url("https://www.amazon.com/dp/B012345678"))
        self.assertFalse(latency.is_product_or_buy_url("-"))
        self.assertFalse(latency.is_product_or_buy_url("YES"))
        self.assertFalse(latency.is_product_or_buy_url("https://github.com/example/project"))

    def test_build_payload_combines_public_and_private_latency_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"

            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    [
                        "Make",
                        "Model",
                        "Device",
                        "Link",
                        "Amazon",
                        "Connection",
                        "Wired/Wireless",
                        "WirelessConnection",
                        "Home Button",
                        "Latency Tier",
                        "Latency (in ms)",
                        "SD",
                        "Max",
                        "Min",
                        "Category",
                        "Face Buttons",
                        "Date Added",
                        "DeviceClean",
                        "DeviceNorm",
                        "Platforms",
                        "Price",
                        "PriceNum",
                        "P99",
                        "PctOnTime",
                        "HasRawCapture",
                        "MetricSource",
                    ],
                    [
                        "Buffalo",
                        "iBuffalo Classic",
                        "Buffalo - iBuffalo Classic",
                        "",
                        "",
                        "Wired USB",
                        "Wired",
                        "-",
                        "NO",
                        "S",
                        "0.69",
                        "0.10",
                        "1.19",
                        "0.19",
                        "Controller",
                        "4",
                        "05/25/2020",
                        "Buffalo - iBuffalo Classic",
                        "buffalo ibuffalo classic",
                        "MiSTer / PC",
                        "$19.99",
                        "19.99",
                        "1.12",
                        "95.9",
                        "TRUE",
                        "Direct measurement",
                    ],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    [
                        "",
                        "Device",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "Number of Samples",
                        "Same Frame Probability",
                        "Average",
                        "Maximum",
                        "Minimum",
                        "Standard Deviation",
                        "Valid Results",
                        "Joystick ID",
                        "Notes",
                        "Tester",
                        "Date Added",
                        "Category",
                        "Original Controller System",
                        "Face Buttons",
                        "Weight (oz)",
                        "'Feel (0-10)'",
                        "Feel Notes",
                        "99%",
                        "Average Tier",
                        "99% Tier",
                        "Result Type",
                    ],
                    [
                        "1",
                        "Reflex Adapt [Neo Geo]",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "2128",
                        "0.9538",
                        "0.77",
                        "1.26",
                        "0.24",
                        "0.29",
                        "YES",
                        "",
                        "lab note",
                        "Porkchop",
                        "",
                        "",
                        "Neo Geo",
                        "",
                        "",
                        "",
                        "",
                        "1.26",
                        "Diamond",
                        "Diamond",
                        "unreleased",
                    ],
                    [
                        "2",
                        "Stale Tier Capture",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "1200",
                        "0.84",
                        "2.50",
                        "3.20",
                        "1.80",
                        "0.31",
                        "YES",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "3.10",
                        "Platinum",
                        "Platinum",
                        "unreleased",
                    ],
                ],
            )
            self.write_csv(
                private_root / "captures" / "experiment.csv",
                [
                    [
                        "",
                        "Device",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "Number of Samples",
                        "Same Frame Probability",
                        "Average",
                        "Maximum",
                        "Minimum",
                        "Standard Deviation",
                        "Valid Results",
                        "Joystick ID",
                        "Notes",
                        "Tester",
                        "Date Added",
                        "Category",
                        "Original Controller System",
                        "Face Buttons",
                        "Weight (oz)",
                        "'Feel (0-10)'",
                        "Feel Notes",
                        "99%",
                        "Average Tier",
                        "99% Tier",
                        "Result Type",
                    ],
                    [
                        "1",
                        "Bootsector ESP32 S3 Simple",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "3642",
                        "0.955232",
                        "0.746",
                        "1.38",
                        "0.23",
                        "0.291",
                        "YES",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "1.24",
                        "Diamond",
                        "Diamond",
                        "experiment",
                    ],
                    [
                        "2",
                        "Stale Tier Capture",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "1200",
                        "0.84",
                        "2.50",
                        "3.20",
                        "1.80",
                        "0.31",
                        "YES",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "3.10",
                        "Platinum",
                        "Platinum",
                        "experiment",
                    ],
                    [
                        "3",
                        "Sony Dual Sense Wireless Option",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "3893",
                        "0.000127716414076323",
                        "84.303231441048",
                        "104.66",
                        "8.38",
                        "17.8659392616522",
                        "YES",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "103.71",
                        "Rust",
                        "Rust",
                        "experiment",
                    ],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root)

        self.assertEqual(payload["summary"]["totalItems"], 3)
        self.assertEqual(payload["summary"]["resultTypes"]["published"], 1)
        self.assertEqual(payload["summary"]["resultTypes"]["unreleased"], 2)
        self.assertNotIn("experiment", payload["summary"]["resultTypes"])
        self.assertEqual(payload["summary"]["bestAverageMs"], 0.69)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertFalse(any(item["resultType"] == "experiment" for item in payload["items"]))
        self.assertNotIn("experiment-bootsector-esp32-s3-simple", by_id)
        self.assertNotIn("experiment-stale-tier-capture", by_id)
        self.assertNotIn("experiment-sony-dual-sense-wireless-option", by_id)
        self.assertEqual(by_id["published-buffalo-ibuffalo-classic"]["averageTier"], "Diamond")
        self.assertEqual(by_id["published-buffalo-ibuffalo-classic"]["sheetTier"], "S")
        self.assertEqual(by_id["published-buffalo-ibuffalo-classic"]["platforms"], ["MiSTer / PC"])
        self.assertEqual(by_id["published-buffalo-ibuffalo-classic"]["dateAddedSort"], "2020-05-25")
        self.assertEqual(by_id["published-buffalo-ibuffalo-classic"]["modeLabel"], "USB")
        self.assertEqual(by_id["unreleased-reflex-adapt"]["sampleCount"], 2128)
        self.assertEqual(by_id["unreleased-reflex-adapt"]["modeLabel"], "Neo Geo")
        self.assertAlmostEqual(by_id["unreleased-reflex-adapt"]["sameFramePct"], 95.38)
        self.assertEqual(by_id["unreleased-stale-tier-capture"]["averageTier"], "Gold")
        self.assertEqual(by_id["unreleased-stale-tier-capture"]["p99Tier"], "Gold")
        self.assertEqual(by_id["unreleased-stale-tier-capture"]["sheetTier"], "Platinum")

    def test_private_capture_titles_are_normalized_into_metadata_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results", "Category", "Connection", "Wired/Wireless"],
                    [
                        "Generic - 2 Port Genesis to USB (Cable Style with 2 Blue Ports)",
                        "19.88",
                        "Generic - 2 Port Genesis to USB (Cable Style with 2 Blue Ports)",
                        "generic 2 port genesis to usb cable style with 2 blue ports",
                        "YES",
                        "Controller Adapter",
                        "Genesis Controller",
                        "Wired",
                    ],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    self.private_row(
                        "Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller - Xinput - 045e_028e",
                        "8.774",
                        category="Controller",
                        p99="17.0",
                    ),
                    self.private_row(
                        "Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller - Dinput - 2563_0575",
                        "14.672",
                        category="Controller",
                        p99="19.5",
                    ),
                    self.private_row(
                        "Sega Infrared Control Pad (HSS-0116) [IR Wireless]",
                        "17.011",
                        category="Controller",
                    ),
                    self.private_row(
                        "Sega Infrared Control Pad (HSS-0116) [IR Wireless].csv",
                        "17.341",
                        category="Controller",
                    ),
                    self.private_row(
                        "vienon PS2 Controller to USB Adapter Converter, 2 Pack Compatible with PS1-PS2 Controller Gamepad to PS3-PC Controller No Need Driver",
                        "9.088",
                        category="Controller Adapter",
                    ),
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertIn("Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller", by_name)
        self.assertIn("Sega Infrared Control Pad (HSS-0116)", by_name)
        self.assertIn("vienon PS1/PS2 to USB Adapter", by_name)
        self.assertIn("Generic - 2-Port Genesis to USB Adapter", by_name)
        self.assertNotIn("Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller - Xinput - 045e_028e", by_name)
        self.assertNotIn("Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller - Dinput - 2563_0575", by_name)
        self.assertNotIn("Sega Infrared Control Pad (HSS-0116) [IR Wireless].csv", by_name)

        retrobit = by_name["Retro-Bit Sega Saturn 2.4GHz Wireless Pro Controller"]
        self.assertEqual(retrobit["modeVariantCount"], 2)
        self.assertEqual(retrobit["outputMode"], "XInput")
        self.assertEqual(retrobit["modeLabel"], "XInput")
        self.assertEqual(retrobit["connectionTag"], "Wireless 2.4GHz")
        self.assertEqual(retrobit["joystickId"], "045e:028e")
        retrobit_variants = {variant["outputMode"]: variant for variant in retrobit["modeVariants"]}
        self.assertEqual(retrobit_variants["DInput"]["joystickId"], "2563:0575")
        self.assertEqual(retrobit_variants["XInput"]["joystickId"], "045e:028e")
        self.assertIn("045e_028e", retrobit["searchText"])

        sega_ir = by_name["Sega Infrared Control Pad (HSS-0116)"]
        self.assertEqual(sega_ir["modeVariantCount"], 2)
        self.assertEqual(sega_ir["connectionTag"], "Wireless")
        self.assertEqual(sega_ir["modeLabel"], "IR Wireless")
        self.assertIn("ir wireless", sega_ir["searchText"])

        vienon = by_name["vienon PS1/PS2 to USB Adapter"]
        self.assertEqual(vienon["category"], "Controller Adapter")
        self.assertEqual(vienon["deviceTypes"], ["Controller Adapter", "PSX Controller"])
        self.assertIn("no need driver", vienon["searchText"])

        generic = by_name["Generic - 2-Port Genesis to USB Adapter"]
        self.assertEqual(generic["category"], "Controller Adapter")
        self.assertEqual(generic["deviceTypes"], ["Controller Adapter", "Genesis Controller"])
        self.assertIn("cable style with 2 blue ports", generic["searchText"])

    def test_public_mode_labels_are_inferred_from_connection_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "WirelessConnection", "Latency (in ms)", "Date Added", "Valid Results"],
                    ["XInput Pad", "xinput pad", "8Bitdo Wireless Bluetooth (X-Input / Select + Up)", "Wireless", "Bluetooth", "2.0", "2026-06-01", "YES"],
                    ["Switch Pad", "switch pad", "8Bitdo Wireless Bluetooth (Switch Mode / Default)", "Wireless", "Bluetooth", "2.1", "bad date", "YES"],
                    ["BT Pad", "bt pad", "BT", "Wireless", "Bluetooth", "2.2", "", "YES"],
                    ["Dongle Pad", "dongle pad", "Wireless USB Dongle", "Wireless", "Bluetooth", "2.3", "", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["published-xinput-pad"]["modeLabel"], "XInput")
        self.assertEqual(by_id["published-xinput-pad"]["dateAddedSort"], "2026-06-01")
        self.assertEqual(by_id["published-switch-pad"]["modeLabel"], "Switch")
        self.assertEqual(by_id["published-switch-pad"]["dateAddedSort"], "")
        self.assertEqual(by_id["published-bt-pad"]["modeLabel"], "Bluetooth")
        self.assertEqual(by_id["published-dongle-pad"]["modeLabel"], "2.4G")
        self.assertEqual(by_id["published-dongle-pad"]["connectionTag"], "Wireless 2.4GHz")

    def test_public_connection_fields_normalize_stale_sheet_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "Latency (in ms)", "Valid Results"],
                    ["Raphnet Adapter", "raphnet adapter", "", "Wired USB", "1.0", "YES"],
                    ["Retro Wireless", "retro wireless", "", "Wireless", "2.0", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["published-raphnet-controller-adapter"]["connectionKind"], "Wired")
        self.assertEqual(by_id["published-raphnet-controller-adapter"]["connection"], "Wired USB")
        self.assertEqual(by_id["published-retro-wireless"]["connectionKind"], "Wireless")
        self.assertEqual(by_id["published-retro-wireless"]["connection"], "Wireless")

    def test_public_rows_are_augmented_with_sheet_product_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Link", "Amazon", "Connection", "Wired/Wireless", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["8BitDo", "M30", "8BitDo - M30", "", "", "Wired USB", "Wired", "1.1", "8BitDo - M30", "8bitdo m30", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "8BitDo",
                    "Model": "M30",
                    "Device": "8BitDo M30 [Wired USB]",
                    "Link": "https://amzn.to/example",
                    "Amazon": "https://amzn.to/affiliate",
                    "Price": "$29.99",
                }
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["link"], "https://amzn.to/example")
        self.assertEqual(item["buyUrl"], "https://amzn.to/affiliate")
        self.assertEqual(item["price"], "$29.99")
        self.assertEqual(item["priceNum"], 29.99)
        self.assertEqual(payload["summary"]["linkedItems"], 1)

    def test_sheet_ba_date_added_updates_public_date_added(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Date Added", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["8BitDo", "M30", "8BitDo - M30", "Wired USB", "Wired", "1.1", "1/1/2020", "8BitDo - M30", "8bitdo m30", "YES"],
                ],
            )
            headers = [f"Column {index}" for index in range(53)]
            headers[0] = "Make"
            headers[1] = "Model"
            headers[2] = "Device"
            headers[3] = "Amazon"
            headers[52] = "Date Added"
            row = [""] * 53
            row[0] = "8BitDo"
            row[1] = "M30"
            row[2] = "8BitDo M30 [Wired USB]"
            row[3] = "https://amzn.to/affiliate"
            row[52] = "6/7/2026"
            sheet_rows = latency.read_sheet_rows_from_text(
                ",".join(headers) + "\n" + ",".join(row) + "\n"
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["dateAdded"], "6/7/2026")
        self.assertEqual(item["dateAddedSort"], "2026-06-07")

    def test_sheet_bb_category_updates_device_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Mayflash", "Adapter", "Mayflash Adapter", "Wired USB", "Wired", "1.1", "Unknown", "Mayflash Adapter", "mayflash adapter", "YES"],
                ],
            )
            headers = [f"Column {index}" for index in range(54)]
            headers[0] = "Make"
            headers[1] = "Model"
            headers[2] = "Device"
            headers[52] = "Date Added"
            headers[53] = "Category"
            row = [""] * 54
            row[0] = "Mayflash"
            row[1] = "Adapter"
            row[2] = "Mayflash Adapter"
            row[53] = "Controller Adapter"
            sheet_rows = latency.read_sheet_rows_from_text(
                ",".join(headers) + "\n" + ",".join(row) + "\n"
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["category"], "Controller Adapter")
        self.assertEqual(item["deviceTypes"], ["Controller Adapter"])
        self.assertEqual(payload["summary"]["deviceTypes"]["Controller Adapter"], 1)

    def test_sheet_controller_category_splits_device_type_by_connection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "WirelessConnection", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["8BitDo", "M30", "8BitDo M30 Wired", "Wired USB", "Wired", "-", "1.1", "Unknown", "8BitDo M30 Wired", "8bitdo m30 wired", "YES"],
                    ["8BitDo", "M30", "8BitDo M30 BT", "Bluetooth", "Wireless", "Bluetooth", "9.1", "Unknown", "8BitDo M30 BT", "8bitdo m30 bt", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "8BitDo",
                    "Model": "M30",
                    "Device": "8BitDo M30 Wired",
                    "Category": "Controller",
                },
                {
                    "Make": "8BitDo",
                    "Model": "M30",
                    "Device": "8BitDo M30 BT",
                    "Category": "Controller",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        by_name = {item["name"]: item for item in payload["items"]}
        item = by_name["8BitDo - M30"]
        self.assertEqual(item["deviceTypes"], ["Wired Controller"])
        self.assertEqual(item["modeVariantCount"], 2)
        self.assertEqual(
            [variant["deviceTypes"] for variant in item["modeVariants"]],
            [["Wired Controller"], ["Wireless Controller"]],
        )

    def test_sheet_compatibility_columns_do_not_override_category_device_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["8BitDo", "M30", "8BitDo - M30", "Wired USB", "Wired", "1.1", "8BitDo - M30", "8bitdo m30", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "8BitDo",
                    "Model": "M30",
                    "Device": "8BitDo M30 [Wired USB]",
                    "MiSTer / PC": "YES",
                    "PS4": "YES",
                    "MacOS": "YES",
                    "Xbox Series": "YES",
                    "Device Types": "Switch 2; Android",
                    "Category": "Controller",
                }
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["category"], "Controller")
        self.assertEqual(item["deviceTypes"], ["Wired Controller"])
        self.assertEqual(item["modeVariants"][0]["deviceTypes"], item["deviceTypes"])
        self.assertEqual(payload["summary"]["deviceTypes"]["Wired Controller"], 1)
        self.assertNotIn("Switch 2", payload["summary"]["deviceTypes"])
        self.assertIn("wired controller", item["searchText"])

    def test_collapsed_mode_variants_keep_specific_adapter_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "WirelessConnection", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Sony", "DualShock 4 (Rev2)", "Sony - DualShock 4 (Rev2)", "Wired USB", "Wired", "-", "3.56", "Sony - DualShock 4 (Rev2)", "sony dualshock 4 rev2", "YES"],
                    ["Sony", "DualShock 4 (Rev2)", "Sony - DualShock 4 (Rev2)", "Sony DualShock 4 Official Wireless Adapter", "Wireless", "Bluetooth", "32.831", "Sony - DualShock 4 (Rev2)", "sony dualshock 4 rev2", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        item = payload["items"][0]
        adapter = next(variant for variant in item["modeVariants"] if variant["averageMs"] == 32.831)
        self.assertEqual(adapter["modeDisplay"], "Sony DualShock 4 Official Wireless Adapter")
        self.assertIn("official wireless adapter", adapter["searchText"])

    def test_collapsed_mode_variants_use_earliest_date_added(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Date Added", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Brook", "Universal Fighting Board", "Brook - Universal Fighting Board [PS4]", "Wired USB", "Wired", "0.80", "9/12/2020", "Brook - Universal Fighting Board [PS4]", "brook universal fighting board ps4", "YES"],
                    ["Brook", "Universal Fighting Board", "Brook - Universal Fighting Board [PS3]", "Wired USB", "Wired", "0.90", "5/10/2020", "Brook - Universal Fighting Board [PS3]", "brook universal fighting board ps3", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        item = payload["items"][0]
        self.assertEqual(item["dateAdded"], "5/10/2020")
        self.assertEqual(item["dateAddedSort"], "2020-05-10")

    def test_mayflash_arcade_stick_modes_collapse_by_model_and_sheet_metadata(self):
        def private_row(device, average):
            row = [""] * len(self.private_header())
            row[latency.PRIVATE_COLUMNS["device"]] = device
            row[latency.PRIVATE_COLUMNS["sample_count"]] = "2000"
            row[latency.PRIVATE_COLUMNS["same_frame"]] = "0.91"
            row[latency.PRIVATE_COLUMNS["average"]] = str(average)
            row[latency.PRIVATE_COLUMNS["maximum"]] = "3.0"
            row[latency.PRIVATE_COLUMNS["minimum"]] = "0.25"
            row[latency.PRIVATE_COLUMNS["sd"]] = "0.40"
            row[latency.PRIVATE_COLUMNS["valid"]] = "YES"
            row[latency.PRIVATE_COLUMNS["p99"]] = "2.0"
            row[latency.PRIVATE_COLUMNS["average_tier"]] = "Platinum"
            row[latency.PRIVATE_COLUMNS["p99_tier"]] = "Platinum"
            row[latency.PRIVATE_COLUMNS["result_type"]] = "unreleased"
            return row

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Reflex", "Reflex", "Reflex - Reflex [3DO 1P]", "1.22", "Reflex - Reflex [3DO 1P]", "reflex reflex 3do 1p", "YES"],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    private_row("Mayflash F300 [Console] FW V1.23", 1.08),
                    private_row("Mayflash F300 [DInput PS3] FW V1.23", 1.27),
                    private_row("Mayflash F300 [Xinput Switch] FW V1.23", 1.40),
                    private_row("Mayflash F500 Elite [DInput PS3 SNK] FW V1.13", 1.35),
                    private_row("Mayflash F500 Elite [Console] FW V1.13", 1.46),
                    private_row("Mayflash F500 V2 [DInput PS3 SNK] FW V1.14", 1.37),
                    private_row("Mayflash F500 V2 [Console] FW V1.14", 1.47),
                ],
            )
            sheet_rows = [
                {
                    "Make": "Mayflash",
                    "Model": "Arcade Stick F300 Rev 1.3",
                    "Device": "Mayflash Arcade Stick F300 Rev 1.3 [Console] FW V1.23",
                    "Mode": "Console",
                    "Output Mode": "Console",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Category": "Arcade Stick",
                    "Date Added": "7/16/2024",
                },
                {
                    "Make": "Mayflash",
                    "Model": "Arcade Stick F300 Rev 1.3",
                    "Device": "Mayflash Arcade Stick F300 Rev 1.3 [DInput PS3] FW V1.23",
                    "Mode": "DInput PS3",
                    "Output Mode": "DInput, PS3",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Category": "Arcade Stick",
                    "Date Added": "7/16/2024",
                },
                {
                    "Make": "Mayflash",
                    "Model": "Arcade Stick F300 Rev 1.3",
                    "Device": "Mayflash Arcade Stick F300 Rev 1.3 [Xinput Switch] FW V1.23",
                    "Mode": "Xinput Switch",
                    "Output Mode": "XInput, Switch",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Category": "Arcade Stick",
                    "Date Added": "7/16/2024",
                },
                {
                    "Make": "Mayflash",
                    "Model": "Arcade Stick F500 V2",
                    "Device": "Mayflash Arcade Stick F500 V2 [DInput PS3 SNK] FW V1.14",
                    "Mode": "DInput PS3 SNK",
                    "Output Mode": "DInput, PS3",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Category": "Arcade Stick",
                    "Date Added": "7/16/2024",
                },
                {
                    "Make": "Mayflash",
                    "Model": "Arcade Stick F500 V2",
                    "Device": "Mayflash Arcade Stick F500 V2 [Console] FW V1.14",
                    "Mode": "Console",
                    "Output Mode": "Console",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Category": "Arcade Stick",
                    "Date Added": "7/16/2024",
                },
            ]

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=sheet_rows)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertIn("Mayflash - F300", by_name)
        self.assertIn("Mayflash - F500 Elite", by_name)
        self.assertIn("Mayflash - F500 V2", by_name)
        f300 = by_name["Mayflash - F300"]
        self.assertEqual(f300["category"], "Arcade Stick")
        self.assertEqual(f300["rankMode"], "Wired Arcade Stick")
        self.assertEqual(f300["modeVariantCount"], 2)
        self.assertEqual(f300["modeLabel"], "DInput, PS3")
        self.assertEqual(
            [variant["outputMode"] for variant in f300["modeVariants"]],
            ["DInput, PS3", "XInput, Switch"],
        )
        self.assertNotIn("Console", [variant["outputMode"] for variant in f300["modeVariants"]])
        f500 = by_name["Mayflash - F500 V2"]
        self.assertEqual(f500["modeVariantCount"], 1)
        self.assertEqual(f500["modeLabel"], "DInput, PS3")
        f500_elite = by_name["Mayflash - F500 Elite"]
        self.assertEqual(f500_elite["category"], "Arcade Stick")
        self.assertEqual(f500_elite["rankMode"], "Arcade Stick")
        self.assertEqual(f500_elite["modeVariantCount"], 1)
        self.assertFalse(
            any(
                variant.get("outputMode") == "Console"
                for item in payload["items"]
                for variant in item.get("modeVariants", [])
            )
        )

    def test_raphnet_adapters_collapse_to_controller_adapter_family(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Raphnet", "SNES Controller to USB Adapter", "Raphnet - SNES Controller to USB Adapter", "Wired USB", "Wired", "1.64", "Controller Adapter", "Raphnet - SNES Controller to USB Adapter", "raphnet snes controller to usb adapter", "YES"],
                    ["Raphnet", "PCEngine Controller to USB Adapter", "Raphnet - PCEngine Controller to USB Adapter", "PC Engine NEC PI-PD6", "Wired", "1.63", "Controller Adapter", "Raphnet - PCEngine Controller to USB Adapter", "raphnet pcengine controller to usb adapter", "YES"],
                ],
            )
            row = [""] * len(self.private_header())
            row[latency.PRIVATE_COLUMNS["device"]] = "raphnet - N64 - 1ms V3.6 - OEM N64"
            row[latency.PRIVATE_COLUMNS["sample_count"]] = "2223"
            row[latency.PRIVATE_COLUMNS["same_frame"]] = "0.90"
            row[latency.PRIVATE_COLUMNS["average"]] = "1.59"
            row[latency.PRIVATE_COLUMNS["maximum"]] = "2.5"
            row[latency.PRIVATE_COLUMNS["minimum"]] = "0.59"
            row[latency.PRIVATE_COLUMNS["sd"]] = "0.41"
            row[latency.PRIVATE_COLUMNS["valid"]] = "YES"
            row[latency.PRIVATE_COLUMNS["p99"]] = "2.48"
            row[latency.PRIVATE_COLUMNS["average_tier"]] = "Platinum"
            row[latency.PRIVATE_COLUMNS["p99_tier"]] = "Platinum"
            row[latency.PRIVATE_COLUMNS["result_type"]] = "unreleased"
            self.write_csv(private_root / "captures" / "unreleased.csv", [self.private_header(), row])

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertIn("Raphnet - Controller Adapter", by_name)
        raphnet = by_name["Raphnet - Controller Adapter"]
        self.assertEqual(raphnet["category"], "Controller Adapter")
        self.assertEqual(raphnet["rankMode"], "Controller Adapter")
        self.assertTrue(raphnet["isOpenSource"])
        self.assertEqual(raphnet["sourceStatus"], "Open Source")
        self.assertEqual(raphnet["modeVariantCount"], 3)
        variant_types = {variant["name"]: variant["deviceTypes"] for variant in raphnet["modeVariants"]}
        self.assertEqual(variant_types["raphnet - N64 - 1ms V3.6 - OEM N64"], ["Controller Adapter", "N64 Controller"])
        self.assertEqual(variant_types["Raphnet - PCEngine Controller to USB Adapter"], ["Controller Adapter", "PC Engine Controller"])
        self.assertEqual(variant_types["Raphnet - SNES Controller to USB Adapter"], ["Controller Adapter", "SNES Controller"])

    def test_private_rows_can_inherit_sheet_date_added(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            private_header = [
                "", "Device", "", "", "", "", "", "", "", "", "", "", "", "", "",
                "Number of Samples", "Same Frame Probability", "Average", "Maximum", "Minimum", "Standard Deviation",
                "Valid Results", "Joystick ID", "Notes", "Tester", "Date Added", "Category", "Original Controller System",
                "Face Buttons", "Weight (oz)", "'Feel (0-10)'", "Feel Notes", "99%", "Average Tier", "99% Tier", "Result Type",
            ]
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    private_header,
                    [
                        "1", "Reflex Encode Fightboard V1", "", "", "", "", "", "", "", "", "", "", "", "", "",
                        "2477", "0.9507", "0.8209", "1.40", "0.26", "0.291", "YES", "", "", "", "",
                        "Arcade Stick Encoder", "", "", "", "", "", "1.34", "Diamond", "Diamond", "unreleased",
                    ],
                ],
            )
            sheet_rows = [
                {
                    "Make": "Reflex",
                    "Model": "Encode Fightboard",
                    "Device": "Reflex Encode Fightboard [Wired USB Xinput]",
                    "Mode": "Wired USB Xinput",
                    "Output Mode": "XInput",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Date Added": "7/12/2024",
                }
            ]

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["name"], "Reflex Encode Fightboard (GP2040-CE)")
        self.assertEqual(item["dateAdded"], "7/12/2024")
        self.assertEqual(item["dateAddedSort"], "2024-07-12")

    def test_internal_reflex_3do_rows_are_excluded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            header = [
                "", "Device", "", "", "", "", "", "", "", "", "", "", "", "", "",
                "Number of Samples", "Same Frame Probability", "Average", "Maximum", "Minimum", "Standard Deviation",
                "Valid Results", "Joystick ID", "Notes", "Tester", "Date Added", "Category", "Original Controller System",
                "Face Buttons", "Weight (oz)", "'Feel (0-10)'", "Feel Notes", "99%", "Average Tier", "99% Tier", "Result Type",
            ]
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    header,
                    ["1", "Reflex [3DO 1P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "4240", "0.92", "1.22", "1.91", "0.52", "0.31", "YES", "", "", "", "", "", "", "", "", "", "", "1.82", "Diamond", "Platinum", "unreleased"],
                    ["2", "Reflex [3DO 2P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2055", "0.91", "1.43", "2.18", "0.65", "0.33", "YES", "", "", "", "", "", "", "", "", "", "", "2.12", "Platinum", "Platinum", "unreleased"],
                    ["3", "Real Controller", "", "", "", "", "", "", "", "", "", "", "", "", "", "1000", "0.90", "5.0", "6.0", "4.0", "0.2", "YES", "", "", "", "", "", "", "", "", "", "", "6.0", "Gold", "Gold", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        self.assertEqual([item["name"] for item in payload["items"]], ["Real Controller"])

    def test_reflex_adapt_pass_through_rows_subtract_adapter_average_and_clean_title(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            header = [
                "", "Device", "", "", "", "", "", "", "", "", "", "", "", "", "",
                "Number of Samples", "Same Frame Probability", "Average", "Maximum", "Minimum", "Standard Deviation",
                "Valid Results", "Joystick ID", "Notes", "Tester", "Date Added", "Category", "Original Controller System",
                "Face Buttons", "Weight (oz)", "'Feel (0-10)'", "Feel Notes", "99%", "Average Tier", "99% Tier", "Result Type",
            ]
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    header,
                    ["1", "Reflex Adapt [GameCube 1P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "3129", "0.83", "2.78051773729626", "3.78", "1.82", "0.40", "YES", "", "", "", "", "", "", "", "", "", "", "3.65", "Platinum", "Platinum", "unreleased"],
                    ["2", "Reflex Adapt [GameCube 2P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2038", "0.85", "2.38090284592738", "3.65", "1.11", "0.55", "YES", "", "", "", "", "", "", "", "", "", "", "3.49", "Platinum", "Platinum", "unreleased"],
                    ["3", "Reflex Adapt [N64 1P MPG HID]", "", "", "", "", "", "", "", "", "", "", "", "", "", "6370", "0.87", "2.0531726844584", "2.84", "1.33", "0.31", "YES", "", "", "", "", "", "", "", "", "", "", "2.69", "Platinum", "Platinum", "unreleased"],
                    ["4", "Reflex Adapt [N64 1P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2104", "0.93", "1.06168726235741", "1.70", "0.43", "0.30", "YES", "", "", "", "", "", "", "", "", "", "", "1.64", "Diamond", "Platinum", "unreleased"],
                    ["5", "AliExpress Gamecube Wireless [2.4GHz via Reflex Adapt]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2108", "0.13", "14.957789373814", "27.87", "9.57", "3.04", "YES", "", "", "", "", "", "", "", "", "", "", "25.35", "Rust", "Silver", "unreleased"],
                    ["6", "VR-ESPECIAL The N64 Bit Controller Wireless [Reflex Adapt]", "", "", "", "", "", "", "", "", "", "", "", "", "", "1085", "0.00", "21.8933732718894", "32.30", "3.75", "1.81", "YES", "", "", "", "", "", "", "", "", "", "", "27.20", "Rust", "Rust", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        gamecube = by_name["AliExpress Gamecube Wireless"]
        n64 = by_name["VR-ESPECIAL The N64 Bit Controller Wireless"]

        self.assertEqual(gamecube["averageMs"], 12.177)
        self.assertEqual(gamecube["averageTier"], "Bronze")
        self.assertEqual(gamecube["measuredAverageMs"], 14.958)
        self.assertEqual(gamecube["adapterAverageMs"], 2.781)
        self.assertEqual(gamecube["adapterMode"], "GameCube 1P")
        self.assertEqual(n64["averageMs"], 20.831)
        self.assertEqual(n64["adapterAverageMs"], 1.062)
        self.assertEqual(n64["adapterMode"], "N64 1P")
        self.assertNotIn("Reflex Adapt", gamecube["name"])
        self.assertNotIn("Reflex Adapt", n64["name"])

    def test_reflex_adapt_pass_through_search_omits_hidden_adapter_provenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    ["1", "Reflex Adapt [GameCube 1P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "3129", "0.83", "2.78051773729626", "3.78", "1.82", "0.40", "YES", "", "", "", "", "Controller Adapter", "", "", "", "", "", "3.65", "Platinum", "Platinum", "unreleased"],
                    ["2", "AliExpress Gamecube Wireless [2.4GHz via Reflex Adapt]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2108", "0.13", "14.957789373814", "27.87", "9.57", "3.04", "YES", "", "", "", "", "", "", "", "", "", "", "25.35", "Rust", "Silver", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        adjusted = by_name["AliExpress Gamecube Wireless"]
        self.assertEqual(adjusted["adapterSourceName"], "Reflex Adapt [GameCube 1P]")
        self.assertNotIn("reflex adapt", adjusted["searchText"])
        matches = [item["name"] for item in payload["items"] if "reflex adapt" in item["searchText"]]
        self.assertTrue(any(name.startswith("Reflex - Adapt") for name in matches))
        self.assertNotIn("AliExpress Gamecube Wireless", matches)

    def test_controller_adapter_device_types_include_input_controller_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["DaemonBite", "Genesis to USB Adapter", "DaemonBite - Genesis to USB Adapter", "Genesis 3 Button Controller", "Wired", "0.75", "Controller Adapter", "DaemonBite - Genesis to USB Adapter", "daemonbite genesis to usb adapter", "YES"],
                    ["DaemonBite", "PC Engine to USB Adapter", "DaemonBite - PC Engine to USB Adapter", "NEC PI-PD6 2 button Controller", "Wired", "0.78", "Controller Adapter", "DaemonBite - PC Engine to USB Adapter", "daemonbite pc engine to usb adapter", "YES"],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    ["1", "Reflex Adapt [Genesis 1P]", "", "", "", "", "", "", "", "", "", "", "", "", "", "7641", "0.94", "0.934423504776862", "1.52", "0.34", "0.29", "YES", "", "", "", "", "Controller Adapter", "", "", "", "", "", "1.46", "Diamond", "Diamond", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        daemonbite = by_name["DaemonBite - Controller Adapter"]
        variant_types = {variant["name"]: variant["deviceTypes"] for variant in daemonbite["modeVariants"]}
        self.assertEqual(variant_types["DaemonBite - Genesis to USB Adapter"], ["Controller Adapter", "Genesis Controller"])
        self.assertEqual(variant_types["DaemonBite - PC Engine to USB Adapter"], ["Controller Adapter", "PC Engine Controller"])
        reflex = next(item for item in payload["items"] if item["name"].startswith("Reflex - Adapt"))
        self.assertEqual(reflex["deviceTypes"], ["Controller Adapter", "Genesis Controller"])
        self.assertIn("Genesis Controller", payload["summary"]["deviceTypes"])

    def test_daemonbite_controller_adapters_collapse_to_one_device_with_modes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["DaemonBite", "Genesis to USB Adapter", "DaemonBite - Genesis to USB Adapter", "Genesis 3 Button Controller", "Wired", "0.75", "Controller Adapter", "DaemonBite - Genesis to USB Adapter", "daemonbite genesis to usb adapter", "YES"],
                    ["DaemonBite", "SNES / SFC to USB Adapter", "DaemonBite - SNES / SFC to USB Adapter", "SNES Controller", "Wired", "1.11", "Controller Adapter", "DaemonBite - SNES / SFC to USB Adapter", "daemonbite snes sfc to usb adapter", "YES"],
                    ["DaemonBite", "Arcade Controller", "DaemonBite - Arcade Controller", "Wired USB", "Wired", "0.76", "Joystick Encoder", "DaemonBite - Arcade Controller", "daemonbite arcade controller", "YES"],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    ["1", "DaemonBite [NES]", "", "", "", "", "", "", "", "", "", "", "", "", "", "2171", "0.94", "0.887858129894058", "1.45", "0.32", "0.28", "YES", "", "", "", "", "", "", "", "", "", "", "1.40", "Diamond", "Diamond", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertIn("DaemonBite - Controller Adapter", by_name)
        self.assertIn("DaemonBite - Arcade Controller", by_name)
        self.assertNotIn("DaemonBite - Genesis to USB Adapter", by_name)
        daemonbite = by_name["DaemonBite - Controller Adapter"]
        self.assertEqual(daemonbite["modeVariantCount"], 3)
        self.assertEqual(daemonbite["averageMs"], 0.75)
        self.assertEqual(daemonbite["outputMode"], "DInput")
        self.assertEqual(daemonbite["modeLabel"], "DInput")
        self.assertEqual(daemonbite["modeDisplay"], "DInput")
        self.assertEqual(daemonbite["rankMode"], "Controller Adapter")
        self.assertEqual(
            sorted(variant["deviceTypes"][-1] for variant in daemonbite["modeVariants"]),
            ["Genesis Controller", "NES Controller", "SNES Controller"],
        )
        for variant in daemonbite["modeVariants"]:
            self.assertEqual(variant["outputMode"], "DInput")
            self.assertEqual(variant["modeDisplay"], "DInput")
        self.assertIn("snes controller", daemonbite["searchText"])

    def test_sheet_sale_status_and_source_firmware_metadata_are_exported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Bootsector", "LLOAD", "Bootsector LLOAD", "Wired USB", "Wired", "0.8", "Bootsector LLOAD", "bootsector lload", "YES"],
                    ["8BitDo", "M30", "8BitDo M30", "Wired USB", "Wired", "1.2", "8BitDo M30", "8bitdo m30", "YES"],
                    ["Old", "Pad", "Old Pad", "Wired USB", "Wired", "10.0", "Old Pad", "old pad", "YES"],
                    ["Reflex", "Adapt", "Reflex Adapt [SNES]", "Wired USB", "Wired", "1.4", "Reflex Adapt [SNES]", "reflex adapt snes", "YES"],
                    ["Timville", "4Dapter", "Timville 4Dapter N64 [HID]", "Wired USB", "Wired", "2.2", "Timville 4Dapter N64 HID", "timville 4dapter n64 hid", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "Bootsector",
                    "Model": "LLOAD",
                    "Device": "Bootsector LLOAD [Wired USB]",
                    "Link": "https://github.com/bootsector/LLOAD",
                },
                {
                    "Make": "8BitDo",
                    "Model": "M30",
                    "Device": "8BitDo M30 [Wired USB]",
                    "Link": "https://amzn.to/example",
                    "Currently Sold": "YES",
                    "Open Source": "NO",
                },
                {
                    "Make": "Old",
                    "Model": "Pad",
                    "Device": "Old Pad [Wired USB]",
                    "Sale Status": "Discontinued",
                },
                {
                    "Make": "Reflex",
                    "Model": "Adapt",
                    "Device": "Reflex Adapt [SNES]",
                },
                {
                    "Make": "Timville",
                    "Model": "4Dapter",
                    "Device": "Timville 4Dapter N64 [HID]",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        by_name = {item["name"]: item for item in payload["items"]}
        closed_with_source_link = by_name["Bootsector - LLOAD"]
        active_item = by_name["8BitDo - M30"]
        old_item = by_name["Old - Pad"]
        reflex_item = by_name["Reflex - Adapt"]
        timville_item = by_name["Timville - 4Dapter"]

        self.assertFalse(closed_with_source_link["isOpenSource"])
        self.assertEqual(closed_with_source_link["sourceStatus"], "Closed Source")
        self.assertEqual(closed_with_source_link["sourceUrl"], "https://github.com/bootsector/LLOAD")
        self.assertEqual(closed_with_source_link["saleStatus"], "Discontinued")
        self.assertFalse(active_item["isOpenSource"])
        self.assertEqual(active_item["sourceStatus"], "Closed Source")
        self.assertEqual(active_item["saleStatus"], "Actively sold")
        self.assertEqual(old_item["saleStatus"], "Discontinued")
        self.assertTrue(reflex_item["isOpenSource"])
        self.assertEqual(reflex_item["sourceStatus"], "Open Source")
        self.assertIn("open source", reflex_item["searchText"])
        self.assertTrue(timville_item["isOpenSource"])
        self.assertEqual(timville_item["sourceStatus"], "Open Source")
        self.assertEqual(payload["summary"]["saleStatuses"]["Actively sold"], 2)
        self.assertEqual(payload["summary"]["saleStatuses"]["Discontinued"], 2)
        self.assertEqual(payload["summary"]["sourceStatuses"]["Open Source"], 2)

    def test_stale_external_product_links_are_replaced(self):
        snes = {
            "name": "8BitDo - SNES Conversion PCB",
            "buyUrl": "https://shop.8bitdo.com/products/mod-kit-for-snes-controller",
            "link": "https://shop.8bitdo.com/products/mod-kit-for-snes-controller",
        }
        retrofi = {
            "name": "bootsector - RetroFi",
            "buyUrl": "https://brunofreitas.myshopify.com/products/retrofi-low-latency-wireless-multiplayer-joystick-adapter",
            "link": "https://brunofreitas.myshopify.com/products/retrofi-low-latency-wireless-multiplayer-joystick-adapter",
        }

        latency.apply_sale_status_overrides(snes)
        latency.apply_sale_status_overrides(retrofi)

        self.assertEqual(snes["saleStatus"], "Actively sold")
        self.assertEqual(snes["buyUrl"], latency.EIGHTBITDO_SNES_MOD_KIT_URL)
        self.assertEqual(snes["link"], latency.EIGHTBITDO_SNES_MOD_KIT_URL)
        self.assertEqual(retrofi["saleStatus"], "Discontinued")
        self.assertEqual(retrofi["buyUrl"], latency.RETROFI_INFO_URL)
        self.assertEqual(retrofi["link"], latency.RETROFI_INFO_URL)

    def test_reflex_ctrl_rows_are_controller_conversion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    ["1", "Reflex CTRL SNES [Dinput]", "", "", "", "", "", "", "", "", "", "", "", "", "", "8135", "0.94", "0.841834050399508", "1.43", "0.28", "0.29", "YES", "", "", "", "", "", "", "", "", "", "", "1.36", "Diamond", "Diamond", "unreleased"],
                    ["2", "Reflex CTRL SNES [Switch]", "", "", "", "", "", "", "", "", "", "", "", "", "", "8264", "0.94", "0.838848015488867", "1.57", "0.27", "0.29", "YES", "", "", "", "", "", "", "", "", "", "", "1.35", "Diamond", "Diamond", "unreleased"],
                    ["3", "Reflex CTRL SNES [Xinput]", "", "", "", "", "", "", "", "", "", "", "", "", "", "3444", "0.94", "0.838519163763066", "2.36", "0.25", "0.28", "YES", "", "", "", "", "", "", "", "", "", "", "1.35", "Diamond", "Diamond", "unreleased"],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        item = payload["items"][0]
        self.assertEqual(item["name"], "Reflex CTRL")
        self.assertEqual(item["category"], "Controller Conversion")
        self.assertEqual(item["deviceTypes"], ["Controller Conversion"])
        self.assertEqual(item["rankMode"], "Controller Conversion")
        self.assertEqual(item["modeVariantCount"], 3)

    def test_hyphenated_public_aliases_stay_consolidated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Reflex", "CTRL", "Reflex - CTRL [Dinput]", "Wired USB", "Wired", "0.84", "Controller Conversion", "Reflex - CTRL [Dinput]", "reflex ctrl dinput", "YES"],
                    ["Reflex", "CTRL SNES", "Reflex - CTRL SNES [Switch]", "Wired USB", "Wired", "0.85", "Controller", "Reflex - CTRL SNES [Switch]", "reflex ctrl snes switch", "YES"],
                    ["Reflex", "Encode Fightboard", "Reflex - Encode Fightboard", "Wired USB", "Wired", "0.95", "Arcade Stick Encoder", "Reflex - Encode Fightboard", "reflex encode fightboard", "YES"],
                    ["Reflex", "Encode Fightboard V1", "Reflex - Encode Fightboard V1", "Wired USB", "Wired", "0.96", "Arcade Stick", "Reflex - Encode Fightboard V1", "reflex encode fightboard v1", "YES"],
                    ["Mayflash", "F300", "Mayflash - F300 [DInput PS3] FW V1.23", "Wired USB", "Wired", "1.27", "Arcade Stick", "Mayflash - F300 [DInput PS3] FW V1.23", "mayflash f300 dinput ps3 fw v1 23", "YES"],
                    ["Mayflash", "Arcade Stick F300 Rev 1.3", "Mayflash - Arcade Stick F300 Rev 1.3 [Xinput Switch] FW V1.23", "Wired USB", "Wired", "1.40", "Arcade Stick", "Mayflash - Arcade Stick F300 Rev 1.3 [Xinput Switch] FW V1.23", "mayflash arcade stick f300 rev 1 3 xinput switch fw v1 23", "YES"],
                    ["Mayflash", "F300 Elite", "Mayflash - F300 Elite [DInput PS3] FW V1.10", "Wired USB", "Wired", "1.25", "Arcade Stick", "Mayflash - F300 Elite [DInput PS3] FW V1.10", "mayflash f300 elite dinput ps3 fw v1 10", "YES"],
                    ["Mayflash", "Arcade Stick F300 Elite", "Mayflash - Arcade Stick F300 Elite [Xinput Switch] FW V1.10", "Wired USB", "Wired", "1.45", "Arcade Stick", "Mayflash - Arcade Stick F300 Elite [Xinput Switch] FW V1.10", "mayflash arcade stick f300 elite xinput switch fw v1 10", "YES"],
                    ["Mayflash", "F500 V2", "Mayflash - F500 V2 [DInput PS3 SNK] FW V1.14", "Wired USB", "Wired", "1.37", "Arcade Stick", "Mayflash - F500 V2 [DInput PS3 SNK] FW V1.14", "mayflash f500 v2 dinput ps3 snk fw v1 14", "YES"],
                    ["Mayflash", "Arcade Stick F500 V2", "Mayflash - Arcade Stick F500 V2 [Xinput] FW V1.14", "Wired USB", "Wired", "1.47", "Arcade Stick", "Mayflash - Arcade Stick F500 V2 [Xinput] FW V1.14", "mayflash arcade stick f500 v2 xinput fw v1 14", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertIn("Reflex CTRL", by_name)
        self.assertNotIn("Reflex - CTRL", by_name)
        self.assertNotIn("Reflex - CTRL SNES", by_name)
        self.assertEqual(by_name["Reflex CTRL"]["category"], "Controller Conversion")
        self.assertEqual(by_name["Reflex CTRL"]["modeVariantCount"], 2)
        self.assertIn("Reflex Encode Fightboard (GP2040-CE)", by_name)
        self.assertNotIn("Reflex - Encode Fightboard", by_name)
        self.assertNotIn("Reflex - Encode Fightboard V1", by_name)
        self.assertEqual(by_name["Reflex Encode Fightboard (GP2040-CE)"]["modeVariantCount"], 2)

        for name in ("Mayflash - F300", "Mayflash - F300 Elite", "Mayflash - F500 V2"):
            with self.subTest(name=name):
                self.assertIn(name, by_name)
                self.assertEqual(by_name[name]["modeVariantCount"], 2)
        self.assertNotIn("Mayflash - Arcade Stick F300 Rev 1.3", by_name)
        self.assertNotIn("Mayflash - Arcade Stick F300 Elite", by_name)
        self.assertNotIn("Mayflash - Arcade Stick F500 V2", by_name)

    def test_known_private_wired_families_get_wired_connection_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [["Device", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"]],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    self.private_header(),
                    self.private_row("Reflex Adapt [Genesis 1P]", "0.77", category="Controller Adapter"),
                    self.private_row("Reflex CTRL SNES [Dinput]", "0.84", category="Controller Conversion"),
                    self.private_row("raphnet - N64 - 1ms V3.6 - OEM N64", "1.59", category="Controller Adapter"),
                    self.private_row("DaemonBite [NES]", "0.89", category="Controller Adapter"),
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        for name in ("Reflex - Adapt", "Reflex CTRL", "Raphnet - Controller Adapter", "DaemonBite - Controller Adapter"):
            with self.subTest(name=name):
                item = by_name[name]
                self.assertEqual(item["connectionKind"], "Wired")
                self.assertEqual(item["connectionTag"], "Wired")

    def test_sheet_output_mode_connection_tag_and_latency_ranks_are_exported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "WirelessConnection", "Category", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Acme", "D1", "Acme D1", "Wired USB", "Wired", "-", "Controller", "1.0", "Acme D1", "acme d1", "YES"],
                    ["Acme", "D2", "Acme D2", "Wired USB", "Wired", "-", "Controller", "0.5", "Acme D2", "acme d2", "YES"],
                    ["Acme", "X1", "Acme X1", "BT (CSR8510)", "Wireless", "Bluetooth", "Controller", "2.0", "Acme X1", "acme x1", "YES"],
                    ["Acme", "R1", "Acme R1", "Wireless USB Dongle", "Wireless", "2.4 GHz", "Controller", "3.0", "Acme R1", "acme r1", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "Acme",
                    "Model": "D1",
                    "Device": "Acme D1 [Wired USB Dinput]",
                    "Mode": "Wired USB Dinput",
                    "Output Mode": "DInput",
                    "Wired / Wireless": "Wired",
                    "Connection": "Wired USB",
                    "Wireless Connection": "-",
                },
                {
                    "Make": "Acme",
                    "Model": "D2",
                    "Device": "Acme D2 [Wired USB Dinput]",
                    "Mode": "Wired USB Dinput",
                    "Output Mode": "DInput",
                    "Wired / Wireless": "Wired",
                    "Connection": "Wired USB",
                    "Wireless Connection": "-",
                },
                {
                    "Make": "Acme",
                    "Model": "X1",
                    "Device": "Acme X1 [BT (CSR8510) XInput]",
                    "Mode": "BT (CSR8510) XInput",
                    "Output Mode": "XInput",
                    "Wired / Wireless": "Wireless",
                    "Connection": "BT (CSR8510)",
                    "Wireless Connection": "Bluetooth",
                },
                {
                    "Make": "Acme",
                    "Model": "R1",
                    "Device": "Acme R1 [Wireless USB Dongle]",
                    "Mode": "Wireless USB Dongle",
                    "Output Mode": "",
                    "Wired / Wireless": "Wireless",
                    "Connection": "Wireless USB Dongle",
                    "Wireless Connection": "2.4 GHz",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["published-acme-d1"]["modeRaw"], "Wired USB Dinput")
        self.assertEqual(by_id["published-acme-d1"]["outputMode"], "DInput")
        self.assertEqual(by_id["published-acme-d1"]["modeLabel"], "DInput")
        self.assertEqual(by_id["published-acme-d1"]["connectionTag"], "Wired")
        self.assertEqual(by_id["published-acme-d1"]["overallRank"], 2)
        self.assertEqual(by_id["published-acme-d1"]["rankMode"], "Wired Controller")
        self.assertEqual(by_id["published-acme-d1"]["modeRank"], 2)
        self.assertEqual(by_id["published-acme-d2"]["overallRank"], 1)
        self.assertEqual(by_id["published-acme-d2"]["modeRank"], 1)
        self.assertEqual(by_id["published-acme-x1"]["connectionTag"], "Wireless BT")
        self.assertEqual(by_id["published-acme-x1"]["rankMode"], "Wireless Controller")
        self.assertEqual(by_id["published-acme-x1"]["modeRank"], 1)
        self.assertEqual(by_id["published-acme-r1"]["connectionTag"], "Wireless 2.4GHz")
        self.assertEqual(by_id["published-acme-r1"]["rankMode"], "Wireless Controller")
        self.assertEqual(by_id["published-acme-r1"]["modeRank"], 2)

    def test_latency_rank_classes_use_device_type_and_transport(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "WirelessConnection", "Category", "Latency (in ms)", "Valid Results"],
                    ["Fast Wired Pad", "fast wired pad", "Wired USB", "Wired", "-", "Controller", "1.0", "YES"],
                    ["Slow Wired Pad", "slow wired pad", "Wired USB", "Wired", "-", "Controller", "4.0", "YES"],
                    ["Wireless Pad", "wireless pad", "BT", "Wireless", "Bluetooth", "Controller", "2.0", "YES"],
                    ["USB Adapter", "usb adapter", "Wired USB", "Wired", "-", "Controller Adapter", "3.0", "YES"],
                    ["Encoder", "encoder", "Wired USB", "Wired", "-", "Joystick Encoder", "0.5", "YES"],
                    ["Wired Stick", "wired stick", "Wired USB", "Wired", "-", "Joystick", "5.0", "YES"],
                    ["Wireless Stick", "wireless stick", "BT", "Wireless", "Bluetooth", "Joystick", "6.0", "YES"],
                    ["Unknown Capture", "unknown capture", "", "Unknown", "", "", "7.0", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["published-fast-wired-pad"]["rankMode"], "Wired Controller")
        self.assertEqual(by_id["published-fast-wired-pad"]["modeRank"], 1)
        self.assertEqual(by_id["published-slow-wired-pad"]["rankMode"], "Wired Controller")
        self.assertEqual(by_id["published-slow-wired-pad"]["modeRank"], 2)
        self.assertEqual(by_id["published-wireless-pad"]["rankMode"], "Wireless Controller")
        self.assertEqual(by_id["published-usb-adapter"]["rankMode"], "Controller Adapter")
        self.assertEqual(by_id["published-encoder"]["rankMode"], "Arcade Stick Encoder")
        self.assertEqual(by_id["published-wired-stick"]["rankMode"], "Wired Arcade Stick")
        self.assertEqual(by_id["published-wireless-stick"]["rankMode"], "Wireless Arcade Stick")
        self.assertEqual(by_id["published-unknown-capture"]["rankMode"], "")
        self.assertIsNone(by_id["published-unknown-capture"]["modeRank"])

    def test_sheet_matching_prefers_variant_output_mode_over_first_make_model_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["8BitDo", "N30 Arcade Stick", "8BitDo - N30 Arcade Stick [X-Input]", "Wired USB", "Wired", "1.0", "8BitDo - N30 Arcade Stick [X-Input]", "8bitdo n30 arcade stick x input", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "8BitDo",
                    "Model": "N30 Arcade Stick",
                    "Device": "8BitDo N30 Arcade Stick [Wired USB Dinput]",
                    "Mode": "Wired USB Dinput",
                    "Output Mode": "DInput",
                    "Wired / Wireless": "Wired",
                    "Connection": "Wired USB",
                },
                {
                    "Make": "8BitDo",
                    "Model": "N30 Arcade Stick",
                    "Device": "8BitDo N30 Arcade Stick [Wired USB Xinput]",
                    "Mode": "Wired USB Xinput",
                    "Output Mode": "XInput",
                    "Wired / Wireless": "Wired",
                    "Connection": "Wired USB",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["modeRaw"], "Wired USB Xinput")
        self.assertEqual(item["outputMode"], "XInput")
        self.assertEqual(item["modeLabel"], "XInput")

    def test_sheet_matching_prefers_exact_measurement_name_for_console_modes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "DeviceClean", "Connection", "Wired/Wireless", "Latency (in ms)", "Valid Results"],
                    ["Qanba", "Drone", "Qanba Drone [Wired USB PS3]", "Wired USB", "Wired", "3.25", "YES"],
                    ["Qanba", "Drone", "Qanba Drone [Wired USB PS4]", "Wired USB", "Wired", "3.265", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "Qanba",
                    "Model": "Drone",
                    "Device": "Qanba Drone [Wired USB PS3]",
                    "Mode": "Wired USB PS3",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Joystick ID": "2c22:2003",
                    "Link": "https://www.amazon.com/dp/B012345678",
                },
                {
                    "Make": "Qanba",
                    "Model": "Drone",
                    "Device": "Qanba Drone [Wired USB PS4]",
                    "Mode": "Wired USB PS4",
                    "Connection": "Wired USB",
                    "Wired / Wireless": "Wired",
                    "Joystick ID": "2c22:2004",
                    "Amazon": "YES",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        variants = {
            variant["measurementName"]: variant
            for variant in payload["items"][0]["modeVariants"]
        }
        self.assertEqual(variants["Qanba Drone [Wired USB PS3]"]["modeRaw"], "Wired USB PS3")
        self.assertEqual(variants["Qanba Drone [Wired USB PS3]"]["joystickId"], "2c22:2003")
        self.assertEqual(variants["Qanba Drone [Wired USB PS4]"]["modeRaw"], "Wired USB PS4")
        self.assertEqual(variants["Qanba Drone [Wired USB PS4]"]["joystickId"], "2c22:2004")
        self.assertEqual(variants["Qanba Drone [Wired USB PS4]"]["buyUrl"], "https://www.amazon.com/dp/B012345678")
        self.assertNotEqual(variants["Qanba Drone [Wired USB PS4]"]["amazon"], "YES")

    def test_sheet_mode_does_not_overwrite_distinct_connection_variants(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "WirelessConnection", "Category", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Sony", "DualShock 4 (Rev2)", "Sony - DualShock 4 (Rev2)", "BT (CSR8510)", "Wireless", "Bluetooth", "Controller", "6.495", "Sony - DualShock 4 (Rev2)", "sony dualshock 4 rev2", "YES"],
                    ["Sony", "DualShock 4 (Rev2)", "Sony - DualShock 4 (Rev2)", "Sony DualShock 4 Official Wireless Adapter", "Wireless", "Bluetooth", "Controller", "32.831", "Sony - DualShock 4 (Rev2)", "sony dualshock 4 rev2", "YES"],
                ],
            )
            sheet_rows = [
                {
                    "Make": "Sony",
                    "Model": "DualShock 4 (Rev2)",
                    "Device": "Sony - DualShock 4 (Rev2)",
                    "Mode": "BT (CSR8510)",
                    "Connection": "BT (CSR8510)",
                    "Wired / Wireless": "Wireless",
                    "Wireless Connection": "Bluetooth",
                    "Amazon": "https://amzn.to/dualshock",
                },
                {
                    "Make": "Sony",
                    "Model": "DualShock 4 (Rev2)",
                    "Device": "Sony - DualShock 4 (Rev2)",
                    "Connection": "Sony DualShock 4 Official Wireless Adapter",
                    "Wired / Wireless": "Wireless",
                    "Wireless Connection": "Bluetooth",
                    "Amazon": "https://amzn.to/dualshock",
                },
            ]

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        variants = {variant["connection"]: variant for variant in item["modeVariants"]}
        official = variants["Sony DualShock 4 Official Wireless Adapter"]
        self.assertEqual(official["modeRaw"], "")
        self.assertEqual(official["modeLabel"], "Bluetooth")
        self.assertEqual(official["rankMode"], "Wireless Controller")
        self.assertEqual(official["modeRank"], 2)
        self.assertEqual(official["buyUrl"], "https://amzn.to/dualshock")

    def test_controller_modes_collapse_to_fastest_visible_result_with_variants(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "Latency (in ms)", "Valid Results"],
                    ["Reflex Adapt [SNES 1P]", "reflex adapt snes 1p", "Wired USB", "Wired", "1.48", "YES"],
                    ["Reflex Adapt [Neo Geo]", "reflex adapt neo geo", "Wired USB", "Wired", "0.77", "YES"],
                    ["Reflex Adapt [N64 1P MPG Xinput]", "reflex adapt n64 1p mpg xinput", "Wired USB", "Wired", "2.04", "YES"],
                    ["Other Pad", "other pad", "Wired USB", "Wired", "0.50", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(payload["summary"]["totalItems"], 2)
        self.assertIn("published-reflex-adapt", by_id)
        self.assertNotIn("published-reflex-adapt-snes-1p", by_id)
        self.assertEqual(by_id["published-reflex-adapt"]["name"], "Reflex - Adapt")
        self.assertEqual(by_id["published-reflex-adapt"]["averageMs"], 0.77)
        self.assertEqual(by_id["published-reflex-adapt"]["modeLabel"], "DInput")
        self.assertEqual(by_id["published-reflex-adapt"]["modeVariantCount"], 2)
        self.assertEqual(
            [variant["modeLabel"] for variant in by_id["published-reflex-adapt"]["modeVariants"]],
            ["DInput", "DInput"],
        )
        self.assertNotIn("n64 1p mpg xinput", by_id["published-reflex-adapt"]["searchText"])

    def test_requested_cleanup_hides_duplicates_and_adjusts_hori_wii_classic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    [
                        "Make", "Model", "Device", "Connection", "Wired/Wireless", "Category",
                        "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results",
                        "HasRawCapture", "N", "P99",
                    ],
                    ["Reflex", "Adapt", "Reflex - Adapt [N64 1P]", "Wired USB", "Wired", "Controller Adapter", "1.062", "Reflex - Adapt [N64 1P]", "reflex adapt n64 1p", "YES", "TRUE", "2104", "1.64"],
                    ["Reflex", "Adapt", "Reflex - Adapt [N64 2P]", "Wired USB", "Wired", "Controller Adapter", "1.148", "Reflex - Adapt [N64 2P]", "reflex adapt n64 2p", "YES", "TRUE", "2084", "1.89"],
                    ["Reflex", "Adapt", "Reflex - Adapt [N64 1P MPG HID]", "Wired USB", "Wired", "Controller Adapter", "2.053", "Reflex - Adapt [N64 1P MPG HID]", "reflex adapt n64 1p mpg hid", "YES", "TRUE", "6370", "2.69"],
                    ["Reflex", "Adapt", "Reflex - Adapt [N64 1P MPG Xinput]", "Wired USB", "Wired", "Controller Adapter", "2.042", "Reflex - Adapt [N64 1P MPG Xinput]", "reflex adapt n64 1p mpg xinput", "YES", "TRUE", "5111", "2.68"],
                    ["Reflex", "Adapt", "Reflex - Adapt [N64 1P MPG Switch]", "Wired USB", "Wired", "Controller Adapter", "2.065", "Reflex - Adapt [N64 1P MPG Switch]", "reflex adapt n64 1p mpg switch", "YES", "TRUE", "2354", "2.68"],
                    ["Reflex", "Adapt N64", "Reflex Adapt N64 [Wired USB Dinput]", "Wired USB", "Wired", "Controller Adapter", "2.95", "Reflex Adapt N64 [Wired USB Dinput]", "reflex adapt n64 wired usb dinput", "YES", "FALSE", "", ""],
                    ["Reflex", "Adapt 3DO", "Reflex Adapt 3DO [Wired USB Dinput]", "Wired USB", "Wired", "Controller Adapter", "1.22", "Reflex Adapt 3DO [Wired USB Dinput]", "reflex adapt 3do wired usb dinput", "YES", "FALSE", "", ""],
                    ["Reflex", "Adapt", "Reflex - Adapt [Saturn 3D 1P]", "Wired USB", "Wired", "Controller Adapter", "6.959", "Reflex - Adapt [Saturn 3D 1P]", "reflex adapt saturn 3d 1p", "YES", "TRUE", "2096", "12.503"],
                    ["FeralAI", "GP2040 Encoder", "FeralAI GP2040 Encoder [Wired USB]", "Wired USB", "Wired", "Arcade Stick Encoder", "0.772", "FeralAI GP2040 Encoder [Wired USB]", "feralai gp2040 encoder wired usb", "YES", "FALSE", "", ""],
                    ["FeralAI", "GP2040 Encoder", "FeralAI - GP2040 Encoder", "Wired USB", "Wired", "Arcade Stick Encoder", "0.775", "FeralAI - GP2040 Encoder", "feralai gp2040 encoder", "YES", "TRUE", "10958", "1.28"],
                    ["Timville", "Triple Controller", "Timville - Triple Controller", "Wired USB", "Wired", "Controller Adapter", "0.816", "Timville - Triple Controller", "timville triple controller", "YES", "TRUE", "2611", "1.359"],
                    ["Timville", "Triple Controller", "Timville Triple Controller [Wired USB]", "Wired USB", "Wired", "Controller Adapter", "1.033", "Timville Triple Controller [Wired USB]", "timville triple controller wired usb", "YES", "FALSE", "", ""],
                    ["Mayflash", "F300", "Mayflash - F300 [DInput PS3 FW V1.23]", "Wired USB", "Wired", "Arcade Stick", "1.271", "Mayflash - F300 [DInput PS3 FW V1.23]", "mayflash f300 dinput ps3 fw v1 23", "YES", "TRUE", "8804", "2.16"],
                    ["Mayflash", "Arcade Stick F300 Rev 1.3", "Mayflash Arcade Stick F300 Rev 1.3 [DInput PS3] FW V1.23", "Wired USB", "Wired", "Arcade Stick", "1.27", "Mayflash Arcade Stick F300 Rev 1.3 [DInput PS3] FW V1.23", "mayflash arcade stick f300 rev 1 3 dinput ps3 fw v1 23", "YES", "FALSE", "", ""],
                    ["Mayflash", "Arcade Stick F300 Rev 1.3", "Mayflash Arcade Stick F300 Rev 1.3 [PC] FW pre-V1.23", "Wired USB", "Wired", "Arcade Stick", "14.349", "Mayflash Arcade Stick F300 Rev 1.3 [PC] FW pre-V1.23", "mayflash arcade stick f300 rev 1 3 pc fw pre v1 23", "YES", "FALSE", "", ""],
                    ["Mayflash", "F300", "Mayflash - F300 [Xinput Switch FW V1.23]", "Wired USB", "Wired", "Arcade Stick", "1.405", "Mayflash - F300 [Xinput Switch FW V1.23]", "mayflash f300 xinput switch fw v1 23", "YES", "TRUE", "2393", "2.171"],
                    ["Mayflash", "Arcade Stick F300 Rev 1.3", "Mayflash Arcade Stick F300 Rev 1.3 [Xinput Switch] FW V1.23", "Wired USB", "Wired", "Arcade Stick", "1.4", "Mayflash Arcade Stick F300 Rev 1.3 [Xinput Switch] FW V1.23", "mayflash arcade stick f300 rev 1 3 xinput switch fw v1 23", "YES", "FALSE", "", ""],
                    ["Mayflash", "Wii Classic to USB", "Mayflash - Wii Classic to USB", "Wired USB", "Wired", "Controller Adapter", "4.867", "Mayflash - Wii Classic to USB", "mayflash wii classic to usb", "YES", "TRUE", "2093", "8.972"],
                    ["Hori", "Fighting Commander Wii Classic", "Hori - Fighting Commander Wii Classic [Mayflash]", "Mayflash", "Wired", "Controller", "34.115", "Hori - Fighting Commander Wii Classic [Mayflash]", "hori fighting commander wii classic mayflash", "YES", "TRUE", "2350", "83.285"],
                    ["Hori", "Fighting Commander Wii Classic", "Hori Fighting Commander Wii Classic [MayFlash Wii Classic USB]", "MayFlash Wii Classic USB", "Wireless", "Controller", "34.115", "Hori Fighting Commander Wii Classic [MayFlash Wii Classic USB]", "hori fighting commander wii classic mayflash wii classic usb", "YES", "FALSE", "", ""],
                    ["Hori", "Fighting Commander Wii Classic", "Hori - Fighting Commander Wii Classic [GBro]", "GBro", "Wired", "Controller", "36.071", "Hori - Fighting Commander Wii Classic [GBro]", "hori fighting commander wii classic gbro", "YES", "TRUE", "2370", "86.494"],
                    ["Raphnet", "N64 - 1ms V3.6 - OEM N64", "Raphnet - N64 - 1ms V3.6 - OEM N64", "Wired USB", "Wired", "Controller Adapter", "1.595", "Raphnet - N64 - 1ms V3.6 - OEM N64", "raphnet n64 1ms v3 6 oem n64", "YES", "TRUE", "2223", "2.488"],
                    ["Raphnet", "SNES Controller to USB Adapter", "Raphnet SNES Controller to USB Adapter [Wired USB]", "Wired USB", "Wired", "Controller Adapter", "1.646", "Raphnet SNES Controller to USB Adapter [Wired USB]", "raphnet snes controller to usb adapter wired usb", "YES", "FALSE", "", ""],
                    ["Raphnet", "Dreamcast - 1ms v2.02 - OEM DC", "Raphnet - Dreamcast - 1ms v2.02 - OEM DC", "Wired USB", "Wired", "Controller Adapter", "2.966", "Raphnet - Dreamcast - 1ms v2.02 - OEM DC", "raphnet dreamcast 1ms v2 02 oem dc", "YES", "TRUE", "2050", "4.56"],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit - Tribute64 Wireless [Xinput]", "2.4GHz USB", "Wireless", "Controller", "4.961", "Retro-Bit - Tribute64 Wireless [Xinput]", "retro bit tribute64 wireless xinput", "YES", "TRUE", "2076", "7.308"],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit Tribute64 Wireless [2.4GHz USB Xinput]", "2.4GHz USB", "Wireless", "Controller", "4.96", "Retro-Bit Tribute64 Wireless [2.4GHz USB Xinput]", "retro bit tribute64 wireless 2 4ghz usb xinput", "YES", "FALSE", "", ""],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit - Tribute64 Wireless [Dinput]", "2.4GHz USB", "Wireless", "Controller", "5.008", "Retro-Bit - Tribute64 Wireless [Dinput]", "retro bit tribute64 wireless dinput", "YES", "TRUE", "2092", "7.271"],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit Tribute64 Wireless [2.4GHz USB Dinput]", "2.4GHz USB", "Wireless", "Controller", "5.01", "Retro-Bit Tribute64 Wireless [2.4GHz USB Dinput]", "retro bit tribute64 wireless 2 4ghz usb dinput", "YES", "FALSE", "", ""],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit Tribute64 Wireless [Wireless N64 Reflex Adapt]", "Wireless N64", "Wireless", "Controller Adapter", "6.76", "Retro-Bit Tribute64 Wireless [Wireless N64 Reflex Adapt]", "retro bit tribute64 wireless wireless n64 reflex adapt", "YES", "FALSE", "", ""],
                    ["Retro-Bit", "Tribute64 Wireless", "Retro-Bit - Tribute64 Wireless [Wireless N64]", "Wireless N64", "Wireless", "Controller Adapter", "6.755", "Retro-Bit - Tribute64 Wireless [Wireless N64]", "retro bit tribute64 wireless wireless n64", "YES", "FALSE", "", ""],
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertNotIn("FeralAI - GP2040 Encoder", by_name)

        reflex_variants = by_name["Reflex - Adapt"]["modeVariants"]
        reflex_measurements = [variant["measurementName"] for variant in reflex_variants]
        self.assertIn("Reflex Adapt 3DO [Wired USB Dinput]", reflex_measurements)
        three_do = next(variant for variant in reflex_variants if variant["measurementName"] == "Reflex Adapt 3DO [Wired USB Dinput]")
        self.assertEqual(three_do["deviceTypes"], ["Controller Adapter", "3DO Controller"])
        self.assertIn("Reflex - Adapt [N64 1P]", reflex_measurements)
        self.assertNotIn("Reflex Adapt N64 [Wired USB Dinput]", reflex_measurements)
        self.assertNotIn("Reflex - Adapt [N64 2P]", reflex_measurements)
        self.assertNotIn("Reflex - Adapt [N64 1P MPG HID]", reflex_measurements)
        self.assertNotIn("Reflex - Adapt [N64 1P MPG Xinput]", reflex_measurements)
        self.assertNotIn("Reflex - Adapt [N64 1P MPG Switch]", reflex_measurements)
        saturn_3d = next(variant for variant in reflex_variants if variant["measurementName"] == "Reflex - Adapt [Saturn 3D 1P]")
        self.assertEqual(saturn_3d["deviceTypes"], ["Controller Adapter", "Saturn 3D Controller"])

        timville = by_name["Timville - Triple Controller"]
        self.assertEqual(timville["averageMs"], 0.816)
        self.assertEqual(timville["modeVariantCount"], 1)
        self.assertTrue(timville["modeVariants"][0]["hasRawCapture"])

        f300 = by_name["Mayflash - F300"]
        self.assertEqual(f300["modeVariantCount"], 2)
        self.assertEqual([variant["measurementName"] for variant in f300["modeVariants"]], [
            "Mayflash - F300 [DInput PS3 FW V1.23]",
            "Mayflash - F300 [Xinput Switch FW V1.23]",
        ])

        hori = by_name["Hori - Fighting Commander Wii Classic"]
        self.assertEqual(hori["modeVariantCount"], 1)
        self.assertEqual(hori["averageMs"], 29.248)
        self.assertEqual(hori["measuredAverageMs"], 34.115)
        self.assertEqual(hori["adapterAverageMs"], 4.867)
        self.assertEqual(hori["adapterSourceName"], "Mayflash - Wii Classic to USB")

        raphnet = by_name["Raphnet - Controller Adapter"]
        self.assertEqual(raphnet["modeVariantCount"], 3)

        tribute64 = by_name["Retro-Bit - Tribute64 Wireless"]
        self.assertEqual(tribute64["modeVariantCount"], 3)
        self.assertEqual(
            [variant["measurementName"] for variant in tribute64["modeVariants"]],
            [
                "Retro-Bit - Tribute64 Wireless [Xinput]",
                "Retro-Bit - Tribute64 Wireless [Dinput]",
                "Retro-Bit - Tribute64 Wireless [Wireless N64]",
            ],
        )

    def test_gamescare_arcade_encoder_duplicates_keep_only_canonical_large_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    [
                        "Make", "Model", "Device", "Connection", "Wired/Wireless", "Category",
                        "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results", "HasRawCapture",
                    ],
                    ["Games", "Care Multi Console Arcade (Small)", "Games - Care Multi Console Arcade (Small)", "Wired USB", "Wired", "Controller", "0.730", "Games - Care Multi Console Arcade (Small)", "games care multi console arcade small", "YES", "TRUE"],
                    ["Games", "Care Multi Console Arcade (Large)", "Games - Care Multi Console Arcade (Large)", "Wired USB", "Wired", "Arcade Stick", "0.739", "Games - Care Multi Console Arcade (Large)", "games care multi console arcade large", "YES", "TRUE"],
                    ["GamesCare", "Multi Console Arcade Stick (Large)", "GamesCare Multi Console Arcade Stick (Large) [Wired USB]", "Wired USB", "Wired", "Arcade Stick Encoder", "0.739", "GamesCare Multi Console Arcade Stick (Large) [Wired USB]", "gamescare multi console arcade stick large wired usb", "YES", "FALSE"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        gamescare_items = [item for item in payload["items"] if "games" in item["name"].lower()]
        self.assertEqual([item["name"] for item in gamescare_items], ["GamesCare - Multi Console Arcade Stick (Large)"])
        self.assertEqual(gamescare_items[0]["measurementName"], "GamesCare Multi Console Arcade Stick (Large) [Wired USB]")

    def test_curated_duplicate_families_follow_physical_device_mode_standard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"

            def result(make, model, device, connection, wireless, average, raw, category="Controller"):
                return [
                    make, model, device, connection, wireless, category, str(average),
                    device, latency.normalize_device_name(device), "YES", "TRUE" if raw else "FALSE",
                ]

            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    [
                        "Make", "Model", "Device", "Connection", "Wired/Wireless", "Category",
                        "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results", "HasRawCapture",
                    ],
                    result("8BitDo", "G Bros", "8BitDo G Bros [Wii Classic Controller]", "Wii Classic Controller", "Wireless", 6.268, False, "Controller Adapter"),
                    result("8BitDo", "GBros", "8BitDo - GBros", "Wired USB", "Wired", 6.268, True, "Controller Adapter"),
                    result("8BitDo", "M30 for Xbox", "8BitDo M30 for Xbox [Wired USB]", "Wired USB", "Wired", 4.540, False),
                    result("8BitDo", "M30 Wired Controller for Xbox", "8BitDo - M30 Wired Controller for Xbox", "Wired USB", "Wired", 4.535, True),
                    result("8BitDo", "NEOGEO Wireless Controller", "8BitDo NEOGEO Wireless Controller [Wired USB] FW 1.09", "Wired USB", "Wired", 6.098, False),
                    result("8BitDo", "NeoGeo USB fw1.09", "8BitDo - NeoGeo USB fw1.09", "Wired USB", "Wired", 6.098, True),
                    result("8BitDo", "NEOGEO Wireless Controller", "8BitDo NEOGEO Wireless Controller [2.4GHz USB] FW 1.09", "2.4GHz USB", "Wireless", 4.514, False),
                    result("8BitDo", "NeoGeo 2.4G fw1.09", "8BitDo - NeoGeo 2.4G fw1.09", "2.4GHz Wireless", "Wireless", 4.514, True),
                    result("8BitDo", "NEOGEO Wireless Controller", "8BitDo NEOGEO Wireless Controller [BT] FW 1.09", "Bluetooth", "Wireless", 9.750, False),
                    result("8BitDo", "NeoGeo BT fw1.09", "8BitDo - NeoGeo BT fw1.09", "Bluetooth", "Wireless", 9.750, True),
                    result("8BitDo", "Ultimate 2C Wireless Controller (Model 81HD)", "8BitDo Ultimate 2C Wireless Controller (Model 81HD) [Wired USB]", "Wired USB", "Wired", 5.006, False),
                    result("8BitDo", "Ultimate 2C Wireless Controller 81HD", "8BitDo - Ultimate 2C Wireless Controller 81HD [Wired USB]", "Wired USB", "Wired", 5.006, False),
                    result("8BitDo", "Ultimate 2C Wireless Controller (Model 81HD)", "8BitDo Ultimate 2C Wireless Controller (Model 81HD) [2.4G]", "2.4GHz USB", "Wireless", 5.610, False),
                    result("8BitDo", "Ultimate 2C Wireless Controller 81HD", "8BitDo - Ultimate 2C Wireless Controller 81HD [Wireless 2.4G]", "2.4GHz Wireless", "Wireless", 5.610, False),
                    result("8BitDo", "Ultimate 2C Wireless Controller (Model 81HD)", "8BitDo Ultimate 2C Wireless Controller (Model 81HD) [BT]", "Bluetooth", "Wireless", 13.394, False),
                    result("8BitDo", "Ultimate 2C Wireless Controller 81HD", "8BitDo - Ultimate 2C Wireless Controller 81HD [Wireless BT]", "Bluetooth", "Wireless", 13.394, False),
                    result("FlyDigi", "Vader 2", "FlyDigi Vader 2 [BT Low Energy]", "BT Low Energy", "Wireless", 17.074, False),
                    result("FlyDigi", "VADER2 Classic Mode", "FlyDigi - VADER2 Classic Mode [Edimax BLE]", "Edimax BLE", "Wireless", 17.074, True),
                    result("FlyDigi", "Vader 2", "FlyDigi Vader 2 [BT CSR8510]", "BT CSR8510", "Wireless", 17.802, False),
                    result("FlyDigi", "VADER2 Classic Mode", "FlyDigi - VADER2 Classic Mode [CSR 4.0]", "CSR 4.0", "Wireless", 17.802, True),
                    result("JAMMIX", "JAMMIX", "JAMMIX JAMMIX [Wired USB]", "Wired USB", "Wired", 2.377, False, "Arcade Stick Encoder"),
                    result("", "", "JAMMIX", "Wired USB", "Wired", 2.381, True, "Arcade Stick Encoder"),
                    result("Mcbazel", "PlayStation 2 Controller to USB Adapter for PC", "Mcbazel PlayStation 2 Controller to USB Adapter for PC [Wired USB]", "Wired USB", "Wired", 11.265, False, "Controller Adapter"),
                    result("Mcbazel", "PlayStation 2 Controller to USB Adapter for PC or Playstation 3 Converter Cable", "Mcbazel - PlayStation 2 Controller to USB Adapter for PC or Playstation 3 Converter Cable", "Wired USB", "Wired", 11.265, True, "Controller Adapter"),
                    result("Generic", "PS2 Controller to USB Adapter Converter Cable", "Generic PS2 Controller to USB Adapter Converter Cable [Wired USB]", "Wired USB", "Wired", 10.589, False, "Controller Adapter"),
                    result("PS2", "Controller to USB Adapter Converter Cable", "PS2 - Controller to USB Adapter Converter Cable", "Wired USB", "Wired", 10.589, True, "Controller Adapter"),
                    result("Sony", "DualSense (Playstation 5)", "Sony DualSense (Playstation 5) [Wired USB]", "Wired USB", "Wired", 1.809, False),
                    result("Sony", "DualSense (Playstation 5)", "Sony DualSense (Playstation 5) [BT CSR8510]", "Bluetooth CSR8510", "Wireless", 6.322, False),
                    result("Sony", "Dual Sense Wired", "Sony - Dual Sense Wired", "Wired USB", "Wired", 1.809, True),
                    result("Sony", "Dual Sense", "Sony - Dual Sense [BT4.2]", "Bluetooth 4.2", "Wireless", 4.786, True),
                    result("Retro Fighters", "Brawler 64 NSO Edition", "Retro Fighters Brawler 64 NSO Edition [Wired USB Dinput]", "Wired USB", "Wired", 4.510, False),
                    result("RetroFighters", "Brawler64", "RetroFighters - Brawler64 [Dinput]", "Wired USB", "Wired", 4.508, True),
                    result("atrac17", "Spinner", "atrac17 - Spinner", "Wired USB", "Wired", 0.747, True, "Arcade Stick Encoder"),
                    result("atrac17 + DJHardRich", "RP2040 LS-30 Rotary Encoder", "atrac17 + DJHardRich RP2040 LS-30 Rotary Encoder [Wired USB]", "Wired USB", "Wired", 0.747, False, "Arcade Stick Encoder"),
                    result("Finera", "USB 2.0 Games Controller Adapter Converter Cable", "Finera - USB 2.0 Games Controller Adapter Converter Cable", "Wired USB", "Wired", 9.107, True, "Controller Adapter"),
                    result("Finiera", "USB 2.0 Games Controller Adapter Converter Cable", "Finiera USB 2.0 Games Controller Adapter Converter Cable [Wired USB]", "Wired USB", "Wired", 9.107, False, "Controller Adapter"),
                    result("Gravis", "Gamepad", "Gravis - Gamepad", "Wired USB", "Wired", 11.813, True),
                    result("Gravis", "GamePad Pro", "Gravis GamePad Pro [Wired USB]", "Wired USB", "Wired", 11.813, False),
                    result("Sega", "Astro City Pad", "Sega - Astro City Pad", "Wired USB", "Wired", 5.037, True),
                    result("Sega", "Astro City Mini Controller (ACS-1002)", "Sega Astro City Mini Controller (ACS-1002) [Wired USB]", "Wired USB", "Wired", 5.037, False),
                    result("Sega", "Astro City Stick", "Sega - Astro City Stick", "Wired USB", "Wired", 5.013, True, "Arcade Stick"),
                    result("Sega", "Astro City Mini Real Arcade Stick", "Sega Astro City Mini Real Arcade Stick [Wired USB]", "Wired USB", "Wired", 5.013, False, "Arcade Stick"),
                    result("Mayflash", "Wii Classic to USB", "Mayflash - Wii Classic to USB", "Wired USB", "Wired", 4.867, True, "Controller Adapter"),
                    result("Mayflash", "Wii Classic Controller Adapter For PC", "Mayflash Wii Classic Controller Adapter For PC [Wired USB]", "Wired USB", "Wired", 4.852, False, "Controller Adapter"),
                ],
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=None)

        by_name = {item["name"]: item for item in payload["items"]}
        expected_variants = {
            "8BitDo - GBros": 1,
            "8BitDo - M30 for Xbox": 1,
            "8BitDo - NEOGEO Wireless Controller": 3,
            "8BitDo - Ultimate 2C Wireless Controller (Model 81HD)": 3,
            "FlyDigi - Vader 2": 2,
            "JAMMIX - JAMMIX": 1,
            "Mcbazel - PlayStation 2 Controller to USB Adapter for PC": 1,
            "Generic - PS2 Controller to USB Adapter Converter Cable": 1,
            "Sony - DualSense (PlayStation 5)": 3,
        }
        for name, variant_count in expected_variants.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["modeVariantCount"], variant_count)

        self.assertIn("Retro Fighters - Brawler 64 NSO Edition", by_name)
        self.assertIn("Retro Fighters - Brawler64", by_name)
        self.assertIn("RP2040 LS-30 rotary encoder", by_name)
        ls30 = by_name["RP2040 LS-30 rotary encoder"]
        self.assertTrue(ls30["isOpenSource"])
        self.assertEqual(ls30["sourceStatus"], "Open Source")
        self.assertEqual(
            ls30["sourceUrl"],
            "https://github.com/va7deo/SNK68/tree/main/dev/rp2040",
        )
        self.assertIn("Finera - USB 2.0 Games Controller Adapter Converter Cable", by_name)
        self.assertIn("Gravis - GamePad Pro", by_name)
        self.assertIn("Sega - Astro City Mini Controller (ACS-1002)", by_name)
        self.assertIn("Sega - Astro City Mini Real Arcade Stick", by_name)
        self.assertIn("Mayflash - Wii Classic Controller Adapter For PC", by_name)

        hidden_names = {
            "atrac17 - Spinner",
            "Finiera - USB 2.0 Games Controller Adapter Converter Cable",
            "Gravis - Gamepad",
            "Sega - Astro City Pad",
            "Sega - Astro City Stick",
            "Mayflash - Wii Classic to USB",
        }
        self.assertTrue(hidden_names.isdisjoint(by_name))

    def test_reflex_adapt_generations_stay_separate_and_each_consolidates_modes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Category", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Reflex", "Adapt Neo Geo", "Reflex Adapt Neo Geo [Wired USB Dinput]", "Wired USB", "Wired", "Controller Adapter", "0.77", "Reflex Adapt Neo Geo [Wired USB Dinput]", "reflex adapt neo geo wired usb dinput", "YES"],
                    ["Reflex", "Adapt SNES", "Reflex Adapt SNES [Wired USB Dinput]", "Wired USB", "Wired", "Controller Adapter", "1.48", "Reflex Adapt SNES [Wired USB Dinput]", "reflex adapt snes wired usb dinput", "YES"],
                    ["Reflex", "Adapt N64", "Reflex Adapt N64 [Wired USB Dinput]", "Wired USB", "Wired", "Controller Adapter", "2.95", "Reflex Adapt N64 [Wired USB Dinput]", "reflex adapt n64 wired usb dinput", "YES"],
                    ["Reflex", "Adapt Classic2USB", "Reflex Adapt Classic2USB [Neo-Geo]", "Wired USB", "Wired", "Controller Adapter", "0.766", "Reflex Adapt Classic2USB [Neo-Geo]", "reflex adapt classic2usb neo geo", "YES"],
                    ["Reflex", "Adapt Classic2USB", "Reflex Adapt Classic2USB [GameCube]", "Wired USB", "Wired", "Controller Adapter", "1.604", "Reflex Adapt Classic2USB [GameCube]", "reflex adapt classic2usb gamecube", "YES"],
                    ["AliExpress", "Gamecube Wireless", "AliExpress Gamecube Wireless [2.4GHz via Reflex Adapt]", "2.4GHz Wireless", "Wireless", "Controller", "14.96", "AliExpress Gamecube Wireless [2.4GHz via Reflex Adapt]", "aliexpress gamecube wireless 2 4ghz via reflex adapt", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertEqual(payload["summary"]["totalItems"], 3)
        self.assertIn("Reflex - Adapt", by_name)
        self.assertIn("Reflex - Adapt Classic2USB", by_name)
        self.assertTrue(any(name.startswith("AliExpress") and "Gamecube Wireless" in name for name in by_name))
        self.assertNotIn("Reflex - Adapt SNES", by_name)
        self.assertNotIn("Reflex - Adapt N64", by_name)
        self.assertEqual(by_name["Reflex - Adapt"]["modeVariantCount"], 3)
        self.assertEqual(by_name["Reflex - Adapt"]["averageMs"], 0.77)
        self.assertIn("adapt snes", by_name["Reflex - Adapt"]["searchText"])
        self.assertEqual(by_name["Reflex - Adapt Classic2USB"]["modeVariantCount"], 2)
        self.assertEqual(by_name["Reflex - Adapt Classic2USB"]["averageMs"], 0.766)
        self.assertNotEqual(
            by_name["Reflex - Adapt"]["controllerGroupKey"],
            by_name["Reflex - Adapt Classic2USB"]["controllerGroupKey"],
        )

    def test_write_payload_can_mirror_shopify_data_asset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "docs" / "data" / "latency.json"
            shopify_output = root / "shopify" / "assets" / "input-latency-data.js"
            payload = {"generatedAt": "2026-07-18T00:00:00Z", "items": []}

            latency.write_payload(payload, output, shopify_data_output=shopify_output)

            self.assertEqual(output.with_suffix(".js").read_bytes(), shopify_output.read_bytes())

    def test_private_source_is_optional(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Latency (in ms)", "Valid Results"],
                    ["Test Pad", "test pad", "4.2", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        self.assertEqual(payload["summary"]["totalItems"], 1)
        self.assertFalse(payload["sources"]["private"]["available"])

    def test_default_payload_does_not_include_private_unreleased_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Latency (in ms)", "Valid Results"],
                    ["Public Pad", "public pad", "4.2", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root)

        self.assertEqual(payload["summary"]["totalItems"], 1)
        self.assertEqual(payload["summary"]["privateItems"], 0)
        self.assertFalse(payload["sources"]["private"]["available"])
        self.assertEqual([item["name"] for item in payload["items"]], ["Public Pad"])

    def test_same_frame_is_average_implied_with_observed_value_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            private_root = root / "input-latency-private"

            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Latency (in ms)", "PctOnTime", "Valid Results"],
                    ["Average Only Pad", "average only pad", "5", "99", "YES"],
                ],
            )
            self.write_csv(
                private_root / "captures" / "unreleased.csv",
                [
                    [
                        "",
                        "Device",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "Number of Samples",
                        "Same Frame Probability",
                        "Average",
                        "Maximum",
                        "Minimum",
                        "Standard Deviation",
                        "Valid Results",
                        "Joystick ID",
                        "Notes",
                        "Tester",
                        "Date Added",
                        "Category",
                        "Original Controller System",
                        "Face Buttons",
                        "Weight (oz)",
                        "'Feel (0-10)'",
                        "Feel Notes",
                        "99%",
                        "Average Tier",
                        "99% Tier",
                        "Result Type",
                    ],
                    [
                        "1",
                        "Raw Capture Pad",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "1000",
                        "0.99",
                        "10",
                        "11",
                        "9",
                        "0.2",
                        "YES",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "11",
                        "Gold",
                        "Gold",
                        "unreleased",
                    ],
                ],
            )

            payload = latency.build_latency_payload(public_root, private_root)

        by_id = {item["id"]: item for item in payload["items"]}
        public_item = by_id["published-average-only-pad"]
        raw_item = by_id["unreleased-raw-capture-pad"]

        self.assertEqual(public_item["sameFramePct"], 70.0)
        self.assertEqual(public_item["observedSameFramePct"], 99.0)
        self.assertEqual(raw_item["sameFramePct"], 40.0)
        self.assertEqual(raw_item["observedSameFramePct"], 99.0)
        self.assertEqual(raw_item["sameFrameSource"], "Average-implied")
        self.assertEqual(payload["summary"]["medianSameFramePct"], 55.0)

    def test_sheet_columns_add_category_face_buttons_home_button_and_weight(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Latency (in ms)", "Category", "DeviceClean", "DeviceNorm", "Valid Results"],
                    ["Acme", "Pad", "Acme Pad", "Wired USB", "Wired", "1.1", "Unknown", "Acme Pad", "acme pad", "YES"],
                ],
            )
            headers = [""] * 58
            headers[0] = "Make"
            headers[1] = "Model"
            headers[2] = "Device"
            headers[39] = "Home Button"
            headers[49] = "VID:PID"
            headers[52] = "Date Added"
            headers[53] = "Category"
            headers[54] = "Face Buttons"
            headers[55] = "Weight (oz)"
            row = [""] * 58
            row[0] = "Acme"
            row[1] = "Pad"
            row[2] = "Acme Pad"
            row[39] = "Yes"
            row[49] = "045e:03ea"
            row[52] = "6/8/2026"
            row[53] = "Controller"
            row[54] = "6.0"
            row[55] = "8.5"
            sheet_rows = latency.read_sheet_rows_from_text(
                ",".join(headers) + "\n" + ",".join(row) + "\n"
            )

            payload = latency.build_latency_payload(public_root, None, sheet_rows=sheet_rows)

        item = payload["items"][0]
        self.assertEqual(item["category"], "Controller")
        self.assertEqual(item["faceButtons"], "6")
        self.assertEqual(item["homeButton"], "Yes")
        self.assertEqual(item["joystickId"], "045e:03ea")
        self.assertEqual(item["weightOz"], "8.5")
        self.assertEqual(item["dateAddedSort"], "2026-06-08")

    def test_connection_capture_suffixes_are_removed_from_display_titles(self):
        self.assertEqual(
            latency.sanitize_display_name("Microsoft Wireless Controller [BT+AC600 Driver Free]"),
            "Microsoft Wireless Controller",
        )
        self.assertEqual(
            latency.sanitize_display_name("Controller Name [BT (CSR8510)]"),
            "Controller Name",
        )

    def test_public_make_model_titles_use_hyphenated_display_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "Device", "Connection", "Wired/Wireless", "Mode", "Latency (in ms)", "DeviceClean", "DeviceNorm", "Valid Results", "Category"],
                    ["Qanba", "Drone 2", "Qanba Drone 2 [PC]", "", "Unknown", "PC", "11.961", "Qanba Drone 2 [PC]", "qanba drone 2 pc", "YES", "Arcade Stick"],
                    ["Buffalo", "iBuffalo Classic", "Buffalo iBuffalo Classic [Wired USB]", "Wired USB", "Wired", "Wired USB", "0.69", "Buffalo iBuffalo Classic [Wired USB]", "buffalo ibuffalo classic wired usb", "YES", "Controller"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_model = {item["model"]: item for item in payload["items"]}
        self.assertEqual(by_model["Drone 2"]["name"], "Qanba - Drone 2")
        self.assertEqual(by_model["iBuffalo Classic"]["name"], "Buffalo - iBuffalo Classic")
        self.assertNotIn("Qanba Drone 2", {item["name"] for item in payload["items"]})

    def test_brand_only_controller_names_get_controller_category(self):
        for name in (
            "8BitDo Ultimate Wireless (80NA)",
            "Gullikit King Kong2",
            "Nintendo Switch Online Genesis [BT]",
            "AliExpress Gamecube Wireless",
            "RetroFighters Brawler64",
        ):
            self.assertEqual(latency.fallback_category_for_name(name), "Controller")

    def test_family_overrides_apply_sale_source_names_and_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "Category", "Latency (in ms)", "Valid Results"],
                    ["DaemonBite - Genesis to USB Adapter", "daemonbite genesis to usb adapter", "Genesis 3 Button Controller", "Wired", "Controller Adapter", "0.75", "YES"],
                    ["Reflex Adapt [Neo Geo]", "reflex adapt neo geo", "Wired USB", "Wired", "Controller Adapter", "0.77", "YES"],
                    ["raphnet - N64 - 1ms V3.6 - OEM N64", "raphnet n64 1ms v3 6 oem n64", "", "Unknown", "Controller Adapter", "1.59", "YES"],
                    ["Reflex Encode Fightboard V1", "reflex encode fightboard v1", "Wired USB", "Wired", "Arcade Stick Encoder", "0.82", "YES"],
                    ["Reflex CTRL SNES [Dinput]", "reflex ctrl snes dinput", "Wired USB", "Wired", "Controller Conversion", "0.84", "YES"],
                    ["Ultimarc - I-PAC", "ultimarc i pac", "Wired USB", "Wired", "Arcade Stick Encoder", "1.0", "YES"],
                    ["Ultimarc - I-PAC Ultimate", "ultimarc i pac ultimate", "Wired USB", "Wired", "Arcade Stick Encoder", "1.2", "YES"],
                    ["bootsector - LLOAD", "bootsector lload", "Wired USB", "Wired", "Controller Conversion", "1.4", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertEqual(by_name["DaemonBite - Controller Adapter"]["saleStatus"], "Discontinued")
        self.assertEqual(by_name["Reflex - Adapt"]["saleStatus"], "Actively sold")
        self.assertEqual(by_name["Reflex - Adapt"]["buyUrl"], "https://misteraddons.com/products/reflex-adapt")
        self.assertEqual(by_name["Raphnet - Controller Adapter"]["saleStatus"], "Actively sold")
        self.assertIn("raphnet-tech.com/products.php?category=Adapters", by_name["Raphnet - Controller Adapter"]["buyUrl"])
        self.assertTrue(by_name["Raphnet - Controller Adapter"]["isOpenSource"])
        self.assertIn("Reflex Encode Fightboard (GP2040-CE)", by_name)
        self.assertNotIn("Reflex Encode Fightboard V1", by_name)
        self.assertTrue(by_name["Reflex Encode Fightboard (GP2040-CE)"]["isOpenSource"])
        self.assertEqual(by_name["Reflex CTRL"]["saleStatus"], "Actively sold")
        self.assertEqual(by_name["Reflex CTRL"]["buyUrl"], "https://misteraddons.com/products/reflex-ctrl")
        self.assertEqual(by_name["Ultimarc - I-PAC"]["saleStatus"], "Actively sold")
        self.assertIn("ultimarc.com/control-interfaces/i-pacs", by_name["Ultimarc - I-PAC"]["buyUrl"])
        self.assertEqual(by_name["Ultimarc - I-PAC Ultimate"]["saleStatus"], "Actively sold")
        self.assertIn("i-pac-ultimate-i-o", by_name["Ultimarc - I-PAC Ultimate"]["buyUrl"])
        self.assertEqual(by_name["bootsector - LLOAD"]["saleStatus"], "Discontinued")

    def test_mode_display_keeps_adapter_inputs_but_simplifies_usb_conversions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "DeviceNorm", "Connection", "Wired/Wireless", "Mode", "Category", "Latency (in ms)", "Valid Results"],
                    ["RetroUSB - RetroKit SNES", "retrousb retrokit snes", "Wired USB", "Wired", "", "Controller Adapter", "2.26", "YES"],
                    ["BlissBox - BlisSTer v2 [Non-LLAPI]", "blissbox blisster v2 non llapi", "NES OEM via Bliss Adapter", "Wired", "Non-LLAPI", "Controller Adapter", "4.10", "YES"],
                    ["raphnet - N64 - 1ms V3.6 - OEM N64", "raphnet n64 1ms v3 6 oem n64", "", "Unknown", "", "Controller Adapter", "1.59", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        by_name = {item["name"]: item for item in payload["items"]}
        self.assertEqual(by_name["RetroUSB - RetroKit SNES"]["category"], "Controller Conversion")
        self.assertEqual(by_name["RetroUSB - RetroKit SNES"]["modeDisplay"], "USB")
        self.assertEqual(by_name["RetroUSB - RetroKit SNES"]["outputMode"], "DInput")
        self.assertEqual(by_name["BlissBox - BlisSTer v2"]["modeDisplay"], "USB")
        self.assertEqual(by_name["Raphnet - Controller Adapter"]["modeDisplay"], "N64 Controller")
        self.assertEqual(
            latency.inferred_output_mode_for_item({"category": "Controller", "connection": "Wired USB"}),
            "DInput",
        )

    def test_connection_tags_split_bluetooth_and_2_4ghz_wireless(self):
        self.assertEqual(
            latency.connection_tag_for_values("", "BT", "Wireless", "Bluetooth"),
            "Wireless BT",
        )
        self.assertEqual(
            latency.connection_tag_for_values("", "Wireless USB Dongle", "Wireless", "2.4GHz"),
            "Wireless 2.4GHz",
        )
        self.assertEqual(
            latency.connection_tag_for_values("", "Wired USB", "Wired", ""),
            "Wired",
        )

    def test_title_metadata_handles_compact_vid_pid_suffixes(self):
        metadata = latency.parse_controller_title_metadata("Google Stadia [BT] 18d19400")

        self.assertEqual(metadata["name"], "Google Stadia")
        self.assertEqual(metadata["modeRaw"], "BT")
        self.assertEqual(metadata["joystickId"], "18d1:9400")
        self.assertEqual(metadata["connectionTag"], "Wireless BT")

    def test_explicit_wired_mode_overrides_wireless_model_name(self):
        metadata = latency.parse_controller_title_metadata(
            "8BitDo Ultimate 2.4G Wireless (81HA) [Wired Direct Input]"
        )

        self.assertEqual(metadata["name"], "8BitDo Ultimate 2.4G Wireless (81HA)")
        self.assertEqual(metadata["modeRaw"], "Wired Direct Input")
        self.assertEqual(metadata["connectionTag"], "Wired")

    def test_write_outputs_json_and_inline_js(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "site" / "data" / "latency.json"
            payload = {"generatedAt": "2026-06-06T00:00:00Z", "summary": {}, "items": []}

            latency.write_payload(payload, output)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), payload)
            inline = output.with_suffix(".js").read_text(encoding="utf-8")
            self.assertTrue(inline.startswith("window.MISTER_LATENCY_DATA = "))
            self.assertIn('"generatedAt": "2026-06-06T00:00:00Z"', inline)

    def test_mode_variant_ids_are_unique_when_a_model_name_ends_in_two(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["Make", "Model", "DeviceClean", "Connection", "Wired/Wireless", "Latency (in ms)", "Valid Results"],
                    ["Qanba", "Drone", "Qanba Drone [Wired USB PS3]", "Wired USB", "Wired", "3.25", "YES"],
                    ["Qanba", "Drone", "Qanba Drone [Wired USB PS4]", "Wired USB", "Wired", "3.265", "YES"],
                    ["Qanba", "Drone 2", "Qanba Drone 2 [Wired USB PS4]", "Wired USB", "Wired", "11.6", "YES"],
                ],
            )

            payload = latency.build_latency_payload(public_root, None)

        variant_ids = [
            variant["id"]
            for item in payload["items"]
            for variant in item["modeVariants"]
        ]
        self.assertEqual(len(variant_ids), len(set(variant_ids)))

    def test_main_does_not_write_degraded_output_when_sheet_fetch_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_root = root / "inputlatency"
            output = root / "latency.json"
            self.write_csv(
                public_root / "results" / "latency_cleaned_export.csv",
                [
                    ["DeviceClean", "Connection", "Wired/Wireless", "Latency (in ms)", "Valid Results"],
                    ["Example Pad", "Wired USB", "Wired", "1.0", "YES"],
                ],
            )
            argv = [
                "build_latency_catalog.py",
                "--public-root",
                str(public_root),
                "--output",
                str(output),
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                latency,
                "read_sheet_rows_from_url",
                side_effect=OSError("offline"),
            ):
                with self.assertRaises(SystemExit):
                    latency.main()

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
