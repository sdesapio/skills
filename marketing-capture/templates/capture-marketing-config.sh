#!/usr/bin/env bash
#
# capture-marketing.sh
# Automated marketing screenshot capture.
#
# Boots target simulators, builds & installs the app, launches it
# with the -MarketingCapture flag, and polls for a `_done` sentinel
# written by the in-app coordinator before advancing to the next
# locale.
#
# For iOS targets the app writes its own JPEG snapshots to the
# target directory before signalling `_done`. For watchOS the app
# writes `ready-<step>.marker` per step and this script responds
# with `xcrun simctl io <udid> screenshot` and a matching
# `shot-<step>.marker` handshake.
#
# Usage:
#   ./capture-marketing.sh                           # everything
#   ./capture-marketing.sh --target ios              # iOS only
#   ./capture-marketing.sh --target watch            # Watch only
#   ./capture-marketing.sh --device iphone-pro-max   # one device
#   ./capture-marketing.sh --locale en               # one locale
#   ./capture-marketing.sh --target ios --device iphone-pro-max --locale en  # smoke test
#
# Portable body: everything below `# === PORTABLE BODY ===` is
# project-agnostic and copies verbatim. Change only the CONFIG
# block when porting.
#
set -euo pipefail

# === CONFIG ===========================================================
# ── Edit this block for your project. Everything below PORTABLE BODY
# ── stays untouched.

WORKSPACE="__YOUR_PROJECT__.xcodeproj"
CONFIG="Debug"

# Target catalog. All arrays are parallel — one row per target.
# TARGET_KEYS values are the filter accepted by `--target` and must
# be filesystem-safe (they become path components under OUTPUT_DIR).
#
# iOS-only example:
#   TARGET_KEYS=(ios)
#   SCHEMES=("YourApp")
#   BUNDLE_IDS=("com.example.yourapp")
#   RUNTIMES=("com.apple.CoreSimulator.SimRuntime.iOS-26-2")
#   TARGET_CAPTURE_MODES=(ios)
#
# iOS + Watch example:
#   TARGET_KEYS=(ios watch)
#   SCHEMES=("YourApp" "YourApp Watch App")
#   BUNDLE_IDS=("com.example.yourapp" "com.example.yourapp.watchkitapp")
#   RUNTIMES=(
#       "com.apple.CoreSimulator.SimRuntime.iOS-26-2"
#       "com.apple.CoreSimulator.SimRuntime.watchOS-26-2"
#   )
#   TARGET_CAPTURE_MODES=(ios watch)

TARGET_KEYS=(ios)
SCHEMES=("__YOUR_SCHEME__")
BUNDLE_IDS=("__YOUR_BUNDLE_ID__")
RUNTIMES=("com.apple.CoreSimulator.SimRuntime.iOS-26-2")
TARGET_CAPTURE_MODES=(ios)

LOCALES=(en)

OUTPUT_DIR="$HOME/Pictures/MarketingCapture/__YOUR_APP__"

# Per-target device matrices. Keys become folder names under OUTPUT_DIR.
IOS_DEVICE_KEYS=(iphone-pro-max)
IOS_DEVICE_NAMES=("iPhone 17 Pro Max")

# Uncomment and populate if adding a watch target:
# WATCH_DEVICE_KEYS=(watch-ultra-3)
# WATCH_DEVICE_NAMES=("Apple Watch Ultra 3 (49mm)")

SENTINEL="_done"
POLL_INTERVAL=2
MAX_WAIT=360

WATCH_POLL_INTERVAL_MS=100

# === PORTABLE BODY ====================================================
# Everything below this line is project-agnostic. Do not edit when
# porting to another app.
