# Local quality gate. Run before every commit. No CI runs in the cloud.
# Every tool runs through the same interpreter (python -m), never whatever comes first on
# PATH. $ErrorActionPreference does NOT stop on a native command's non-zero exit, so each
# exit code is checked explicitly: a red gate must fail, never pass silently.
$ErrorActionPreference = "Stop"

function Invoke-Step($label, [scriptblock]$cmd) {
    Write-Host "== $label =="
    & $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $label (exit $LASTEXITCODE)"; exit $LASTEXITCODE }
}

Invoke-Step "ruff format" { python -m ruff format --check . }
Invoke-Step "ruff lint"   { python -m ruff check . }
Invoke-Step "mypy"        { python -m mypy --strict src tests scripts }
Invoke-Step "pytest"      { python -m pytest }
Write-Host "gate green"
