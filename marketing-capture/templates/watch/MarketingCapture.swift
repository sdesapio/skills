//
//  MarketingCapture.swift  (watchOS)
//
//  Watch-side twin of the iOS `MarketingCapture` enum. Reads the same
//  launch arguments the bash script passes (`-MarketingCapture`,
//  `-MarketingLocale`, `-MarketingDeviceKey`, `-MarketingTargetKey`,
//  `-MarketingSchemeName`, `-MarketingOutputRoot`) and resolves the
//  same `<root>/<scheme>/<device>/<locale>/` output folder.
//
//  Key difference from the iOS version: the watchOS target cannot
//  render an arbitrary window snapshot in-process. Screenshots are
//  captured externally by the bash script via `xcrun simctl io`;
//  the app's job here is only to drive the UI into the target state
//  and coordinate with the script via sentinel files written into the
//  same output directory. See `WatchCaptureBridge` for the IPC.
//
//  Compiled out of Release builds via `#if DEBUG`. Zero bytes ship.
//

#if DEBUG
import Foundation

/// Project-agnostic façade over the launch-argument-driven capture system.
/// watchOS flavor — omits the UIKit image-writing API from its iOS
/// counterpart, keeps everything else byte-identical so step lists and
/// seed data are trivially portable between the two targets.
enum MarketingCapture {

    // MARK: - Activation

    /// True when the Watch app was launched with `-MarketingCapture 1`.
    static var isActive: Bool {
        let args = ProcessInfo.processInfo.arguments
        guard let idx = args.firstIndex(of: "-MarketingCapture"),
              idx + 1 < args.count else { return false }
        return args[idx + 1] == "1" || args[idx + 1].lowercased() == "true"
    }

    // MARK: - Launch arguments

    /// Locale folder, passed via `-MarketingLocale`. Falls back to the
    /// system language code.
    static var localeFolder: String {
        if let value = launchArgValue(for: "-MarketingLocale") {
            return value
        }
        return Locale.current.language.languageCode?.identifier
            ?? Locale.current.identifier
    }

    /// Device folder, passed via `-MarketingDeviceKey`. Falls back to
    /// `"watch"` so ad-hoc simulator runs still produce a sane folder.
    static var deviceFolder: String {
        if let value = launchArgValue(for: "-MarketingDeviceKey") {
            return value
        }
        return "watch"
    }

    /// Target-family key, passed via `-MarketingTargetKey`. Always
    /// defaults to `"watch"` on this target.
    static var targetKey: String {
        if let value = launchArgValue(for: "-MarketingTargetKey"), !value.isEmpty {
            return value
        }
        return "watch"
    }

    /// Scheme/app folder, passed via `-MarketingSchemeName`. Falls back
    /// to `CFBundleName` with spaces collapsed to hyphens so the result
    /// is filesystem-friendly.
    static var schemeFolder: String {
        if let value = launchArgValue(for: "-MarketingSchemeName") {
            return value.replacingOccurrences(of: " ", with: "-")
        }
        let name = (Bundle.main.object(forInfoDictionaryKey: "CFBundleName") as? String)
            ?? (Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String)
            ?? "WatchApp"
        return name.replacingOccurrences(of: " ", with: "-")
    }

    /// Reads a launch arg value by flag name.
    static func launchArgValue(for flag: String) -> String? {
        let args = ProcessInfo.processInfo.arguments
        guard let idx = args.firstIndex(of: flag), idx + 1 < args.count else {
            return nil
        }
        return args[idx + 1]
    }

    // MARK: - Output paths

    /// Filename the bash script polls for at the end of a run.
    static let sentinelFilename = "_done"

    /// Base output directory. Resolved in priority order:
    /// 1. `-MarketingOutputRoot <path>` launch arg.
    /// 2. `~/Pictures/MarketingCapture/<bundleIdentifier>` fallback.
    static var baseOutputDirectory: URL {
        if let path = launchArgValue(for: "-MarketingOutputRoot"), !path.isEmpty {
            return URL(fileURLWithPath: path, isDirectory: true)
        }
        let bundleID = Bundle.main.bundleIdentifier ?? "UnknownWatchApp"
        let home = URL(fileURLWithPath: NSHomeDirectory(), isDirectory: true)
        return home
            .appendingPathComponent("Pictures", isDirectory: true)
            .appendingPathComponent("MarketingCapture", isDirectory: true)
            .appendingPathComponent(bundleID, isDirectory: true)
    }

    /// Full output directory for the current run.
    /// `<base>/<scheme>/<device>/<locale>/`. Created on demand.
    static var outputDirectory: URL {
        let root = baseOutputDirectory
            .appendingPathComponent(schemeFolder, isDirectory: true)
            .appendingPathComponent(deviceFolder, isDirectory: true)
            .appendingPathComponent(localeFolder, isDirectory: true)
        try? FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }

    // MARK: - Sentinel

    /// Writes the `_done` sentinel file the bash script polls for.
    /// Call exactly once at the end of a capture run.
    static func writeSentinel() {
        let url = outputDirectory.appendingPathComponent(sentinelFilename)
        try? Data().write(to: url)
        print("[MarketingCapture][watch] sentinel written: \(url.path)")
    }
}

// MARK: - Output path unit test hook

extension MarketingCapture {
    /// Test-friendly path resolver — matches the iOS version so shared
    /// tests can exercise both.
    static func resolveOutputDirectory(
        outputRoot: String,
        scheme: String,
        device: String,
        locale: String
    ) -> URL {
        let safeScheme = scheme.replacingOccurrences(of: " ", with: "-")
        return URL(fileURLWithPath: outputRoot, isDirectory: true)
            .appendingPathComponent(safeScheme, isDirectory: true)
            .appendingPathComponent(device, isDirectory: true)
            .appendingPathComponent(locale, isDirectory: true)
    }
}

#endif // DEBUG
