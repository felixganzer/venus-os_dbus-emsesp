#!/bin/sh

set -e

APP_NAME="venus-os_dbus-emsesp"
GITHUB_USER="felixganzer"
GITHUB_REPO="venus-os_dbus-emsesp"

INSTALL_DIR="/data/${APP_NAME}"
TEMP_DIR="/tmp/${APP_NAME}"
ZIP_FILE="${TEMP_DIR}/release.zip"

echo "======================================"
echo "Installing ${APP_NAME}"
echo "======================================"

# Prüfen ob curl vorhanden ist
command -v curl >/dev/null 2>&1 || {
    echo "ERROR: curl not found"
    exit 1
}

# temporäres Verzeichnis
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# neueste Release-Version ermitteln
LATEST_TAG=$(
    curl -s \
    "https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/releases/latest" |
    grep '"tag_name"' |
    cut -d '"' -f 4
)

if [ -z "${LATEST_TAG}" ]; then
    echo "ERROR: no GitHub release found"
    exit 1
fi

echo "Latest release: ${LATEST_TAG}"

# Release herunterladen
curl -L \
    -o "${ZIP_FILE}" \
    "https://github.com/${GITHUB_USER}/${GITHUB_REPO}/archive/refs/tags/${LATEST_TAG}.zip"

# alte Installation entfernen
rm -rf "${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"

# entpacken
unzip -q "${ZIP_FILE}" -d "${TEMP_DIR}"

# Projektordner finden
PROJECT_DIR=$(find "${TEMP_DIR}" -maxdepth 1 -type d -name "${GITHUB_REPO}-*" | head -n 1)

if [ ! -d "${PROJECT_DIR}" ]; then
    echo "ERROR: extracted project not found"
    exit 1
fi

# Dateien kopieren
cp -R "${PROJECT_DIR}/." "${INSTALL_DIR}/"

# Rechte setzen
chmod +x "${INSTALL_DIR}"/*.sh 2>/dev/null || true
chmod +x "${INSTALL_DIR}/service/run" 2>/dev/null || true
chmod +x "${INSTALL_DIR}/test_dummy.py" 2>/dev/null || true

# Installation starten
cd "${INSTALL_DIR}"
sh install.sh

echo ""
echo "======================================"
echo "Installation completed"
echo "======================================"
echo ""
echo "Status prüfen:"
echo "sv status /service/dbus-emsesp"
echo ""
echo "D-Bus prüfen:"
echo "dbus -y com.victronenergy.heatpump.emsesp"

rm -rf "${TEMP_DIR}"
