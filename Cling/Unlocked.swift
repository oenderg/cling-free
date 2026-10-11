// Added by cling-free's unlock_pro.py. Upstream's public sources reference these symbols but
// no longer define them, so a clean checkout doesn't compile without them.

/// The flag every Pro gate in the app reads.
@inline(__always) var proactive: Bool { true }

/// Gate on the search path: `false` would make every search return early.
func validReq() -> Bool { true }

/// Licence-enforcement hooks called for effect only; nothing to enforce here.
@discardableResult func invalidReq(_: [Any], _: Any?) -> Bool { false }
@discardableResult func invalidReq3(_: [Any], _: Any?) -> Bool { false }
