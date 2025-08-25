# Scriptorium: The Scriptor Installer for Windows
# This script automates the complete installation and configuration of the Scribo toolset on Windows.

# --- Configuration ---
$RepoUrl = "https://github.com/IsidoreLands/scribo.git"
$RepoDir = "$HOME\Documents\scribo"
$InboxDir = "$HOME\scribo_inbox"

# --- Helper Functions ---
function Write-Header {
    param([string]$Message)
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
}

function Exit-OnError {
    param([string]$Message)
    Write-Host "`n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Red
    Write-Host " ERROR: $Message" -ForegroundColor Red
    Write-Host " Installation failed. Please check the output above for details." -ForegroundColor Red
    Write-Host "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" -ForegroundColor Red
    exit 1
}

# --- Main Installation Logic ---

# 1. Check for Chocolatey Package Manager
Write-Header "Step 1: Checking for Prerequisites (Chocolatey, Git, Python)"
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey not found. Please install it first from https://chocolatey.org/"
    Exit-OnError "Chocolatey is required to automate prerequisite installation."
}
choco install git python -y --force || Exit-OnError "Failed to install Git and Python using Chocolatey."

# 2. Install pipx
Write-Header "Step 2: Installing pipx"
python -m pip install --user pipx || Exit-OnError "Failed to install pipx."
python -m pipx ensurepath || Write-Host "pipx path already configured."
# Refresh environment variables for the current session
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")

# 3. Clone the Scribo Repository
Write-Header "Step 3: Cloning the Scribo Repository"
if (Test-Path $RepoDir) {
    Write-Host "Removing existing repository directory..."
    Remove-Item -Recurse -Force $RepoDir
}
git clone $RepoUrl $RepoDir || Exit-OnError "Failed to clone the Scribo repository."
Set-Location $RepoDir || Exit-OnError "Failed to enter the repository directory."

# 4. Install Scribo using pipx
Write-Header "Step 4: Installing Scribo Tools (compara & speculator)"
pipx install . || Exit-OnError "Failed to install Scribo with pipx."

# 5. Create Inbox Directory
Write-Header "Step 5: Creating Inbox Directory"
New-Item -ItemType Directory -Force -Path $InboxDir | Out-Null

# 6. Create Scheduled Task for Speculator
Write-Header "Step 6: Configuring Speculator to run on Login"
$taskName = "ScriptorSpeculatorDaemon"
$speculatorPath = "$HOME\.local\bin\speculator.exe"
$action = New-ScheduledTaskAction -Execute $speculatorPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
# Register the task, replacing any existing one with the same name
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force -Description "Starts the Scribo Speculator daemon on user login." | Out-Null
# Start the task immediately for the first time
Start-ScheduledTask -TaskName $taskName

# --- Success ---
Write-Host "`n"
Write-Header "Installation Complete"
Write-Host "Scribo is now installed and the 'speculator' daemon will run automatically on login."
Write-Host "The service has been started for the current session."
Write-Host "You can now use the 'compara' command from any new terminal."
