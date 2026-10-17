# Build and upload the current version to PyPI. Stops at the first failure.
# The gate runs first; the version must not be on PyPI yet; the token comes from a secret
# store, never from git.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

& powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
if ($LASTEXITCODE -ne 0) { throw "The gate failed (exit $LASTEXITCODE): nothing was built or uploaded." }

$version = (python -c "import sys; sys.path.insert(0, 'src'); import typedmultidict; print(typedmultidict.__version__)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw "Could not read the version." }

# Works on both Windows PowerShell 5.1 and pwsh 7 (generic catch, no PS7-only types).
$published = $true
try {
    Invoke-WebRequest -UseBasicParsing "https://pypi.org/pypi/typedmultidict/$version/json" | Out-Null
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) { $published = $false } else { throw }
}
if ($published) { throw "typedmultidict $version is already on PyPI. Raise the version first." }

$token = $env:PYPI_TOKEN
if (-not $token -and (Test-Path "C:\secrets\pypi-token.txt")) {
    $token = (Get-Content "C:\secrets\pypi-token.txt" -Raw).Trim()
}
if (-not $token) {
    throw "No PyPI token. Set `$env:PYPI_TOKEN or save it to C:\secrets\pypi-token.txt (never commit it)."
}

Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
python -m build
if ($LASTEXITCODE -ne 0) { throw "The build failed (exit $LASTEXITCODE)." }
python -m twine check --strict dist/*
if ($LASTEXITCODE -ne 0) { throw "twine check failed (exit $LASTEXITCODE)." }

$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $token
try {
    python -m twine upload dist/*
    if ($LASTEXITCODE -ne 0) { throw "The upload failed (exit $LASTEXITCODE)." }
} finally { Remove-Item Env:\TWINE_PASSWORD -ErrorAction SilentlyContinue }
