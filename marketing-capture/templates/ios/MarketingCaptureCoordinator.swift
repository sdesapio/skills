//
//  MarketingCaptureCoordinator.swift
//
//  Walks an array of `CaptureStep`s in order: run each step's async
//  `navigate`, wait `settle`, snapshot the window, write JPEG, run
//  optional cleanup, wait `cleanupSettle`, repeat. Writes the `_done`
//  sentinel when the whole list finishes so the bash script knows to
//  advance to the next locale.
//
//  Project-agnostic. The step list is built per-project and handed in.
//

#if DEBUG
import Foundation

#if canImport(UIKit) && !os(watchOS)
import UIKit
#endif

@MainActor
final class MarketingCaptureCoordinator {
    static let shared = MarketingCaptureCoordinator()
    private init() {}

    private var isRunning = false

    /// Runs the step list. Safe to call multiple times — subsequent calls
    /// while a run is in flight are ignored. Writes `_done` at the end
    /// regardless of whether individual snapshots succeeded.
    func run(steps: [CaptureStep]) async {
        guard !isRunning else {
            print("[MarketingCapture] coordinator already running, ignoring duplicate call")
            return
        }
        isRunning = true
        defer { isRunning = false }

        print("[MarketingCapture] ▶ run locale=\(MarketingCapture.localeFolder) device=\(MarketingCapture.deviceFolder) scheme=\(MarketingCapture.schemeFolder) steps=\(steps.count)")

        for (index, step) in steps.enumerated() {
            print("[MarketingCapture] step \(index + 1)/\(steps.count): \(step.name)")

            await step.navigate()
            try? await Task.sleep(for: step.settle)

            #if canImport(UIKit) && !os(watchOS)
            if let image = WindowSnapshot.capture() {
                MarketingCapture.writeImage(image, name: step.name)
            } else {
                print("[MarketingCapture] snapshot failed: \(step.name)")
            }
            #endif

            if let cleanup = step.cleanup {
                await cleanup()
                try? await Task.sleep(for: step.cleanupSettle)
            }
        }

        MarketingCapture.writeSentinel()
        print("[MarketingCapture] ■ done locale=\(MarketingCapture.localeFolder)")
    }
}

#endif // DEBUG
