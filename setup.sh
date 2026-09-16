#!/bin/sh
set -eu
REPO=felixganzer/venus-os_dbus-emsesp
APP=/data/venus-os_dbus-emsesp
TMP=/tmp/venus-os_dbus-emsesp-setup
rm -rf "$TMP"
mkdir -p "$TMP"
if command -v curl >/dev/null 2>&1; then
    TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d '"' -f 4)
    curl -fsSL -o "$TMP/release.zip" "https://github.com/$REPO/archive/refs/tags/$TAG.zip"
elif command -v wget >/dev/null 2>&1; then
    TAG=$(wget -qO- "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | head -1 | cut -d '"' -f 4)
    wget -qO "$TMP/release.zip" "https://github.com/$REPO/archive/refs/tags/$TAG.zip"
else
    echo "curl or wget required" >&2; exit 1
fi
[ -n "$TAG" ] || { echo "No GitHub release found" >&2; exit 1; }
unzip -q "$TMP/release.zip" -d "$TMP"
SOURCE=$(find "$TMP" -maxdepth 1 -type d -name 'venus-os_dbus-emsesp-*' | head -1)
[ -d "$SOURCE" ] || { echo "Extracted project not found" >&2; exit 1; }
sh "$SOURCE/install.sh"
rm -rf "$TMP"
