<div align="center">

# **CacheKaro**

### Cross-Platform Storage & Cache Manager

**CacheKaro** - *Clean It Up!*

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](#-platform-support)
[![Tests](https://img.shields.io/badge/tests-53%20passing-brightgreen.svg)](#-development)

[Overview](#-overview) · [Installation](#-installation) · [Uninstall](#-uninstall) · [Quick Start](#-quick-start) · [Commands](#-commands) · [Detection](#-what-it-detects) · [Safety](#-safety--risk-levels) · [Export Formats](#-export-formats) · [Config](#-configuration) · [Development](#-development) · [Platform Support](#-platform-support) · [License](#-license)

</div>

---

## ▸ Overview

**CacheKaro** is a cross-platform CLI tool to analyze and clean cache/storage on **macOS**, **Linux** and **Windows**. It automatically discovers caches from all installed applications and games.

### Why CacheKaro?

| # | Feature | Description |
|:-:|---------|-------------|
| 1 | **Auto-Discovery** | Automatically detects 300+ known apps and any new software you install |
| 2 | **Cross-Platform** | One tool for macOS, Linux and Windows |
| 3 | **Developer Friendly** | Cleans npm, pip, Gradle, Maven, Cargo, Go, Docker and more |
| 4 | **Game Support** | Steam, Epic Games, Riot Games, Battle.net, Minecraft and more |
| 5 | **Creative Suite** | Adobe CC, DaVinci Resolve, Blender, Ableton, AutoCAD and more |
| 6 | **Safe by Default** | Risk-based classification prevents accidental data loss |
| 7 | **Beautiful Reports** | Cyberpunk-themed HTML reports with charts |

---

## ▸ Installation

### • Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### • Install via pip (Recommended)

```bash
pip install cachekaro
```

### • Install from Source

```bash
# 1. Clone the repository
git clone https://github.com/Mohit-Bagri/cachekaro.git

# 2. Navigate to the ROOT folder (not cachekaro/cachekaro)
cd cachekaro

# 3. Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# OR
.\venv\Scripts\activate         # Windows

# 4. Install CacheKaro
pip install -e .
```

### • Verify Installation

```bash
cachekaro --version
```

> **Note:** If installed from source, the `cachekaro` command only works when the virtual environment is activated. Always run `source venv/bin/activate` before using CacheKaro.

---

## ▸ Uninstall

```bash
pip uninstall cachekaro
```

To also remove configuration files:

| Platform | Command |
|----------|---------|
| macOS/Linux | `rm -rf ~/.config/cachekaro` |
| Windows | `rmdir /s %APPDATA%\cachekaro` |

---

## ▸ Quick Start

```bash
# ► Analyze your storage
cachekaro analyze

# ► Preview what can be cleaned (safe mode)
cachekaro clean --dry-run

# ► Clean caches interactively
cachekaro clean

# ► Auto-clean all safe items without prompts
cachekaro clean --auto

# ► Generate cyberpunk HTML report
cachekaro report --output report.html
```

---

## ▸ Commands

### • `cachekaro analyze`

Scans and displays all cache/storage usage on your system.

```bash
cachekaro analyze                          # Basic analysis
cachekaro analyze -f json                  # Output as JSON
cachekaro analyze -f csv -o data.csv       # Export to CSV
cachekaro analyze -c browser               # Only browser caches
cachekaro analyze --min-size 100MB         # Only items > 100MB
cachekaro analyze --stale-days 7           # Mark items older than 7 days as stale
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Output format: `text`, `json`, `csv` | `text` |
| `--output` | `-o` | Save output to file | stdout |
| `--category` | `-c` | Filter: `browser`, `development`, `game`, `application`, `system` | all |
| `--min-size` | — | Minimum size filter (e.g., `50MB`, `1GB`) | `0` |
| `--stale-days` | — | Days threshold for stale detection | `30` |

---

### • `cachekaro clean`

Removes cache files based on selected criteria.

```bash
cachekaro clean                            # Interactive mode
cachekaro clean --dry-run                  # Preview only, no deletion
cachekaro clean --auto                     # Auto-clean without prompts
cachekaro clean --auto --risk moderate     # Include moderate risk items
cachekaro clean -c browser                 # Clean only browser caches
cachekaro clean --stale-only               # Clean only stale items
```

| Option | Description | Default |
|--------|-------------|---------|
| `--dry-run` | Preview what would be deleted without actually deleting | `false` |
| `--auto` | Automatically clean all items without confirmation prompts | `false` |
| `--category` | Category to clean: `browser`, `development`, `game`, `application`, `system` | all |
| `--risk` | Maximum risk level: `safe`, `moderate`, `caution` | `safe` |
| `--stale-only` | Only clean items older than stale threshold | `false` |

---

### • `cachekaro report`

Generates detailed visual reports with charts.

```bash
cachekaro report                           # Generate HTML report
cachekaro report -o myreport.html          # Custom filename
cachekaro report -f json -o report.json    # JSON format
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--format` | `-f` | Report format: `html`, `json`, `csv`, `text` | `html` |
| `--output` | `-o` | Output file path | `cachekaro_report_<timestamp>.html` |

---

### • `cachekaro info`

Displays system information and CacheKaro configuration.

```bash
cachekaro info
```

---

### • `cachekaro update`

Check for updates and get upgrade instructions.

```bash
cachekaro update                           # Check for new versions
```

CacheKaro automatically notifies you when a new version is available each time you run a command.

---

## ▸ What It Detects

### • Automatic Discovery

CacheKaro automatically scans standard cache directories and identifies **any** application by its folder name. It recognizes 300+ known apps with friendly names.

### • Categories

| # | Category | Examples |
|:-:|----------|----------|
| 1 | **Browser** | Chrome, Firefox, Safari, Edge, Brave, Arc, Vivaldi, Opera |
| 2 | **Development** | npm, pip, Cargo, Gradle, Maven, Docker, VS Code, JetBrains, Xcode |
| 3 | **Games** | Steam, Epic Games, Riot Games, Battle.net, Minecraft, Unity, GOG |
| 4 | **Creative** | Photoshop, Premiere Pro, After Effects, DaVinci Resolve, Final Cut Pro |
| 5 | **3D & Design** | Blender, Cinema 4D, Maya, ZBrush, SketchUp, Figma, Sketch |
| 6 | **Audio** | Ableton Live, FL Studio, Logic Pro, Pro Tools, Cubase, GarageBand |
| 7 | **Engineering** | AutoCAD, SolidWorks, Fusion 360, MATLAB, Simulink, Revit |
| 8 | **Applications** | Spotify, Discord, Slack, Zoom, WhatsApp, Notion, Obsidian |
| 9 | **System** | OS caches, temp files, logs, crash reports, font caches |

### • Platform-Specific Paths

| Platform | Locations Scanned |
|----------|-------------------|
| **macOS** | `~/Library/Caches`, `~/.cache`, `~/Library/Logs`, `~/Library/Application Support` |
| **Linux** | `~/.cache`, `~/.config`, `~/.local/share`, `~/.steam`, `~/.var/app` |
| **Windows** | `%LOCALAPPDATA%`, `%APPDATA%`, `%TEMP%`, `%USERPROFILE%` |

---

## ▸ Safety & Risk Levels

| Level | Icon | Description | Examples |
|-------|------|-------------|----------|
| **Safe** | 🟢 | 100% safe to delete, no data loss | Browser cache, npm cache, pip cache, temp files |
| **Moderate** | 🟡 | Generally safe, may require re-login or re-download | HuggingFace models, Maven repo, Docker images |
| **Caution** | 🔴 | Review before deleting, may contain user data | Downloads folder, application data |

```bash
# ► Only clean safe items (default behavior)
cachekaro clean --risk safe

# ► Include moderate risk items
cachekaro clean --risk moderate

# ► Preview caution-level items before cleaning
cachekaro clean --risk caution --dry-run
```

---

## ▸ Export Formats

| # | Format | Use Case | Command Example |
|:-:|--------|----------|-----------------|
| 1 | **Text** | Terminal output with colors | `cachekaro analyze` |
| 2 | **JSON** | APIs and automation | `cachekaro analyze -f json` |
| 3 | **CSV** | Spreadsheet analysis | `cachekaro analyze -f csv -o data.csv` |
| 4 | **HTML** | Interactive reports with charts | `cachekaro report` |

---

## ▸ Configuration

### • Config File Location

| Platform | Path |
|----------|------|
| macOS/Linux | `~/.config/cachekaro/config.yaml` |
| Windows | `%APPDATA%\cachekaro\config.yaml` |

### • Example Config

```yaml
settings:
  stale_threshold_days: 30      # Days before item is considered stale
  default_format: text          # Default output format
  color_output: true            # Enable colored terminal output
  backup_before_delete: false   # Create backup before deletion

custom_paths:                   # Add your own cache paths
  - path: ~/my-app/cache
    name: My App Cache
    category: custom
    risk_level: safe
```

---

## ▸ Development

```bash
# ► Setup development environment
git clone https://github.com/Mohit-Bagri/cachekaro.git
cd cachekaro
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# ► Run tests
pytest

# ► Linting & type checking
ruff check .
mypy cachekaro
```

---

## ▸ Platform Support

| OS | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 |
|----|:----------:|:-----------:|:-----------:|:-----------:|
| macOS | ✓ | ✓ | ✓ | ✓ |
| Ubuntu | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ |

---

## ▸ License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

Made in 🇮🇳 with ❤️ by [MOHIT BAGRI](https://github.com/Mohit-Bagri)

**CacheKaro** - *Clean It Up!*

</div>
