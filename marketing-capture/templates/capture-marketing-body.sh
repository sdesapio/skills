
FILTER_TARGET=""
FILTER_DEVICE=""
FILTER_LOCALE=""
FILTER_STEP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) FILTER_TARGET="$2"; shift 2 ;;
        --device) FILTER_DEVICE="$2"; shift 2 ;;
        --locale) FILTER_LOCALE="$2"; shift 2 ;;
        --step)   FILTER_STEP="$2";   shift 2 ;;
        -h|--help)
            grep -E '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -n "$FILTER_TARGET" ]]; then
    found=0
    for k in "${TARGET_KEYS[@]}"; do
        [[ "$k" == "$FILTER_TARGET" ]] && found=1 && break
    done
    if [[ $found -eq 0 ]]; then
        echo "Unknown --target '$FILTER_TARGET'. Valid: ${TARGET_KEYS[*]}"
        exit 1
    fi
fi

log() { echo "[capture] $*"; }

sim_udid() {
    local device_name="$1"
    local runtime="$2"
    xcrun simctl list devices available -j \
        | python3 -c "
import json, sys
data = json.load(sys.stdin)
runtime_key = '$runtime'
for rt, devs in data['devices'].items():
    if runtime_key not in rt:
        continue
    for d in devs:
        if d['name'] == '$device_name' and d['isAvailable']:
            print(d['udid']); sys.exit(0)
print('NOT_FOUND', file=sys.stderr)
sys.exit(1)"
}

watch_pair_udids() {
    local watch_name="$1"
    xcrun simctl list pairs -j \
        | python3 -c "
import json, sys
data = json.load(sys.stdin)
watch_name = '$watch_name'
best = None
for pair_id, pair in data['pairs'].items():
    if pair['watch']['name'] == watch_name:
        is_active = '(active' in pair.get('state', '')
        if best is None or (is_active and '(active' not in best[2]):
            best = (pair['watch']['udid'], pair['phone']['udid'], pair.get('state', ''))
if best:
    print(best[0])
    print(best[1])
    sys.exit(0)
print('NOT_FOUND', file=sys.stderr)
sys.exit(1)"
}

wait_for_sentinel_ios() {
    local target_dir="$1"
    local waited=0

    local sentinel_path="$target_dir/$SENTINEL"
    log "    Waiting for sentinel: $sentinel_path"

    while [[ ! -f "$sentinel_path" ]]; do
        sleep "$POLL_INTERVAL"
        waited=$((waited + POLL_INTERVAL))
        if [[ $waited -ge $MAX_WAIT ]]; then
            log "    ERROR: Timed out after ${MAX_WAIT}s waiting for $sentinel_path"
            return 1
        fi
    done
    log "    Sentinel found after ${waited}s"
}

wait_for_sentinel_watch() {
    local target_dir="$1"
    local udid="$2"
    local sentinel_path="$target_dir/$SENTINEL"
    local elapsed_ms=0
    local total_shots=0

    log "    Waiting for ready markers / sentinel in: $target_dir"

    local poll_s
    poll_s=$(python3 -c "print($WATCH_POLL_INTERVAL_MS/1000.0)")

    while :; do
        if [[ -f "$sentinel_path" ]]; then
            log "    Sentinel found (${total_shots} shots taken)"
            return 0
        fi

        while IFS= read -r ready_marker; do
            local fname step shot_marker out_png
            fname=$(basename "$ready_marker")
            step="${fname#ready-}"
            step="${step%.marker}"
            shot_marker="$target_dir/shot-${step}.marker"
            out_png="$target_dir/${step}.png"

            if [[ -f "$shot_marker" ]]; then
                continue
            fi

            log "    » $step — taking screenshot"
            if xcrun simctl io "$udid" screenshot "$out_png" >/dev/null 2>&1; then
                : > "$shot_marker"
                total_shots=$((total_shots + 1))
            else
                log "    ⚠︎ screenshot failed for $step"
                : > "$shot_marker"
            fi
        done < <(find "$target_dir" -maxdepth 1 -name 'ready-*.marker' -type f 2>/dev/null)

        sleep "$poll_s"
        elapsed_ms=$((elapsed_ms + WATCH_POLL_INTERVAL_MS))
        if [[ $elapsed_ms -ge $((MAX_WAIT * 1000)) ]]; then
            log "    ERROR: Timed out after ${MAX_WAIT}s waiting for sentinel"
            return 1
        fi
    done
}

open -a Simulator

for ti in "${!TARGET_KEYS[@]}"; do
    TARGET_KEY="${TARGET_KEYS[$ti]}"
    SCHEME="${SCHEMES[$ti]}"
    BUNDLE_ID="${BUNDLE_IDS[$ti]}"
    RUNTIME="${RUNTIMES[$ti]}"
    CAPTURE_MODE="${TARGET_CAPTURE_MODES[$ti]}"

    if [[ -n "$FILTER_TARGET" && "$TARGET_KEY" != "$FILTER_TARGET" ]]; then
        continue
    fi

    log "╔═════════════════════════════════════════════════════════"
    log "║ Target: $TARGET_KEY (scheme: $SCHEME, mode: $CAPTURE_MODE)"
    log "╚═════════════════════════════════════════════════════════"

    if [[ "$TARGET_KEY" == "ios" ]]; then
        DEVICE_KEYS=("${IOS_DEVICE_KEYS[@]}")
        DEVICE_NAMES=("${IOS_DEVICE_NAMES[@]}")
        PRODUCTS_SUBDIR="${CONFIG}-iphonesimulator"
    elif [[ "$TARGET_KEY" == "watch" ]]; then
        DEVICE_KEYS=("${WATCH_DEVICE_KEYS[@]}")
        DEVICE_NAMES=("${WATCH_DEVICE_NAMES[@]}")
        PRODUCTS_SUBDIR="${CONFIG}-watchsimulator"
    else
        log "ERROR: unknown target '$TARGET_KEY' — no device matrix defined"
        continue
    fi

    for di in "${!DEVICE_KEYS[@]}"; do
        DEVICE_KEY="${DEVICE_KEYS[$di]}"
        DEVICE_NAME="${DEVICE_NAMES[$di]}"

        if [[ -n "$FILTER_DEVICE" && "$DEVICE_KEY" != "$FILTER_DEVICE" ]]; then
            continue
        fi

        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log "Device: $DEVICE_NAME ($DEVICE_KEY)"
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        COMPANION_PHONE_UDID=""

        if [[ "$CAPTURE_MODE" == "watch" ]]; then
            pair_output=$(watch_pair_udids "$DEVICE_NAME" 2>&1) || true
            UDID=$(echo "$pair_output" | sed -n '1p')
            COMPANION_PHONE_UDID=$(echo "$pair_output" | sed -n '2p')

            if [[ -z "$UDID" || "$UDID" == "NOT_FOUND" || -z "$COMPANION_PHONE_UDID" ]]; then
                log "ERROR: No paired iPhone found for Watch '$DEVICE_NAME'"
                log "  Pair one in Simulator → Window → Devices and Simulators,"
                log "  or run: xcrun simctl pair <watch-udid> <phone-udid>"
                continue
            fi
            log "UDID: $UDID (from active pair)"
            log "Companion iPhone UDID: $COMPANION_PHONE_UDID"
        else
            UDID=$(sim_udid "$DEVICE_NAME" "$RUNTIME")
            if [[ -z "$UDID" || "$UDID" == "NOT_FOUND" ]]; then
                log "ERROR: No simulator found for '$DEVICE_NAME' with runtime $RUNTIME"
                log "  Run: xcrun simctl create \"$DEVICE_NAME\" \"$DEVICE_NAME\" $RUNTIME"
                continue
            fi
            log "UDID: $UDID"
        fi

        xcrun simctl shutdown all 2>/dev/null || true
        sleep 1

        if [[ -n "$COMPANION_PHONE_UDID" ]]; then
            xcrun simctl boot "$COMPANION_PHONE_UDID" 2>/dev/null || true
            sleep 2
        fi
        xcrun simctl boot "$UDID" 2>/dev/null || true
        sleep 4

        log "  ━━━ Building: $SCHEME (target: $TARGET_KEY) ━━━"

        xcodebuild \
            -project "$WORKSPACE" \
            -scheme "$SCHEME" \
            -configuration "$CONFIG" \
            -destination "id=$UDID" \
            -derivedDataPath build \
            build \
            ONLY_ACTIVE_ARCH=YES \
            2>&1 | tail -5

        APP_PATH=$(find "build/Build/Products/$PRODUCTS_SUBDIR" -name "$SCHEME.app" -maxdepth 1 2>/dev/null || true)

        if [[ -z "$APP_PATH" ]]; then
            log "    ERROR: Could not find .app for $SCHEME under $PRODUCTS_SUBDIR"
            continue
        fi

        log "    Installing $APP_PATH"
        xcrun simctl install "$UDID" "$APP_PATH"

        SAFE_SCHEME=$(echo "$SCHEME" | tr ' ' '-')

        for LOCALE in "${LOCALES[@]}"; do
            if [[ -n "$FILTER_LOCALE" && "$LOCALE" != "$FILTER_LOCALE" ]]; then
                continue
            fi

            log "    ── Locale: $LOCALE ──"

            TARGET_DIR="$OUTPUT_DIR/$SAFE_SCHEME/$DEVICE_KEY/$LOCALE"
            mkdir -p "$TARGET_DIR"
            rm -f "$TARGET_DIR/$SENTINEL" 2>/dev/null || true
            find "$TARGET_DIR" -maxdepth 1 \( -name 'ready-*.marker' -o -name 'shot-*.marker' \) -type f -delete 2>/dev/null || true

            LAUNCH_ARGS=(
                "$UDID" "$BUNDLE_ID"
                -MarketingCapture 1
                -MarketingLocale "$LOCALE"
                -MarketingDeviceKey "$DEVICE_KEY"
                -MarketingTargetKey "$TARGET_KEY"
                -MarketingSchemeName "$SAFE_SCHEME"
                -MarketingOutputRoot "$OUTPUT_DIR"
            )
            if [[ -n "$FILTER_STEP" ]]; then
                LAUNCH_ARGS+=( -MarketingStepFilter "$FILTER_STEP" )
            fi
            LAUNCH_ARGS+=(
                -AppleLanguages "($LOCALE)"
                -AppleLocale "$LOCALE"
            )

            xcrun simctl launch "${LAUNCH_ARGS[@]}"

            if [[ "$CAPTURE_MODE" == "watch" ]]; then
                wait_for_sentinel_watch "$TARGET_DIR" "$UDID"
            else
                wait_for_sentinel_ios "$TARGET_DIR"
            fi

            xcrun simctl terminate "$UDID" "$BUNDLE_ID" 2>/dev/null || true
            sleep 1
        done

        xcrun simctl shutdown "$UDID" 2>/dev/null || true
        if [[ -n "$COMPANION_PHONE_UDID" ]]; then
            xcrun simctl shutdown "$COMPANION_PHONE_UDID" 2>/dev/null || true
        fi
    done
done

log "━━━ Done! Screenshots in $OUTPUT_DIR ━━━"
