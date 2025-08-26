{{Scribo Version|3.1.0}} {{Project Status|Beta}} 

**Scriptor** is a unified, command-line SDK designed to intelligently and automatically apply code changes from a revised file to an original source file. It streamlines the development workflow by creating a robust, autonomous system for integrating discrete revisions. It was co-developed by [[User:Isidore Lands|Isidore Lands]] and [[User:Alex M. Xlea|Alex M. Xlea]]. The system is architected as a producer/consumer toolset, consisting of the patch generator command, **scriptor compara**, and an autonomous background daemon, **scriptor speculator**, which detects and processes patches.

## Architecture and Philosophy

The core philosophy of Scriptor is to make the revision process invisible, robust, and safe. A developer should only need to be concerned with writing the code, not the mechanics of integrating it. Scriptor v3.1 achieves this through a sophisticated, multi-stage pipeline:

- **Producer/Consumer Model:** The **speculator** daemon's sole responsibility is to detect new patches and place them on a work queue. A separate worker thread, the **Operarius** (workman), pulls from this queue to process each patch sequentially, ensuring the system is resilient to rapid, multiple patch submissions.
- **Atomic Operations:** No change is committed until it is fully verified. Before patching, a temporary backup of the original file is created. The system then applies the patch, formats the code, and runs tests. Only if all stages succeed is the backup removed. If any stage fails, the original file is instantly restored from the backup and the faulty patch is quarantined.
- **Automated Verification (The Probator):** After a patch is applied and formatted, the **Probator** (tester) automatically discovers and runs the project's **pytest** suite. This crucial step prevents patches that break existing functionality from ever being integrated.
- **Persistent Logging:** All actions are recorded in a rotating log file, **Acta Scriptoris** (The Records of Scriptor), providing a durable audit trail of every patch that was applied, rejected, or quarantined.
- **True Daemonization:** The **speculator** is designed to run as a proper background service using **systemd**, ensuring it is always running, automatically starts on login, and restarts itself on failure.

## Core Components & Commands

The Scriptor SDK is a single, unified tool (scriptor) that provides several subcommands.

- **scriptor compara** (The Comparer): Generates a self-contained .patch file by comparing an original and a revised source file.
- **scriptor speculator** (The Watcher): The file system watcher daemon that detects new patches in the inbox.
- **scriptor inceptor** (The Inceptor): A project scaffolding tool that creates new, sandboxed development initiatives.
- **scriptor praetor** (The Praetor): The Fleet Commander, used for deploying tools and managing multiple development nodes.

The core modules that power these commands are:

- **Operarius** (The Workman): The background worker thread that executes the processing pipeline for each patch.
- **Perfector** (The Completer): The module responsible for applying the patch to the target file.
- **Ornator** (The Arranger): The module that runs code formatters (like Black and Ruff) on newly patched files.
- **Probator** (The Tester): The verification module that runs the project's test suite to confirm the patch's integrity.

## Installation

Scriptor is designed as a global command-line tool using pipx to ensure it operates in an isolated environment.

#### Prerequisites

- Python 3.8+
- [[https://pypa.github.io/pipx/ pipx]]
- [[https://git-scm.com/ Git]] (for the Probator's project root discovery)

#### Installation Steps

1. Clone the repository from GitHub:

```bash
git clone https://github.com/IsidoreLands/scribo.git
cd scribo
```

2. Use pipx to install the package. This builds the tool and makes the scriptor command globally available.

```bash
pipx install .
```

3. Create the inbox directory that the Speculator will monitor:

```bash
mkdir ~/scribo_inbox
```

## Operation

The standard workflow involves running the speculator daemon as a background service and using the other scriptor commands to perform tasks.

#### Step 1: Run Speculator as a Service

The recommended way to run the watcher is as a systemd user service.

1. Create the service file at ~/.config/systemd/user/scriptor.service:

```ini
[Unit]
Description=Scriptor Daemon (via Scriptor SDK)
After=network.target

[Service]
ExecStart=%h/.local/bin/scriptor speculator
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

You can check its status or view live logs with systemctl --user status scriptor.service and journalctl --user -u scriptor.service -f.

#### Step 2: Generate a Patch

As a developer, you have your original file (guide_main.py) and a revised version (guide_v4.py). To integrate the changes, run the compara command:

```bash
scriptor compara guide_main.py guide_v4.py
```

The moment the patch file is created in ~/scribo_inbox/, the speculator service will detect it and trigger the full automated pipeline: apply, format, test, and commit or revert.

## Development Journal

#### Version 3.1 (Current)

- **Architectural Unification:** All tools have been refactored into a single, unified SDK with a main scriptor command and logical subcommands (speculator, compara, praetor, inceptor).
- **Enhanced Patching Logic:** The core patching engine (Perfector and Comparator) was completely overhauled to use git-style relative paths, making it vastly more robust and reliable.
- **Hardened Verification:** The Probator and Ornator modules were refined to be more intelligent and fault-tolerant, correctly handling non-Python files and projects without tests.

''(For previous versions, see the Git history.)''

## Roadmap (Future Development)

- **Praetor Fleet Command:** Fully implement the praetor deploy-sensor command to provision new machines with the System Maneuverability toolset. Integrate the SM and Agentic Maneuverability (AM) scores into the Praetor's decision-making process for intelligent task dispatching.
- **ARC Integration:** Bridge the Scriptor SDK with the AetherOS Navigator ARC, allowing the ARC to autonomously propose and test patches to its own codebase.
- **Initiative Scaffolding:** Evolve the inceptor into a full-fledged project scaffolding tool that can bootstrap new initiatives with pre-configured ARCs and best-practice repository structures.

## Repository

- The official source code is hosted on GitHub: [[https://github.com/IsidoreLands/scribo]]
