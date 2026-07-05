#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_ROOT = REPO_ROOT
DEFAULT_PRIVATE_ROOT = REPO_ROOT.parent / "input-latency-private"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "data" / "latency.json"
DEFAULT_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1KlRObr3Be4zLch7Zyqg6qCJzGuhyGmXaOIUrpfncXIM/export?format=csv&gid=0"
SHEET_DATE_ADDED_BA_INDEX = 52
SHEET_DATE_ADDED_BA_KEY = "_sheetDateAddedBA"
SHEET_CATEGORY_BB_INDEX = 53
SHEET_CATEGORY_BB_KEY = "_sheetCategoryBB"
SHEET_FACE_BUTTONS_BC_INDEX = 54
SHEET_FACE_BUTTONS_BC_KEY = "_sheetFaceButtonsBC"
SHEET_WEIGHT_BD_INDEX = 55
SHEET_WEIGHT_BD_KEY = "_sheetWeightBD"
SHEET_JOYSTICK_ID_AX_INDEX = 49
SHEET_JOYSTICK_ID_AX_KEY = "_sheetJoystickIdAX"
SHEET_HOME_BUTTON_AN_INDEX = 39
SHEET_HOME_BUTTON_AN_KEY = "_sheetHomeButtonAN"

PUBLIC_CSV = "results/latency_cleaned_export.csv"
PRIVATE_CSVS = (
    ("unreleased", "captures/unreleased.csv"),
)
PRIVATE_COLUMNS = {
    "device": 1,
    "sample_count": 15,
    "same_frame": 16,
    "average": 17,
    "maximum": 18,
    "minimum": 19,
    "sd": 20,
    "valid": 21,
    "joystick_id": 22,
    "notes": 23,
    "tester": 24,
    "date_added": 25,
    "category": 26,
    "original_system": 27,
    "face_buttons": 28,
    "weight_oz": 29,
    "feel": 30,
    "feel_notes": 31,
    "p99": 32,
    "average_tier": 33,
    "p99_tier": 34,
    "result_type": 35,
}
MODE_VARIANT_FIELDS = (
    "id",
    "name",
    "measurementName",
    "averageMs",
    "averageTier",
    "p99Ms",
    "p99Tier",
    "sameFramePct",
    "observedSameFramePct",
    "sampleCount",
    "measuredAverageMs",
    "adapterAverageMs",
    "adapterMode",
    "adapterSourceName",
    "connection",
    "connectionKind",
    "wirelessConnection",
    "connectionTag",
    "modeRaw",
    "outputMode",
    "modeLabel",
    "modeDisplay",
    "deviceTypes",
    "rankMode",
    "overallRank",
    "modeRank",
    "resultType",
    "resultLabel",
    "category",
    "faceButtons",
    "homeButton",
    "weightOz",
    "dateAdded",
    "dateAddedSort",
    "hasRawCapture",
    "metricSource",
    "notes",
    "tester",
    "originalSystem",
    "saleStatus",
    "sourceStatus",
    "isOpenSource",
    "sourceUrl",
    "buyUrl",
    "link",
    "amazon",
    "joystickId",
    "searchText",
)
SAME_FRAME_WINDOW_MS = 100 / 6
TWO_FRAME_WINDOW_MS = SAME_FRAME_WINDOW_MS * 2
AVERAGE_TIER_THRESHOLDS = (
    ("Diamond", 1),
    ("Platinum", 2),
    ("Gold", 5),
    ("Silver", 10),
    ("Bronze", SAME_FRAME_WINDOW_MS),
    ("Copper", TWO_FRAME_WINDOW_MS),
)
P99_TIER_THRESHOLDS = (
    ("Diamond", 1),
    ("Platinum", 2),
    ("Gold", 5),
    ("Silver", 10),
    ("Bronze", SAME_FRAME_WINDOW_MS),
    ("Copper", TWO_FRAME_WINDOW_MS),
)
SALE_STATUS_ORDER = (
    "Actively sold",
    "Discontinued",
    "Unknown",
)
SOURCE_STATUS_ORDER = (
    "Open Source",
    "Closed Source",
)
DEVICE_TYPE_ORDER = (
    "Wired Controller",
    "Wireless Controller",
    "Controller",
    "Controller Adapter",
    "Genesis Controller",
    "NES Controller",
    "SNES Controller",
    "N64 Controller",
    "GameCube Controller",
    "PC Engine Controller",
    "Saturn Controller",
    "Neo Geo Controller",
    "PSX Controller",
    "SMS Controller",
    "Jaguar Controller",
    "Virtual Boy Controller",
    "Wii Classic Controller",
    "Controller Conversion",
    "Wired Arcade Stick",
    "Wireless Arcade Stick",
    "Arcade Stick",
    "Arcade Stick Encoder",
    "Joystick",
    "Joystick Encoder",
    "Supergun",
    "Unknown",
    "Uncategorized",
    "PC",
    "MiSTer",
    "Mac",
    "Android",
    "iOS",
    "Mobile",
    "Switch",
    "Switch 2",
    "PS3",
    "PS4",
    "PS5",
    "Xbox 360",
    "Xbox One",
    "Xbox Series X",
    "Astro City Mini",
    "Genesis",
    "Genesis Mini",
    "NES Classic",
    "SNES",
    "SNES Classic",
    "N64",
    "Neo Geo Mini",
    "PlayStation Classic",
    "Saturn",
    "TurboGrafx-16 Mini",
    "Wii Classic",
    "Wii U",
)
SHEET_DEVICE_TYPE_COLUMNS = (
    ("MiSTer / PC", ("MiSTer", "PC")),
    ("Astro City Mini", ("Astro City Mini",)),
    ("Android", ("Android",)),
    ("iOS", ("iOS",)),
    ("Switch", ("Switch",)),
    ("Switch 2", ("Switch 2",)),
    ("Mobile", ("Mobile",)),
    ("SNES", ("SNES",)),
    ("N64", ("N64",)),
    ("Neo Geo Mini", ("Neo Geo Mini",)),
    ("NES Classic", ("NES Classic",)),
    ("SNES Classic", ("SNES Classic",)),
    ("Wii Classic", ("Wii Classic",)),
    ("TurboGrafx-16 Mini", ("TurboGrafx-16 Mini",)),
    ("Playstation Clasisic", ("PlayStation Classic",)),
    ("PlayStation Classic", ("PlayStation Classic",)),
    ("Genesis Mini", ("Genesis Mini",)),
    ("Genesis", ("Genesis",)),
    ("Saturn", ("Saturn",)),
    ("MacOS", ("Mac",)),
    ("Mac", ("Mac",)),
    ("Wii U", ("Wii U",)),
    ("PS3", ("PS3",)),
    ("PS4", ("PS4",)),
    ("PS5", ("PS5",)),
    ("Xbox 360", ("Xbox 360",)),
    ("Xbox One", ("Xbox One",)),
    ("Xbox Series", ("Xbox Series X",)),
    ("Xbox Series X", ("Xbox Series X",)),
)
DEVICE_TYPE_FREE_TEXT_FIELDS = (
    "Device Type",
    "Device Types",
    "Compatible Device",
    "Compatible Devices",
    "Compatibility",
)
DEVICE_TYPE_ALIASES = {
    "mister": "MiSTer",
    "mister fpga": "MiSTer",
    "pc": "PC",
    "windows": "PC",
    "mac": "Mac",
    "macos": "Mac",
    "mac os": "Mac",
    "android": "Android",
    "ios": "iOS",
    "mobile": "Mobile",
    "switch": "Switch",
    "switch 2": "Switch 2",
    "nintendo switch 2": "Switch 2",
    "ps3": "PS3",
    "playstation 3": "PS3",
    "ps4": "PS4",
    "playstation 4": "PS4",
    "ps5": "PS5",
    "playstation 5": "PS5",
    "xbox 360": "Xbox 360",
    "xbox one": "Xbox One",
    "xbox series": "Xbox Series X",
    "xbox series x": "Xbox Series X",
    "xbox series xs": "Xbox Series X",
    "astro city mini": "Astro City Mini",
    "genesis": "Genesis",
    "genesis mini": "Genesis Mini",
    "nes classic": "NES Classic",
    "snes": "SNES",
    "snes classic": "SNES Classic",
    "n64": "N64",
    "neo geo mini": "Neo Geo Mini",
    "playstation classic": "PlayStation Classic",
    "playstation clasisic": "PlayStation Classic",
    "saturn": "Saturn",
    "turbografx 16 mini": "TurboGrafx-16 Mini",
    "wii classic": "Wii Classic",
    "wii u": "Wii U",
    "wired controller": "Wired Controller",
    "wireless controller": "Wireless Controller",
    "controller": "Controller",
    "controller adapter": "Controller Adapter",
    "genesis controller": "Genesis Controller",
    "nes controller": "NES Controller",
    "snes controller": "SNES Controller",
    "sfc controller": "SNES Controller",
    "n64 controller": "N64 Controller",
    "gamecube controller": "GameCube Controller",
    "game cube controller": "GameCube Controller",
    "pc engine controller": "PC Engine Controller",
    "pce controller": "PC Engine Controller",
    "turbografx controller": "PC Engine Controller",
    "saturn controller": "Saturn Controller",
    "neo geo controller": "Neo Geo Controller",
    "psx controller": "PSX Controller",
    "playstation controller": "PSX Controller",
    "dreamcast controller": "Dreamcast Controller",
    "sms controller": "SMS Controller",
    "master system controller": "SMS Controller",
    "jaguar controller": "Jaguar Controller",
    "virtual boy controller": "Virtual Boy Controller",
    "wii classic controller": "Wii Classic Controller",
    "controller conversion": "Controller Conversion",
    "arcade stick": "Arcade Stick",
    "arcade stick encoder": "Arcade Stick Encoder",
    "wired arcade stick": "Wired Arcade Stick",
    "wireless arcade stick": "Wireless Arcade Stick",
    "joystick": "Arcade Stick",
    "joystick encoder": "Arcade Stick Encoder",
    "supergun": "Supergun",
    "unknown": "Unknown",
    "uncategorized": "Uncategorized",
}
EXCLUDED_RESULT_TYPES = {"experiment", "experimental"}
REFLEX_ADAPT_SYSTEM_PATTERNS = (
    ("3DO", r"\b3do\b"),
    ("GameCube", r"\bgame\s*cube\b|\bgamecube\b"),
    ("N64", r"\bn64\b|tribute64|bit controller"),
    ("NES", r"\bnes\b"),
    ("SNES", r"\bsnes\b"),
    ("Genesis", r"\bgenesis\b"),
    ("Jaguar", r"\bjaguar\b"),
    ("Neo Geo", r"\bneo\s*geo\b"),
    ("PCE", r"\bpce\b|\bpc\s*engine\b|\bturbografx\b"),
    ("PSX", r"\bpsx\b|\bplaystation\b"),
    ("Saturn 3D", r"\bsaturn\s+3d\b"),
    ("Saturn", r"\bsaturn\b"),
    ("SMS", r"\bsms\b|\bmaster\s*system\b"),
    ("Virtual Boy", r"\bvirtual\s*boy\b"),
    ("Wii Classic", r"\bwii\s*classic\b"),
)
ADAPTER_INPUT_SYSTEM_PATTERNS = (
    ("GameCube", r"\bgame\s*cube\b|\bgamecube\b"),
    ("N64", r"\bn64\b"),
    ("SNES", r"\bsnes\b|\bsfc\b"),
    ("NES", r"\bnes\b"),
    ("Genesis", r"\bgenesis\b|\bmegadrive\b|mega\s*drive"),
    ("PC Engine", r"\bpce\b|\bpc\s*engine\b|\bturbografx\b|\bnec\s+pi\b"),
    ("Saturn", r"\bsaturn\b"),
    ("Neo Geo", r"\bneo\s*geo\b"),
    ("PSX", r"\bpsx\b|\bplaystation\b|\bps1\b"),
    ("Dreamcast", r"\bdreamcast\b|\bdc\b"),
    ("SMS", r"\bsms\b|\bmaster\s*system\b"),
    ("Jaguar", r"\bjaguar\b"),
    ("Virtual Boy", r"\bvirtual\s*boy\b"),
    ("Wii Classic", r"\bwii\s*classic\b"),
)
OUTPUT_MODE_PATTERNS = (
    ("DInput", r"\bd[\s-]?input\b|direct input|\bwindows\b|\bpc\b(?!\s*engine)|\busb\b"),
    ("XInput", r"\bx[\s-]?input\b"),
    ("Switch", r"\bswitch\b"),
    ("PS5", r"\bps5\b|playstation 5"),
    ("PS4", r"\bps4\b|playstation 4"),
    ("PS3", r"\bps3\b|playstation 3"),
    ("Xbox Series", r"xbox series"),
    ("Xbox One", r"xbox one"),
    ("Xbox 360", r"xbox 360"),
    ("Wii U", r"\bwii u\b"),
    ("Android", r"\bandroid\b"),
    ("macOS", r"\bmacos\b|\bmac os\b"),
    ("Console", r"\bconsole\b"),
)
DISPLAY_NAME_ALIASES = (
    (
        re.compile(
            r"^vienon\s+ps2\s+controller\s+to\s+usb\s+adapter\s+converter,?\s+2\s+pack\s+compatible\s+with\s+ps1-ps2\s+controller\s+gamepad\s+to\s+ps3-pc\s+controller\s+no\s+need\s+driver$",
            flags=re.IGNORECASE,
        ),
        "vienon PS1/PS2 to USB Adapter",
    ),
    (
        re.compile(
            r"^generic\s*-\s*2\s+port\s+genesis\s+to\s+usb\s+\(cable\s+style\s+with\s+2\s+blue\s+ports\)$",
            flags=re.IGNORECASE,
        ),
        "Generic - 2-Port Genesis to USB Adapter",
    ),
)
VID_PID_SUFFIX_RE = re.compile(r"(?:\s+[-–]\s*|\s+)(?P<vid>[0-9a-fA-F]{4})[_:]?(?P<pid>[0-9a-fA-F]{4})\s*$")
DASH_MODE_SUFFIX_RE = re.compile(
    r"\s+[-–]\s*(?P<mode>d[\s-]?input|direct\s+input|x[\s-]?input|switch|hid|pc|usb)\s*$",
    flags=re.IGNORECASE,
)

REFLEX_ADAPT_URL = "https://misteraddons.com/products/reflex-adapt"
REFLEX_CTRL_URL = "https://misteraddons.com/products/reflex-ctrl"
RAPHNET_ADAPTER_URL = "https://www.raphnet-tech.com/products.php?category=Adapters"
RETROUSB_USB_ADAPTER_URL = "https://retrousb.com/products/USB_adapter"
ULTIMARC_IPAC_URL = "https://www.ultimarc.com/control-interfaces/i-pacs/"
ULTIMARC_IPAC_ULTIMATE_URL = "https://www.ultimarc.com/control-interfaces/i-pacs/i-pac-ultimate-i-o/"
ULTIMARC_JPAC_URL = "https://www.ultimarc.com/control-interfaces/j-pac-en/"


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_device_name(value: Any) -> str:
    normalized = normalize_text(value).lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def strip_capture_filename_suffix(value: Any) -> str:
    return re.sub(r"\.csv\s*$", "", normalize_text(value), flags=re.IGNORECASE).strip()


def normalize_joystick_id(value: Any) -> str:
    text = normalize_text(value)
    match = re.fullmatch(r"(?P<vid>[0-9a-fA-F]{4})[_:](?P<pid>[0-9a-fA-F]{4})", text)
    if match:
        return f"{match.group('vid').lower()}:{match.group('pid').lower()}"
    return text


def extract_trailing_joystick_id(value: Any) -> tuple[str, str]:
    text = normalize_text(value)
    match = VID_PID_SUFFIX_RE.search(text)
    if not match:
        return text, ""
    base = text[: match.start()].rstrip(" -–")
    joystick_id = normalize_joystick_id(f"{match.group('vid')}:{match.group('pid')}")
    return base or text, joystick_id


def make_slug(value: Any) -> str:
    slug = normalize_device_name(value).replace(" ", "-")
    return slug or "unknown"


def first_present_value(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = normalize_text(row.get(key))
        if value:
            return value
    return ""


def is_source_code_url(value: Any) -> bool:
    return bool(re.search(r"\b(github|gitlab|codeberg|sourcehut|bitbucket)\.", normalize_text(value), flags=re.IGNORECASE))


def is_product_or_buy_url(value: Any) -> bool:
    text = normalize_text(value)
    return bool(text) and not is_source_code_url(text)


def strip_firmware_suffix(value: Any) -> str:
    return re.sub(r"\s+fw\s+(?:pre-)?v?\d+(?:\.\d+)*\s*$", "", normalize_text(value), flags=re.IGNORECASE).strip()


def normalize_sale_status(value: Any, bool_context: bool = False) -> str:
    text = normalize_text(value).lower()
    if not text:
        return ""
    normalized = normalize_device_name(text)
    active_values = {
        "active",
        "actively sold",
        "available",
        "currently sold",
        "for sale",
        "in stock",
        "sold",
        "yes",
        "true",
        "1",
        "y",
    }
    discontinued_values = {
        "discontinued",
        "not actively sold",
        "not currently sold",
        "not sold",
        "no",
        "false",
        "0",
        "n",
        "retired",
    }
    if normalized in active_values:
        return "Actively sold"
    if normalized in discontinued_values:
        return "Discontinued"
    if "discontinued" in normalized or "retired" in normalized:
        return "Discontinued"
    if bool_context and normalized.startswith("no"):
        return "Discontinued"
    if "active" in normalized or "available" in normalized or "for sale" in normalized:
        return "Actively sold"
    return ""


def sale_status_from_values(*, amazon: Any = "", link: Any = "", explicit: Any = "", bool_value: Any = "") -> str:
    status = normalize_sale_status(explicit)
    if status:
        return status
    status = normalize_sale_status(bool_value, bool_context=True)
    if status:
        return status
    if is_product_or_buy_url(amazon) or is_product_or_buy_url(link):
        return "Actively sold"
    return "Unknown"


def parse_open_source_status(value: Any, link: Any = "", amazon: Any = "") -> tuple[bool, str]:
    return False, "Closed Source"


def source_url_from_values(*values: Any) -> str:
    for value in values:
        text = normalize_text(value)
        if is_source_code_url(text):
            return text
    return ""


def alias_display_name(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    for pattern, replacement in DISPLAY_NAME_ALIASES:
        if pattern.match(text):
            return replacement
    return text


def make_model_display_name(make: Any, model: Any) -> str:
    make_text = normalize_text(make)
    model_text = normalize_text(model)
    if not make_text or not model_text:
        return ""
    return f"{make_text} - {model_text}"


def split_bracket_mode_suffix(value: Any) -> tuple[str, str]:
    text = strip_capture_filename_suffix(value)
    if not text:
        return "", ""
    match = re.match(
        r"^(?P<base>.+?)\s+\[(?P<mode>[^\]]+)\]\s*(?:(?:fw\s+(?:pre-)?v?\d+(?:\.\d+)*)|(?:\d{6,8}))?\s*$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return text, ""
    base = re.sub(r"\s+", " ", match.group("base")).strip()
    mode = re.sub(r"\bvia\s+reflex adapt\b", "", match.group("mode"), flags=re.IGNORECASE)
    mode = re.sub(r"\breflex adapt\b", "", mode, flags=re.IGNORECASE)
    mode = re.sub(r"\s+", " ", mode).strip(" -/")
    return base or text, mode


def parse_controller_title_metadata(value: Any) -> dict[str, str]:
    raw = normalize_text(value)
    text = strip_capture_filename_suffix(raw)
    text, joystick_id = extract_trailing_joystick_id(text)

    mode_parts: list[str] = []
    dash_match = DASH_MODE_SUFFIX_RE.search(text)
    if dash_match:
        mode_parts.append(re.sub(r"\s+", " ", dash_match.group("mode")).strip())
        text = text[: dash_match.start()].rstrip(" -–")

    base, bracket_mode = split_bracket_mode_suffix(text)
    if bracket_mode:
        mode_parts.append(bracket_mode)

    mode_raw = " ".join(part for part in mode_parts if part).strip()
    display_name = alias_display_name(base)
    mode_has_connection_hint = bool(
        re.search(
            r"\b(wired|wireless|bluetooth|bt|2\.?\s*4\s*g(?:hz)?|dongle|usb)\b",
            mode_raw,
            flags=re.IGNORECASE,
        )
    )
    connection_probe = mode_raw if mode_has_connection_hint else " ".join(part for part in (raw, mode_raw) if part)
    connection_tag = connection_tag_for_values(connection_probe, "", "Unknown", "")
    return {
        "name": display_name or text or raw,
        "modeRaw": mode_raw,
        "joystickId": joystick_id,
        "connectionTag": connection_tag,
    }


def split_controller_mode_suffix(value: Any) -> tuple[str, str]:
    metadata = parse_controller_title_metadata(value)
    return metadata["name"], metadata["modeRaw"]


def is_reflex_adapt_pass_through_name(value: Any) -> bool:
    text = normalize_text(value)
    if not text:
        return False
    if re.match(r"^reflex adapt\s+\[", text, flags=re.IGNORECASE):
        return False
    return bool(re.search(r"\[[^\]]*\breflex adapt\b[^\]]*\]", text, flags=re.IGNORECASE))


def clean_reflex_adapt_pass_through_name(value: Any) -> str:
    base, _mode = split_controller_mode_suffix(value)
    return base or normalize_text(value)


def is_reflex_adapt_baseline_name(value: Any) -> bool:
    return bool(re.match(r"^reflex adapt\s+\[", normalize_text(value), flags=re.IGNORECASE))


def is_reflex_ctrl_name(value: Any) -> bool:
    return bool(re.match(r"^reflex\s*(?:[-–]\s*)?ctrl\b", normalize_text(value), flags=re.IGNORECASE))


def is_daemonbite_name(value: Any) -> bool:
    return bool(re.match(r"^daemon\s*bite\b|^daemonbite\b", normalize_text(value), flags=re.IGNORECASE))


def is_raphnet_name(value: Any) -> bool:
    return bool(re.match(r"^raphnet\b", normalize_text(value), flags=re.IGNORECASE))


def is_timville_name(value: Any) -> bool:
    return bool(re.match(r"^timville\b", normalize_text(value), flags=re.IGNORECASE))


def is_reflex_encode_fightboard_name(value: Any) -> bool:
    return bool(
        re.search(
            r"\breflex\s*(?:[-–]\s*)?encode\s+fightboard\b",
            normalize_text(value),
            flags=re.IGNORECASE,
        )
    )


def is_reflex_adapt_device_name(value: Any) -> bool:
    return bool(re.match(r"^reflex\s*[-–]?\s*adapt\b", normalize_text(value), flags=re.IGNORECASE))


def is_reflex_adapt_adapter_item(item: dict[str, Any]) -> bool:
    if not is_controller_adapter_item(item):
        return False
    return any(
        is_reflex_adapt_device_name(value)
        for value in (
            item.get("name"),
            item.get("measurementName"),
            make_model_display_name(item.get("make"), item.get("model")),
        )
    )


def is_blisster_name(value: Any) -> bool:
    return bool(re.search(r"\bblisster\b|\bblissbox\b", normalize_text(value), flags=re.IGNORECASE))


def is_retrousb_retrokit_name(value: Any) -> bool:
    return bool(re.match(r"^retrousb\s*-\s*retrokit\b", normalize_text(value), flags=re.IGNORECASE))


def is_lload_name(value: Any) -> bool:
    return bool(re.search(r"\blload\b", normalize_text(value), flags=re.IGNORECASE))


def is_ultimarc_ipac_ultimate_name(value: Any) -> bool:
    return bool(re.search(r"\bultimarc\b.*\bi-?pac\s+ultimate\b", normalize_text(value), flags=re.IGNORECASE))


def is_ultimarc_ipac_legacy_name(value: Any) -> bool:
    text = normalize_text(value)
    return bool(
        re.search(r"\bultimarc\b.*\bi-?pac\b", text, flags=re.IGNORECASE)
        and re.search(r"\b2004\b|\bps/2\b|\bps2\b", text, flags=re.IGNORECASE)
    )


def is_ultimarc_ipac_name(value: Any) -> bool:
    text = normalize_text(value)
    return bool(
        re.search(r"\bultimarc\b.*\bi-?pac\b", text, flags=re.IGNORECASE)
        and not is_ultimarc_ipac_ultimate_name(text)
        and not is_ultimarc_ipac_legacy_name(text)
    )


def is_ultimarc_jpac_name(value: Any) -> bool:
    return bool(re.search(r"\bultimarc\b.*\bj-?pac\b", normalize_text(value), flags=re.IGNORECASE))


def item_name_text(item: dict[str, Any]) -> str:
    return normalize_text(item.get("measurementName") or item.get("name"))


def is_open_source_firmware_family(*values: Any) -> bool:
    return any(
        is_reflex_adapt_device_name(value) or is_raphnet_name(value) or is_timville_name(value)
        or is_reflex_encode_fightboard_name(value)
        for value in values
    )


def is_known_wired_family(*values: Any) -> bool:
    return any(
        is_reflex_adapt_device_name(value)
        or is_reflex_ctrl_name(value)
        or is_raphnet_name(value)
        or is_daemonbite_name(value)
        for value in values
    )


def apply_source_firmware_status(item: dict[str, Any]) -> None:
    if is_open_source_firmware_family(
        item.get("name"),
        item.get("measurementName"),
        item.get("make"),
        item.get("model"),
    ):
        item["isOpenSource"] = True
        item["sourceStatus"] = "Open Source"
    else:
        item["isOpenSource"] = False
        item["sourceStatus"] = "Closed Source"


def apply_connection_metadata_overrides(item: dict[str, Any]) -> None:
    if not is_known_wired_family(
        item.get("name"),
        item.get("measurementName"),
        item.get("make"),
        item.get("model"),
    ):
        return
    if is_wireless_latency_item(item):
        return
    if normalize_text(item.get("connectionKind")) in {"", "Unknown"}:
        item["connectionKind"] = "Wired"
    if not normalize_text(item.get("connectionTag")):
        item["connectionTag"] = "Wired"


def set_item_sale_status(item: dict[str, Any], status: str, url: str = "", force_url: bool = False) -> None:
    item["saleStatus"] = status
    if url and (force_url or not item.get("buyUrl")):
        item["buyUrl"] = url
        if not item.get("link") and not is_source_code_url(url):
            item["link"] = url


def apply_sale_status_overrides(item: dict[str, Any]) -> None:
    name = item_name_text(item)
    search = normalize_device_name(name)

    if is_reflex_adapt_device_name(name):
        set_item_sale_status(item, "Actively sold", REFLEX_ADAPT_URL, force_url=True)
    elif is_raphnet_name(name):
        set_item_sale_status(item, "Actively sold", RAPHNET_ADAPTER_URL, force_url=True)
    elif is_reflex_ctrl_name(name):
        set_item_sale_status(item, "Actively sold", REFLEX_CTRL_URL, force_url=True)
    elif is_daemonbite_name(name):
        set_item_sale_status(item, "Discontinued")
    elif is_lload_name(name):
        set_item_sale_status(item, "Discontinued")
    elif is_blisster_name(name):
        set_item_sale_status(item, "Actively sold")
    elif "freejoy" in search:
        set_item_sale_status(item, "Discontinued")
    elif "paradise arcade lono" in search:
        set_item_sale_status(item, "Discontinued")
    elif "xinmotek" in search or "xm 08" in search:
        set_item_sale_status(item, "Discontinued")
    elif "generic 1 port snes to usb" in search or "generic 2 port genesis to usb" in search:
        set_item_sale_status(item, "Discontinued")
    elif "mayflash megadrive" in search:
        set_item_sale_status(item, "Discontinued")
    elif "retro bit nes to usb" in search:
        set_item_sale_status(item, "Discontinued")
    elif "retrousb" in search:
        if "nes" in search and ("usb" in search or "retrokit" in search):
            set_item_sale_status(item, "Actively sold", RETROUSB_USB_ADAPTER_URL)
        else:
            set_item_sale_status(item, "Discontinued")
    elif is_ultimarc_jpac_name(name):
        set_item_sale_status(item, "Actively sold", ULTIMARC_JPAC_URL)
    elif is_ultimarc_ipac_legacy_name(name):
        set_item_sale_status(item, "Discontinued")
    elif is_ultimarc_ipac_ultimate_name(name):
        set_item_sale_status(item, "Actively sold", ULTIMARC_IPAC_ULTIMATE_URL)
    elif is_ultimarc_ipac_name(name):
        set_item_sale_status(item, "Actively sold", ULTIMARC_IPAC_URL)


def mayflash_arcade_stick_display_name(value: Any) -> str:
    text = normalize_text(value)
    match = re.match(
        r"^mayflash\s*(?:[-–]\s*)?(?:arcade\s+stick\s+)?(f(?:300|500|700))\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    model = match.group(1).upper()
    suffix = ""
    if re.search(r"\belite\b", text, flags=re.IGNORECASE):
        suffix = " Elite"
    elif re.search(r"\bv\s*2\b|\bv2\b", text, flags=re.IGNORECASE):
        suffix = " V2"
    return f"Mayflash - {model}{suffix}"


def is_mayflash_arcade_stick_name(value: Any) -> bool:
    return bool(mayflash_arcade_stick_display_name(value))


def is_excluded_latency_item(item: dict[str, Any]) -> bool:
    name = item.get("measurementName") or item.get("name")
    if is_internal_reflex_experimental_device(name):
        return True
    output_mode = normalize_text(item.get("outputMode"))
    mode_raw = normalize_text(item.get("modeRaw"))
    if not is_mayflash_arcade_stick_name(name):
        return False
    search = " ".join(normalize_text(item.get(field)) for field in ("name", "measurementName", "modeRaw"))
    return (
        output_mode == "Console"
        or re.search(r"\bconsole\b", mode_raw, flags=re.IGNORECASE) is not None
        or re.search(r"\bpre-?\s*v\d", search, flags=re.IGNORECASE) is not None
    )


def is_internal_reflex_experimental_device(value: Any) -> bool:
    return bool(
        re.match(
            r"^reflex\s*(?:[-–]\s*reflex)?\s+\[3do\s+\d+p\]",
            normalize_text(value),
            flags=re.IGNORECASE,
        )
    )


def fallback_category_for_name(value: Any) -> str:
    text = normalize_text(value).lower()
    if not text:
        return ""
    if is_reflex_ctrl_name(text) or is_retrousb_retrokit_name(text):
        return "Controller Conversion"
    if is_reflex_encode_fightboard_name(text):
        return "Arcade Stick Encoder"
    if re.search(r"\b(i-?pac|j-?pac|xinmotek|freejoy|lono|jvs|encoder|spinner|trackball)\b", text):
        return "Arcade Stick Encoder"
    if re.search(r"\b(adapter|4dapter|blisster|blissbox|to usb|usb adapter|converter|mayflash n64|mayflash gamecube)\b", text):
        return "Controller Adapter"
    if re.search(r"\b(arcade stick|fighting stick|fightstick|fight board|fightboard|qanba|raion|versus controller)\b", text):
        return "Arcade Stick"
    if re.search(
        r"\b(controller|gamepad|pad|dualshock|dualsense|stadia|gravis|brawler|brawler64|defender|admiral|saffun|8bitdo|gullikit)\b",
        text,
    ):
        return "Controller"
    if re.search(r"\b(nintendo switch online|gamecube wireless)\b", text):
        return "Controller"
    return ""


def infer_reflex_adapt_system(value: Any) -> str:
    text = normalize_text(value)
    for label, pattern in REFLEX_ADAPT_SYSTEM_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return label
    return ""


def infer_adapter_input_system(value: Any) -> str:
    text = normalize_text(value)
    for label, pattern in ADAPTER_INPUT_SYSTEM_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return label
    return ""


def inferred_category_for_item(item: dict[str, Any]) -> str:
    category = normalize_text(item.get("category"))
    name = normalize_text(item.get("measurementName") or item.get("name"))

    if category == "Joystick":
        return "Arcade Stick"
    if category == "Joystick Encoder":
        return "Arcade Stick Encoder"
    if is_reflex_ctrl_name(name):
        return "Controller Conversion"
    if is_retrousb_retrokit_name(name):
        return "Controller Conversion"
    if is_reflex_encode_fightboard_name(name):
        return "Arcade Stick Encoder"
    if is_reflex_adapt_baseline_name(name):
        return "Controller Adapter"
    if is_daemonbite_name(name):
        if category in {"", "Unknown", "Uncategorized", "Controller Adapter"} and not re.search(
            r"\barcade\b",
            name,
            flags=re.IGNORECASE,
        ):
            return "Controller Adapter"
    if is_raphnet_name(name) and category in {"", "Unknown", "Uncategorized", "Controller Adapter"}:
        return "Controller Adapter"
    if is_mayflash_arcade_stick_name(name) and category in {"", "Unknown", "Uncategorized", "Arcade Stick"}:
        return "Arcade Stick"
    if category in {"", "Unknown", "Uncategorized"}:
        return fallback_category_for_name(name) or category
    return category


def is_controller_adapter_item(item: dict[str, Any]) -> bool:
    return normalize_text(item.get("category")) == "Controller Adapter"


def inferred_output_mode_for_item(item: dict[str, Any]) -> str:
    output_mode = normalize_text(item.get("outputMode"))
    if output_mode:
        return output_mode
    name = normalize_text(item.get("measurementName") or item.get("name"))
    if is_controller_adapter_item(item) and is_daemonbite_name(name):
        return "DInput"
    if is_blisster_name(name):
        return "DInput"
    if is_retrousb_retrokit_name(name):
        return "DInput"
    search = " ".join(
        normalize_text(item.get(field)).lower()
        for field in ("connection", "modeRaw", "modeLabel", "modeDisplay")
    )
    if "usb" in search:
        return "DInput"
    return ""


def adapter_input_device_type_for_item(item: dict[str, Any]) -> str:
    if not is_controller_adapter_item(item):
        return ""
    search = " ".join(
        normalize_text(item.get(field))
        for field in (
            "name",
            "measurementName",
            "deviceNorm",
            "connection",
            "modeRaw",
            "modeLabel",
            "modeDisplay",
            "originalSystem",
            "model",
        )
    )
    system = infer_adapter_input_system(search)
    return f"{system} Controller" if system else ""


def apply_item_classification(item: dict[str, Any]) -> None:
    category = inferred_category_for_item(item)
    if category:
        item["category"] = category
    apply_connection_metadata_overrides(item)
    item["deviceTypes"] = device_types_for_item(item)
    output_mode = inferred_output_mode_for_item(item)
    if output_mode:
        item["outputMode"] = output_mode
        name = normalize_text(item.get("measurementName") or item.get("name"))
        if is_daemonbite_name(name) or is_reflex_adapt_baseline_name(name):
            item["modeLabel"] = output_mode


def reflex_adapt_baseline_mode(value: Any) -> str:
    if not is_reflex_adapt_baseline_name(value):
        return ""
    _base, mode = split_controller_mode_suffix(value)
    return mode


def reflex_adapt_baseline_sort_key(item: dict[str, Any]) -> tuple[int, int, int, float, str]:
    mode_text = normalize_text(item.get("adapterMode"))
    mode_norm = normalize_device_name(mode_text)
    has_1p = bool(re.search(r"\b1p\b", mode_norm))
    has_port = bool(re.search(r"\b\d+p\b", mode_norm))
    has_legacy_suffix = bool(re.search(r"\b\d{6,8}\s*$", normalize_text(item.get("name"))))
    has_mpg = "mpg" in mode_norm
    return (
        0 if has_1p else 1 if not has_port else 2,
        1 if has_legacy_suffix else 0,
        1 if has_mpg else 0,
        item.get("averageMs") if item.get("averageMs") is not None else float("inf"),
        mode_text.lower(),
    )


def controller_group_display_name(item: dict[str, Any]) -> str:
    base, _mode = split_controller_mode_suffix(item.get("name"))
    base = strip_firmware_suffix(base)
    base = re.sub(
        r"\s*[-–]\s*(?:d[\s-]?input|x[\s-]?input|switch|hid|direct input)\s*$",
        "",
        base,
        flags=re.IGNORECASE,
    )
    base = re.sub(r"\s+", " ", base).strip()
    if is_reflex_ctrl_name(base):
        return "Reflex CTRL"
    if is_reflex_adapt_adapter_item(item):
        return "Reflex - Adapt"
    if is_reflex_encode_fightboard_name(base):
        return "Reflex Encode Fightboard (GP2040-CE)"
    if is_controller_adapter_item(item) and is_daemonbite_name(base):
        return "DaemonBite - Controller Adapter"
    if is_controller_adapter_item(item) and is_raphnet_name(base):
        return "Raphnet - Controller Adapter"
    make_model = make_model_display_name(item.get("make"), item.get("model"))
    mayflash_display = mayflash_arcade_stick_display_name(base) or mayflash_arcade_stick_display_name(make_model)
    if mayflash_display:
        return mayflash_display
    if make_model:
        return make_model
    return base or normalize_text(item.get("name"))


def sanitize_display_name(value: Any) -> str:
    text = strip_capture_filename_suffix(value)
    if not text:
        return ""
    text, _joystick_id = extract_trailing_joystick_id(text)
    dash_match = DASH_MODE_SUFFIX_RE.search(text)
    if dash_match:
        text = text[: dash_match.start()].rstrip(" -–")
    connection_suffix = re.compile(
        r"\s*\[\s*(?:"
        r"(?:bt|bluetooth|2\.?4\s*ghz|wired|wireless|usb|hid|pc|"
        r"d[\s-]?input|direct\s+input|x[\s-]?input|switch|ps[345]|"
        r"xbox(?:\s*(?:360|one|series\s*x))?|ac600|csr8510|driver\s+free|"
        r"wii\s*u|wii\s+classic|android|mac(?:os)?)"
        r"|[\s,+()/.-]"
        r")+\]\s*$",
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(r"\s+", " ", connection_suffix.sub("", text)).strip() or text
    return alias_display_name(sanitized)


def controller_group_key(item: dict[str, Any]) -> str:
    is_adapter_family = is_controller_adapter_item(item) and (
        is_daemonbite_name(item.get("name"))
        or is_raphnet_name(item.get("name"))
        or is_reflex_adapt_adapter_item(item)
    )
    is_forced_family = is_adapter_family or is_reflex_ctrl_name(item.get("name")) or is_reflex_encode_fightboard_name(item.get("name"))
    result_type = "" if is_forced_family else normalize_text(item.get("resultType")).lower()
    return "|".join(
        (
            result_type,
            normalize_device_name(controller_group_display_name(item)),
        )
    )


def product_family_name(value: Any) -> str:
    text = strip_firmware_suffix(value)
    mayflash_display = mayflash_arcade_stick_display_name(text)
    if mayflash_display:
        return normalize_device_name(mayflash_display)
    base, _mode = split_controller_mode_suffix(text)
    normalized = normalize_device_name(strip_firmware_suffix(base))
    if not normalized:
        return ""

    words = normalized.split()
    cleaned: list[str] = []
    skip_revision_number = False
    for word in words:
        if word in {"rev", "revision"}:
            skip_revision_number = True
            continue
        if skip_revision_number and word.isdigit():
            continue
        skip_revision_number = False
        if word in {"arcade", "stick"}:
            continue
        cleaned.append(word)
    return " ".join(cleaned)


def parse_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text or text in {"-", "NA", "N/A"}:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    number = parse_float(value)
    return None if number is None else int(round(number))


def parse_bool(value: Any) -> bool | None:
    text = normalize_text(value).lower()
    if text in {"true", "yes", "1", "y"}:
        return True
    if text in {"false", "no", "0", "n"}:
        return False
    return None


def round_optional(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(value, digits)


def same_frame_from_average(average_ms: float | None) -> float | None:
    if average_ms is None:
        return None
    return max(0, min(100, (1 - average_ms / SAME_FRAME_WINDOW_MS) * 100))


def parse_date_added(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    for date_format in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            continue
    return ""


def output_mode_for_values(output_mode: Any, mode_raw: Any = "") -> str:
    explicit_output_mode = normalize_text(output_mode)
    search = explicit_output_mode or normalize_text(mode_raw)
    if not search:
        return ""

    labels = []
    lowered = search.lower()
    for label, pattern in OUTPUT_MODE_PATTERNS:
        if re.search(pattern, lowered) and label not in labels:
            labels.append(label)
    return ", ".join(labels)


def primary_mode_rank_label(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return normalize_text(re.split(r"[,;/]", text, maxsplit=1)[0])


def is_wireless_latency_item(item: dict[str, Any]) -> bool:
    tag = normalize_text(item.get("connectionTag"))
    kind = normalize_text(item.get("connectionKind"))
    search = " ".join(
        normalize_text(item.get(field)).lower()
        for field in ("connection", "wirelessConnection", "modeRaw")
    )
    return tag in {"BT", "2.4GHz", "Wireless", "Wireless BT", "Wireless 2.4GHz"} or kind == "Wireless" or "wireless" in search


def is_wired_latency_item(item: dict[str, Any]) -> bool:
    tag = normalize_text(item.get("connectionTag"))
    kind = normalize_text(item.get("connectionKind"))
    search = " ".join(
        normalize_text(item.get(field)).lower()
        for field in ("connection", "modeRaw")
    )
    return tag == "Wired" or kind == "Wired" or "wired" in search


def mode_display_for_values(
    connection: Any,
    connection_kind: Any,
    mode_raw: Any = "",
    output_mode: Any = "",
    mode_label: Any = "",
    wireless_connection: Any = "",
) -> str:
    label = normalize_text(output_mode) or normalize_text(mode_label)
    connection_text = normalize_text(connection)
    mode = normalize_text(mode_raw)
    connection_kind_text = normalize_text(connection_kind)
    wireless_text = normalize_text(wireless_connection)
    generic_labels = {"bluetooth", "bt", "wireless", "unknown", "2 4g", "2 4ghz"}

    if label and normalize_device_name(label) not in generic_labels:
        return label
    if connection_text:
        return connection_text
    if mode:
        return mode
    if label:
        return label
    if connection_kind_text and connection_kind_text != "Unknown":
        return connection_kind_text
    if wireless_text and wireless_text != "-":
        return wireless_text
    return ""


def mode_display_for_item(item: dict[str, Any]) -> str:
    name = item_name_text(item)
    category = normalize_text(item.get("category"))
    if is_blisster_name(name):
        return "USB"
    if is_retrousb_retrokit_name(name):
        return "USB"
    if category == "Controller Conversion":
        search = " ".join(
            normalize_text(item.get(field)).lower()
            for field in ("connection", "modeRaw", "modeLabel", "modeDisplay", "outputMode")
        )
        if "usb" in search or "dinput" in search:
            return "USB"
    display = mode_display_for_values(
        item.get("connection"),
        item.get("connectionKind"),
        item.get("modeRaw"),
        item.get("outputMode"),
        item.get("modeLabel"),
        item.get("wirelessConnection"),
    )
    adapter_input = adapter_input_device_type_for_item(item)
    if adapter_input and normalize_device_name(display) in {"", "wired", "wireless", "usb", "unknown"}:
        return adapter_input
    return display


def rank_class_for_item(item: dict[str, Any]) -> str:
    category = normalize_text(item.get("category"))
    wireless = is_wireless_latency_item(item)
    wired = is_wired_latency_item(item)

    if category == "Controller":
        if wireless:
            return "Wireless Controller"
        if wired:
            return "Wired Controller"
        return "Controller"
    if category == "Arcade Stick":
        if wireless:
            return "Wireless Arcade Stick"
        if wired:
            return "Wired Arcade Stick"
        return "Arcade Stick"
    if category == "Joystick":
        if wireless:
            return "Wireless Joystick"
        if wired:
            return "Wired Joystick"
        return "Joystick"
    if category == "Controller Adapter":
        return "Controller Adapter"
    if category in {"Arcade Stick Encoder", "Joystick Encoder"}:
        return "Arcade Stick Encoder"
    if category and category not in {"Unknown", "Uncategorized"}:
        return category
    return ""


def connection_tag_for_values(mode_raw: Any, connection: Any, connection_kind: Any, wireless_connection: Any = "") -> str:
    connection_kind_text = normalize_text(connection_kind)
    search = f"{normalize_text(mode_raw)} {normalize_text(connection)} {connection_kind_text} {normalize_text(wireless_connection)}".lower()
    if "2.4" in search or "2.4g" in search or "dongle" in search or "wireless usb" in search:
        return "Wireless 2.4GHz"
    if "bluetooth" in search or re.search(r"\bbt\b", search):
        return "Wireless BT"
    if "wired" in search or connection_kind_text == "Wired":
        return "Wired"
    if "wireless" in search or re.search(r"\bir\b", search):
        return "Wireless"
    if connection_kind_text == "Wireless":
        return "Wireless"
    return ""


def mode_label_for_values(
    connection: Any,
    connection_kind: Any,
    original_system: Any = "",
    mode_raw: Any = "",
    output_mode: Any = "",
    wireless_connection: Any = "",
) -> str:
    output_mode_text = normalize_text(output_mode)
    if output_mode_text:
        return output_mode_text
    connection_text = normalize_text(connection)
    connection_kind_text = normalize_text(connection_kind)
    original_system_text = normalize_text(original_system)
    mode_raw_text = normalize_text(mode_raw)
    wireless_connection_text = normalize_text(wireless_connection)
    search = f"{mode_raw_text} {connection_text} {connection_kind_text} {original_system_text} {wireless_connection_text}".lower()

    if re.search(r"\bx[\s-]?input\b", search):
        return "XInput"
    if re.search(r"\bd[\s-]?input\b", search):
        return "DInput"
    if "switch" in search:
        return "Switch"
    if "2.4" in search or "2.4g" in search or "dongle" in search:
        return "2.4G"
    if "bluetooth" in search or re.search(r"\bbt\b", search):
        return "Bluetooth"
    if mode_raw_text and not re.search(r"\b(wired|wireless|usb|bluetooth|bt|2\.4|dongle)\b", mode_raw_text.lower()):
        return mode_raw_text
    if "usb" in search:
        return "USB"
    if connection_kind_text and connection_kind_text != "Unknown":
        return connection_kind_text
    return original_system_text or mode_raw_text


def parse_same_frame_pct(value: Any) -> float | None:
    number = parse_float(value)
    if number is None:
        return None
    return number * 100 if number <= 1 else number


def normalize_connection_fields(connection: Any, connection_kind: Any) -> tuple[str, str]:
    connection_text = normalize_text(connection)
    kind_text = normalize_text(connection_kind)
    kind_key = normalize_device_name(kind_text)

    if kind_key in {"wired usb", "usb wired"}:
        return connection_text or "Wired USB", "Wired"
    if kind_key == "wired":
        return connection_text or "Wired USB", "Wired"
    if kind_key in {"bluetooth", "bt"}:
        return connection_text or "Bluetooth", "Wireless"
    if kind_key in {"24ghz wireless", "24g wireless", "24ghz", "24g"}:
        return connection_text or "2.4GHz Wireless", "Wireless"
    if kind_key == "wireless":
        return connection_text or "Wireless", "Wireless"
    return connection_text, kind_text or "Unknown"


def split_list(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]


def is_yes_cell(value: Any) -> bool:
    return normalize_text(value).lower() in {"yes", "y", "true", "1", "x"}


def normalize_device_type_label(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    normalized = normalize_device_name(text)
    return DEVICE_TYPE_ALIASES.get(normalized, text)


def ordered_device_types(values: list[str]) -> list[str]:
    unique = []
    for value in values:
        label = normalize_device_type_label(value)
        if label and label not in unique:
            unique.append(label)

    order = {label: index for index, label in enumerate(DEVICE_TYPE_ORDER)}
    return sorted(unique, key=lambda label: (order.get(label, len(order)), normalize_device_name(label)))


def split_device_types(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    text = re.sub(r"\bMiSTer\s*/\s*PC\b", "MiSTer,PC", text, flags=re.IGNORECASE)
    return ordered_device_types([part for part in re.split(r"[,;|]", text) if part.strip()])


def device_types_from_platforms(value: Any) -> list[str]:
    types: list[str] = []
    for part in split_list(value):
        types.extend(split_device_types(part))
    return ordered_device_types(types)


def device_types_from_category_values(
    category: Any,
    connection: Any = "",
    connection_kind: Any = "",
    wireless_connection: Any = "",
    mode_raw: Any = "",
    connection_tag: Any = "",
) -> list[str]:
    category_text = normalize_text(category)
    if not category_text or category_text in {"Unknown", "Uncategorized"}:
        return []
    if category_text == "Controller":
        tag = normalize_text(connection_tag) or connection_tag_for_values(
            mode_raw,
            connection,
            connection_kind,
            wireless_connection,
        )
        probe = {
            "category": category_text,
            "connection": connection,
            "connectionKind": connection_kind,
            "wirelessConnection": wireless_connection,
            "modeRaw": mode_raw,
            "connectionTag": tag,
        }
        if is_wireless_latency_item(probe):
            return ["Wireless Controller"]
        if is_wired_latency_item(probe):
            return ["Wired Controller"]
    if category_text == "Arcade Stick":
        tag = normalize_text(connection_tag) or connection_tag_for_values(
            mode_raw,
            connection,
            connection_kind,
            wireless_connection,
        )
        probe = {
            "category": category_text,
            "connection": connection,
            "connectionKind": connection_kind,
            "wirelessConnection": wireless_connection,
            "modeRaw": mode_raw,
            "connectionTag": tag,
        }
        if is_wireless_latency_item(probe):
            return ["Wireless Arcade Stick"]
        if is_wired_latency_item(probe):
            return ["Wired Arcade Stick"]
    return ordered_device_types([category_text])


def device_types_for_item(item: dict[str, Any]) -> list[str]:
    types = device_types_from_category_values(
        item.get("category"),
        item.get("connection"),
        item.get("connectionKind"),
        item.get("wirelessConnection"),
        item.get("modeRaw"),
        item.get("connectionTag"),
    )
    adapter_input = adapter_input_device_type_for_item(item)
    if adapter_input:
        types.append(adapter_input)
    return ordered_device_types(types)


def sheet_category(row: dict[str, Any]) -> str:
    return (
        normalize_text(row.get(SHEET_CATEGORY_BB_KEY))
        or normalize_text(row.get("Category"))
        or normalize_text(row.get("Device Category"))
        or normalize_text(row.get("Device Type"))
    )


def normalize_face_buttons(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    try:
        numeric = float(text)
    except ValueError:
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return text


def sheet_face_buttons(row: dict[str, Any]) -> str:
    return (
        normalize_face_buttons(row.get(SHEET_FACE_BUTTONS_BC_KEY))
        or normalize_face_buttons(row.get("Face Buttons"))
    )


def sheet_weight_oz(row: dict[str, Any]) -> str:
    return (
        normalize_text(row.get(SHEET_WEIGHT_BD_KEY))
        or normalize_text(row.get("Weight (oz)"))
        or normalize_text(row.get("Weight"))
    )


def normalize_home_button(value: Any) -> str:
    text = normalize_text(value)
    lowered = text.lower()
    if lowered in {"yes", "y", "true", "1", "x"}:
        return "Yes"
    if lowered in {"no", "n", "false", "0"}:
        return "No"
    if lowered in {"n/a", "na", "not applicable"}:
        return "N/A"
    return text


def sheet_home_button(row: dict[str, Any]) -> str:
    return normalize_home_button(
        normalize_text(row.get(SHEET_HOME_BUTTON_AN_KEY))
        or normalize_text(row.get("Home Button"))
    )


def sheet_joystick_id(row: dict[str, Any]) -> str:
    return (
        normalize_text(row.get(SHEET_JOYSTICK_ID_AX_KEY))
        or normalize_text(row.get("Joystick ID"))
        or normalize_text(row.get("VID:PID"))
        or normalize_text(row.get("VID PID"))
    )


def sheet_device_types(row: dict[str, Any], item: dict[str, Any] | None = None) -> list[str]:
    category = sheet_category(row)
    if category:
        probe = {
            "name": (item or {}).get("name") or row.get("Device"),
            "measurementName": (item or {}).get("measurementName"),
            "deviceNorm": (item or {}).get("deviceNorm") or normalize_device_name(row.get("Device")),
            "category": category,
            "connection": (item or {}).get("connection") or row.get("Connection"),
            "connectionKind": (item or {}).get("connectionKind") or row.get("Wired / Wireless") or row.get("Wired/Wireless"),
            "wirelessConnection": (item or {}).get("wirelessConnection") or row.get("Wireless Connection") or row.get("WirelessConnection"),
            "modeRaw": (item or {}).get("modeRaw") or row.get("Mode"),
            "modeLabel": (item or {}).get("modeLabel"),
            "modeDisplay": (item or {}).get("modeDisplay"),
            "originalSystem": (item or {}).get("originalSystem"),
            "model": (item or {}).get("model") or row.get("Model"),
            "connectionTag": (item or {}).get("connectionTag"),
        }
        return device_types_for_item(probe)
    return []


def strip_variant_suffix(value: Any) -> str:
    base, _mode = split_controller_mode_suffix(value)
    if base != normalize_text(value):
        return strip_firmware_suffix(base)
    return strip_firmware_suffix(re.sub(r"\s*\[[^\]]+\]\s*$", "", normalize_text(value)))


def strip_version_suffix(value: Any) -> str:
    return re.sub(r"\s+v\d+(?:\.\d+)?$", "", normalize_text(value), flags=re.IGNORECASE)


def tier_for_value(value: float | None, thresholds: tuple[tuple[str, float], ...]) -> str:
    if value is None:
        return ""
    for label, cutoff in thresholds:
        if value <= cutoff:
            return label
    return "Rust"


def tier_for_average(value: float | None) -> str:
    return tier_for_value(value, AVERAGE_TIER_THRESHOLDS)


def tier_for_p99(value: float | None) -> str:
    return tier_for_value(value, P99_TIER_THRESHOLDS)


def is_excluded_latency_result(result_type: Any, device: Any) -> bool:
    return (
        normalize_text(result_type).lower() in EXCLUDED_RESULT_TYPES
        or is_internal_reflex_experimental_device(device)
    )


def public_csv_path(public_root: Path) -> Path:
    return public_root / PUBLIC_CSV


def private_csv_paths(private_root: Path | None) -> list[tuple[str, str, Path]]:
    if private_root is None:
        return []
    return [
        (result_type, relative_path, private_root / relative_path)
        for result_type, relative_path in PRIVATE_CSVS
    ]


def read_public_rows(public_root: Path) -> list[dict[str, Any]]:
    source = public_csv_path(public_root)
    if not source.exists():
        raise FileNotFoundError(f"Missing public latency export: {source}")

    items = []
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            average = parse_float(row.get("Latency (in ms)"))
            if average is None:
                continue
            raw_device = normalize_text(row.get("DeviceClean") or row.get("Device"))
            if not raw_device:
                continue
            base_display_name, name_mode = split_controller_mode_suffix(raw_device)
            display_name = (
                make_model_display_name(row.get("Make"), row.get("Model"))
                or base_display_name
                or raw_device
            )
            device_norm = normalize_device_name(display_name)
            p99 = parse_float(row.get("P99"))
            observed_same_frame_pct = parse_same_frame_pct(row.get("PctOnTime"))
            connection, connection_kind = normalize_connection_fields(
                row.get("Connection"),
                row.get("Wired/Wireless"),
            )
            wireless_connection = normalize_text(row.get("WirelessConnection"))
            mode_raw = normalize_text(row.get("Mode")) or name_mode
            output_mode = output_mode_for_values(row.get("Output Mode"), mode_raw)
            date_added = normalize_text(row.get("Date Added"))
            platforms = split_list(row.get("Platforms"))
            category = normalize_text(row.get("Category")) or "Unknown"
            open_source, source_status = parse_open_source_status(
                first_present_value(row, ("Open Source", "Open Source?", "Source Available", "Source")),
                row.get("Link"),
                row.get("Amazon"),
            )
            device_types = device_types_from_category_values(
                category,
                connection,
                connection_kind,
                wireless_connection,
                mode_raw,
            )
            item = {
                "id": f"published-{make_slug(device_norm)}",
                "name": display_name,
                "measurementName": raw_device,
                "deviceNorm": device_norm,
                "make": normalize_text(row.get("Make")),
                "model": normalize_text(row.get("Model")),
                "link": normalize_text(row.get("Link")),
                "amazon": normalize_text(row.get("Amazon")),
                "buyUrl": normalize_text(row.get("Amazon")) or normalize_text(row.get("Link")),
                "connection": connection,
                "connectionKind": connection_kind,
                "wirelessConnection": wireless_connection,
                "modeRaw": mode_raw,
                "outputMode": output_mode,
                "connectionTag": connection_tag_for_values(mode_raw, connection, connection_kind, wireless_connection),
                "modeLabel": mode_label_for_values(
                    connection,
                    connection_kind,
                    mode_raw=mode_raw,
                    output_mode=output_mode,
                    wireless_connection=wireless_connection,
                ),
                "modeDisplay": "",
                "rankMode": "",
                "overallRank": None,
                "modeRank": None,
                "homeButton": normalize_home_button(row.get("Home Button")),
                "resultType": "published",
                "resultLabel": "Published",
                "category": category,
                "faceButtons": normalize_face_buttons(row.get("Face Buttons")),
                "weightOz": normalize_text(row.get("Weight (oz)") or row.get("Weight")),
                "dateAdded": date_added,
                "dateAddedSort": parse_date_added(date_added),
                "platforms": platforms,
                "deviceTypes": device_types,
                "price": normalize_text(row.get("Price")),
                "priceNum": round_optional(parse_float(row.get("PriceNum")), 2),
                "sheetTier": normalize_text(row.get("Latency Tier")),
                "averageTier": tier_for_average(average),
                "p99Tier": tier_for_p99(p99),
                "averageMs": round_optional(average),
                "sdMs": round_optional(parse_float(row.get("SD"))),
                "maxMs": round_optional(parse_float(row.get("Max"))),
                "minMs": round_optional(parse_float(row.get("Min"))),
                "p99Ms": round_optional(p99),
                "sampleCount": parse_int(row.get("N")),
                "sameFramePct": round_optional(same_frame_from_average(average), 2),
                "observedSameFramePct": round_optional(observed_same_frame_pct, 2),
                "sameFrameSource": "Average-implied",
                "hasRawCapture": parse_bool(row.get("HasRawCapture")),
                "metricSource": normalize_text(row.get("MetricSource")) or "Direct measurement",
                "notes": "",
                "tester": "",
                "originalSystem": "",
                "saleStatus": sale_status_from_values(
                    amazon=row.get("Amazon"),
                    link=row.get("Link"),
                    explicit=first_present_value(row, ("Sale Status", "Availability", "Product Status")),
                    bool_value=first_present_value(row, ("Currently Sold", "Actively Sold", "Active")),
                ),
                "sourceStatus": source_status,
                "isOpenSource": open_source,
                "sourceUrl": source_url_from_values(row.get("Link"), row.get("Amazon")),
                "joystickId": normalize_text(row.get("Joystick ID")),
                "searchText": "",
            }
            apply_item_classification(item)
            apply_source_firmware_status(item)
            apply_sale_status_overrides(item)
            item["modeDisplay"] = mode_display_for_item(item)
            item["searchText"] = build_search_text(item)
            items.append(item)
    return items


def cell(row: list[str], key: str) -> str:
    index = PRIVATE_COLUMNS[key]
    return normalize_text(row[index]) if len(row) > index else ""


def read_private_file(source: Path, fallback_result_type: str) -> list[dict[str, Any]]:
    if not source.exists():
        return []

    items = []
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            valid = cell(row, "valid").lower()
            if valid and valid not in {"yes", "true", "1"}:
                continue
            average = parse_float(cell(row, "average"))
            device = cell(row, "device")
            if average is None or not device:
                continue
            result_type = cell(row, "result_type").lower() or fallback_result_type
            if is_excluded_latency_result(result_type, device):
                continue
            p99 = parse_float(cell(row, "p99"))
            observed_same_frame_pct = parse_same_frame_pct(cell(row, "same_frame"))
            original_system = cell(row, "original_system")
            date_added = cell(row, "date_added")
            category = cell(row, "category") or "Uncategorized"
            title_metadata = parse_controller_title_metadata(device)
            display_name = title_metadata["name"] or device
            mode_raw = title_metadata["modeRaw"]
            output_mode = output_mode_for_values("", mode_raw)
            connection_tag = title_metadata["connectionTag"] or connection_tag_for_values(mode_raw, "", "Unknown", "")
            joystick_id = normalize_joystick_id(cell(row, "joystick_id")) or title_metadata["joystickId"]
            item = {
                "id": f"{result_type}-{make_slug(display_name)}",
                "name": display_name,
                "deviceNorm": normalize_device_name(display_name),
                "make": "",
                "model": "",
                "link": "",
                "amazon": "",
                "buyUrl": "",
                "connection": "",
                "connectionKind": "Unknown",
                "wirelessConnection": "",
                "modeRaw": mode_raw,
                "outputMode": output_mode,
                "connectionTag": connection_tag,
                "modeLabel": mode_label_for_values("", "Unknown", original_system, mode_raw, output_mode),
                "modeDisplay": "",
                "rankMode": "",
                "overallRank": None,
                "modeRank": None,
                "homeButton": "",
                "resultType": result_type,
                "resultLabel": result_type.replace("-", " ").title(),
                "category": category,
                "faceButtons": normalize_face_buttons(cell(row, "face_buttons")),
                "weightOz": cell(row, "weight_oz"),
                "dateAdded": date_added,
                "dateAddedSort": parse_date_added(date_added),
                "platforms": [],
                "deviceTypes": device_types_from_category_values(
                    category,
                    "",
                    "Unknown",
                    "",
                    mode_raw,
                    connection_tag,
                ),
                "price": "",
                "priceNum": None,
                "sheetTier": cell(row, "average_tier"),
                "averageTier": tier_for_average(average),
                "p99Tier": tier_for_p99(p99),
                "averageMs": round_optional(average),
                "measuredAverageMs": None,
                "adapterAverageMs": None,
                "adapterMode": "",
                "adapterSourceName": "",
                "sdMs": round_optional(parse_float(cell(row, "sd"))),
                "maxMs": round_optional(parse_float(cell(row, "maximum"))),
                "minMs": round_optional(parse_float(cell(row, "minimum"))),
                "p99Ms": round_optional(p99),
                "sampleCount": parse_int(cell(row, "sample_count")),
                "sameFramePct": round_optional(same_frame_from_average(average), 2),
                "observedSameFramePct": round_optional(observed_same_frame_pct, 2),
                "sameFrameSource": "Average-implied",
                "hasRawCapture": True,
                "metricSource": "Raw capture",
                "notes": cell(row, "notes"),
                "tester": cell(row, "tester"),
                "originalSystem": original_system,
                "saleStatus": "Unknown",
                "sourceStatus": "Closed Source",
                "isOpenSource": False,
                "sourceUrl": "",
                "joystickId": joystick_id,
                "measurementName": device,
                "searchText": "",
            }
            apply_item_classification(item)
            apply_source_firmware_status(item)
            apply_sale_status_overrides(item)
            item["modeDisplay"] = mode_display_for_item(item)
            item["searchText"] = build_search_text(item)
            items.append(item)
    return items


def read_private_rows(private_root: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if private_root is None:
        return [], {"available": False, "files": []}

    files = []
    items = []
    for result_type, relative_path, source in private_csv_paths(private_root):
        file_items = read_private_file(source, result_type)
        files.append(
            {
                "resultType": result_type,
                "file": str(Path(relative_path).as_posix()),
                "available": source.exists(),
                "count": len(file_items),
            }
        )
        items.extend(file_items)

    return items, {
        "available": any(file_info["available"] for file_info in files),
        "files": files,
    }


def read_sheet_rows_from_text(csv_text: str) -> list[dict[str, str]]:
    reader = csv.reader(io.StringIO(csv_text))
    try:
        headers = next(reader)
    except StopIteration:
        return []

    rows: list[dict[str, str]] = []
    for values in reader:
        row = {
            header: values[index] if index < len(values) else ""
            for index, header in enumerate(headers)
        }
        row[SHEET_DATE_ADDED_BA_KEY] = (
            values[SHEET_DATE_ADDED_BA_INDEX]
            if SHEET_DATE_ADDED_BA_INDEX < len(values)
            else ""
        )
        row[SHEET_CATEGORY_BB_KEY] = (
            values[SHEET_CATEGORY_BB_INDEX]
            if SHEET_CATEGORY_BB_INDEX < len(values)
            else ""
        )
        row[SHEET_FACE_BUTTONS_BC_KEY] = (
            values[SHEET_FACE_BUTTONS_BC_INDEX]
            if SHEET_FACE_BUTTONS_BC_INDEX < len(values)
            else ""
        )
        row[SHEET_WEIGHT_BD_KEY] = (
            values[SHEET_WEIGHT_BD_INDEX]
            if SHEET_WEIGHT_BD_INDEX < len(values)
            else ""
        )
        row[SHEET_JOYSTICK_ID_AX_KEY] = (
            values[SHEET_JOYSTICK_ID_AX_INDEX]
            if SHEET_JOYSTICK_ID_AX_INDEX < len(values)
            else ""
        )
        row[SHEET_HOME_BUTTON_AN_KEY] = (
            values[SHEET_HOME_BUTTON_AN_INDEX]
            if SHEET_HOME_BUTTON_AN_INDEX < len(values)
            else ""
        )
        rows.append(row)
    return rows


def read_sheet_rows_from_url(url: str) -> list[dict[str, str]]:
    with urlopen(url, timeout=30) as response:
        return read_sheet_rows_from_text(response.read().decode("utf-8-sig"))


def read_sheet_rows_from_path(path: Path) -> list[dict[str, str]]:
    return read_sheet_rows_from_text(path.read_text(encoding="utf-8-sig"))


def sheet_match_keys(row: dict[str, Any]) -> list[str]:
    device = normalize_text(row.get("Device") or row.get("DeviceClean") or row.get("name"))
    make = normalize_text(row.get("Make") or row.get("make"))
    model = normalize_text(row.get("Model") or row.get("model"))
    device_base = strip_variant_suffix(device)
    make_model = f"{make} {model}"
    make_model_base = strip_variant_suffix(make_model)
    keys = [
        normalize_device_name(device),
        normalize_device_name(device_base),
        product_family_name(device),
        normalize_device_name(strip_version_suffix(device)),
        normalize_device_name(strip_version_suffix(device_base)),
        normalize_device_name(make_model),
        normalize_device_name(make_model_base),
        product_family_name(make_model),
        normalize_device_name(strip_version_suffix(make_model)),
        normalize_device_name(strip_version_suffix(make_model_base)),
    ]
    return [key for index, key in enumerate(keys) if key and key not in keys[:index]]


def sheet_date_added(row: dict[str, Any]) -> str:
    return (
        normalize_text(row.get(SHEET_DATE_ADDED_BA_KEY))
        or normalize_text(row.get("Date Added"))
        or normalize_text(row.get("Date added"))
        or normalize_text(row.get("dateAdded"))
    )


def build_sheet_lookup(sheet_rows: list[dict[str, Any]] | None) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for row in sheet_rows or []:
        link = normalize_text(row.get("Link"))
        amazon = normalize_text(row.get("Amazon"))
        price = normalize_text(row.get("Price"))
        mode_raw = normalize_text(row.get("Mode"))
        output_mode = normalize_text(row.get("Output Mode"))
        date_added = sheet_date_added(row)
        face_buttons = sheet_face_buttons(row)
        home_button = sheet_home_button(row)
        weight_oz = sheet_weight_oz(row)
        joystick_id = sheet_joystick_id(row)
        device_types = sheet_device_types(row)
        sale_status = first_present_value(row, ("Sale Status", "Availability", "Product Status", "Currently Sold", "Actively Sold", "Active"))
        open_source = first_present_value(row, ("Open Source", "Open Source?", "Source Available", "Source", "Source URL", "Source Code URL"))
        if (
            not link
            and not amazon
            and not price
            and not mode_raw
            and not output_mode
            and not date_added
            and not face_buttons
            and not home_button
            and not weight_oz
            and not joystick_id
            and not device_types
            and not sale_status
            and not open_source
        ):
            continue
        for key in sheet_match_keys(row):
            lookup.setdefault(key, []).append(row)
    return lookup


def sheet_match_output_hint(item: dict[str, Any]) -> str:
    explicit = output_mode_for_values(item.get("outputMode"), item.get("modeRaw"))
    if explicit:
        return primary_mode_rank_label(explicit)
    _name_base, name_mode = split_controller_mode_suffix(item.get("name"))
    item_text = " ".join(
        normalize_text(item.get(field))
        for field in ("modeRaw", "modeLabel", "modeDisplay")
    )
    item_text = " ".join(part for part in (item_text, normalize_text(name_mode)) if part)
    return primary_mode_rank_label(output_mode_for_values("", item_text))


def sheet_candidate_score(item: dict[str, Any], candidate: dict[str, Any]) -> int:
    item_output_hint = sheet_match_output_hint(item)
    candidate_mode_raw = normalize_text(candidate.get("Mode"))
    candidate_output = output_mode_for_values(candidate.get("Output Mode"), candidate_mode_raw)
    candidate_output_primary = primary_mode_rank_label(candidate_output)

    item_connection_tag = connection_tag_for_values(
        "",
        item.get("connection"),
        item.get("connectionKind"),
        item.get("wirelessConnection"),
    )
    candidate_connection_tag = connection_tag_for_values(
        candidate_mode_raw,
        candidate.get("Connection"),
        candidate.get("Wired / Wireless") or candidate.get("Wired/Wireless"),
        candidate.get("Wireless Connection") or candidate.get("WirelessConnection"),
    )
    item_connection = normalize_device_name(item.get("connection"))
    candidate_connection = normalize_device_name(candidate.get("Connection"))

    item_device = normalize_device_name(item.get("name"))
    candidate_device = normalize_device_name(candidate.get("Device"))
    item_base = normalize_device_name(strip_version_suffix(strip_variant_suffix(item.get("name"))))
    candidate_base = normalize_device_name(strip_version_suffix(strip_variant_suffix(candidate.get("Device"))))
    item_family = product_family_name(item.get("name"))
    candidate_family = product_family_name(candidate.get("Device") or f"{candidate.get('Make')} {candidate.get('Model')}")
    item_make_model = normalize_device_name(f"{item.get('make')} {item.get('model')}")
    candidate_make_model = normalize_device_name(f"{candidate.get('Make')} {candidate.get('Model')}")

    score = 0
    if item_device and candidate_device and item_device == candidate_device:
        score += 100
    if item_base and candidate_base and item_base == candidate_base:
        score += 40
    if item_family and candidate_family and item_family == candidate_family:
        score += 35
    if item_make_model and candidate_make_model and item_make_model == candidate_make_model:
        score += 30
    if item_output_hint and candidate_output_primary == item_output_hint:
        score += 60
    elif item_output_hint and candidate_output_primary and item_output_hint != candidate_output_primary:
        score -= 45
    if item_connection and candidate_connection and item_connection == candidate_connection:
        score += 50
    if item_connection_tag and candidate_connection_tag and item_connection_tag == candidate_connection_tag:
        score += 20
    return score


def sheet_candidate_mode_compatible(item: dict[str, Any], candidate: dict[str, Any]) -> bool:
    item_output_hint = sheet_match_output_hint(item)
    candidate_output = primary_mode_rank_label(output_mode_for_values(candidate.get("Output Mode"), candidate.get("Mode")))
    return not item_output_hint or not candidate_output or item_output_hint == candidate_output


def find_sheet_match(item: dict[str, Any], lookup: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    seen: set[int] = set()
    for key in sheet_match_keys({"Device": item.get("name"), "Make": item.get("make"), "Model": item.get("model")}):
        for candidate in lookup.get(key, []):
            candidate_id = id(candidate)
            if candidate_id not in seen:
                seen.add(candidate_id)
                candidates.append(candidate)
    if not candidates:
        return None

    return max(candidates, key=lambda candidate: sheet_candidate_score(item, candidate))


def augment_items_with_sheet_links(items: list[dict[str, Any]], sheet_rows: list[dict[str, Any]] | None) -> int:
    lookup = build_sheet_lookup(sheet_rows)
    linked = 0
    for item in items:
        match = find_sheet_match(item, lookup)
        if not match:
            continue

        is_published = item.get("resultType") == "published"
        link = normalize_text(match.get("Link"))
        amazon = normalize_text(match.get("Amazon"))
        price = normalize_text(match.get("Price"))
        date_added = sheet_date_added(match)
        sheet_category_value = sheet_category(match)
        sheet_face_buttons_value = sheet_face_buttons(match)
        sheet_home_button_value = sheet_home_button(match)
        sheet_weight_value = sheet_weight_oz(match)
        sheet_joystick_id_value = sheet_joystick_id(match)
        mode_raw = normalize_text(match.get("Mode"))
        output_mode = output_mode_for_values(match.get("Output Mode"), mode_raw)
        mode_has_output_hint = bool(output_mode)
        mode_compatible = sheet_candidate_mode_compatible(item, match)
        sheet_connection = normalize_text(match.get("Connection")) or item.get("connection", "")
        sheet_connection_kind = (
            normalize_text(match.get("Wired / Wireless"))
            or normalize_text(match.get("Wired/Wireless"))
            or item.get("connectionKind", "")
        )
        sheet_wireless_connection = (
            normalize_text(match.get("Wireless Connection"))
            or normalize_text(match.get("WirelessConnection"))
            or item.get("wirelessConnection", "")
        )
        source_hint = first_present_value(match, ("Open Source", "Open Source?", "Source Available", "Source"))
        source_url = first_present_value(match, ("Source URL", "Source Code URL"))
        if is_published and link and not item.get("link"):
            item["link"] = link
        if is_published and amazon and not item.get("amazon"):
            item["amazon"] = amazon
        if is_published and price and not item.get("price"):
            item["price"] = price
            item["priceNum"] = round_optional(parse_float(price), 2)
        if date_added:
            item["dateAdded"] = date_added
            item["dateAddedSort"] = parse_date_added(date_added)
        if sheet_category_value:
            item["category"] = sheet_category_value
        if sheet_face_buttons_value:
            item["faceButtons"] = sheet_face_buttons_value
        if sheet_home_button_value:
            item["homeButton"] = sheet_home_button_value
        if sheet_weight_value:
            item["weightOz"] = sheet_weight_value
        if sheet_joystick_id_value:
            item["joystickId"] = sheet_joystick_id_value
        if mode_compatible and mode_has_output_hint and mode_raw:
            item["modeRaw"] = mode_raw
        if mode_compatible and output_mode:
            item["outputMode"] = output_mode
        if mode_compatible and sheet_connection and not item.get("connection"):
            item["connection"] = sheet_connection
        if mode_compatible and sheet_connection_kind and item.get("connectionKind") in {"", "Unknown"}:
            item["connectionKind"] = sheet_connection_kind
        if mode_compatible and sheet_wireless_connection and not item.get("wirelessConnection"):
            item["wirelessConnection"] = sheet_wireless_connection
        if mode_compatible:
            item["connectionTag"] = connection_tag_for_values(
                item.get("modeRaw"),
                sheet_connection,
                sheet_connection_kind,
                sheet_wireless_connection,
            )
            item["modeLabel"] = mode_label_for_values(
                sheet_connection,
                sheet_connection_kind,
                item.get("originalSystem"),
                item.get("modeRaw"),
                item.get("outputMode"),
                sheet_wireless_connection,
            )
        device_types = sheet_device_types(match, item)
        if device_types:
            item["deviceTypes"] = device_types
        item["saleStatus"] = sale_status_from_values(
            amazon=item.get("amazon") or amazon,
            link=item.get("link") or link,
            explicit=first_present_value(match, ("Sale Status", "Availability", "Product Status")),
            bool_value=first_present_value(match, ("Currently Sold", "Actively Sold", "Active")),
        )
        is_open_source, source_status = parse_open_source_status(
            source_hint,
            source_url or item.get("link") or link,
            item.get("amazon") or amazon,
        )
        item["isOpenSource"] = is_open_source
        item["sourceStatus"] = source_status
        item["sourceUrl"] = source_url_from_values(source_url, item.get("link"), link, item.get("amazon"), amazon)
        apply_item_classification(item)
        apply_source_firmware_status(item)
        apply_sale_status_overrides(item)
        item["modeDisplay"] = mode_display_for_item(item)
        if is_published:
            item["buyUrl"] = item.get("amazon") or item.get("link") or ""
        item["searchText"] = build_search_text(item)
        if is_published and item["buyUrl"]:
            linked += 1
    return linked


def build_reflex_adapt_baseline_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    candidates_by_system: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        name = item.get("measurementName") or item.get("name")
        mode = reflex_adapt_baseline_mode(name)
        average = item.get("averageMs")
        if not mode or average is None:
            continue
        system = infer_reflex_adapt_system(mode)
        if not system:
            continue
        candidates_by_system.setdefault(system, []).append(
            {
                "name": name,
                "averageMs": average,
                "adapterMode": mode,
            }
        )

    return {
        system: sorted(candidates, key=reflex_adapt_baseline_sort_key)[0]
        for system, candidates in candidates_by_system.items()
    }


def apply_reflex_adapt_pass_through_adjustments(items: list[dict[str, Any]]) -> None:
    baselines = build_reflex_adapt_baseline_lookup(items)
    for item in items:
        measurement_name = item.get("measurementName") or item.get("name")
        if not is_reflex_adapt_pass_through_name(measurement_name):
            continue

        clean_name = clean_reflex_adapt_pass_through_name(measurement_name)
        if clean_name:
            item["name"] = clean_name
            item["deviceNorm"] = normalize_device_name(clean_name)
            item["id"] = f"{item.get('resultType', 'result')}-{make_slug(clean_name)}"

        system = infer_reflex_adapt_system(measurement_name)
        baseline = baselines.get(system)
        measured_average = item.get("averageMs")
        adapter_average = baseline.get("averageMs") if baseline else None
        if measured_average is not None and adapter_average is not None:
            adjusted_average = max(0, measured_average - adapter_average)
            item["measuredAverageMs"] = measured_average
            item["adapterAverageMs"] = round_optional(adapter_average)
            item["adapterMode"] = normalize_text(baseline.get("adapterMode"))
            item["adapterSourceName"] = normalize_text(baseline.get("name"))
            item["averageMs"] = round_optional(adjusted_average)
            item["averageTier"] = tier_for_average(adjusted_average)
            item["sameFramePct"] = round_optional(same_frame_from_average(adjusted_average), 2)
            item["sameFrameSource"] = "Reflex Adapt adjusted average-implied"
            item["metricSource"] = "Raw capture, Reflex Adapt adjusted"

        apply_item_classification(item)
        apply_source_firmware_status(item)
        apply_sale_status_overrides(item)
        item["modeDisplay"] = mode_display_for_item(item)
        item["searchText"] = build_search_text(item)


def item_search_blob(item: dict[str, Any]) -> str:
    return " ".join(
        normalize_text(item.get(field))
        for field in (
            "name",
            "measurementName",
            "make",
            "model",
            "deviceNorm",
            "connection",
            "modeRaw",
            "outputMode",
            "modeLabel",
            "modeDisplay",
            "category",
        )
    )


def is_feralai_gp2040_item(item: dict[str, Any]) -> bool:
    search = item_search_blob(item)
    return bool(re.search(r"\bferalai\b", search, flags=re.IGNORECASE)) and bool(
        re.search(r"\bgp2040\b", search, flags=re.IGNORECASE)
    )


def is_hori_fighting_commander_wii_classic_item(item: dict[str, Any]) -> bool:
    return bool(
        re.search(
            r"\bhori\b.*\bfighting\s+commander\s+wii\s+classic\b",
            item_search_blob(item),
            flags=re.IGNORECASE,
        )
    )


def is_hori_wii_classic_mayflash_item(item: dict[str, Any]) -> bool:
    return is_hori_fighting_commander_wii_classic_item(item) and bool(
        re.search(r"\bmay\s*flash\b", item_search_blob(item), flags=re.IGNORECASE)
    )


def is_hori_wii_classic_hidden_adapter_item(item: dict[str, Any]) -> bool:
    if not is_hori_fighting_commander_wii_classic_item(item):
        return False
    search = item_search_blob(item)
    return bool(re.search(r"\bgbro?s?\b|8bitdo\s+gc", search, flags=re.IGNORECASE))


def is_reflex_adapt_two_player_item(item: dict[str, Any]) -> bool:
    if not is_reflex_adapt_adapter_item(item):
        return False
    search = " ".join(normalize_text(item.get(field)) for field in ("measurementName", "modeRaw", "name"))
    return bool(re.search(r"\b2p\b", search, flags=re.IGNORECASE))


def is_mayflash_wii_classic_baseline_item(item: dict[str, Any]) -> bool:
    if not is_controller_adapter_item(item):
        return False
    search = item_search_blob(item)
    return bool(re.search(r"\bmay\s*flash\b", search, flags=re.IGNORECASE)) and bool(
        re.search(r"\bwii\s+classic\b", search, flags=re.IGNORECASE)
    )


def mayflash_wii_classic_baseline_sort_key(item: dict[str, Any]) -> tuple[int, int, float, str]:
    search = item_search_blob(item)
    exact_raw = bool(re.search(r"mayflash\s*-\s*wii\s+classic\s+to\s+usb", search, flags=re.IGNORECASE))
    return (
        0 if item.get("hasRawCapture") else 1,
        0 if exact_raw else 1,
        item.get("averageMs") if item.get("averageMs") is not None else float("inf"),
        normalize_text(item.get("measurementName") or item.get("name")).lower(),
    )


def mayflash_wii_classic_baseline(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        item
        for item in items
        if is_mayflash_wii_classic_baseline_item(item) and item.get("averageMs") is not None
    ]
    return sorted(candidates, key=mayflash_wii_classic_baseline_sort_key)[0] if candidates else None


def apply_hori_wii_classic_adapter_adjustments(items: list[dict[str, Any]]) -> None:
    baseline = mayflash_wii_classic_baseline(items)
    if not baseline:
        return
    adapter_average = baseline.get("averageMs")
    if adapter_average is None:
        return

    for item in items:
        if not is_hori_wii_classic_mayflash_item(item):
            continue
        measured_average = item.get("averageMs")
        if measured_average is None:
            continue
        adjusted_average = max(0, measured_average - adapter_average)
        item["measuredAverageMs"] = measured_average
        item["adapterAverageMs"] = round_optional(adapter_average)
        item["adapterMode"] = normalize_text(baseline.get("modeDisplay") or baseline.get("modeRaw") or "Wii Classic to USB")
        item["adapterSourceName"] = normalize_text(baseline.get("measurementName") or baseline.get("name"))
        item["averageMs"] = round_optional(adjusted_average)
        item["averageTier"] = tier_for_average(adjusted_average)
        item["sameFramePct"] = round_optional(same_frame_from_average(adjusted_average), 2)
        item["sameFrameSource"] = "Adapter adjusted average-implied"
        item["metricSource"] = "Raw capture, adapter adjusted" if item.get("hasRawCapture") else "Adapter adjusted"
        item["modeDisplay"] = mode_display_for_item(item)
        item["searchText"] = build_search_text(item)


def explicit_output_mode_key(item: dict[str, Any]) -> str:
    mode_text = normalize_text(item.get("modeRaw"))
    measurement_text = normalize_text(item.get("measurementName"))
    output_text = normalize_text(item.get("outputMode"))
    primary = " ".join((mode_text, measurement_text)).lower()
    if re.search(r"\bx[\s-]?input\b", primary):
        return "xinput"
    if re.search(r"\bd[\s-]?input\b|direct\s+input", primary):
        return "dinput"
    if re.search(r"\bswitch\b", primary):
        return "switch"
    if re.search(r"\bps5\b", primary):
        return "ps5"
    if re.search(r"\bps4\b", primary):
        return "ps4"
    if re.search(r"\bps3\b", primary):
        return "ps3"

    output = output_text.lower()
    if "xinput" in output:
        return "xinput"
    if "dinput" in output:
        return "dinput"
    return normalize_device_name(output_text or mode_text or measurement_text)


def reflex_adapt_variant_profile(item: dict[str, Any]) -> str:
    search = " ".join(normalize_text(item.get(field)) for field in ("measurementName", "modeRaw", "name"))
    return "mpg" if re.search(r"\bmpg\b", search, flags=re.IGNORECASE) else "standard"


def requested_cleanup_duplicate_key(item: dict[str, Any]) -> tuple[str, ...] | None:
    search = item_search_blob(item)
    display_name = normalize_device_name(controller_group_display_name(item))

    if is_reflex_adapt_adapter_item(item):
        system = infer_reflex_adapt_system(search)
        return ("reflex-adapt", system, reflex_adapt_variant_profile(item), explicit_output_mode_key(item))

    if is_mayflash_arcade_stick_name(search):
        return ("mayflash-arcade", display_name, explicit_output_mode_key(item))

    if is_timville_name(search):
        return ("timville", display_name, explicit_output_mode_key(item) or "usb")

    if is_hori_wii_classic_mayflash_item(item):
        return ("hori-wii-classic", "mayflash")

    if re.search(r"\bretro[\s-]?bit\b.*\btribute64\s+wireless\b", search, flags=re.IGNORECASE):
        if re.search(r"\bn64\b", search, flags=re.IGNORECASE):
            return ("retro-bit-tribute64", "n64")
        return ("retro-bit-tribute64", explicit_output_mode_key(item))

    return None


def requested_cleanup_prefer_item(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    candidate_adjusted = candidate.get("adapterAverageMs") is not None
    current_adjusted = current.get("adapterAverageMs") is not None
    if candidate_adjusted != current_adjusted:
        return candidate_adjusted
    candidate_raw = candidate.get("hasRawCapture") is True
    current_raw = current.get("hasRawCapture") is True
    if candidate_raw != current_raw:
        return candidate_raw
    return latency_item_sort_key(candidate) < latency_item_sort_key(current)


def cleanup_requested_latency_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible = [
        item
        for item in items
        if not is_feralai_gp2040_item(item)
        and not is_hori_wii_classic_hidden_adapter_item(item)
        and not is_reflex_adapt_two_player_item(item)
    ]

    raw_keys = {
        key
        for item in visible
        if item.get("hasRawCapture") is True
        for key in [requested_cleanup_duplicate_key(item)]
        if key is not None
    }
    result: list[dict[str, Any]] = []
    key_indexes: dict[tuple[str, ...], int] = {}

    for item in visible:
        key = requested_cleanup_duplicate_key(item)
        if key is not None and item.get("hasRawCapture") is not True and key in raw_keys:
            continue
        if key is not None and key in key_indexes:
            existing_index = key_indexes[key]
            if requested_cleanup_prefer_item(item, result[existing_index]):
                result[existing_index] = item
            continue
        if key is not None:
            key_indexes[key] = len(result)
        result.append(item)

    return result


def build_search_text(item: dict[str, Any]) -> str:
    measurement_name = normalize_text(item.get("measurementName"))
    parts = [
        item.get("name"),
        item.get("deviceNorm"),
        item.get("make"),
        item.get("model"),
        item.get("connection"),
        item.get("connectionKind"),
        item.get("wirelessConnection"),
        item.get("modeRaw"),
        item.get("outputMode"),
        item.get("connectionTag"),
        item.get("modeLabel"),
        item.get("modeDisplay"),
        item.get("deviceTypes"),
        item.get("rankMode"),
        item.get("resultType"),
        item.get("resultLabel"),
        item.get("category"),
        item.get("faceButtons"),
        item.get("homeButton"),
        item.get("weightOz"),
        item.get("averageTier"),
        item.get("p99Tier"),
        item.get("sheetTier"),
        item.get("adapterMode"),
        item.get("originalSystem"),
        item.get("saleStatus"),
        item.get("sourceStatus"),
        "open source" if item.get("isOpenSource") else "",
        item.get("sourceUrl"),
        item.get("platforms"),
        item.get("notes"),
        item.get("tester"),
        item.get("joystickId"),
        "raw capture" if item.get("hasRawCapture") else "",
        "buy link" if item.get("buyUrl") else "",
    ]
    if measurement_name and not is_reflex_adapt_pass_through_name(measurement_name):
        parts.append(measurement_name)
    flattened: list[str] = []
    for part in parts:
        if isinstance(part, list):
            flattened.extend(part)
        else:
            flattened.append(normalize_text(part))
    return " ".join(part.lower() for part in flattened if part)


def count_by(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = normalize_text(item.get(field)) or "Unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda pair: pair[0].lower()))


def count_list_by(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        values = item.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            label = normalize_text(value)
            if label:
                counts[label] = counts.get(label, 0) + 1

    order = {label: index for index, label in enumerate(DEVICE_TYPE_ORDER)}
    return dict(sorted(counts.items(), key=lambda pair: (order.get(pair[0], len(order)), pair[0].lower())))


def build_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    averages = [item["averageMs"] for item in items if item.get("averageMs") is not None]
    same_frame = [item["sameFramePct"] for item in items if item.get("sameFramePct") is not None]
    raw_count = sum(1 for item in items if item.get("hasRawCapture") is True)
    linked_count = sum(1 for item in items if item.get("buyUrl"))
    return {
        "totalItems": len(items),
        "publishedItems": sum(1 for item in items if item.get("resultType") == "published"),
        "privateItems": sum(1 for item in items if item.get("resultType") != "published"),
        "rawCaptureItems": raw_count,
        "rawCoveragePct": round(raw_count / len(items) * 100, 1) if items else 0,
        "linkedItems": linked_count,
        "bestAverageMs": round(min(averages), 3) if averages else None,
        "medianAverageMs": median(averages),
        "medianSameFramePct": median(same_frame),
        "resultTypes": count_by(items, "resultType"),
        "connectionKinds": count_by(items, "connectionKind"),
        "categories": count_by(items, "category"),
        "averageTiers": count_by(items, "averageTier"),
        "connectionTags": count_by(items, "connectionTag"),
        "outputModes": count_by(items, "outputMode"),
        "rankClasses": count_by(items, "rankMode"),
        "saleStatuses": count_by(items, "saleStatus"),
        "sourceStatuses": count_by(items, "sourceStatus"),
        "deviceTypes": count_list_by(items, "deviceTypes"),
    }


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[midpoint], 3)
    return round((ordered[midpoint - 1] + ordered[midpoint]) / 2, 3)


def unique_ids(items: list[dict[str, Any]]) -> None:
    seen: dict[str, int] = {}
    for item in items:
        item_id = item["id"]
        count = seen.get(item_id, 0)
        seen[item_id] = count + 1
        if count:
            item["id"] = f"{item_id}-{count + 1}"


def latency_item_sort_key(item: dict[str, Any]) -> tuple[float, str, str]:
    return (
        item["averageMs"] if item.get("averageMs") is not None else float("inf"),
        item.get("name", "").lower(),
        item.get("resultType", ""),
    )


def mode_variant_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {field: item.get(field) for field in MODE_VARIANT_FIELDS}


def earliest_date_added(items: list[dict[str, Any]]) -> tuple[str, str]:
    best_label = ""
    best_sort = ""
    for item in items:
        label = normalize_text(item.get("dateAdded"))
        sort_value = normalize_text(item.get("dateAddedSort")) or parse_date_added(label)
        if sort_value and (not best_sort or sort_value < best_sort):
            best_label = label or sort_value
            best_sort = sort_value
    return best_label, best_sort


def variant_search_text(variant: dict[str, Any]) -> str:
    measurement_name = normalize_text(variant.get("measurementName"))
    parts = [
        variant.get("name"),
        "" if is_reflex_adapt_pass_through_name(measurement_name) else measurement_name,
        variant.get("connection"),
        variant.get("connectionKind"),
        variant.get("wirelessConnection"),
        variant.get("connectionTag"),
        variant.get("modeRaw"),
        variant.get("outputMode"),
        variant.get("modeLabel"),
        variant.get("modeDisplay"),
        variant.get("deviceTypes"),
        variant.get("rankMode"),
        variant.get("averageTier"),
        variant.get("p99Tier"),
        variant.get("category"),
        variant.get("faceButtons"),
        variant.get("homeButton"),
        variant.get("weightOz"),
        variant.get("resultType"),
        variant.get("resultLabel"),
        variant.get("saleStatus"),
        variant.get("sourceStatus"),
        "open source" if variant.get("isOpenSource") else "",
        variant.get("sourceUrl"),
        variant.get("notes"),
        variant.get("tester"),
        variant.get("originalSystem"),
        variant.get("searchText"),
    ]
    return " ".join(normalize_text(part).lower() for part in parts if normalize_text(part))


def collapse_mode_variants(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(controller_group_key(item), []).append(item)

    collapsed: list[dict[str, Any]] = []
    for key, group_items in grouped.items():
        variants = sorted(group_items, key=latency_item_sort_key)
        representative = variants[0]
        variant_summaries = [mode_variant_summary(variant) for variant in variants]
        display_name = controller_group_display_name(representative)
        sanitized_name = sanitize_display_name(representative.get("name"))
        representative["controllerGroupKey"] = key
        representative["modeVariantCount"] = len(variant_summaries)
        representative["modeVariants"] = variant_summaries
        date_added, date_added_sort = earliest_date_added(variants)
        if date_added_sort:
            representative["dateAdded"] = date_added
            representative["dateAddedSort"] = date_added_sort
        should_rename = (
            len(variants) > 1
            or is_reflex_adapt_baseline_name(representative.get("name"))
            or is_reflex_adapt_adapter_item(representative)
            or (is_controller_adapter_item(representative) and is_daemonbite_name(representative.get("name")))
            or (is_controller_adapter_item(representative) and is_raphnet_name(representative.get("name")))
            or is_reflex_ctrl_name(representative.get("name"))
            or is_reflex_encode_fightboard_name(representative.get("name"))
            or is_mayflash_arcade_stick_name(representative.get("name"))
        )
        if should_rename:
            representative["name"] = display_name
            representative["deviceNorm"] = normalize_device_name(display_name)
            representative["id"] = f"{representative.get('resultType', 'result')}-{make_slug(display_name)}"
        elif sanitized_name and sanitized_name != normalize_text(representative.get("name")):
            representative["name"] = sanitized_name
            representative["deviceNorm"] = normalize_device_name(sanitized_name)
            representative["id"] = f"{representative.get('resultType', 'result')}-{make_slug(sanitized_name)}"
        representative["searchText"] = " ".join(
            [
                build_search_text(representative),
                " ".join(variant_search_text(variant) for variant in variant_summaries),
            ]
        ).strip()
        collapsed.append(representative)

    return sorted(collapsed, key=latency_item_sort_key)


def assign_latency_ranks(items: list[dict[str, Any]]) -> None:
    ranked_items = sorted([item for item in items if item.get("averageMs") is not None], key=latency_item_sort_key)
    for rank, item in enumerate(ranked_items, start=1):
        item["overallRank"] = rank
        item["rankMode"] = rank_class_for_item(item)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in ranked_items:
        rank_mode = normalize_text(item.get("rankMode"))
        if rank_mode:
            grouped.setdefault(rank_mode, []).append(item)

    for group_items in grouped.values():
        for rank, item in enumerate(group_items, start=1):
            item["modeRank"] = rank


def build_latency_payload(
    public_root: Path,
    private_root: Path | None = None,
    sheet_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    public_root = Path(public_root)
    private_root = Path(private_root) if private_root else None

    public_items = read_public_rows(public_root)
    private_items, private_source = read_private_rows(private_root)
    linked_items = augment_items_with_sheet_links(public_items + private_items, sheet_rows)
    catalog_items = [
        item
        for item in public_items + private_items
        if not is_excluded_latency_item(item)
    ]
    apply_reflex_adapt_pass_through_adjustments(catalog_items)
    apply_hori_wii_classic_adapter_adjustments(catalog_items)
    catalog_items = cleanup_requested_latency_items(catalog_items)
    items = sorted(
        catalog_items,
        key=latency_item_sort_key,
    )
    unique_ids(items)
    assign_latency_ranks(items)
    items = collapse_mode_variants(items)
    unique_ids(items)
    assign_latency_ranks(items)

    return {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "schemaVersion": 8,
        "sources": {
            "public": {
                "available": public_csv_path(public_root).exists(),
                "file": PUBLIC_CSV,
                "count": len(public_items),
            },
            "sheet": {
                "available": sheet_rows is not None,
                "count": len(sheet_rows or []),
                "linkedItems": linked_items,
            },
            "private": private_source,
        },
        "summary": build_summary(items),
        "items": items,
    }


def write_payload(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(payload, indent=2, ensure_ascii=False)
    output.write_text(json_text + "\n", encoding="utf-8")
    output.with_suffix(".js").write_text(
        "window.MISTER_LATENCY_DATA = " + json_text + ";\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MiSTer input latency explorer data")
    parser.add_argument("--public-root", type=Path, default=DEFAULT_PUBLIC_ROOT)
    parser.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE_ROOT)
    parser.add_argument("--include-private", action="store_true")
    parser.add_argument("--no-private", action="store_true")
    parser.add_argument("--sheet-csv", type=Path)
    parser.add_argument("--sheet-csv-url", default=DEFAULT_SHEET_CSV_URL)
    parser.add_argument("--no-sheet-links", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    private_root = args.private_root if args.include_private and not args.no_private else None
    sheet_rows = None
    if not args.no_sheet_links:
        if args.sheet_csv:
            sheet_rows = read_sheet_rows_from_path(args.sheet_csv)
        elif args.sheet_csv_url:
            try:
                sheet_rows = read_sheet_rows_from_url(args.sheet_csv_url)
            except OSError as error:
                print(f"Warning: could not load sheet product links: {error}", file=sys.stderr)
    payload = build_latency_payload(args.public_root, private_root, sheet_rows=sheet_rows)
    write_payload(payload, args.output)
    linked = payload["summary"].get("linkedItems", 0)
    print(f"Wrote {payload['summary']['totalItems']} latency rows to {args.output} ({linked} with product links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
