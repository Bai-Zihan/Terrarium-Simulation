param(
    [string]$Python = "python",
    [switch]$NoPath
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

function Get-NormalizedPath([string]$PathValue) {
    $Expanded = [Environment]::ExpandEnvironmentVariables($PathValue.Trim().Trim('"'))
    return [System.IO.Path]::GetFullPath($Expanded).TrimEnd("\")
}

function Add-UserPathEntry([string]$Directory) {
    $NormalizedDirectory = Get-NormalizedPath $Directory
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $Entries = @()
    if ($UserPath) {
        $Entries = $UserPath -split ";" | Where-Object { $_.Trim() }
    }
    $NormalizedEntries = $Entries | ForEach-Object { Get-NormalizedPath $_ }

    if ($NormalizedEntries -contains $NormalizedDirectory) {
        Write-Host "PATH already contains:"
        Write-Host "  $NormalizedDirectory"
        return $false
    }

    $NewPath = ((@($Entries) + $NormalizedDirectory) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $EnvironmentKey = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Environment")
    try {
        $EnvironmentKey.SetValue("Path", $NewPath, [Microsoft.Win32.RegistryValueKind]::ExpandString)
    }
    finally {
        $EnvironmentKey.Close()
    }
    if (($env:Path -split ";" | ForEach-Object { if ($_) { Get-NormalizedPath $_ } }) -notcontains $NormalizedDirectory) {
        $env:Path = "$env:Path;$NormalizedDirectory"
    }
    Write-Host "Added to user PATH:"
    Write-Host "  $NormalizedDirectory"
    return $true
}

Push-Location $Root
try {
    & $Python -m pip install --user --editable . --no-warn-script-location
    $ScriptsDir = (& $Python -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))").Trim()
    $CommandPath = Join-Path $ScriptsDir "terrarium.exe"
    if (-not (Test-Path -LiteralPath $CommandPath)) {
        $FallbackScriptsDir = (& $Python -c "import sysconfig; print(sysconfig.get_path('scripts'))").Trim()
        $FallbackCommandPath = Join-Path $FallbackScriptsDir "terrarium.exe"
        if (Test-Path -LiteralPath $FallbackCommandPath) {
            $ScriptsDir = $FallbackScriptsDir
            $CommandPath = $FallbackCommandPath
        }
    }

    if (-not (Test-Path -LiteralPath $CommandPath)) {
        Write-Host ""
        Write-Host "Installed the package, but could not find terrarium.exe automatically."
        Write-Host "Check the pip output above for the script install directory."
        exit 1
    }

    if (-not $NoPath) {
        $PathChanged = Add-UserPathEntry $ScriptsDir
    }

    Write-Host ""
    Write-Host "Installed the 'terrarium' command:"
    Write-Host "  $CommandPath"
    if (-not $NoPath -and $PathChanged) {
        Write-Host "Open a new terminal so Windows reloads PATH, then run:"
    }
    else {
        Write-Host "Run from any terminal:"
    }
    Write-Host "  terrarium"
}
finally {
    Pop-Location
}
