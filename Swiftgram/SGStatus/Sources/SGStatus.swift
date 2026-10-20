import Foundation
import SwiftSignalKit
import TelegramCore

/// Local fork policy: Swiftgram Pro is always enabled.
/// Telegram Premium uses separate Telegram/StoreKit logic and is not changed here.
public struct SGStatus: Equatable, Codable {
    public var status: Int64 {
        get { return 2 }
        set { /* Keep local Swiftgram Pro enabled. */ }
    }

    public static var `default`: SGStatus {
        return SGStatus(status: 2)
    }

    public init(status: Int64) {
        // Ignore persisted/server status in this fork: Pro is always enabled locally.
    }

    public init(from decoder: Decoder) throws {
        // Do not restore a locked Swiftgram Pro status from existing preferences.
        self.init(status: 2)
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: StringCodingKey.self)
        try container.encode(Int64(2), forKey: "status")
    }
}

public func updateSGStatusInteractively(accountManager: AccountManager<TelegramAccountManagerTypes>, _ f: @escaping (SGStatus) -> SGStatus) -> Signal<Void, NoError> {
    return accountManager.transaction { transaction -> Void in
        transaction.updateSharedData(ApplicationSpecificSharedDataKeys.sgStatus, { entry in
            let currentSettings: SGStatus
            if let entry = entry?.get(SGStatus.self) {
                currentSettings = entry
            } else {
                currentSettings = SGStatus.default
            }
            return SharedPreferencesEntry(f(currentSettings))
        })
    }
}
