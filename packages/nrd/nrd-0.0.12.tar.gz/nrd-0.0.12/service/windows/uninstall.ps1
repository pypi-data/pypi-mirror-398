# NRD Service Uninstallation Script for Windows
# Run this script as Administrator

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Error: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Uninstalling NRD service for Windows..." -ForegroundColor Green

$taskName = "NRD-Service"

# Check if the task exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $existingTask) {
    Write-Host "NRD service is not installed (task '$taskName' not found)" -ForegroundColor Yellow
    exit 1
}

# Stop the task if running
Write-Host "Stopping task..."
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

# Unregister the scheduled task
Write-Host "Removing scheduled task..."
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false

Write-Host "`n✓ NRD service uninstalled successfully!" -ForegroundColor Green
