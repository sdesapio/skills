//
//  ListPager.swift
//
//  Finds the tallest visible `UICollectionView` (SwiftUI `List` and
//  `Form` are backed by one on iOS 16+), then scrolls it page-by-page,
//  snapshotting at each offset. Stops when the scroll view reaches the
//  bottom or `maxPages` is hit.
//
//  Project-agnostic — can be dropped into any SwiftUI app with a
//  `List` or `Form` that needs multi-page captures.
//

#if DEBUG && canImport(UIKit) && !os(watchOS)
import UIKit

enum ListPager {

    /// Captures a tall scrollable view page-by-page. Writes JPEGs named
    /// `<baseName>-p1`, `<baseName>-p2`, ... Returns the number of
    /// pages written (always ≥ 1).
    @MainActor
    @discardableResult
    static func capturePages(baseName: String, maxPages: Int = 20) async -> Int {
        try? await Task.sleep(for: .milliseconds(600))

        guard let cv = findTallestCollectionView() else {
            print("[ListPager] no collection view — single-page fallback for \(baseName)")
            if let image = WindowSnapshot.capture() {
                MarketingCapture.writeImage(image, name: "\(baseName)-p1")
            }
            return 1
        }

        print("[ListPager] \(baseName): content=\(Int(cv.contentSize.height)) viewport=\(Int(cv.bounds.height))")

        var pagesWritten = 0

        for page in 0..<maxPages {
            try? await Task.sleep(for: .milliseconds(page == 0 ? 100 : 400))

            if let image = WindowSnapshot.capture() {
                MarketingCapture.writeImage(image, name: "\(baseName)-p\(page + 1)")
                pagesWritten += 1
            } else {
                print("[ListPager] snapshot failed: \(baseName)-p\(page + 1)")
            }

            let currentMaxY = cv.contentSize.height
                + cv.adjustedContentInset.bottom
                - cv.bounds.height

            if cv.contentOffset.y >= currentMaxY - 1 { break }

            let nextY = nextPageOffset(for: cv) ?? currentMaxY
            var target = min(nextY, currentMaxY)

            if target <= cv.contentOffset.y + 1 {
                target = currentMaxY
            }
            if target <= cv.contentOffset.y + 1 { break }

            cv.setContentOffset(CGPoint(x: 0, y: target), animated: false)
        }

        return max(pagesWritten, 1)
    }

    // MARK: - Collection view discovery

    @MainActor
    static func findTallestCollectionView() -> UICollectionView? {
        if let presentedView = topmostPresentedView() {
            var best: UICollectionView?
            var bestHeight: CGFloat = 0
            findCollectionView(in: presentedView, best: &best, bestHeight: &bestHeight)
            if best != nil { return best }
        }

        var best: UICollectionView?
        var bestHeight: CGFloat = 0
        for scene in UIApplication.shared.connectedScenes {
            guard let ws = scene as? UIWindowScene else { continue }
            for window in ws.windows where !window.isHidden && window.alpha > 0 {
                findCollectionView(in: window, best: &best, bestHeight: &bestHeight)
            }
        }
        return best
    }

    @MainActor
    private static func topmostPresentedView() -> UIView? {
        for scene in UIApplication.shared.connectedScenes {
            guard let ws = scene as? UIWindowScene else { continue }
            for window in ws.windows where !window.isHidden && window.alpha > 0 {
                var vc = window.rootViewController
                var topPresented: UIViewController?
                while let next = vc?.presentedViewController {
                    topPresented = next
                    vc = next
                }
                if let topPresented { return topPresented.view }
            }
        }
        return nil
    }

    @MainActor
    private static func findCollectionView(
        in view: UIView,
        best: inout UICollectionView?,
        bestHeight: inout CGFloat
    ) {
        if let cv = view as? UICollectionView, cv.contentSize.height > bestHeight {
            best = cv
            bestHeight = cv.contentSize.height
        }
        for child in view.subviews {
            findCollectionView(in: child, best: &best, bestHeight: &bestHeight)
        }
    }

    // MARK: - Page offset math

    @MainActor
    private static func nextPageOffset(for cv: UICollectionView) -> CGFloat? {
        let insets = cv.adjustedContentInset
        let offsetY = cv.contentOffset.y
        let visibleBottom = offsetY + cv.bounds.height - insets.bottom

        let visibleRect = CGRect(
            x: 0,
            y: offsetY + insets.top,
            width: cv.bounds.width,
            height: cv.bounds.height - insets.top - insets.bottom
        )

        guard let attrs = cv.collectionViewLayout
            .layoutAttributesForElements(in: visibleRect) else { return nil }

        let rows = attrs
            .filter { $0.representedElementCategory != .decorationView && $0.frame.height > 1 }
            .sorted { $0.frame.minY < $1.frame.minY }

        guard let last = rows.last(where: { $0.frame.minY < visibleBottom }) else {
            return nil
        }

        return last.frame.minY - insets.top
    }
}

#endif // DEBUG && UIKit && !watchOS
