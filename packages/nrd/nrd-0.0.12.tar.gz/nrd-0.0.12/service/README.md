# NRD Service Installation Guide

This guide explains how to set up NRD as an autostart service on macOS, Linux, and Windows.

## Overview

The NRD service runs Vite dev servers in the background and automatically starts when your system boots up. This ensures your development servers are always running without manual intervention.

## Prerequisites

- Python 3.8 or higher installed and available in PATH
- NRD package installed (`pip install nrd`)
- Required dependencies (npm, node, herd) properly configured
- Administrative/sudo privileges for installation

## Installation

After installing NRD via pip (`pip install nrd`), you can use the built-in service management commands.

### macOS

**Install the service:**
```bash
nrd-service-install
```

The command will:
- Detect your Python installation
- Create a LaunchAgent plist file with correct paths
- Install it to `~/Library/LaunchAgents/`
- Load and start the service automatically

**Management commands:**
```bash
# Check service status
launchctl list | grep nrd

# View logs
tail -f /tmp/nrd.log
tail -f /tmp/nrd.error.log

# Stop service
launchctl unload ~/Library/LaunchAgents/li.problem.nrd.plist

# Start service
launchctl load ~/Library/LaunchAgents/li.problem.nrd.plist

# Uninstall
nrd-service-uninstall
```

### Linux

**Install the service:**
```bash
sudo nrd-service-install
```

The command will:
- Detect your Python installation
- Create a systemd service file
- Install it to `/etc/systemd/system/`
- Enable and start the service for your user

**Management commands:**
```bash
# Check service status
sudo systemctl status nrd@$USER

# View logs (follow)
sudo journalctl -u nrd@$USER -f

# View recent logs
sudo journalctl -u nrd@$USER -n 50

# Stop service
sudo systemctl stop nrd@$USER

# Start service
sudo systemctl start nrd@$USER

# Restart service
sudo systemctl restart nrd@$USER

# Disable autostart
sudo systemctl disable nrd@$USER

# Enable autostart
sudo systemctl enable nrd@$USER

# Uninstall
sudo nrd-service-uninstall
```

### Windows

**Install the service:**

Open PowerShell or Command Prompt as Administrator and run:
```powershell
nrd-service-install
```

The command will:
- Detect your Python installation
- Create a Scheduled Task
- Configure it to run at system startup
- Start the task immediately

**Management commands:**
```powershell
# Check service status
Get-ScheduledTask -TaskName "NRD-Service"

# View task details
Get-ScheduledTaskInfo -TaskName "NRD-Service"

# Stop task
Stop-ScheduledTask -TaskName "NRD-Service"

# Start task
Start-ScheduledTask -TaskName "NRD-Service"

# Disable task
Disable-ScheduledTask -TaskName "NRD-Service"

# Enable task
Enable-ScheduledTask -TaskName "NRD-Service"

# Uninstall (run as Administrator)
nrd-service-uninstall
```

## Service Configuration

### macOS (LaunchAgent)
- **Config file**: `~/Library/LaunchAgents/li.problem.nrd.plist`
- **Logs**: `/tmp/nrd.log` and `/tmp/nrd.error.log`
- **Run as**: Current user
- **Auto-restart**: Yes (KeepAlive enabled)

### Linux (systemd)
- **Config file**: `/etc/systemd/system/nrd@.service`
- **Logs**: System journal (use `journalctl`)
- **Run as**: Specified user (via `nrd@username.service`)
- **Auto-restart**: Yes (RestartSec=10)

### Windows (Scheduled Task)
- **Task name**: `NRD-Service`
- **Logs**: Task Scheduler logs and Windows Event Viewer
- **Run as**: Current user
- **Auto-restart**: Yes (3 attempts with 1-minute intervals)

## Troubleshooting

### Service won't start

1. **Check Python is in PATH:**
   ```bash
   # macOS/Linux
   which python3
   
   # Windows
   where python
   ```

2. **Check NRD is installed:**
   ```bash
   python3 -m nrd.nrd --help
   ```

3. **Check logs for errors:**
   - macOS: `/tmp/nrd.error.log`
   - Linux: `sudo journalctl -u nrd@$USER -n 50`
   - Windows: Event Viewer or Task Scheduler history

### Service crashes on startup

Check if all dependencies are installed:
- `npm` and `node` must be in PATH
- `herd` command must be available
- Sites configuration is correct

### Permission issues

- **macOS**: Ensure the LaunchAgent plist has correct permissions (644)
- **Linux**: Install script must be run with `sudo`
- **Windows**: PowerShell must be run as Administrator

## Advanced Configuration

### Changing the Python interpreter

If you need to use a different Python interpreter (e.g., a virtual environment):

**macOS:**
Edit `~/Library/LaunchAgents/li.problem.nrd.plist` and change the Python path in the `ProgramArguments` array.

**Linux:**
Edit `/etc/systemd/system/nrd@.service` and change the `ExecStart` line, then run:
```bash
sudo systemctl daemon-reload
sudo systemctl restart nrd@$USER
```

**Windows:**
Uninstall and reinstall the task, or manually edit the task in Task Scheduler.

### Environment Variables

**macOS:**
Add to the `EnvironmentVariables` dict in the plist file.

**Linux:**
Add `Environment="KEY=VALUE"` lines to the service file.

**Windows:**
Modify the task XML to include environment variables in the `<Exec>` section.

## Uninstallation

To completely remove the NRD service:

```bash
# macOS
cd service/macos
./uninstall.sh

# Linux
cd service/linux
sudo ./uninstall.sh

# Windows (PowerShell as Administrator)
cd service\windows
.\uninstall.ps1
```

## Files Included

- **macOS**:
  - `li.problem.nrd.plist` - LaunchAgent configuration template
  - `install.sh` - Installation script
  - `uninstall.sh` - Uninstallation script

- **Linux**:
  - `nrd.service` - systemd service template
  - `install.sh` - Installation script
  - `uninstall.sh` - Uninstallation script

- **Windows**:
  - `nrd-task.xml` - Scheduled Task XML template
  - `install.ps1` - Installation script
  - `uninstall.ps1` - Uninstallation script

## Support

For issues or questions:
- GitHub: https://github.com/blemli/nrd2/issues
- Email: info@problem.li
