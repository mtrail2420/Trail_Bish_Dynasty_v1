# setup_autostart.ps1 — Trail & Bish Dynasty
# Registers watch.ps1 as a Windows Task Scheduler job that starts
# automatically every time you log in. Run this script once, ever.
# Usage: Right-click → "Run with PowerShell"

$repo      = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchScript = Join-Path $repo "watch.ps1"
$taskName  = "TrailBishDynasty_AutoDeploy"
$logPath   = Join-Path $repo "autodeploy.log"

# Check the watch script exists
if (-not (Test-Path $watchScript)) {
    Write-Host "ERROR: watch.ps1 not found at $watchScript" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Setting up Trail & Bish auto-deployer..." -ForegroundColor Cyan

# Remove existing task if it's there (clean reinstall)
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Action: run watch.ps1 hidden, log output to autodeploy.log
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File `"$watchScript`" *>> `"$logPath`" 2>&1"

# Trigger: at login of the current user
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: restart on failure, don't stop after 3 days
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Auto-deploys Trail & Bish Dynasty changes to GitHub whenever files are saved." `
    -RunLevel Highest `
    -Force | Out-Null

# Start it right now too (don't wait for next login)
Start-ScheduledTask -TaskName $taskName

Write-Host "  Done. Auto-deployer is running now and will start automatically at every login." -ForegroundColor Green
Write-Host ""
Write-Host "  Task name : $taskName" -ForegroundColor DarkGray
Write-Host "  Log file  : $logPath" -ForegroundColor DarkGray
Write-Host "  To stop   : Stop-ScheduledTask -TaskName '$taskName'" -ForegroundColor DarkGray
Write-Host "  To remove : Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor DarkGray
Write-Host ""
