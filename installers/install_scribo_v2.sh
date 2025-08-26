#!/bin/bash
# Scriptorium: The Scriptor Installer (v2 - Idempotent)
export DEBIAN_FRONTEND=noninteractive
REPO_URL="https://github.com/IsidoreLands/scribo.git"
REPO_DIR="$HOME/scribo"
INBOX_DIR="$HOME/scribo_inbox"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="scriptor.service"

print_header() {
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}
exit_on_error() {
    echo ""; echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!";
    echo " ERROR: $1";
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"; exit 1;
}

print_header "Step 1: Verifying Prerequisites (Python, pip, Git, venv, gpg)"
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null || ! command -v git &> /dev/null || ! command -v gpg &> /dev/null; then
    echo "One or more prerequisites are missing. Attempting installation with sudo..."
    sudo apt-get update -y || exit_on_error "Failed to update package lists with sudo."
    sudo apt-get install python3 python3-pip git python3.10-venv gnupg -y || exit_on_error "Failed to install required packages with sudo."
else
    echo "All prerequisites are already installed. Skipping sudo."
fi

print_header "Step 2: Installing pipx"
python3 -m pip install --user pipx || exit_on_error "Failed to install pipx."
python3 -m pipx ensurepath || echo "pipx path already configured."

print_header "Step 3: Cloning the Scribo Repository"
if [ -d "$REPO_DIR" ]; then
    echo "Removing existing repository directory for a clean install..."
    rm -rf "$REPO_DIR"
fi
git clone "$REPO_URL" "$REPO_DIR" || exit_on_error "Failed to clone the Scribo repository."
cd "$REPO_DIR" || exit_on_error "Failed to enter the repository directory."

print_header "Step 4: Installing Scriptor Tools"
pipx install . || exit_on_error "Failed to install Scribo with pipx."

print_header "Step 5: Creating Inbox and systemd Directories"
mkdir -p "$INBOX_DIR" || exit_on_error "Failed to create inbox directory."
mkdir -p "$SYSTEMD_USER_DIR" || exit_on_error "Failed to create systemd user directory."

print_header "Step 6: Configuring the Speculator Background Service"
cat > "$SYSTEMD_USER_DIR/$SERVICE_FILE" << EOL
[Unit]
Description=Scriptor Daemon (via Scriptor SDK)
After=network.target
[Service]
ExecStart=$HOME/.local/bin/scriptor speculator
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=default.target
EOL

echo "Service file created at SYSTEMDUSER/SERVICE_FILE"
print_header "Step 7: Enabling and Starting the Service"
systemctl --user daemon-reload || exit_on_error "Failed to reload systemd daemon."
systemctl --user enable --now "$SERVICE_FILE" || exit_on_error "Failed to enable and start the service."
sleep 2
systemctl --user is-active --quiet "$SERVICE_FILE" || exit_on_error "Service started but is not active. Check logs for errors."

echo ""; print_header "Installation Complete";
echo "Scribo is now installed and the 'speculator' daemon is running.";
echo "You can check status with: systemctl --user status $SERVICE_FILE"; exit 0;
