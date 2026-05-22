param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location $Root
try {
    & $Python -m pip install --upgrade pyinstaller
    & $Python -m PyInstaller `
        --onefile `
        --console `
        --name terrarium `
        --clean `
        packaging\terrarium_launcher.py

    Write-Host ""
    Write-Host "Built standalone game executable:"
    Write-Host "  $Root\dist\terrarium.exe"
}
finally {
    Pop-Location
}
