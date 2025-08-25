#!/bin/bash

# Scriptorium Secure Bootstrapper
# This script securely downloads and verifies the main Scribo installer before execution.
# It uses GPG to ensure the installer is authentic and has not been tampered with.

# --- Configuration ---
# The base URL for raw files from your GitHub repository.
# IMPORTANT: Update this if your username or repo name changes.
BASE_URL="https://raw.githubusercontent.com/IsidoreLands/scribo/main"

# The developer's public GPG key.
PUBKEY_URL="${BASE_URL}/isidore_lands_pubkey.asc"

# Determine the correct installer for the OS.
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Linux*)   INSTALLER_NAME="install_scribo.sh";;
    Darwin*)  INSTALLER_NAME="install_scribo_mac.sh";;
    *)        echo "ERROR: Unsupported operating system: $OS_TYPE"; exit 1;;
esac

INSTALLER_URL="${BASE_URL}/installers/${INSTALLER_NAME}"
SIGNATURE_URL="${INSTALLER_URL}.asc"

# Temporary directory for downloads
TMP_DIR=$(mktemp -d)
# Ensure the temporary directory is cleaned up on exit
trap 'rm -rf -- "$TMP_DIR"' EXIT

# --- Helper Functions ---
print_header() {
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}

exit_on_error() {
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo " SECURITY ALERT: $1"
    echo " The installation has been aborted to protect your system."
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    exit 1
}

# --- Main Logic ---
print_header "Scribo Secure Installer"

# 1. Check for GPG
if ! command -v gpg &> /dev/null; then
    echo "GPG is not installed. Attempting to install..."
    if [[ "$OS_TYPE" == "Linux"* ]]; then
        sudo apt-get update && sudo apt-get install -y gnupg || exit_on_error "GPG is required for verification but could not be installed."
    elif [[ "$OS_TYPE" == "Darwin"* ]]; then
        brew install gnupg || exit_on_error "GPG is required for verification but could not be installed via Homebrew."
    fi
fi

# 2. Download the necessary files
echo "Downloading installer, signature, and public key..."
curl -sSLo "$TMP_DIR/$INSTALLER_NAME" "$INSTALLER_URL" || exit_on_error "Failed to download the main installer script."
curl -sSLo "$TMP_DIR/$INSTALLER_NAME.asc" "$SIGNATURE_URL" || exit_on_error "Failed to download the signature file."
curl -sSLo "$TMP_DIR/pubkey.asc" "$PUBKEY_URL" || exit_on_error "Failed to download the public key."

# 3. Verify the signature
echo "Verifying the integrity of the installer..."
# Import the public key into a temporary GPG keyring to avoid cluttering the user's main keyring.
gpg --no-default-keyring --keyring "$TMP_DIR/keyring.gpg" --import "$TMP_DIR/pubkey.asc" 2>/dev/null
# Verify the installer against the signature using the temporary keyring.
if gpg --no-default-keyring --keyring "$TMP_DIR/keyring.gpg" --verify "$TMP_DIR/$INSTALLER_NAME.asc" "$TMP_DIR/$INSTALLER_NAME"; then
    echo "Verification successful. The installer is authentic."
else
    exit_on_error "The installer's signature is INVALID. The file may have been tampered with."
fi

# 4. Execute the main installer
print_header "Handing over to the main installer..."
# Make the verified installer executable and run it.
bash "$TMP_DIR/$INSTALLER_NAME"

