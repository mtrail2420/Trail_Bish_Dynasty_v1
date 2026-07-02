# deploy.ps1 — Trail & Bish Dynasty
# Run this any time Claude finishes a batch of changes.
# Usage: Right-click → "Run with PowerShell"  OR  .\deploy.ps1  in terminal

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

Write-Host "`n[1/4] Clearing stale git lock files..." -ForegroundColor Cyan
Get-ChildItem -Path ".git" -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "  removed $($_.Name)" -ForegroundColor DarkGray }

Write-Host "[2/4] Staging all changes..." -ForegroundColor Cyan
git add .

Write-Host "[3/4] Committing..." -ForegroundColor Cyan
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "deploy: $stamp"

Write-Host "[4/4] Pushing to GitHub (Streamlit Cloud auto-deploys)..." -ForegroundColor Cyan
git push origin main

Write-Host "`nDone. Streamlit Cloud will pick up the changes in ~60 seconds." -ForegroundColor Green
