# watch.ps1 — Trail & Bish Dynasty auto-deployer
# Watches for file changes and auto-commits + pushes to GitHub.
# Run once at the start of a session, then minimize and forget.
# Usage: .\watch.ps1
#
# Whitelisted paths (the only things this script will ever commit):
#   backend/AP_Dynasty_Backend.xlsx         — source of truth
#   Trail_Bish_Dynasty_Premium.xlsx         — generated output
#   draft_entry_*.txt                       — annual draft-day change logs
#
# When the backend workbook changes, make_premium.py runs first to regenerate
# the Premium, then both workbooks are committed together so they never drift.

$repo       = Split-Path -Parent $MyInvocation.MyCommand.Path
$debounceMs = 4000   # wait 4s after last change before pushing (batches rapid saves)
$python     = "python"   # adjust if your venv uses a different python path

Set-Location $repo

Write-Host ""
Write-Host "  Trail & Bish Dynasty — Auto Deployer" -ForegroundColor Cyan
Write-Host "  Watching backend workbook + draft logs." -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

# ── File system watcher ────────────────────────────────────────────────────────
$watcher                       = New-Object System.IO.FileSystemWatcher
$watcher.Path                  = $repo
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents   = $true
$watcher.NotifyFilter          = [System.IO.NotifyFilters]'FileName, LastWrite'

$lastFired = [datetime]::MinValue

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $rel  = $path.Replace($using:repo + "\", "")

    # ── Guard: only act on whitelisted paths ───────────────────────────────────
    $isBackend  = ($rel -eq "backend\AP_Dynasty_Backend.xlsx")
    $isPremium  = ($rel -eq "Trail_Bish_Dynasty_Premium.xlsx")
    $isDraftLog = ($rel -match "^draft_entry_\d{4}\.txt$")

    if (-not ($isBackend -or $isPremium -or $isDraftLog)) { return }

    # Skip git internals and lock files
    if ($path -match '\\\.git\\' -or $path -match '\.lock$') { return }

    # ── Debounce — one push per burst of saves ─────────────────────────────────
    $now = [datetime]::Now
    if (($now - $script:lastFired).TotalMilliseconds -lt $using:debounceMs) { return }
    $script:lastFired = $now

    $ts = [datetime]::Now.ToString('HH:mm:ss')
    Write-Host "  $ts  detected: $rel" -ForegroundColor Yellow

    Start-Sleep -Milliseconds ($using:debounceMs)

    # Clear stale git locks
    Get-ChildItem -Path "$using:repo\.git" -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }

    Set-Location $using:repo

    # ── If the backend workbook changed, regenerate Premium first ──────────────
    if ($using:isBackend) {
        $ts = [datetime]::Now.ToString('HH:mm:ss')
        Write-Host "  $ts  backend changed — regenerating Premium..." -ForegroundColor Cyan
        $result = & $using:python make_premium.py 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  make_premium.py failed:" -ForegroundColor Red
            Write-Host "  $result" -ForegroundColor Red
            # Still push the backend even if Premium generation failed
        } else {
            Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  Premium regenerated." -ForegroundColor Cyan
        }
    }

    # ── Stage only the whitelisted files that exist ────────────────────────────
    $toAdd = @(
        "backend\AP_Dynasty_Backend.xlsx",
        "Trail_Bish_Dynasty_Premium.xlsx"
    )
    # Also stage any draft_entry log files
    Get-ChildItem -Path $using:repo -Filter "draft_entry_*.txt" -ErrorAction SilentlyContinue |
        ForEach-Object { $toAdd += $_.Name }

    foreach ($f in $toAdd) {
        $full = Join-Path $using:repo $f
        if (Test-Path $full) {
            git add $full 2>&1 | Out-Null
        }
    }

    # ── Commit + push ──────────────────────────────────────────────────────────
    $status = git status --porcelain 2>&1
    if (-not $status) {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  nothing to commit" -ForegroundColor DarkGray
        return
    }

    $stamp = [datetime]::Now.ToString("yyyy-MM-dd HH:mm")
    git commit -m "auto-deploy: $stamp" 2>&1 | Out-Null
    $push  = git push origin main 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  pushed. Streamlit redeploys in ~60s." -ForegroundColor Green
    } else {
        Write-Host "  $([datetime]::Now.ToString('HH:mm:ss'))  push failed: $push" -ForegroundColor Red
    }
}

# Register events
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

# Keep alive
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "`n  Watcher stopped." -ForegroundColor DarkGray
}
