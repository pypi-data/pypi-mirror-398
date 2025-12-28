# PowerShell script to uninstall Topaz Agent Kit services
#
# Usage:
#   .\uninstall_services.ps1
#
# Parameters:
#   -NSSMPath: Path to NSSM executable (default: nssm)

param(
    [Parameter(Mandatory=$false)]
    [string]$NSSMPath = "nssm"
)

# Service names
$serviceNames = @(
    "TopazAgentKit-MCP",
    "TopazAgentKit-Services",
    "TopazAgentKit-FastAPI"
)

Write-Host "Uninstalling Topaz Agent Kit services..." -ForegroundColor Cyan

foreach ($serviceName in $serviceNames) {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Host "`nRemoving service: $serviceName" -ForegroundColor Yellow
        
        # Stop service if running
        if ($service.Status -eq "Running") {
            Write-Host "Stopping service..." -ForegroundColor Yellow
            Stop-Service -Name $serviceName -Force
            Start-Sleep -Seconds 2
        }
        
        # Remove service using NSSM
        & $NSSMPath remove $serviceName confirm
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service $serviceName removed successfully!" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Failed to remove service $serviceName" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Service $serviceName not found, skipping..." -ForegroundColor Gray
    }
}

Write-Host "`nUninstallation complete!" -ForegroundColor Green

