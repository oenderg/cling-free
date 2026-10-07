import Foundation

// Same surface Cling's SendManager uses from upstream's private WarpDrop package, with no
// transport behind it: "Send securely" fails with a readable error instead of sending anything.

public struct WarpDropUnavailable: LocalizedError {
    public var errorDescription: String? {
        "Send securely is not available in this build: its WarpDrop transport is not published upstream."
    }
}

public final class SendFileList: @unchecked Sendable {
    public init() {}

    public func add(files _: [URL]) throws {
        throw WarpDropUnavailable()
    }
}

public struct WarpDropClient: Sendable {
    public init() {}

    public func send(
        files _: [URL],
        multi _: Bool,
        maxReceivers _: Int,
        fileList _: SendFileList,
        onRoomCreated _: @escaping @Sendable (String) -> Void,
        onDownloadCompleted _: @escaping @Sendable (Int) -> Void
    ) async throws -> String {
        throw WarpDropUnavailable()
    }
}
