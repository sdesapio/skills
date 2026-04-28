# Marketing Capture — Project-Specific Examples

These examples are from a real interval-timer app. The types referenced
(`TimerManager`, `UserDefaultsKeys`, `TimerRunSeed`) are app-specific —
they illustrate the pattern, not the exact code you'll write. Read them
to understand the structure for the three project-specific files.

## Example: Capture Steps (`<App>CaptureSteps.swift`)

An `@MainActor` enum with a static `all` property returning `[CaptureStep]`. Each step has a `name` (output filename stem), a `navigate` closure to drive the UI, and an optional `cleanup` closure.

```swift
#if DEBUG
import Foundation
import UIKit

@MainActor
enum MyCaptureSteps {

    private static let sheetAppearSettle: Duration = .milliseconds(900)
    private static let seedRenderSettle: Duration = .milliseconds(1500)
    private static let dismissSettle: Duration = .milliseconds(1200)

    static var all: [CaptureStep] {
        var steps: [CaptureStep] = []
        steps.append(homeExpandedStep)
        steps.append(homeCollapsedStep)
        steps.append(contentsOf: timerRunSteps)
        steps.append(contentsOf: timerEditSteps)
        return steps
    }

    // Simple step — just flip a UserDefaults flag, snapshot the home view.
    private static var homeExpandedStep: CaptureStep {
        CaptureStep(
            name: "home-expanded",
            settle: .milliseconds(800),
            navigate: {
                UserDefaults.standard.set(false, forKey: UserDefaultsKeys.compactViewEnabled.key)
            }
        )
    }

    // Complex step — open a sheet via notification, wait for it, seed
    // mid-run state via another notification, then snapshot.
    private static var timerRunSteps: [CaptureStep] {
        TimerManager.defaultTimerUIDsInDisplayOrder.map { uid in
            let safeName = uid
                .replacingOccurrences(of: "default.", with: "")
                .replacingOccurrences(of: ".", with: "-")
            return CaptureStep(
                name: "timer-run-\(safeName)",
                settle: seedRenderSettle,
                cleanupSettle: dismissSettle,
                navigate: {
                    guard let timer = TimerManager.shared.timers.first(where: {
                        $0.defaultTimerUID == uid
                    }) else { return }

                    NotificationCenter.default.post(
                        name: MarketingNotifications.openTimerRun,
                        object: nil,
                        userInfo: [MarketingNotifications.Key.timerID: timer.id.uuidString]
                    )
                    try? await Task.sleep(for: sheetAppearSettle)

                    let seed = TimerRunSeed.seed(for: uid)
                    NotificationCenter.default.post(
                        name: MarketingNotifications.applyTimerSeed,
                        object: nil,
                        userInfo: [MarketingNotifications.Key.seed: seed]
                    )
                },
                cleanup: {
                    NotificationCenter.default.post(
                        name: MarketingNotifications.dismissSheet,
                        object: nil
                    )
                }
            )
        }
    }
}
#endif
```

Key patterns:
- Steps communicate with views via `NotificationCenter`. The step posts; the view observes and mutates `@State`.
- `navigate` is `async` — it can `Task.sleep` to wait for sheet animations before seeding state.
- `cleanup` dismisses whatever the step opened so the next step starts from a clean baseline.
- Settle durations are tuned empirically per animation type (sheet appear, render, dismiss).

## Example: Notifications (`MarketingNotifications.swift`)

```swift
#if DEBUG
import Foundation

enum MarketingNotifications {
    enum Key {
        static let timerID = "timerID"
        static let seed = "seed"
    }

    static let openTimerRun = Notification.Name("MyApp.MarketingCapture.openTimerRun")
    static let openTimerEdit = Notification.Name("MyApp.MarketingCapture.openTimerEdit")
    static let openSettings = Notification.Name("MyApp.MarketingCapture.openSettings")
    static let dismissSheet = Notification.Name("MyApp.MarketingCapture.dismissSheet")
    static let applyTimerSeed = Notification.Name("MyApp.MarketingCapture.applyTimerSeed")
}
#endif
```

One `Notification.Name` per navigation action. Views add `.onReceive` observers gated on `#if DEBUG` and `MarketingCapture.isActive`.

## Example: Setup (`MarketingCaptureSetup.swift`)

```swift
#if DEBUG
import Foundation

enum MarketingCaptureSetup {

    private static var originalValues: [String: Any?] = [:]

    static func applyIfActive() {
        guard MarketingCapture.isActive else { return }
        let defaults = UserDefaults.standard

        // Snapshot originals for restore
        for key in mutatedKeys {
            originalValues[key] = defaults.object(forKey: key)
        }

        // Force PRO subscription
        defaults.set(true, forKey: "debugSubscriptionOverrideEnabled")
        defaults.set(true, forKey: "debugSubscriptionOverride")

        // Force visual state
        defaults.set(true, forKey: "darkModeEnabled")
        defaults.set(false, forKey: "compactViewEnabled")
        defaults.set(true, forKey: "advancedModeEnabled")

        // Suppress all modals
        defaults.set(true, forKey: "hasCompletedOnboarding")
        defaults.set(true, forKey: "hasShownLegacyUserMessage")
        // ... etc

        defaults.synchronize()

        // Seed deterministic content
        installPresetTimers()
    }
}
#endif
```

The setup runs in `App.init()` *before* any manager initializes, so they read the overridden values on first load. The goal: every screenshot shows the app fully unlocked, fully populated, with all modals suppressed.

## Example: View Wiring (`HomeView.swift`)

```swift
.task {
    #if DEBUG
    if MarketingCapture.isActive {
        try? await Task.sleep(for: .milliseconds(1200))
        await MarketingCaptureCoordinator.shared.run(steps: MyCaptureSteps.all)
    }
    #endif
}

#if DEBUG
.onReceive(NotificationCenter.default.publisher(for: MarketingNotifications.openTimerRun)) { note in
    guard MarketingCapture.isActive,
          let idString = note.userInfo?[MarketingNotifications.Key.timerID] as? String,
          let id = UUID(uuidString: idString) else { return }
    selectedTimerForRun = id
    showingTimerRun = true
}
.onReceive(NotificationCenter.default.publisher(for: MarketingNotifications.dismissSheet)) { _ in
    guard MarketingCapture.isActive else { return }
    showingTimerRun = false
    showingEdit = false
    showingSettings = false
}
#endif
```
