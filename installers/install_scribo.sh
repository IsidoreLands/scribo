#!/bin/bash

# Scriptorium: The Scriptor Installer
# This script automates the complete installation and configuration of the Scribo toolset on a Debian-based system (like Ubuntu).
# It ensures all prerequisites are met, installs the tools, and configures the background daemon.

# --- Configuration ---
# Use the non-interactive frontend for apt to avoid prompts
export DEBIAN_FRONTEND=noninteractive
# GitHub repository URL
REPO_URL="https://github.com/IsidoreLands/scribo.git"
# Local directory for the cloned repo
REPO_DIR="scribo"
# Inbox directory for the watcher
INBOX_DIR="$HOME/scribo_inbox"
# Systemd user service directory
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
# Service file name
SERVICE_FILE="scriptor.service"

# --- Helper Functions ---
# Prints a formatted header message.
print_header() {
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}

# Prints a success message and exits the script.
exit_on_success() {
    echo ""
    print_header "Installation Complete"
    echo "Scribo is now installed and the 'speculator' daemon is running in the background."
    echo "You can now use the 'compara' command to generate patches."
    echo "To check the status of the background service, run:"
    echo "  systemctl --user status $SERVICE_FILE"
    echo "To view live logs, run:"
    echo "  journalctl --user -u $SERVICE_FILE -f"
    exit 0
}

# Prints an error message and exits the script.
exit_on_error() {
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo " ERROR: $1"
    echo " Installation failed. Please check the output above for details."
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    exit 1
}

# --- Main Installation Logic ---

# 1. Update and Install Prerequisites
print_header "Step 1: Installing Prerequisites (Python, pip, Git, venv)"
sudo apt-get update -y || exit_on_error "Failed to update package lists."
sudo apt-get install python3 python3-pip git python3.10-venv -y || exit_on_error "Failed to install required packages."

# 2. Install pipx
print_header "Step 2: Installing pipx"
python3 -m pip install --user pipx || exit_on_error "Failed to install pipx."
python3 -m pipx ensurepath || echo "pipx path already configured."

# 3. Clone the Scribo Repository
print_header "Step 3: Cloning the Scribo Repository"
# Remove the directory if it already exists for a clean installation
if [ -d "$REPO_DIR" ]; then
    echo "Removing existing repository directory..."
    rm -rf "$REPO_DIR"
fi
git clone "$REPO_URL" "$REPO_DIR" || exit_on_error "Failed to clone the Scribo repository."
cd "$REPO_DIR" || exit_on_error "Failed to enter the repository directory."

# 4. Install Scribo using pipx
print_header "Step 4: Installing Scribo Tools (compara & speculator)"
# The project to install is inside the 'coniunctor' subdirectory
pipx install . || exit_on_error "Failed to install Scribo with pipx."

# 5. Create Required Directories
print_header "Step 5: Creating Inbox and systemd Directories"
mkdir -p "$INBOX_DIR" || exit_on_error "Failed to create inbox directory."
mkdir -p "$SYSTEMD_USER_DIR" || exit_on_error "Failed to create systemd user directory."

# 6. Create and Configure the systemd Service
print_header "Step 6: Configuring the Speculator Background Service"
# Use a 'here document' to write the service file configuration.
cat > "$SYSTEMD_USER_DIR/$SERVICE_FILE" << EOL
[Unit]
Description=Scriptor Speculator Daemon
After=network.target

[Service]
ExecStart=$HOME/.local/bin/speculator
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOL

echo "Service file created at $SYSTEMD_USER_DIR/$SERVICE_FILE"

# 7. Enable and Start the Service
print_header "Step 7: Enabling and Starting the Service"
systemctl --user daemon-reload || exit_on_error "Failed to reload systemd daemon."
systemctl --user enable --now "$SERVICE_FILE" || exit_on_error "Failed to enable and start the service."

# --- Final Check and Exit ---
# A brief pause to allow the service to initialize
sleep 2
systemctl --user is-active --quiet "$SERVICE_FILE" || exit_on_error "Service started but is not active. Check logs for errors."

exit_on_success
