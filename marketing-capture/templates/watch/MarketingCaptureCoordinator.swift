//
//  MarketingCaptureCoordinator.swift  (watchOS)
//
//  Watch-side twin of the iOS coordinator. Same step loop; capture
//  delegated to `WatchCaptureBridge` so the bash script can take the
//  screenshot externally via `xcrun simctl io`.
//

#if DEBUG
import Foundation

@MainActor
final class MarketingCaptureCoordinator {
    static let shared = MarketingCaptureCoordinator()
    private init() {}

    private var isRunning = false

    func run(steps: [CaptureStep]) async {
        guard !isRunning else {
            print("[MarketingCapture][watch] coordinator already running, ignoring duplicate call")
            return
        }
        isRunning = true
        defer { isRunning = false }

        print(
            "[MarketingCapture][watch] ▶ run"
            + " locale=\(MarketingCapture.localeFolder)"
            + " device=\(MarketingCapture.deviceFolder)"
            + " scheme=\(MarketingCapture.schemeFolder)"
            + " steps=\(steps.count)"
        )

        WatchCaptureBridge.purgeStaleMarkers()

        for (index, step) in steps.enumerated() {
            print("[MarketingCapture][watch] step \(index + 1)/\(steps.count): \(step.name)")

            await step.navigate()
            try? await Task.sleep(for: step.settle)
            await WatchCaptureBridge.requestScreenshot(name: step.name)

            if let cleanup = step.cleanup {
                await cleanup()
                try? await Task.sleep(for: step.cleanupSettle)
            }
        }

        MarketingCapture.writeSentinel()
        print("[MarketingCapture][watch] ■ done locale=\(MarketingCapture.localeFolder)")
    }
}

#endif // DEBUG
