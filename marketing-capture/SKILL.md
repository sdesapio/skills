---
name: marketing-capture
description: >-
  Add automated App Store screenshot capture to an iOS (and optionally watchOS)
  project. Installs portable Swift files and a bash orchestration script, then
  guides creation of project-specific capture steps, notification glue, and
  deterministic setup. Use when the user says "build the screen capture
  mechanism", "add marketing screenshots", "set up automated App Store
  captures", or similar.
---

# Marketing Screenshot Capture

Automated system for generating App Store screenshots across devices and
locales. A bash script boots simulators, builds/installs the app, launches
it with `-MarketingCapture 1`, and the in-app coordinator drives the UI
through a scripted sequence of `CaptureStep`s, snapshotting each one.

## How it works

```
capture-marketing.sh
  └── for each target (ios, watch)
        └── for each device
              ├── boot simulator
              ├── xcodebuild → install .app
              └── for each locale
                    ├── launch with -MarketingCapture 1
                    ├── iOS: app writes JPEGs, script polls for _done
                    ├── Watch: app writes ready-*.marker, script screenshots via simctl, writes shot-*.marker
                    └── terminate app
```

iOS captures are taken in-process via `WindowSnapshot` (composites all
`UIWindowScene` windows). Watch captures use `xcrun simctl io screenshot`
externally, coordinated via filesystem marker handshake (`WatchCaptureBridge`).

## Compatibility

- iOS 16+ (SwiftUI `List`/`Form` backed by `UICollectionView` for `ListPager`)
- watchOS 10+ (for `WatchCaptureBridge` filesystem access in simulator)
- Xcode 16+ / Swift 5.9+ (`Duration` type, async closures)

## Template files

All templates live in this skill's `templates/` directory, relative to
this `SKILL.md` file.

```
templates/
├── ios/
│   ├── MarketingCapture.swift              # launch arg parsing, output paths, JPEG writing
│   ├── CaptureStep.swift                   # step struct (name, settle, navigate, cleanup)
│   ├── WindowSnapshot.swift                # UIWindowScene compositor
│   ├── MarketingCaptureCoordinator.swift   # step walker, sentinel writer
│   └── ListPager.swift                     # paginated scroll-and-capture for long lists
├── watch/
│   ├── MarketingCapture.swift              # watch twin (no UIKit image writing)
│   ├── CaptureStep.swift                   # identical to iOS copy
│   ├── MarketingCaptureCoordinator.swift   # delegates capture to WatchCaptureBridge
│   └── WatchCaptureBridge.swift            # filesystem marker handshake IPC
├── capture-marketing-config.sh             # CONFIG block template (edit per project)
└── capture-marketing-body.sh               # portable body (never edit)
```

## Installation steps

### 1. Copy iOS portable files

Read and copy these 5 files verbatim from `templates/ios/` into a
`Screenshotting/` group in the project's iOS target:

- `MarketingCapture.swift`
- `CaptureStep.swift`
- `WindowSnapshot.swift`
- `MarketingCaptureCoordinator.swift`
- `ListPager.swift`

Do not modify these files. They are project-agnostic.

### 2. Create the shell script

Read `templates/capture-marketing-config.sh` and
`templates/capture-marketing-body.sh`. Concatenate them into a single
`capture-marketing.sh` at the project root. Then edit the CONFIG block:

- `WORKSPACE` — the `.xcodeproj` filename
- `SCHEMES` / `BUNDLE_IDS` — from the project's targets
- `RUNTIMES` — match installed simulator runtimes
- `TARGET_KEYS` / `TARGET_CAPTURE_MODES` — `(ios)` for iOS-only, `(ios watch)` for both
- `LOCALES` — which locales to capture
- `OUTPUT_DIR` — where screenshots land
- `IOS_DEVICE_KEYS` / `IOS_DEVICE_NAMES` — App Store device matrix
- `WATCH_DEVICE_KEYS` / `WATCH_DEVICE_NAMES` — if watch target exists

Determine values from the project's `.xcodeproj`, scheme list, and
`Info.plist` / build settings. Ask the user for `OUTPUT_DIR` and `LOCALES`
if not obvious.

Make the script executable: `chmod +x capture-marketing.sh`.

### 3. Write project-specific Swift files

Create 3 files in the same `Screenshotting/` group, all `#if DEBUG`:

**a) `<App>CaptureSteps.swift`**

An `@MainActor` enum with `static var all: [CaptureStep]`. Each step:

- `name`: output filename stem (no extension, no path)
- `settle`: wait after navigate before snapshot (tune per animation)
- `navigate`: async closure that drives the UI to the desired state
- `cleanup`: optional async closure to dismiss/reset for the next step

Steps communicate with views via `NotificationCenter`. The step posts a
notification; the view observes it (gated on `MarketingCapture.isActive`)
and mutates `@State` to navigate.

Read [examples.md](examples.md) for a working implementation pattern.

**b) `MarketingNotifications.swift`**

An enum declaring `Notification.Name` constants — one per navigation action
the steps need (open sheet, dismiss sheet, seed state, etc.). Plus a `Key`
enum for `userInfo` dictionary keys.

**c) `MarketingCaptureSetup.swift`**

An enum with `static func applyIfActive()` that:

1. Guards on `MarketingCapture.isActive`
2. Snapshots current `UserDefaults` values for restorability
3. Forces the app into a deterministic, fully-unlocked state:
   - Subscription/entitlement active (via whatever debug override the app has)
   - Onboarding / first-run / update modals marked as already shown
   - Preferred visual state (dark mode, expanded view, etc.)
   - Sample/seed data installed
4. Calls `defaults.synchronize()`

This must run in `App.init()` **before** any manager or view model initializes.

### 4. Wire into the app

**`App.init()`:**
```swift
init() {
    #if DEBUG
    MarketingCaptureSetup.applyIfActive()
    #endif
    // ... existing init ...
}
```

**Root view `.task`:**
```swift
.task {
    #if DEBUG
    if MarketingCapture.isActive {
        try? await Task.sleep(for: .milliseconds(1200))
        await MarketingCaptureCoordinator.shared.run(steps: <App>CaptureSteps.all)
    }
    #endif
}
```

**View observers** (on root view and any target views):
```swift
#if DEBUG
.onReceive(NotificationCenter.default.publisher(for: MarketingNotifications.<name>)) { note in
    guard MarketingCapture.isActive else { return }
    // mutate @State to navigate
}
#endif
```

### 5. Watch target (only if the app has one)

1. Copy 4 files from `templates/watch/` into the Watch target's `Screenshotting/` group.
2. Write 3 watch-specific files: `WatchCaptureSteps.swift`, `WatchMarketingNotifications.swift`, `WatchMarketingCaptureSetup.swift`.
3. Wire `WatchMarketingCaptureSetup.applyIfActive()` into the Watch `App.init()`.
4. Launch coordinator from the Watch root view's `.task`.
5. Update `capture-marketing.sh` CONFIG: add `watch` to `TARGET_KEYS`, `SCHEMES`, `BUNDLE_IDS`, `RUNTIMES`, `TARGET_CAPTURE_MODES`; define `WATCH_DEVICE_KEYS` / `WATCH_DEVICE_NAMES`.

Watch captures require iOS captures to have run first for the same locale
(iOS populates data files the Watch app reads in simulator mode).

### 6. Verify

- `./capture-marketing.sh --target ios --device <first-device> --locale en` for a smoke test
- Check output directory for JPEGs with correct naming
- Confirm all steps completed (check console for `[MarketingCapture] ■ done`)

## Key constraints

- All `Screenshotting/` code is `#if DEBUG`. Zero bytes ship in Release.
- The coordinator is `@MainActor` — all UI mutations happen on main.
- `navigate` closures are `async` — they can sleep to wait for animations.
- Steps run serially. No parallelism within a locale run.
- The 1.2s initial sleep in the `.task` gives the SwiftUI nav stack time to settle. Adjust if the root view has slow-loading data.

## Additional resources

- [examples.md](examples.md) — Examples of steps, notifications, setup, and view wiring from a real project.
