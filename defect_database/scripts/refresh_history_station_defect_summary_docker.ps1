# Updated: 2026-04-14 19:58 Asia/Shanghai
# Changes:
# 1. Add a wrapper to trigger defect-refresh via Docker Desktop
# 2. Keep this script suitable for Windows Task Scheduler
# 3. Keep ProjectRoot at repo root after moving under defect_database/scripts
# 4. Use ASCII messages for better PowerShell 5.1 compatibility

param(
    [string]$Mode = "--refresh"
)

$AllowedModes = @("--init-state", "--refresh", "--print-status")
if ($AllowedModes -notcontains $Mode) {
    Write-Error "Unsupported Mode. Allowed values: $($AllowedModes -join ', ')"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "history_station_defect_summary_docker.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectRoot

$startAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$startAt] start docker defect refresh mode=$Mode"

docker compose --profile manual run --rm defect-refresh $Mode *>> $LogFile
$exitCode = $LASTEXITCODE

$endAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$endAt] finish docker defect refresh mode=$Mode exit_code=$exitCode"

exit $exitCode
