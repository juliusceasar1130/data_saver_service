# 修改时间：2026-04-13 18:05 Asia/Shanghai
# 主要修改内容：
# 1. 新增 Docker Desktop 下触发 defect-refresh 容器的包装脚本
# 2. 供 Windows 任务计划程序按单次任务方式调用

param(
    [string]$Mode = "--refresh"
)

$AllowedModes = @("--init-state", "--refresh", "--print-status")
if ($AllowedModes -notcontains $Mode) {
    Write-Error "Mode 仅支持: $($AllowedModes -join ', ')"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
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
