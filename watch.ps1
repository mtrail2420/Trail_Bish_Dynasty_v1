# watch.ps1 — Trail & Bish Dynasty auto-deployer
# Watches for file changes and auto-commits + pushes to GitHub.
# Run once at the start of a session, then minimize and forget.
# Usage: .\watch.ps1

$repo    = Split-Path -Parent $MyInvocation.MyCommand.Path
$filter  = "*.py", "*.css", "*.toml", "*.txt", "*.md"
$debounceMs = 4000   # wait 4s after last change before pushing (batches rapid saves)

Set-Location $repo

Write-Host ""
Write-Host "  Trail & Bish Dynasty — Auto Deployer" -ForegroundColor Cyan
Write-Host "  Watching for changes. Minimize this window." -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

# Set up the watcher
$watcher                  = New-Object System.IO.FileSystemWatcher
$watcher.Path             = $repo
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents   = $true
$watcher.NotifyFilter     = [System.IO.NotifyFilters]'FileName, LastWrite'

$lastFired = [datetime]::MinValue

$action = {
    $path = $Event.SourceEventArgs.FullPath

    # Ignore git internals, pycache, and the watcher scripts themselves
    if ($path -match '\\\.git\\' -or
        $path -match '__pycache__' -or
        $path -match 'watch\.ps1' -or
        $path -match 'deploy\.ps1') { return }

    # Debounce — only fire once per burst of saves
    $now = [datetime]::Now
    if (($now - $script:lastFired).TotalMilliseconds -lt $using:debounceMs) { return }
    $script:lastFired = $now

    Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  change detected: $(Split-Path $path -Leaf)" -ForegroundColor Yellow

    Start-Sleep -Milliseconds $using:debounceMs

    # Clear stale git locks
    Get-ChildItem -Path "$using:repo\.git" -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }

    # Stage + commit + push
    Set-Location $using:repo
    git add . 2>&1 | Out-Null

    $status = git status --porcelain 2>&1
    if (-not $status) {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  nothing to commit" -ForegroundColor DarkGray
        return
    }

    $stamp = [datetime]::Now.ToString("yyyy-MM-dd HH:mm")
    git commit -m "auto-deploy: $stamp" 2>&1 | Out-Null
    $push  = git push origin main 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  pushed to GitHub. Streamlit deploys in ~60s." -ForegroundColor Green
    } else {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  push failed: $push" -ForegroundColor Red
    }
}

# Register events for Created, Changed, Renamed
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

# Keep the script alive
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "`n  Watcher stopped." -ForegroundColor DarkGray
}
