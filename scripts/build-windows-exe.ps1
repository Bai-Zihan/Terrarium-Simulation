param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location $Root
try {
    & $Python -m pip install --upgrade ".[bundle]"
    & $Python scripts\build-release.py --platform-label windows-x64

    Write-Host ""
    Write-Host "Built standalone Windows game package:"
    Write-Host "  $Root\dist\release\terrarium-sim-*-windows-x64.zip"
}
finally {
    Pop-Location
}
