//
//  CaptureStep.swift  (watchOS)
//
//  Identical to the iOS version. Duplicated because iOS and Watch
//  targets don't share a module.
//

#if DEBUG
import Foundation

struct CaptureStep {
    let name: String
    let settle: Duration
    let cleanupSettle: Duration
    let navigate: @MainActor () async -> Void
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
