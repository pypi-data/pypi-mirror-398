# nrd

Run `npm run dev` in background for all your Laravel Herd sites.

## Installation

```bash
pipx install nrd
```

**Important: After installing, set up the autostart service:**

**macOS:**
```bash
nrd-service-install
```

**Linux:**

```bash
sudo nrd-service-install
```

**Windows (Run PowerShell as Administrator):**

```powershell
nrd-service-install
```

This installs NRD as a system service that automatically starts when your computer boots, keeping your Vite dev servers running in the background.

## Usage

If you have installed the background service you don't have to do anything.

Otherwise simply run the nrd command to start all Vite dev servers for your secured Herd sites:

```bash
nrd
```

Or run it as a module:

```bash
python -m nrd.nrd
```


## Uninstall Service

**macOS:**
```bash
nrd-service-uninstall
```

**Linux:**
```bash
sudo nrd-service-uninstall
```

**Windows (Run as Administrator):**
```powershell
nrd-service-uninstall
```

For detailed instructions, troubleshooting, and management commands, see the [Service Installation Guide](service/README.md).

## Features

- Automatically detects all secured Laravel Herd sites
- Runs Vite dev servers in the background
- Cross-platform service support (macOS, Linux, Windows)
- Auto-restart on failure
- Easy installation and management scripts

## Requirements

- Python 3.8 or higher
- Laravel Herd installed and configured
- npm and node.js
- Sites with Vite configured

## How It Works

NRD uses the `herd parked --json` command to discover all your secured Herd sites, then starts `npm run dev` for each site in the background. When configured as a service, it automatically starts on system boot and keeps your dev servers running.
