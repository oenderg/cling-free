#!/usr/bin/env bash
# Install the latest unlocked Cling build.
#
#   curl -fsSL https://raw.githubusercontent.com/oenderg/cling-free/main/tools/install.sh | bash
#
# No sudo: /Applications is writable by admin users and tccutil works on your own TCC database.
# If anything here asks you for a password, something is wrong — stop and read the script.
set -euo pipefail

REPO="${REPO:-oenderg/cling-free}"
APP="/Applications/Cling.app"
BUNDLE_ID="com.lowtechguys.Cling"
BACKUPS="$HOME/Library/Application Support/Cling-backups"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say() { printf '\033[1m==>\033[0m %s\n' "$1"; }
fail() { printf '\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || fail "macOS only"
[ "$(sw_vers -productVersion | cut -d. -f1)" -ge 14 ] || fail "needs macOS 14 or newer"
[ -w /Applications ] || fail "/Applications isn't writable by your user — you need an admin account"

say "Finding the latest release"
url=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | sed -n 's/.*"browser_download_url": *"\([^"]*\.zip\)".*/\1/p' | head -1)
[ -n "$url" ] || fail "no release asset found for $REPO"
version=$(basename "$url" | sed -E 's/^Cling-(.*)-unlocked\.zip$/\1/')
say "Downloading Cling $version"
curl -fsSL "$url" -o "$TMP/Cling.zip"
ditto -x -k "$TMP/Cling.zip" "$TMP/extracted"
new="$TMP/extracted/Cling.app"
[ -d "$new" ] || fail "the downloaded archive didn't contain Cling.app"

codesign --verify --deep --strict "$new" || fail "downloaded app failed signature verification"
new_req=$(codesign -d -r- "$new" 2>&1 | sed -n 's/^designated => //p')
say "Signed as: ${new_req:-unknown}"

old_req=""
if [ -d "$APP" ]; then
  old_req=$(codesign -d -r- "$APP" 2>&1 | sed -n 's/^designated => //p' || true)
  old_version=$(defaults read "$APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo unknown)
  mkdir -p "$BACKUPS"
  say "Backing up the installed Cling $old_version"
  rm -rf "$BACKUPS/Cling-$old_version.app"
  ditto "$APP" "$BACKUPS/Cling-$old_version.app"
fi

osascript -e 'quit app "Cling"' >/dev/null 2>&1 || true
sleep 2
pkill -f "$APP/Contents/MacOS/Cling" 2>/dev/null || true

say "Installing to $APP"
rm -rf "$APP"
ditto "$new" "$APP"
# curl doesn't set com.apple.quarantine, but a re-run over a browser-downloaded copy might have.
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

# macOS binds a permission grant to the bundle ID *and* the code signature. Resetting when the
# signature is unchanged would needlessly throw away a working grant, so only do it when the
# identity actually differs — e.g. coming from upstream's Developer ID build.
if [ -n "$old_req" ] && [ "$old_req" != "$new_req" ]; then
  say "Signing identity changed — resetting permissions so the new grant can bind"
  tccutil reset SystemPolicyAllFiles "$BUNDLE_ID" >/dev/null 2>&1 || true
  tccutil reset Accessibility "$BUNDLE_ID" >/dev/null 2>&1 || true
  needs_grant=1
elif [ -z "$old_req" ]; then
  needs_grant=1
else
  say "Same signing identity — your existing permissions carry over"
  needs_grant=0
fi

say "Launching Cling $version"
open "$APP"

if [ "$needs_grant" = "1" ]; then
  cat <<'EOF'

One thing left: Cling indexes the whole disk, so it needs Full Disk Access.

  System Settings > Privacy & Security > Full Disk Access  →  enable Cling

Opening that pane now.
EOF
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
fi

say "Done. Backups of previous versions live in $BACKUPS"
