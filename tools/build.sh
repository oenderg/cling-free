#!/usr/bin/env bash
# Build Cling from an already-unlocked checkout.
# Usage: build.sh <checkout-dir> <version> [output-dir]
#
# Builds ad-hoc, then re-signs with $SIGN_IDENTITY when set (plus $SIGN_KEYCHAIN if the identity
# lives outside the default search list). The identity matters: an ad-hoc signature makes the
# designated requirement a cdhash, so macOS treats every build as a different app and drops its
# Accessibility and Full Disk Access grants. A certificate makes it `identifier and certificate
# leaf`, which is stable across builds.
#
# Re-signing after the fact rather than handing the identity to Xcode is deliberate: Xcode only
# selects identities that pass a trust evaluation, and a self-signed cert never will. It silently
# falls back to ad-hoc instead of failing, which is the worst of both worlds.
set -euo pipefail

SRC="$(cd "$1" && pwd)"
VERSION="$2"
OUT="$(mkdir -p "${3:-$PWD/dist}" && cd "${3:-$PWD/dist}" && pwd)"

cd "$SRC"
xcodebuild -project Cling.xcodeproj -scheme Cling -configuration Release \
  -derivedDataPath DerivedData \
  ARCHS="arm64 x86_64" ONLY_ACTIVE_ARCH=NO \
  CODE_SIGN_IDENTITY=- CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM= ENABLE_HARDENED_RUNTIME=NO \
  build

APP="$SRC/DerivedData/Build/Products/Release/Cling.app"
[ -d "$APP" ] || { echo "no Cling.app at $APP" >&2; exit 1; }

if [ -n "${SIGN_IDENTITY:-}" ]; then
  # Sign nested code first (deepest paths first), then the app itself. --deep alone misses XPC
  # services and helper apps inside Sparkle and Paddle on newer toolchains. The app keeps the
  # entitlements Xcode embedded.
  sign() { codesign --force --sign "$SIGN_IDENTITY" ${SIGN_KEYCHAIN:+--keychain "$SIGN_KEYCHAIN"} "$@"; }
  while IFS= read -r -d '' nested; do
    sign --preserve-metadata=entitlements,flags "$nested"
  done < <(find "$APP/Contents" \( -name '*.xpc' -o -name '*.app' -o -name '*.framework' -o -name '*.dylib' \) -print0 | sort -z -r)
  sign --preserve-metadata=entitlements,flags "$APP"
  authority=$(codesign -dv --verbose=2 "$APP" 2>&1 | sed -n 's/^Authority=//p')
  [ -n "$authority" ] || { echo "asked to sign as '$SIGN_IDENTITY' but the app is still ad-hoc" >&2; exit 1; }
  echo "signed by: $authority"
else
  echo "signed by: ad-hoc"
fi

codesign --verify --deep --strict "$APP"
test "$(defaults read "$APP/Contents/Info.plist" CFBundleShortVersionString)" = "$VERSION"
codesign -d -r- "$APP" 2>&1 | sed -n 's/^#* *designated => /designated requirement: /p'
echo "architectures: $(lipo -archs "$APP/Contents/MacOS/Cling")"

ditto -c -k --keepParent "$APP" "$OUT/Cling-$VERSION-unlocked.zip"
echo "built $OUT/Cling-$VERSION-unlocked.zip"
