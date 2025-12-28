Param(
    [Parameter(Mandatory=$true)] [string]$ResourceGroupName
)
$ErrorActionPreference = "Stop"

$workspaces = az monitor log-analytics workspace list --resource-group $ResourceGroupName --output json | ConvertFrom-Json

if ($workspaces.Count -gt 0) {
    # LOGIC UPDATE: Automation priority
    # 1. Look for standard name "$ResourceGroupName-law"
    $targetWs = $workspaces | Where-Object { $_.name -eq "$ResourceGroupName-law" } | Select-Object -First 1
    
    # 2. If not found, pick the first one
    if (-not $targetWs) {
        $targetWs = $workspaces[0]
    }
    
    Write-Output "LOG ANALYTICS WORKSPACE FOUND: $($targetWs.name)"
} else {
    Write-Output "LOG ANALYTICS WORKSPACE NOT FOUND. Creating..."
    $wsName = "$ResourceGroupName-law"
    az monitor log-analytics workspace create --resource-group $ResourceGroupName --workspace-name $wsName --location "eastus" --output none
    Write-Output "LOG ANALYTICS WORKSPACE FOUND: $wsName"
}