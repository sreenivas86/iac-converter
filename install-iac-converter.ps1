#requires -Version 5.1

<#
.SYNOPSIS
    Installs IAC Converter and configures the Windows User PATH.

.DESCRIPTION
    - Checks Python availability and version.
    - Locates the IAC Converter project.
    - Creates a Python virtual environment.
    - Installs IAC Converter and dependencies.
    - Adds the virtual environment Scripts directory to User PATH.
    - Refreshes PATH in the current PowerShell session.
    - Verifies the CLI installation.

.NOTES
    Run this script from the IAC Converter project directory.
    Python 3.11 or newer is required.
#>

$ErrorActionPreference = "Stop"

# --------------------------------------------------
# Display installer header
# --------------------------------------------------

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "          IAC CONVERTER INSTALLER           " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {

    # --------------------------------------------------
    # 1. Check Python installation
    # --------------------------------------------------

    Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if (-not $PythonCommand) {
        throw "Python was not found. Install Python 3.11 or newer and add it to PATH."
    }

    $PythonVersionOutput = & python --version 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to execute Python."
    }

    Write-Host "Detected: $PythonVersionOutput" -ForegroundColor Green

    $PythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

    $VersionParts = $PythonVersion.Split(".")
    $MajorVersion = [int]$VersionParts[0]
    $MinorVersion = [int]$VersionParts[1]

    if (($MajorVersion -lt 3) -or
        (($MajorVersion -eq 3) -and ($MinorVersion -lt 11))) {
        throw "Python 3.11 or newer is required."
    }

    # --------------------------------------------------
    # 2. Locate project directory
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[2/7] Locating IAC Converter project..." -ForegroundColor Yellow

    $ProjectRoot = $PSScriptRoot

    if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
        throw "Unable to determine the installer directory."
    }

    $PyProjectFile = Join-Path $ProjectRoot "pyproject.toml"

    if (-not (Test-Path $PyProjectFile)) {
        throw "pyproject.toml was not found in $ProjectRoot"
    }

    Write-Host "Project directory: $ProjectRoot" -ForegroundColor Green

    # --------------------------------------------------
    # 3. Create virtual environment
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[3/7] Preparing Python virtual environment..." -ForegroundColor Yellow

    $VenvDirectory = Join-Path $ProjectRoot ".venv"
    $VenvPython = Join-Path $VenvDirectory "Scripts\python.exe"
    $VenvScripts = Join-Path $VenvDirectory "Scripts"

    if (-not (Test-Path $VenvPython)) {

        Write-Host "Creating virtual environment..."

        & python -m venv $VenvDirectory

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create Python virtual environment."
        }
    }
    else {
        Write-Host "Existing virtual environment found."
    }

    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment Python executable was not created."
    }

    Write-Host "Virtual environment ready." -ForegroundColor Green

    # --------------------------------------------------
    # 4. Upgrade pip and install application
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[4/7] Installing IAC Converter dependencies..." -ForegroundColor Yellow

    & $VenvPython -m pip install --upgrade pip

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip."
    }

    Write-Host ""
    Write-Host "Installing IAC Converter..."

    & $VenvPython -m pip install $ProjectRoot

    if ($LASTEXITCODE -ne 0) {
        throw "IAC Converter installation failed."
    }

    Write-Host "Application installed successfully." -ForegroundColor Green

    # --------------------------------------------------
    # 5. Configure Windows User PATH
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[5/7] Configuring Windows User PATH..." -ForegroundColor Yellow

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")

    $PathEntries = @()

    if (-not [string]::IsNullOrWhiteSpace($UserPath)) {
        $PathEntries = @(
            $UserPath -split ";" |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )
    }

    $AlreadyConfigured = $false

    foreach ($Entry in $PathEntries) {

        $ExistingPath = [Environment]::ExpandEnvironmentVariables(
            $Entry.Trim().TrimEnd("\")
        )

        $NewPath = $VenvScripts.TrimEnd("\")

        if ($ExistingPath -ieq $NewPath) {
            $AlreadyConfigured = $true
            break
        }
    }

    if (-not $AlreadyConfigured) {

        $UpdatedEntries = @($PathEntries) + $VenvScripts

        $UpdatedUserPath = $UpdatedEntries -join ";"

        [Environment]::SetEnvironmentVariable(
            "Path",
            $UpdatedUserPath,
            "User"
        )

        Write-Host "Added Scripts directory to User PATH." -ForegroundColor Green
    }
    else {
        Write-Host "Scripts directory already exists in User PATH." -ForegroundColor Green
    }

    Write-Host "PATH entry: $VenvScripts"

    # --------------------------------------------------
    # 6. Refresh PATH and verify CLI
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[6/7] Refreshing current PowerShell PATH..." -ForegroundColor Yellow

    $env:Path = "$VenvScripts;$env:Path"

    $CliLauncher = Join-Path $VenvScripts "iac-converter.exe"

    if (-not (Test-Path $CliLauncher)) {
        throw "CLI launcher was not created: $CliLauncher"
    }

    Write-Host "CLI launcher found." -ForegroundColor Green

    Write-Host ""
    Write-Host "Checking installed package version..."

    # Use the Python module invocation for verification.
    # This also works if the Windows console launcher has execution restrictions.

    & $VenvPython -m iac_converter.cli --version

    if ($LASTEXITCODE -ne 0) {
        throw "CLI version verification failed."
    }

    # --------------------------------------------------
    # 7. Final installation information
    # --------------------------------------------------

    Write-Host ""
    Write-Host "[7/7] Installation completed." -ForegroundColor Yellow

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "     IAC CONVERTER INSTALLED SUCCESSFULLY   " -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green

    Write-Host ""
    Write-Host "Installation directory:" -ForegroundColor Cyan
    Write-Host $ProjectRoot

    Write-Host ""
    Write-Host "CLI executable:" -ForegroundColor Cyan
    Write-Host $CliLauncher

    Write-Host ""
    Write-Host "PATH configured:" -ForegroundColor Cyan
    Write-Host $VenvScripts

    Write-Host ""
    Write-Host "You can now try these commands:" -ForegroundColor Cyan

    Write-Host "  iac-converter --version"
    Write-Host "  iac-converter --help"
    Write-Host "  iac-converter validate --help"

    Write-Host ""
    Write-Host "Restart PowerShell to use the command in new sessions." -ForegroundColor Yellow

    Write-Host ""

}
catch {

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "          INSTALLATION FAILED               " -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red

    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    exit 1
}