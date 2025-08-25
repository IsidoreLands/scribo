#!/bin/bash

# Scriptorium: The Scriptor Installer for macOS
# This script automates the complete installation of the Scribo toolset on macOS.

# --- Configuration ---
REPO_URL="https://github.com/IsidoreLands/scribo.git"
REPO_DIR="$HOME/scribo"
INBOX_DIR="$HOME/scribo_inbox"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="com.isidorelands.scriptor.plist"

# --- Helper Functions (same as Ubuntu script) ---
print_header() {
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}

exit_on_error() {
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo " ERROR: $1"
    echo " Installation failed. Please check the output above for details."
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    exit 1
}

# --- Main Installation Logic ---

# 1. Install Homebrew and Prerequisites
print_header "Step 1: Installing Prerequisites (Homebrew, Git, Python)"
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || exit_on_error "Failed to install Homebrew."
fi
brew install git python || exit_on_error "Failed to install Git and Python using Homebrew."

# 2. Install pipx
print_header "Step 2: Installing pipx"
python3 -m pip install --user pipx || exit_on_error "Failed to install pipx."
python3 -m pipx ensurepath || echo "pipx path already configured."

# 3. Clone the Scribo Repository
print_header "Step 3: Cloning the Scribo Repository"
if [ -d "$REPO_DIR" ]; then
    echo "Removing existing repository directory..."
    rm -rf "$REPO_DIR"
fi
git clone "$REPO_URL" "$REPO_DIR" || exit_on_error "Failed to clone the Scribo repository."
cd "$REPO_DIR" || exit_on_error "Failed to enter the repository directory."

# 4. Install Scribo using pipx
print_header "Step 4: Installing Scribo Tools (compara & speculator)"
pipx install . || exit_on_error "Failed to install Scribo with pipx."

# 5. Create Required Directories
print_header "Step 5: Creating Inbox and LaunchAgent Directories"
mkdir -p "$INBOX_DIR" || exit_on_error "Failed to create inbox directory."
mkdir -p "$LAUNCHD_DIR" || exit_on_error "Failed to create LaunchAgents directory."

# 6. Create the launchd Agent
print_header "Step 6: Configuring the Speculator Background Service"
# Use a 'here document' to write the .plist file configuration.
cat > "$LAUNCHD_DIR/$PLIST_FILE" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.isidorelands.scriptor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$HOME/.local/bin/speculator</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INBOX_DIR/Acta_Scriptoris.log</string>
    <key>StandardErrorPath</key>
    <string>$INBOX_DIR/Acta_Scriptoris.log</string>
</dict>
</plist>
EOL
echo "Launchd agent created at $LAUNCHD_DIR/$PLIST_FILE"

# 7. Load the Service
print_header "Step 7: Loading and Starting the Service"
# Unload any existing version first
launchctl unload "$LAUNCHD_DIR/$PLIST_FILE" 2>/dev/null
# Load the new service
launchctl load "$LAUNCHD_DIR/$PLIST_FILE" || exit_on_error "Failed to load and start the launchd agent."

# --- Success ---
echo ""
print_header "Installation Complete"
echo "Scribo is now installed and the 'speculator' daemon is running in the background."
echo "To check the status of the service, run:"
echo "  launchctl list | grep com.isidorelands.scriptor"
