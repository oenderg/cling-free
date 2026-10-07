#!/usr/bin/env python3
"""Re-appliable unlock patch for a pristine FuzzyIdeas/Cling checkout.

Anchors on Swift declarations and literal call sites rather than line numbers, so it survives
most upstream churn. A missing required anchor is a hard failure: better a red build than a
silently locked one.

What it changes, and why:
  1. `proactive` — the flag every Pro gate in Cling reads — plus `validReq`, `invalidReq` and
     `invalidReq3`. Upstream's public sources call these but no longer define them (they moved
     out of the repo in 2.1.2), so this defines them: `proactive` is `true`, `validReq()` lets
     searches through, the other two do nothing.
  2. `pro.checkProLicense()` becomes `pro.enablePro()` plus `pro.onTrial = false`, so the app
     never asks Paddle about a trial or licence at launch, `pro.active` (the flag the Settings
     and filter UI read) is true at once, and the licence page reads "Licensed on this Mac"
     instead of counting down a trial.
  3. The private `WarpDrop` package, referenced by a path that only exists on the author's
     machine, is repointed at a stub so the project resolves and builds.
  4. Sparkle is pointed at this fork's appcast and public key, so the app can't replace itself
     with the official, locked build.
  5. Error reporting to the author's Sentry project is switched off for this unofficial build.

Usage: unlock_pro.py <path-to-Cling-checkout>
"""
import re
import shutil
import sys
from pathlib import Path

applied, skipped = [], []

# Public by design: the appcast this fork's CI publishes and the public half of the EdDSA key
# it signs it with. Sparkle rejects any update whose signature doesn't verify against this key.
# Checked in CI by tools/verify_unlock.py against every upstream release.
APPCAST_URL = "https://raw.githubusercontent.com/oenderg/cling-free/main/appcast.xml"
SPARKLE_PUBLIC_KEY = "MQEMtxrlAP1XyYthvetCdxX11JMtzPPh4HFRNNYCZ+M="

WARPDROP_PATH = "../../../Github/alin23/warpdrop/packages/swift"
WARPDROP_STUB = "Stubs/WarpDrop"

UNLOCKED_SWIFT = """\
// Added by cling-free's unlock_pro.py. Upstream's public sources reference these symbols but
// no longer define them, so a clean checkout doesn't compile without them.

/// The flag every Pro gate in the app reads.
@inline(__always) var proactive: Bool { true }

/// Gate on the search path: `false` would make every search return early.
func validReq() -> Bool { true }

/// Licence-enforcement hooks called for effect only; nothing to enforce here.
@discardableResult func invalidReq(_: [Any], _: Any?) -> Bool { false }
@discardableResult func invalidReq3(_: [Any], _: Any?) -> Bool { false }
"""

PROVIDED_SYMBOLS = r"(var proactive\b|func (validReq|invalidReq|invalidReq3)\b)"


def record(label, required, reason):
    if required:
        raise SystemExit(f"ERROR: unlock patch anchor drifted — {label}: {reason}")
    skipped.append(f"{label} ({reason})")


def replace_literal(path, old, new, label, required=True, count=1):
    s = path.read_text()
    if old not in s:
        record(label, required, f"not found in {path.name}: {old!r}")
        return
    path.write_text(s.replace(old, new) if count == 0 else s.replace(old, new, count))
    applied.append(label)


def replace_regex(path, pattern, replacement, label, required=True):
    s = path.read_text()
    patched, n = re.subn(pattern, replacement, s, count=1)
    if n == 0:
        record(label, required, f"no match in {path.name}: {pattern!r}")
        return
    path.write_text(patched)
    applied.append(label)


def patch_proactive(root):
    # The Cling/ folder is a file-system-synchronized Xcode group, so a new file is compiled
    # without touching the project file.
    target = root / "Cling/Unlocked.swift"
    target.write_text(UNLOCKED_SWIFT)
    applied.append("proactive == true, licence hooks stubbed (Cling/Unlocked.swift)")
    # If upstream ever defines it again, two definitions would collide: fail loudly.
    for f in (root / "Cling").rglob("*.swift"):
        if f.name == "Unlocked.swift":
            continue
        if re.search(r"^\s*(@inline\(__always\)\s*|@discardableResult\s*)?(public\s+)?" + PROVIDED_SYMBOLS,
                     f.read_text(), re.M):
            raise SystemExit(f"ERROR: upstream now defines one of our stand-in symbols in {f} — update unlock_pro.py")


def patch_licence_check(root):
    app = root / "Cling/ClingApp.swift"
    # enablePro() marks the product activated; the Paddle SDK's local trial counter would still
    # leave `onTrial` true for 14 days and the licence page reading "Trial, 14 days remaining"
    # with a Buy button. We're on the main thread here, so enablePro() has run by the next line.
    replace_literal(app, "pro.checkProLicense()",
                    "pro.enablePro()\n            pro.onTrial = false  // show \"Licensed\", not a trial countdown",
                    "no Paddle licence check, no trial state")
    replace_literal(app, "if Defaults[.enableSentry] {", "if false { // unofficial build: no reports to upstream's Sentry",
                    "Sentry off", required=False)


def patch_warpdrop(root, stubs_dir):
    pbx = root / "Cling.xcodeproj/project.pbxproj"
    replace_literal(pbx, WARPDROP_PATH, WARPDROP_STUB, "WarpDrop -> stub package", count=0)
    dest = root / WARPDROP_STUB
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(stubs_dir / "WarpDrop", dest)


def patch_sparkle(root):
    plist = root / "Cling/Info.plist"
    replace_regex(plist, r"(<key>SUFeedURL</key>\s*<string>)[^<]*(</string>)",
                  lambda m: m.group(1) + APPCAST_URL + m.group(2), "SUFeedURL")
    replace_regex(plist, r"(<key>SUPublicEDKey</key>\s*<string>)[^<]*(</string>)",
                  lambda m: m.group(1) + SPARKLE_PUBLIC_KEY + m.group(2), "SUPublicEDKey")


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (root / "Cling/ClingApp.swift").exists() or not (root / "Cling.xcodeproj").exists():
        raise SystemExit(f"ERROR: {root} does not look like a Cling checkout")
    stubs_dir = Path(__file__).resolve().parent / "stubs"
    patch_proactive(root)
    patch_licence_check(root)
    patch_warpdrop(root, stubs_dir)
    patch_sparkle(root)
    print(f"unlocked {root}")
    for label in applied:
        print(f"  applied: {label}")
    for label in skipped:
        print(f"  skipped: {label}")


if __name__ == "__main__":
    main()
