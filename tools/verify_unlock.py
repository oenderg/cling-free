#!/usr/bin/env python3
"""Check that an unlock patch did what it should, and nothing else.

Usage: verify_unlock.py <checkout>

<checkout> is a pristine upstream clone (with its .git) that tools/unlock_pro.py has already been
run against. Everything is judged from `git diff` against upstream, so the checks hold whatever
the patch script looks like:

  1. Only the files the unlock is allowed to touch changed, and each stays small.
  2. The diff adds nothing that talks to the network, spawns processes or runs scripts.
  3. The things the unlock exists to do are actually there, and the old gates are gone.

This file is deliberately outside the set of files an automated fixer may edit, so a fix can't
loosen the check it is judged by.
"""
import re
import subprocess
import sys
from pathlib import Path

# path (regex) -> maximum added+removed lines
ALLOWED = {
    r"Cling/Unlocked\.swift": 40,
    r"Cling/ClingApp\.swift": 12,
    r"Cling\.xcodeproj/project\.pbxproj": 8,
    r"Cling/Info\.plist": 8,
    r"Stubs/WarpDrop/.*": 120,
}

# Anything in added lines that reaches outside the process. The appcast URL is the one exception.
RISKY = re.compile(
    r"URLSession|NSURLConnection|URLRequest|Process\(|NSTask|posix_spawn|execv|system\(|popen|dlopen|"
    r"NSAppleScript|osascript|/bin/|curl\b|wget\b|https?://|NSWorkspace|Keychain|SecItem|"
    r"UserDefaults\.standard\.(set|removeObject)",
    re.I,
)
APPCAST_PREFIX = "https://raw.githubusercontent.com/oenderg/cling-free/"

failures = []


def fail(message):
    failures.append(message)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def main():
    root = Path(sys.argv[1]).resolve()
    if not (root / ".git").exists():
        raise SystemExit("ERROR: needs the upstream clone with its .git, to diff against")

    git(root, "add", "-N", ".")  # make new files visible to diff
    numstat = [line.split("\t") for line in git(root, "diff", "--numstat").splitlines() if line]

    changed = {}
    for added, removed, path in numstat:
        if added == "-":
            fail(f"binary file changed: {path}")
            continue
        changed[path] = int(added) + int(removed)
        limit = next((cap for pattern, cap in ALLOWED.items() if re.fullmatch(pattern, path)), None)
        if limit is None:
            fail(f"changed a file the unlock may not touch: {path}")
        elif changed[path] > limit:
            fail(f"{path}: {changed[path]} changed lines, limit is {limit}")

    for line in git(root, "diff", "-U0").splitlines():
        if line.startswith("+++") or not line.startswith("+"):
            continue
        body = line[1:]
        if RISKY.search(body) and APPCAST_PREFIX not in body:
            fail(f"added line looks like it reaches outside the app: {body.strip()[:120]}")

    def text(rel):
        p = root / rel
        return p.read_text() if p.exists() else ""

    unlocked = text("Cling/Unlocked.swift")
    for needle in ("var proactive: Bool { true }", "func validReq() -> Bool { true }"):
        if needle not in unlocked:
            fail(f"Cling/Unlocked.swift is missing `{needle}`")
    app = text("Cling/ClingApp.swift")
    if "checkProLicense()" in app:
        fail("ClingApp.swift still calls pro.checkProLicense()")
    if "pro.enablePro()" not in app or "pro.onTrial = false" not in app:
        fail("ClingApp.swift does not enable Pro and clear the trial flag")
    pbx = text("Cling.xcodeproj/project.pbxproj")
    if "Github/alin23/warpdrop" in pbx:
        fail("the private WarpDrop path is still in the Xcode project")
    if "Stubs/WarpDrop" not in pbx:
        fail("the Xcode project does not point at the WarpDrop stub")
    plist = text("Cling/Info.plist")
    feed = re.search(r"<key>SUFeedURL</key>\s*<string>([^<]*)</string>", plist)
    if not feed or not feed.group(1).startswith(APPCAST_PREFIX):
        fail("Sparkle's feed is not this repo's appcast")
    if "lowtechguys.com" in (feed.group(1) if feed else ""):
        fail("Sparkle would still update from upstream's feed")

    if failures:
        print("verify_unlock: FAILED")
        for message in failures:
            print(f"  - {message}")
        sys.exit(1)
    print("verify_unlock: ok — " + ", ".join(f"{p} ({n})" for p, n in sorted(changed.items())))


if __name__ == "__main__":
    main()
