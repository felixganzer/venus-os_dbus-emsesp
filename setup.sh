#!/bin/sh
#!/bin/sh

set -eu

REPOSITORY="felixganzer/venus-os_dbus-emsesp"
BRANCH="main"

TEMP_DIR="/tmp/venus-os_dbus-emsesp-setup"
ZIP_FILE="${TEMP_DIR}/repository.zip"
SOURCE_DIR="${TEMP_DIR}/venus-os_dbus-emsesp-${BRANCH}"

echo "======================================"
echo "Installing venus-os_dbus-emsesp"
echo "Branch: ${BRANCH}"
echo "======================================"

rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

DOWNLOAD_URL="https://github.com/${REPOSITORY}/archive/refs/heads/${BRANCH}.zip"

if command -v wget >/dev/null 2>&1; then
    wget -qO "${ZIP_FILE}" "${DOWNLOAD_URL}"
elif command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${ZIP_FILE}" "${DOWNLOAD_URL}"
else
    echo "ERROR: wget or curl is required" >&2
    exit 1
fi

if [ ! -s "${ZIP_FILE}" ]; then
    echo "ERROR: Download failed or ZIP file is empty" >&2
    exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
    echo "ERROR: unzip is required" >&2
    exit 1
fi

unzip -q "${ZIP_FILE}" -d "${TEMP_DIR}"

if [ ! -d "${SOURCE_DIR}" ]; then
    echo "ERROR: Extracted project directory not found:"
    echo "${SOURCE_DIR}"
    exit 1
fi

chmod +x "${SOURCE_DIR}/install.sh"
chmod +x "${SOURCE_DIR}/uninstall.sh"
chmod +x "${SOURCE_DIR}/setup.sh"
chmod +x "${SOURCE_DIR}/service/run"
chmod +x "${SOURCE_DIR}/test_three_devices.py"

sh "${SOURCE_DIR}/install.sh"

rm -rf "${TEMP_DIR}"

echo ""
echo "======================================"
echo "Installation completed"
echo "======================================"
echo ""
echo "D-Bus services:"
echo "com.victronenergy.heatpump.emsesp_heating"
echo "com.victronenergy.heatpump.emsesp_dhw"
echo "com.victronenergy.heatpump.emsesp_aux"