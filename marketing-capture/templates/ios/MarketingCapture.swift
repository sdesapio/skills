//
//  MarketingCapture.swift
//
//  Project-agnostic core of the automated marketing screenshot system.
//  Activated by launching the app with `-MarketingCapture 1`. Reads locale,
//  device, scheme, and output root from launch arguments passed by
//  `capture-marketing.sh`. Writes JPEGs and a `_done` sentinel file that
//  the bash script polls for to advance to the next locale/step.
//
//  This file has no knowledge of the host app — it is intended to be copied
//  verbatim into other apps. Project-specific glue (capture step list,
//  setup defaults, seed data, notification names) lives alongside this
//  file but in separate *-specific files.
//
//  Compiled out of Release builds via #if DEBUG. Zero bytes ship.
//

#if DEBUG
import Foundation

#if canImport(UIKit) && !os(watchOS)
import UIKit
#endif

/// Project-agnostic façade over the launch-argument-driven capture system.
enum MarketingCapture {

    // MARK: - Activation

    /// True when the host app was launched with `-MarketingCapture 1`.
    /// Cheap to call — reads `ProcessInfo.arguments` only.
    static var isActive: Bool {
        let args = ProcessInfo.processInfo.arguments
        guard let idx = args.firstIndex(of: "-MarketingCapture"),
              idx + 1 < args.count else { return false }
        return args[idx + 1] == "1" || args[idx + 1].lowercased() == "true"
    }

    // MARK: - Launch arguments

    /// The locale folder name passed via `-MarketingLocale <id>`.
    /// Falls back to the system language code, then the full locale identifier.
    static var localeFolder: String {
        if let value = launchArgValue(for: "-MarketingLocale") {
            return value
        }
        return Locale.current.language.languageCode?.identifier
            ?? Locale.current.identifier
    }

    /// The device folder name passed via `-MarketingDeviceKey <key>`.
    /// Bash script supplies `iphone-pro-max`, `iphone-pro`, `ipad`, etc.
    /// Falls back to a coarse `UIDevice.current.model` bucket so ad-hoc
    /// runs without the script still produce a sane folder.
    static var deviceFolder: String {
        if let value = launchArgValue(for: "-MarketingDeviceKey") {
            return value
        }
        #if canImport(UIKit) && !os(watchOS)
        return UIDevice.current.model.lowercased()
        #else
        return "device"
        #endif
    }

    /// The target-family key passed via `-MarketingTargetKey <key>`.
    /// Bash script supplies `ios` or `watch`. Falls back to `"ios"` for
    /// ad-hoc runs on iOS/iPadOS and `"watch"` on watchOS.
    static var targetKey: String {
        if let value = launchArgValue(for: "-MarketingTargetKey"), !value.isEmpty {
            return value
        }
        #if os(watchOS)
        return "watch"
        #else
        return "ios"
        #endif
    }

    /// The scheme/app folder name passed via `-MarketingSchemeName <name>`.
    /// Falls back to `CFBundleName`, with spaces collapsed to hyphens so the
    /// result is filesystem-friendly.
    static var schemeFolder: String {
        if let value = launchArgValue(for: "-MarketingSchemeName") {
            return value.replacingOccurrences(of: " ", with: "-")
        }
        let name = (Bundle.main.object(forInfoDictionaryKey: "CFBundleName") as? String)
            ?? (Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String)
            ?? "App"
        return name.replacingOccurrences(of: " ", with: "-")
    }

    /// Reads a launch arg value by flag name. Returns `nil` if the flag is
    /// absent or has no following argument.
    static func launchArgValue(for flag: String) -> String? {
        let args = ProcessInfo.processInfo.arguments
        guard let idx = args.firstIndex(of: flag), idx + 1 < args.count else {
            return nil
        }
        return args[idx + 1]
    }

    // MARK: - Output paths

    /// Sentinel filename written at the end of every capture run.
    /// Matches the name `capture-marketing.sh` polls for.
    static let sentinelFilename = "_done"

    /// Base output directory. Resolved in priority order:
    /// 1. `-MarketingOutputRoot <path>` launch arg (what the bash script passes).
    /// 2. `~/Pictures/MarketingCapture/<bundleIdentifier>` fallback for
    ///    ad-hoc simulator runs without the script. Safe default; doesn't
    ///    leak paths specific to any one developer's machine.
    static var baseOutputDirectory: URL {
        if let path = launchArgValue(for: "-MarketingOutputRoot"), !path.isEmpty {
            return URL(fileURLWithPath: path, isDirectory: true)
        }
        let bundleID = Bundle.main.bundleIdentifier ?? "UnknownApp"
        let home = URL(fileURLWithPath: NSHomeDirectory(), isDirectory: true)
        return home
            .appendingPathComponent("Pictures", isDirectory: true)
            .appendingPathComponent("MarketingCapture", isDirectory: true)
            .appendingPathComponent(bundleID, isDirectory: true)
    }

    /// Full output directory for the current run: `<base>/<scheme>/<device>/<locale>/`.
    /// Created on demand. All capture writes go here.
    static var outputDirectory: URL {
        let root = baseOutputDirectory
            .appendingPathComponent(schemeFolder, isDirectory: true)
            .appendingPathComponent(deviceFolder, isDirectory: true)
            .appendingPathComponent(localeFolder, isDirectory: true)
        try? FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }

    // MARK: - Image writing

    #if canImport(UIKit) && !os(watchOS)
    /// Writes a JPEG into the current output directory. `name` is the
    /// filename stem; the `.jpg` extension is appended automatically.
    static func writeJPEG(_ image: UIImage, name: String, quality: CGFloat = 0.95) {
        let url = outputDirectory.appendingPathComponent("\(name).jpg")
        guard let data = image.jpegData(compressionQuality: quality) else {
            print("[MarketingCapture] failed to encode JPEG for \(name)")
            return
        }
        do {
            try data.write(to: url, options: .atomic)
            print("[MarketingCapture] wrote \(url.path)")
        } catch {
            print("[MarketingCapture] write failed: \(error)")
        }
    }

    /// Preferred writer. Alias of `writeJPEG`.
    static func writeImage(_ image: UIImage, name: String) {
        writeJPEG(image, name: name)
    }
    #endif

    // MARK: - Sentinel

    /// Writes the `_done` sentinel file the bash script polls for. Call
    /// exactly once at the end of a capture run.
    static func writeSentinel() {
        let url = outputDirectory.appendingPathComponent(sentinelFilename)
        try? Data().write(to: url)
        print("[MarketingCapture] sentinel written: \(url.path)")
    }
}

// MARK: - Output path unit test hook

extension MarketingCapture {
    /// Test-friendly path resolver. Takes explicit arg values so tests can
    /// verify the partition layout without depending on live `ProcessInfo`
    /// state.
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
