//
//  WindowSnapshot.swift
//
//  Captures the entire visible UI of an iOS app, including windows that
//  live in auxiliary `UIWindowScene`s (the software keyboard, alerts,
//  system overlays). Walks every connected scene so nothing important
//  is missed.
//
//  Project-agnostic. Zero knowledge of the host app.
//

#if DEBUG && canImport(UIKit) && !os(watchOS)
import UIKit

enum WindowSnapshot {

    /// Renders the current screen as a single `UIImage`. Layers all
    /// visible windows across all connected scenes in `windowLevel`
    /// order so the keyboard / alerts / overlays are included.
    ///
    /// Returns `nil` only if there is no visible window at all.
    @MainActor
    static func capture() -> UIImage? {
        let allWindows = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .filter { !$0.isHidden && $0.alpha > 0 }
            .sorted { $0.windowLevel.rawValue < $1.windowLevel.rawValue }

        guard let bounds = allWindows.first?.screen.bounds else { return nil }

        let renderer = UIGraphicsImageRenderer(bounds: bounds)
        return renderer.image { _ in
            for window in allWindows {
                window.drawHierarchy(in: window.frame, afterScreenUpdates: true)
            }
        }
    }
}

#endif // DEBUG && UIKit && !watchOS
