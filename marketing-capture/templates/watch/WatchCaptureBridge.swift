//
//  WatchCaptureBridge.swift
//
//  File-system handshake between the watchOS app and
//  `capture-marketing.sh`. The watch target cannot snapshot its own
//  UI, so screenshots are taken externally via `xcrun simctl io`.
//
//  Protocol per step:
//    1. App writes  `ready-<name>.marker`, begins polling.
//    2. Script sees marker, runs `xcrun simctl io screenshot`,
//       writes `shot-<name>.marker`.
//    3. App sees shot marker, deletes both, returns.
//

#if DEBUG
import Foundation

enum WatchCaptureBridge {

    // MARK: - Tuning

    private static let shotTimeout: Duration = .seconds(30)
    private static let pollInterval: Duration = .milliseconds(100)

    // MARK: - Marker filenames

    static func readyMarkerURL(stepName: String) -> URL {
        MarketingCapture.outputDirectory
            .appendingPathComponent("ready-\(stepName).marker")
    }

    static func shotMarkerURL(stepName: String) -> URL {
        MarketingCapture.outputDirectory
            .appendingPathComponent("shot-\(stepName).marker")
    }

    // MARK: - Public API

    /// Signals the script to take a screenshot and awaits confirmation.
    static func requestScreenshot(name: String) async {
        let ready = readyMarkerURL(stepName: name)
        let shot = shotMarkerURL(stepName: name)

        removeFileQuietly(at: shot)
        writeReadyMarker(at: ready, stepName: name)

        let ok = await waitForShotMarker(at: shot, stepName: name)

        removeFileQuietly(at: ready)
        removeFileQuietly(at: shot)

        if !ok {
            print(
                "[MarketingCapture][watch][bridge] ⚠︎ timed out"
                + " waiting for shot-\(name).marker; advancing anyway"
            )
        }
    }

    /// Deletes stale `ready-*` / `shot-*` markers from prior runs.
    static func purgeStaleMarkers() {
        let dir = MarketingCapture.outputDirectory
        let fm = FileManager.default
        guard let entries = try? fm.contentsOfDirectory(atPath: dir.path) else {
            return
        }
        for entry in entries
        where entry.hasPrefix("ready-") || entry.hasPrefix("shot-") {
            let url = dir.appendingPathComponent(entry)
            removeFileQuietly(at: url)
        }
    }

    // MARK: - Internals

    private static func writeReadyMarker(at url: URL, stepName: String) {
        let payload = "\(stepName)\t\(Date().timeIntervalSince1970)\n"
        do {
            try payload.data(using: .utf8)?.write(to: url, options: .atomic)
            print("[MarketingCapture][watch][bridge] ready: \(url.lastPathComponent)")
        } catch {
            print("[MarketingCapture][watch][bridge] ⚠︎ failed to write \(url.lastPathComponent): \(error.localizedDescription)")
        }
    }

    private static func waitForShotMarker(at url: URL, stepName: String) async -> Bool {
        let start = ContinuousClock.now
        let fm = FileManager.default
        while !fm.fileExists(atPath: url.path) {
            if ContinuousClock.now - start >= shotTimeout {
                return false
            }
            try? await Task.sleep(for: pollInterval)
        }
        let waited = ContinuousClock.now - start
        print("[MarketingCapture][watch][bridge] shot: \(url.lastPathComponent) after \(waited)")
        return true
    }

    private static func removeFileQuietly(at url: URL) {
        try? FileManager.default.removeItem(at: url)
    }
}

#endif // DEBUG
