# NRD Service Installation Script for Windows
# Run this script as Administrator

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Error: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing NRD service for Windows..." -ForegroundColor Green

# Get current user
$currentUser = [Environment]::UserName
$userProfile = $env:USERPROFILE

Write-Host "Installing for user: $currentUser"

# Check if Python is installed
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pythonPath"

# Create the scheduled task XML
$taskName = "NRD-Service"
$xmlContent = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>NRD - Vite Dev Server Background Service</Description>
    <Author>Problemli GmbH</Author>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$currentUser</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$pythonPath</Command>
      <Arguments>-m nrd.nrd</Arguments>
      <WorkingDirectory>$userProfile</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

# Save XML to temp file
$tempXmlPath = "$env:TEMP\nrd-task.xml"
$xmlContent | Out-File -FilePath $tempXmlPath -Encoding unicode

# Unregister existing task if present
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Register the scheduled task
Write-Host "Registering scheduled task..."
Register-ScheduledTask -Xml (Get-Content $tempXmlPath | Out-String) -TaskName $taskName

# Start the task
Write-Host "Starting task..."
Start-ScheduledTask -TaskName $taskName

# Clean up temp file
Remove-Item $tempXmlPath

Write-Host "`n✓ NRD service installed and started successfully!" -ForegroundColor Green
Write-Host "`nTask Name: $taskName"
Write-Host "`nManagement commands:"
Write-Host "  Check status: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  View logs: Get-Content '$userProfile\nrd.log'"
Write-Host "  Stop task: Stop-ScheduledTask -TaskName '$taskName'"
Write-Host "  Start task: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  Disable: Disable-ScheduledTask -TaskName '$taskName'"
Write-Host "  Enable: Enable-ScheduledTask -TaskName '$taskName'"
Write-Host "  Uninstall: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
