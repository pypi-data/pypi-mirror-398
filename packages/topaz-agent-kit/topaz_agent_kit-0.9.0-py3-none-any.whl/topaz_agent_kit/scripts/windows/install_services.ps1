# PowerShell script to install Topaz Agent Kit services using NSSM
# 
# Prerequisites:
# 1. NSSM must be installed and in PATH, or specify path in $nssmPath variable
# 2. Python must be installed and in PATH
# 3. Topaz Agent Kit must be installed: pip install topaz-agent-kit
#
# Usage:
#   .\install_services.ps1 -ProjectDir "C:\GenAI\ensemble" -LogDir "C:\GenAI\ensemble\logs"
#
# Parameters:
#   -ProjectDir: Path to the project directory (required)
#   -LogDir: Path to log directory (default: C:\GenAI\ensemble\logs)
#   -PythonPath: Path to Python executable (default: python)
#   -NSSMPath: Path to NSSM executable (default: nssm)
#   -ServiceUser: Windows user account to run services (default: LocalSystem)

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectDir,
    
    [Parameter(Mandatory=$false)]
    [string]$LogDir = "C:\GenAI\ensemble\logs",
    
    [Parameter(Mandatory=$false)]
    [string]$PythonPath = "python",
    
    [Parameter(Mandatory=$false)]
    [string]$NSSMPath = "nssm",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceUser = "LocalSystem"
)

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Administrator privileges are required to install Windows services." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host "`nRight-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Get script directory (service scripts are in the same directory as this install script)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceScriptsDir = $ScriptDir

# Validate project directory
if (-not (Test-Path $ProjectDir)) {
    Write-Host "ERROR: Project directory does not exist: $ProjectDir" -ForegroundColor Red
    exit 1
}

# Validate Python and get full path
# First check for venv Python in project directory, then fall back to system Python
$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$venvEntryPoint = Join-Path $ProjectDir ".venv\Scripts\topaz-agent-kit.exe"
$useEntryPoint = $false

if (Test-Path $venvPython) {
    Write-Host "Found venv Python in project directory" -ForegroundColor Green
    $PythonPath = $venvPython
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Gray
    Write-Host "Python path: $PythonPath" -ForegroundColor Gray
    
    # Check if entry point exists (preferred for venv)
    if (Test-Path $venvEntryPoint) {
        Write-Host "Found topaz-agent-kit entry point in venv" -ForegroundColor Green
        $useEntryPoint = $true
        $PythonPath = $venvEntryPoint  # Use entry point instead of Python module
    }
} else {
    try {
        $pythonVersion = & $PythonPath --version 2>&1
        Write-Host "Found system Python: $pythonVersion" -ForegroundColor Green
        
        # Get full path to Python executable (important for services)
        $pythonFullPath = (Get-Command $PythonPath).Source
        Write-Host "Python path: $pythonFullPath" -ForegroundColor Gray
        $PythonPath = $pythonFullPath  # Use full path for service installation
    } catch {
        Write-Host "ERROR: Python not found. Please install Python and ensure it's in PATH." -ForegroundColor Red
        Write-Host "Or create a virtual environment in the project directory (.venv)" -ForegroundColor Yellow
        exit 1
    }
}

# Validate NSSM
try {
    $nssmVersion = & $NSSMPath version 2>&1
    Write-Host "Found NSSM: $nssmVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: NSSM not found. Please install NSSM from https://nssm.cc/download" -ForegroundColor Red
    Write-Host "Or specify path using -NSSMPath parameter" -ForegroundColor Yellow
    exit 1
}

# Note: We use Python directly instead of uv to avoid certificate/network issues
# The package should be installed in the Python environment (pip install topaz-agent-kit)

# Service configurations - batch files will be created dynamically
$services = @(
    @{
        Name = "TopazAgentKit-MCP"
        DisplayName = "Topaz Agent Kit - MCP Server"
        Description = "MCP server for Topaz Agent Kit"
        ScriptBat = "start_mcp.bat"
        BatchContent = @"
@echo off
setlocal
REM Simple batch script to start MCP service via CLI
REM Usage: start_mcp.bat <project_dir>
REM Set UTF-8 encoding for Windows compatibility (fixes charmap codec errors)
set PYTHONIOENCODING=utf-8
cd /d %1
if errorlevel 1 (
    echo ERROR: Failed to change directory to %1
    exit /b 1
)
PYTHON_PLACEHOLDER -m topaz_agent_kit.cli.main serve mcp -p .
if errorlevel 1 (
    echo ERROR: Failed to start MCP service
    exit /b 1
)
"@
    },
    @{
        Name = "TopazAgentKit-Services"
        DisplayName = "Topaz Agent Kit - Agent Services"
        Description = "Agent services (A2A) for Topaz Agent Kit"
        ScriptBat = "start_services.bat"
        BatchContent = @"
@echo off
setlocal
REM Simple batch script to start Agent Services via CLI
REM Usage: start_services.bat <project_dir>
REM Set UTF-8 encoding for Windows compatibility (fixes charmap codec errors)
set PYTHONIOENCODING=utf-8
cd /d %1
if errorlevel 1 (
    echo ERROR: Failed to change directory to %1
    exit /b 1
)
PYTHON_PLACEHOLDER -m topaz_agent_kit.cli.main serve services -p .
if errorlevel 1 (
    echo ERROR: Failed to start Agent Services
    exit /b 1
)
"@
    },
    @{
        Name = "TopazAgentKit-FastAPI"
        DisplayName = "Topaz Agent Kit - FastAPI Server"
        Description = "FastAPI server for Topaz Agent Kit"
        ScriptBat = "start_fastapi.bat"
        BatchContent = @"
@echo off
setlocal
REM Simple batch script to start FastAPI service via CLI
REM Usage: start_fastapi.bat <project_dir>
REM Set UTF-8 encoding for Windows compatibility (fixes charmap codec errors)
set PYTHONIOENCODING=utf-8
cd /d %1
if errorlevel 1 (
    echo ERROR: Failed to change directory to %1
    exit /b 1
)
PYTHON_PLACEHOLDER -m topaz_agent_kit.cli.main serve fastapi -p .
if errorlevel 1 (
    echo ERROR: Failed to start FastAPI service
    exit /b 1
)
"@
    }
)

# Function to install a service
function Install-Service {
    param(
        [string]$ServiceName,
        [string]$DisplayName,
        [string]$Description,
        [string]$ScriptBatName,
        [string]$BatchContent
    )
    
    Write-Host "`nInstalling service: $ServiceName" -ForegroundColor Cyan
    
    # Check if service already exists and remove it
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "Service $ServiceName already exists. Removing existing service..." -ForegroundColor Yellow
        
        # Stop the service if it's running
        if ($existingService.Status -eq 'Running') {
            Write-Host "Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Remove the service using NSSM
        Write-Host "Removing service..." -ForegroundColor Yellow
        $removeOutput = & $NSSMPath remove $ServiceName confirm 2>&1
        $removeExitCode = $LASTEXITCODE
        
        if ($removeExitCode -ne 0) {
            Write-Host "WARNING: Failed to remove existing service. Attempting to continue..." -ForegroundColor Yellow
            Write-Host "NSSM output: $removeOutput" -ForegroundColor Yellow
        }
        
        # Wait for service to be fully removed (Windows services can take time to delete)
        Write-Host "Waiting for service to be fully removed..." -ForegroundColor Yellow
        $maxWaitTime = 30  # Maximum wait time in seconds
        $waitInterval = 2   # Check every 2 seconds
        $waited = 0
        $serviceRemoved = $false
        
        while ($waited -lt $maxWaitTime) {
            Start-Sleep -Seconds $waitInterval
            $waited += $waitInterval
            $stillExists = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
            if (-not $stillExists) {
                $serviceRemoved = $true
                Write-Host "Service removed successfully (waited $waited seconds)." -ForegroundColor Green
                break
            }
            Write-Host "  Still waiting... ($waited / $maxWaitTime seconds)" -ForegroundColor Gray
        }
        
        if (-not $serviceRemoved) {
            Write-Host "ERROR: Service still exists after $maxWaitTime seconds. Cannot proceed with installation." -ForegroundColor Red
            Write-Host "Please manually remove the service and try again:" -ForegroundColor Yellow
            Write-Host "  nssm remove $ServiceName confirm" -ForegroundColor White
            Write-Host "  (Then wait a few seconds and run this script again)" -ForegroundColor Yellow
            return $false
        }
    }
    
    # Get full path to batch script
    $scriptPath = Join-Path $ServiceScriptsDir $ScriptBatName
    
    # Create .bat file with required content
    # Replace PYTHON_PLACEHOLDER with full path to Python executable or entry point (handle paths with spaces)
    if (Test-Path $scriptPath) {
        Write-Host "Overwriting existing batch file: $ScriptBatName" -ForegroundColor Yellow
    } else {
        Write-Host "Creating batch file: $ScriptBatName" -ForegroundColor Yellow
    }
    try {
        # Replace PYTHON_PLACEHOLDER with full path (quote if path contains spaces)
        $executablePathQuoted = if ($PythonPath -match '\s') { "`"$PythonPath`"" } else { $PythonPath }
        
        # If using entry point, replace the entire command; otherwise use Python module path
        if ($useEntryPoint) {
            # Using entry point: replace "PYTHON_PLACEHOLDER -m topaz_agent_kit.cli.main" with just the entry point
            $BatchContentWithPython = $BatchContent -replace 'PYTHON_PLACEHOLDER -m topaz_agent_kit\.cli\.main', $executablePathQuoted
        } else {
            # Using Python module: replace just PYTHON_PLACEHOLDER
            $BatchContentWithPython = $BatchContent -replace 'PYTHON_PLACEHOLDER', $executablePathQuoted
        }
        
        # -Force flag ensures existing files are overwritten
        $BatchContentWithPython | Out-File -FilePath $scriptPath -Encoding ASCII -Force
        Write-Host "Created/Updated $ScriptBatName successfully" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to create batch file $ScriptBatName : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Verify the file was created
    if (-not (Test-Path $scriptPath)) {
        Write-Host "ERROR: Batch file was not created: $scriptPath" -ForegroundColor Red
        return $false
    }
    
    # Install service using cmd.exe to run the batch file
    Write-Host "Installing service with NSSM..." -ForegroundColor Yellow
    Write-Host "Script: $scriptPath" -ForegroundColor Gray
    Write-Host "Arguments: $ProjectDir" -ForegroundColor Gray
    $installOutput = & $NSSMPath install $ServiceName "cmd.exe" "/c" "$scriptPath" "$ProjectDir" 2>&1
    $installExitCode = $LASTEXITCODE
    
    if ($installExitCode -ne 0) {
        Write-Host "ERROR: Failed to install service $ServiceName" -ForegroundColor Red
        Write-Host "NSSM output: $installOutput" -ForegroundColor Red
        return $false
    }
    
    # Verify service was created
    Start-Sleep -Seconds 1
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "ERROR: Service $ServiceName was not created successfully" -ForegroundColor Red
        return $false
    }
    
    # Configure service
    Write-Host "Configuring service..." -ForegroundColor Yellow
    $configErrors = @()
    
    # Helper function to run NSSM set commands and check for errors
    function Set-NSSMParam {
        param([string]$ServiceName, [string]$Parameter, [string]$Value)
        $output = & $NSSMPath set $ServiceName $Parameter $Value 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        return $true
    }
    
    # Set display name
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "DisplayName" -Value "$DisplayName")) {
        $configErrors += "DisplayName"
    }
    
    # Set description
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "Description" -Value "$Description")) {
        $configErrors += "Description"
    }
    
    # Set working directory
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "AppDirectory" -Value "$ProjectDir")) {
        $configErrors += "AppDirectory"
    }
    
    # Set environment variables (NSSM requires all variables in one call)
    $envOutput = & $NSSMPath set $ServiceName AppEnvironmentExtra "TOPAZ_PROJECT_DIR=$ProjectDir" "TOPAZ_LOG_DIR=$LogDir" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $configErrors += "AppEnvironmentExtra"
    }
    
    # Set startup type to automatic
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "Start" -Value "SERVICE_AUTO_START")) {
        $configErrors += "Start"
    }
    
    # Set service account
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "ObjectName" -Value "$ServiceUser")) {
        $configErrors += "ObjectName"
    }
    
    # Configure output (stdout) - with datetime in filename
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stdoutLog = Join-Path $LogDir "$ServiceName-$timestamp.log"
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "AppStdout" -Value "$stdoutLog")) {
        $configErrors += "AppStdout"
    }
    
    # Configure error output (stderr) - combine with stdout (same file)
    # NSSM will append stderr to the same file
    if (-not (Set-NSSMParam -ServiceName $ServiceName -Parameter "AppStderr" -Value "$stdoutLog")) {
        $configErrors += "AppStderr"
    }
    
    # Rotate logs
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppStdoutCreationDisposition" -Value "4" | Out-Null
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppStderrCreationDisposition" -Value "4" | Out-Null
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppRotateFiles" -Value "1" | Out-Null
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppRotateOnline" -Value "1" | Out-Null
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppRotateSeconds" -Value "0" | Out-Null
    Set-NSSMParam -ServiceName $ServiceName -Parameter "AppRotateBytes" -Value "10485760" | Out-Null
    
    if ($configErrors.Count -gt 0) {
        Write-Host "WARNING: Some configuration parameters failed to set: $($configErrors -join ', ')" -ForegroundColor Yellow
        Write-Host "Service was installed but may not be fully configured." -ForegroundColor Yellow
    } else {
        Write-Host "Service $ServiceName installed and configured successfully!" -ForegroundColor Green
    }
    
    return $true
}

# Create log directory
if (-not (Test-Path $LogDir)) {
    Write-Host "Creating log directory: $LogDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Install all services
$successCount = 0
foreach ($service in $services) {
    if (Install-Service -ServiceName $service.Name -DisplayName $service.DisplayName -Description $service.Description -ScriptBatName $service.ScriptBat -BatchContent $service.BatchContent) {
        $successCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Successfully installed: $successCount / $($services.Count) services" -ForegroundColor $(if ($successCount -eq $services.Count) { "Green" } else { "Yellow" })

if ($successCount -eq $services.Count) {
    Write-Host "`nTo start services, run:" -ForegroundColor Green
    foreach ($service in $services) {
        Write-Host "  Start-Service -Name $($service.Name)" -ForegroundColor White
    }
    
    Write-Host "`nOr start all at once:" -ForegroundColor Green
    Write-Host "  Get-Service -Name TopazAgentKit-* | Start-Service" -ForegroundColor White
    
    Write-Host "`nTo check service status:" -ForegroundColor Green
    Write-Host "  Get-Service -Name TopazAgentKit-*" -ForegroundColor White
} else {
    Write-Host "`nSome services failed to install. Please check the errors above." -ForegroundColor Red
    exit 1
}

