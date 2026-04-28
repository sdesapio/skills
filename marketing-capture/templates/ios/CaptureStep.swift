//
//  CaptureStep.swift
//
//  One unit of work in a capture run: navigate somewhere, let the UI
//  settle, snapshot, optionally clean up. Project-agnostic — the step
//  list is built per-project.
//

#if DEBUG
import Foundation

/// A single screen to capture. The coordinator walks an array of these
/// in order: `navigate()` → sleep(`settle`) → snapshot → optional
/// `cleanup()` → sleep(`cleanupSettle`).
struct CaptureStep {
    /// Filename stem for the output JPEG. No extension, no path.
    let name: String

    /// How long to wait after `navigate()` returns before taking the
    /// snapshot. Tune to match the slowest animation on the target
    /// screen (sheet presentation, progress bar growth, etc.).
    let settle: Duration

    /// How long to wait after `cleanup()` returns before starting the
    /// next step. Defaults to 600ms, which is enough for a sheet
    /// dismiss animation on a fast simulator.
    let cleanupSettle: Duration

    /// Drives the app to the state we want to capture. Can await
    /// anything needed (animations, state seeding, etc.).
    let navigate: @MainActor () async -> Void

    /// Optional teardown (dismiss sheets, reset state) so the next
    /// step starts from a known baseline.
    let cleanup: (@MainActor () async -> Void)?

    init(
        name: String,
        settle: Duration = .milliseconds(1200),
        cleanupSettle: Duration = .milliseconds(600),
        navigate: @escaping @MainActor () async -> Void,
        cleanup: (@MainActor () async -> Void)? = nil
    ) {
        self.name = name
        self.settle = settle
        self.cleanupSettle = cleanupSettle
        self.navigate = navigate
        self.cleanup = cleanup
    }
}

#endif // DEBUG
