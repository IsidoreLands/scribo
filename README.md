## Scribo

Scribo is a suite of command-line utilities designed to intelligently and automatically apply code changes from a revised file to an original source file. It streamlines the development workflow by creating a robust, autonomous system for integrating discrete revisions. It was co-developed by Isidore Lands and the AetherOS architect, Alex.

The system is architected as a producer/consumer toolset, consisting of the patch generator, Compara, and an autonomous background daemon, Speculator, which detects and processes patches.

## Architecture and Philosophy

The core philosophy of Scribo is to make the revision process invisible, robust, and safe. A developer should only need to be concerned with writing the code, not the mechanics of integrating it. Scribo v3.0 achieves this through a sophisticated, multi-stage pipeline:

- **Producer/Consumer Model**: The Speculator daemon's sole responsibility is to detect new patches and place them on a work queue. A separate worker thread, the Operarius (workman), pulls from this queue to process each patch sequentially, ensuring the system is resilient to rapid, multiple patch submissions.
- **Atomic Operations**: No change is committed until it is fully verified. Before patching, a temporary backup of the original file is created. The system then applies the patch, formats the code, and runs tests. Only if all stages succeed is the backup removed. If any stage fails, the original file is instantly restored from the backup and the faulty patch is quarantined.
- **Automated Verification (The Probator)**: After a patch is applied and formatted, the Probator (tester) automatically discovers and runs the project's pytest suite. This crucial step prevents patches that break existing functionality from ever being integrated.
- **Persistent Logging**: All actions are recorded in a rotating log file, *Acta Scriptoris* (The Records of Scriptor), providing a durable audit trail of every patch that was applied, rejected, or quarantined.
- **True Daemonization**: The Speculator is designed to run as a proper background service using systemd, ensuring it is always running, automatically starts on login, and restarts itself on failure.

## Core Components

The Scribo suite is composed of several specialized tools that form the automation pipeline:

- **Compara (The Comparer)**: Generates a self-contained `.patch` file by comparing an original and a revised source file.
- **Speculator (The Watcher)**: The file system watcher daemon that detects new patches in the inbox.
- **Operarius (The Workman)**: The background worker thread that executes the processing pipeline for each patch.
- **Perfector (The Completer)**: The module responsible for applying the patch to the target file.
- **Ornator (The Arranger)**: The module that runs code formatters (like Black and Ruff) on the newly patched file.
- **Probator (The Tester)**: The verification module that runs the project's test suite to confirm the patch's integrity.

## Installation

#### Prerequisites

- Python 3.8+
- pipx
- Git (for the Probator's project root discovery)
- A test runner like pytest installed in projects you wish to verify.

#### Installation Steps

1. Clone the repository from GitHub:

   ```bash
   git clone https://github.com/IsidoreLands/scribo.git
   cd scribo/coniunctor
   ```

2. Use pipx to install the package. This builds the tool and makes the `compara` and `speculator` commands globally available:

   ```bash
   pipx install .
   ```

3. Create the inbox directory that the Speculator will monitor:

   ```bash
   mkdir ~/scribo_inbox
   ```

## Operation

The standard workflow involves running the `speculator` daemon as a background service and using `compara` to generate patches.

#### Step 1: Run Speculator as a Service

The recommended way to run the watcher is as a systemd user service. This ensures it's always running in the background.

1. Create the service file at `~/.config/systemd/user/scriptor.service`:

   ```ini
   [Unit]
   Description=Scriptor Speculator Daemon
   After=network.target

   [Service]
   ExecStart=%h/.local/bin/speculator
   Restart=on-failure
   RestartSec=5s

   [Install]
   WantedBy=default.target
   ```

2. Enable and start the service:

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now scriptor.service
   ```

You can check its status or view live logs with:

```bash
systemctl --user status scriptor.service
journalctl --user -u scriptor.service -f
```

#### Step 2: Generate a Patch

As a developer, you have your original file (`guide_main.py`) and a revised version (`guide_v4.py`). To integrate the changes, run the `compara` command:

```bash
compara guide_main.py guide_v4.py
```

The moment the patch file is created in `~/scribo_inbox/`, the `speculator` service will detect it and trigger the full automated pipeline: apply, format, test, and commit or revert. Your work is done.

## Development Journal

#### Version 3.0 (Current)

- **Thematic Rebranding**: All components were renamed with authentic Latin terms to create a cohesive and memorable toolset.
- **Architectural Overhaul**: Implemented a robust producer/consumer model using a queue and a worker thread (Operarius) to handle patch processing.
- **Test-Driven Verification**: Introduced the Probator module, which integrates pytest directly into the pipeline, enabling automated regression testing for every patch.
- **Atomic Operations**: The entire patch process is now atomic, with an automatic backup and revert mechanism that guarantees a patch either succeeds completely or the system is returned to its original state.
- **Daemonization**: Added full support for running Speculator as a systemd service for true "fire-and-forget" background operation.
- **Persistent Logging**: Replaced console output with a formal, rotating log file (`Acta_Scriptoris.log`) via Python's logging module.

#### Version 1.1

- **Architecture Refactor**: Split the original monolithic patcher script into a two-part system.
- **Formalized Patch Format**: Patches now contain a metadata header specifying the target file path.
- **Quarantine System**: Added logic to move failing patches to a quarantine directory.

## Roadmap (Future Development)

- **Conflict Resolution TUI**: For patches that cannot be applied cleanly, develop a simple Text-based User Interface (TUI) that presents conflicting hunks for manual resolution.
- **Plugin System**: Allow for custom post-verification scripts (e.g., trigger notifications, deploy to staging).
- **Remote Inbox**: Explore options for using a message queue (like RabbitMQ or Redis) as an inbox for distributed development workflows.

## Repository

The official source code is hosted on GitHub: [https://github.com/IsidoreLands/scribo](https://github.com/IsidoreLands/scribo)
