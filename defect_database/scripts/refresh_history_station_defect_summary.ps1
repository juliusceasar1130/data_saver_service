# Updated: 2026-04-14 19:56 Asia/Shanghai
# Changes:
# 1. Add a host-side wrapper for refresh_history_station_defect_summary.py
# 2. Prefer host scheduling for enterprise network source databases
# 3. Reuse the active Conda env only when it matches the target env name
# 4. Prefer conda run -n websoket before falling back to PATH python
# 5. Move this script under defect_database/scripts and keep ProjectRoot at repo root

param(
    [string]$Mode = "--refresh",
    [string]$PythonExe = "",
    [string]$CondaEnv = "websoket"
)

$AllowedModes = @("--init-state", "--refresh", "--print-status")
if ($AllowedModes -notcontains $Mode) {
    Write-Error "Unsupported Mode. Allowed values: $($AllowedModes -join ', ')"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "history_station_defect_summary_refresh.log"

function Resolve-PythonExecutor {
    param(
        [string]$PreferredPythonExe,
        [string]$PreferredCondaEnv
    )

    if ($PreferredPythonExe) {
        if (-not (Test-Path -LiteralPath $PreferredPythonExe)) {
            throw "The specified PythonExe does not exist: $PreferredPythonExe"
        }
        return @{
            Kind = "python"
            Command = $PreferredPythonExe
        }
    }

    if ($env:CONDA_PREFIX -and $env:CONDA_DEFAULT_ENV -eq $PreferredCondaEnv) {
        $condaPython = Join-Path $env:CONDA_PREFIX "python.exe"
        if (Test-Path -LiteralPath $condaPython) {
            return @{
                Kind = "python"
                Command = $condaPython
            }
        }
    }

    $condaCommand = Get-Command conda -ErrorAction SilentlyContinue
    if ($condaCommand) {
        return @{
            Kind = "conda"
            Command = $condaCommand.Source
            EnvName = $PreferredCondaEnv
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @{
            Kind = "python"
            Command = $pythonCommand.Source
        }
    }

    throw "No usable Python runtime was found. Pass -PythonExe or ensure python/conda is available in PATH."
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectRoot

$executor = Resolve-PythonExecutor -PreferredPythonExe $PythonExe -PreferredCondaEnv $CondaEnv
$startAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$startAt] start refresh mode=$Mode executor=$($executor.Kind):$($executor.Command)"

if ($executor.Kind -eq "python") {
    & $executor.Command "defect_database/refresh_history_station_defect_summary.py" $Mode *>> $LogFile
} else {
    $previousCondaNoPlugins = $env:CONDA_NO_PLUGINS
    $env:CONDA_NO_PLUGINS = "true"
    try {
        & $executor.Command --no-plugins run -n $executor.EnvName python "defect_database/refresh_history_station_defect_summary.py" $Mode *>> $LogFile
    } finally {
        if ($null -eq $previousCondaNoPlugins) {
            Remove-Item Env:CONDA_NO_PLUGINS -ErrorAction SilentlyContinue
        } else {
            $env:CONDA_NO_PLUGINS = $previousCondaNoPlugins
        }
    }
}

$exitCode = $LASTEXITCODE
$endAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$endAt] finish refresh mode=$Mode exit_code=$exitCode"

exit $exitCode
