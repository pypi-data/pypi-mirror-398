Param(
    [Parameter(Mandatory=$true)] [string]$ResourceGroupName,
    [Parameter(Mandatory=$true)] [string]$WorkspaceId,
    [Parameter(Mandatory=$true)] [string]$ResourceId
)
$ErrorActionPreference = "Stop"

$diagName = "diag-" + ($ResourceId -split '/')[-1]

# Check if setting already exists to avoid errors? 
# Az diagnostic-settings create is idempotent (it updates if exists), so safe to run.

az monitor diagnostic-settings create `
    --name $diagName `
    --resource $ResourceId `
    --workspace $WorkspaceId `
    --logs '[{"categoryGroup":"allLogs","enabled":true}]' `
    --metrics '[{"category":"AllMetrics","enabled":true}]' `
    --output none 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Output "Diagnostic setting '$diagName' successfully configured."
} else {
    Write-Error "Failed to configure diagnostic setting. Resource type might not support 'allLogs' or 'AllMetrics'."
    exit 1
}