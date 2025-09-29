param(
    [switch]$Full,
    [int]$Port = 8848,
    [switch]$Listen,
    [switch]$Share,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
function Get-PythonCmd {
    try { $null = & py -0p 2>$null; if ($LASTEXITCODE -eq 0) { return 'py' } } catch {}
    return 'python'
}

$python = Get-PythonCmd
Write-Host "Using Python launcher: $python"

if (-not (Test-Path '.venv')) {
    Write-Host 'Creating virtual environment (.venv)...'
    & $python -m venv .venv
}

$activate = ".\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $activate)) { Write-Error "Activation script not found: $activate" }
. $activate

# Configure Google credentials if a local service_account.json exists
# Note: A template file 'service_account.json.templete' is provided. Copy it to 'service_account.json' and fill in real values.
$saJson = Join-Path $PSScriptRoot 'service_account.json'
if (Test-Path $saJson) {
    if (-not $env:GOOGLE_APPLICATION_CREDENTIALS) {
        $env:GOOGLE_APPLICATION_CREDENTIALS = $saJson
        Write-Host "Set GOOGLE_APPLICATION_CREDENTIALS to $saJson"
    } else {
        Write-Host "GOOGLE_APPLICATION_CREDENTIALS already set. Using existing value." -ForegroundColor Yellow
    }
    try {
        $sa = Get-Content $saJson -Raw | ConvertFrom-Json
        if ($sa.project_id) {
            $env:GOOGLE_CLOUD_PROJECT = $sa.project_id
            Write-Host "Set GOOGLE_CLOUD_PROJECT to $($sa.project_id)"
        }
    } catch {}
}

# Upgrade pip tooling
python -m pip install --upgrade pip wheel setuptools | Out-Host

# Install requirements
Write-Host 'Installing minimal requirements...'
pip install -r requirements.txt | Out-Host

if ($Full) {
    Write-Host 'Installing optional requirements (this may take a while)...'
    pip install -r requirements-optional.txt | Out-Host
}

# Build run args
$runArgs = @('gpt-caption.py','--port', $Port)
if ($Listen)   { $runArgs += '--listen' }
if ($Share)    { $runArgs += '--share' }
if ($NoBrowser){ $runArgs += '--no-browser' }

Write-Host "Launching app: python $($runArgs -join ' ')"
python @runArgs
