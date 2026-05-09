# Updated: 2026-04-14 22:12 Asia/Shanghai
# Changes:
# 1. Add a host-side wrapper for analytics_db refresh scheduling
# 2. Prefer psql from explicit path before falling back to PATH lookup
# 3. Write start and finish logs to logs/analytics_db_refresh.log
# 4. Support optional DbPassword while preferring pgpass for scheduled runs

param(
    [string]$PsqlExe = "",
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432",
    [string]$DbName = "analytics_db",
    [string]$DbUser = "root",
    [string]$DbPassword = "root",
    [string]$ProcedureName = "meta.refresh_analytics_all"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "analytics_db_refresh.log"
$Sql = "CALL $ProcedureName();"

function Resolve-PsqlExecutor {
    param(
        [string]$PreferredPsqlExe
    )

    if ($PreferredPsqlExe) {
        if (-not (Test-Path -LiteralPath $PreferredPsqlExe)) {
            throw "The specified PsqlExe does not exist: $PreferredPsqlExe"
        }
        return $PreferredPsqlExe
    }

    $psqlCommand = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlCommand) {
        return $psqlCommand.Source
    }

    throw "No usable psql executable was found. Pass -PsqlExe or ensure psql is available in PATH."
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectRoot

$resolvedPsql = Resolve-PsqlExecutor -PreferredPsqlExe $PsqlExe
$startAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$startAt] start refresh db=$DbName host=$DbHost port=$DbPort user=$DbUser psql=$resolvedPsql procedure=$ProcedureName"

$previousPgPassword = $env:PGPASSWORD
if ($DbPassword) {
    $env:PGPASSWORD = $DbPassword
}

try {
    & $resolvedPsql `
        -h $DbHost `
        -p $DbPort `
        -U $DbUser `
        -d $DbName `
        -v ON_ERROR_STOP=1 `
        -c $Sql *>> $LogFile
} finally {
    if ($DbPassword) {
        if ($null -eq $previousPgPassword) {
            Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        } else {
            $env:PGPASSWORD = $previousPgPassword
        }
    }
}

$exitCode = $LASTEXITCODE
$endAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$endAt] finish refresh db=$DbName exit_code=$exitCode"

exit $exitCode
