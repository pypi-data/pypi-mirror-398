"""
Azure Resource Management Tools
Contains all Azure-specific MCP tools and helper functions.
"""
import subprocess
import os
import re
import shutil
import json
from typing import Dict, Tuple, Optional

# Get shared server instance
try:
    from . import server
except ImportError:
    import server

# Use server.mcp directly for decorators
run_command = server.run_command
_get_script_path = server._get_script_path
_get_template_path = server._get_template_path
_run_powershell_script = server._run_powershell_script

# --- AZURE CONFIGURATION ---

# Resources that should be attached to NSP (suggestion will be provided after creation)
NSP_MANDATORY_RESOURCES = [
    "storage-account",  # ADLS is usually a storage account with HNS enabled
    "key-vault",
    "cosmos-db",
    "sql-db"
]

# Resources that should have diagnostic settings (suggestion will be provided after creation)
LOG_ANALYTICS_MANDATORY_RESOURCES = [
    "logic-app",
    "function-app",
    "app-service",
    "key-vault",
    "openai",
    "synapse",
    "data-factory",
    "ai-hub",
    "ai-project",
    "ai-foundry",
    "ai-services",
    "ai-search",
    "front-door",
    "virtual-machine",
    "redis-cache",
    "redis-enterprise"
]

# Bicep Templates
TEMPLATE_MAP = {
    "storage-account": "templates/storage-account.bicep",
    "key-vault": "templates/azure-key-vaults.bicep",
    "openai": "templates/azure-openai.bicep",
    "ai-search": "templates/ai-search.bicep",
    "ai-foundry": "templates/ai-foundry.bicep",
    "cosmos-db": "templates/cosmos-db.bicep",
    "log-analytics": "templates/log-analytics.bicep",
    "uami": "templates/user-assigned-managed-identity.bicep",
    "nsp": "templates/nsp.bicep",
    "fabric-capacity": "templates/fabric-capacity.bicep",
}

# Operational Scripts
OP_SCRIPTS = {
    "permissions": "list-azure-permissions.ps1",
    "resources": "list-resources.ps1",
    "create-rg": "create-resourcegroup.ps1",
    "deploy-bicep": "deploy-bicep.ps1"
}

# --- AZURE HELPER FUNCTIONS ---

def _get_rg_location(resource_group: str) -> str:
    """Fetches location of the resource group."""
    try:
        res = run_command(["az", "group", "show", "-n", resource_group, "--query", "location", "-o", "tsv"])
        return res.strip()
    except:
        return "eastus"  # Fallback

def _get_resource_id(resource_group: str, resource_type: str, parameters: Dict[str, str]) -> Optional[str]:
    """
    Attempts to find the Resource ID based on parameters provided during creation.
    We look for common naming parameter keys.
    """
    # Common parameter names for resource names in Bicep templates
    name_keys = [
        "name", "accountName", "keyVaultName", "serverName", "databaseName", "storageAccountName",
        "workspaceName", "searchServiceName", "serviceName", "vmName", "virtualMachineName",
        "siteName", "functionAppName", "appServiceName", "logicAppName", "workflowName",
        "factoryName", "cacheName", "frontDoorName", "clusterName"
    ]
    
    resource_name = None
    for key in name_keys:
        if key in parameters:
            resource_name = parameters[key]
            break
            
    if not resource_name:
        return None

    # Map internal types to Azure Resource Provider types for CLI lookup
    provider_map = {
        "storage-account": "Microsoft.Storage/storageAccounts",
        "key-vault": "Microsoft.KeyVault/vaults",
        "cosmos-db": "Microsoft.DocumentDB/databaseAccounts",
        "sql-db": "Microsoft.Sql/servers",
        "logic-app": "Microsoft.Logic/workflows",
        "function-app": "Microsoft.Web/sites",
        "app-service": "Microsoft.Web/sites",
        "synapse": "Microsoft.Synapse/workspaces",
        "data-factory": "Microsoft.DataFactory/factories",
        "ai-hub": "Microsoft.MachineLearningServices/workspaces",
        "ai-project": "Microsoft.MachineLearningServices/workspaces",
        "ai-foundry": "Microsoft.CognitiveServices/accounts",
        "ai-services": "Microsoft.CognitiveServices/accounts",
        "ai-search": "Microsoft.Search/searchServices",
        "front-door": "Microsoft.Network/frontDoors",
        "virtual-machine": "Microsoft.Compute/virtualMachines",
        "redis-cache": "Microsoft.Cache/redis",
        "redis-enterprise": "Microsoft.Cache/redisEnterprise"
    }
    
    provider = provider_map.get(resource_type)
    if not provider:
        return None

    try:
        cmd = [
            "az", "resource", "show", 
            "-g", resource_group, 
            "-n", resource_name, 
            "--resource-type", provider, 
            "--query", "id", "-o", "tsv"
        ]
        return run_command(cmd).strip()
    except:
        return None

def _format_deployment_details(resource_type: str, resource_group: str, parameters: Dict[str, str]) -> str:
    """Format deployment details in a user-friendly way based on resource type."""
    details = []
    details.append("═" * 70)
    details.append("✅ DEPLOYMENT SUCCESSFUL")
    details.append("═" * 70)
    details.append("")
    details.append("📦 Deployment Details:")
    details.append("")
    
    # Common details for all resources
    location = parameters.get("location", "N/A")
    
    if resource_type == "storage-account":
        storage_name = parameters.get("storageAccountName", "N/A")
        access_tier = parameters.get("accessTier", "N/A")
        hns_enabled = parameters.get("enableHierarchicalNamespace", "true")
        
        details.append(f"   Storage Account: {storage_name}")
        details.append(f"   Location: {location}")
        details.append(f"   Access Tier: {access_tier}")
        details.append(f"   ADLS Gen2: {'Enabled' if hns_enabled.lower() == 'true' else 'Disabled'}")
        details.append(f"   Blob Endpoint: https://{storage_name}.blob.core.windows.net/")
        details.append(f"   DFS Endpoint: https://{storage_name}.dfs.core.windows.net/")
    
    elif resource_type == "key-vault":
        vault_name = parameters.get("keyVaultName", "N/A")
        details.append(f"   Key Vault: {vault_name}")
        details.append(f"   Location: {location}")
        details.append(f"   Vault URI: https://{vault_name}.vault.azure.net/")
    
    elif resource_type == "cosmos-db":
        account_name = parameters.get("cosmosAccountName", "N/A")
        details.append(f"   Cosmos DB Account: {account_name}")
        details.append(f"   Location: {location}")
    
    elif resource_type == "openai":
        openai_name = parameters.get("openAIServiceName", "N/A")
        details.append(f"   Azure OpenAI: {openai_name}")
        details.append(f"   Location: {location}")
        details.append(f"   Endpoint: https://{openai_name}.openai.azure.com/")
    
    elif resource_type == "ai-search":
        search_name = parameters.get("searchServiceName", "N/A")
        sku = parameters.get("sku", "standard")
        details.append(f"   AI Search Service: {search_name}")
        details.append(f"   Location: {location}")
        details.append(f"   SKU: {sku}")
        details.append(f"   Endpoint: https://{search_name}.search.windows.net/")
    
    elif resource_type == "log-analytics":
        workspace_name = parameters.get("workspaceName", "N/A")
        details.append(f"   Log Analytics Workspace: {workspace_name}")
        details.append(f"   Location: {location}")
    
    else:
        # Generic fallback for other resources
        name_keys = ["name", "accountName", "serverName", "serviceName"]
        resource_name = None
        for key in name_keys:
            if key in parameters:
                resource_name = parameters[key]
                break
        
        if resource_name:
            details.append(f"   Resource Name: {resource_name}")
        details.append(f"   Resource Type: {resource_type}")
        details.append(f"   Location: {location}")
    
    details.append("")
    details.append("─" * 70)
    details.append("")
    
    return "\n".join(details)

def _parse_bicep_parameters(template_path: str) -> Dict[str, Tuple[bool, Optional[str]]]:
    params: Dict[str, Tuple[bool, Optional[str]]] = {}
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_strip = line.strip()
                if line_strip.startswith('param '):
                    m = re.match(r"param\s+(\w+)\s+[^=\n]+(?:=\s*(.+))?", line_strip)
                    if m:
                        name = m.group(1)
                        default_raw = m.group(2).strip() if m.group(2) else None
                        required = default_raw is None
                        params[name] = (required, default_raw)
    except Exception:
        pass
    return params

def _validate_bicep_parameters(resource_type: str, provided: Dict[str, str]) -> Tuple[bool, str, Dict[str, Tuple[bool, Optional[str]]]]:
    if resource_type not in TEMPLATE_MAP:
        return False, f"Unknown resource_type '{resource_type}'.", {}
    template_path = _get_template_path(TEMPLATE_MAP[resource_type])
    if not os.path.exists(template_path):
        return False, f"Template not found at {template_path}", {}
    params = _parse_bicep_parameters(template_path)
    missing = [p for p, (req, _) in params.items() if req and (p not in provided or provided[p] in (None, ""))]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}", params
    return True, "OK", params

def _deploy_bicep(resource_group: str, resource_type: str, parameters: Dict[str, str]) -> str:
    if resource_type not in TEMPLATE_MAP:
        return f"Unknown resource_type '{resource_type}'."
    template_path = _get_template_path(TEMPLATE_MAP[resource_type])
    if not os.path.exists(template_path):
        return f"Template not found: {template_path}"
    
    # Normalize case-sensitive parameters for storage accounts
    if resource_type == "storage-account" and "accessTier" in parameters:
        parameters["accessTier"] = parameters["accessTier"].lower().capitalize()
    
    # Build parameters string for PowerShell (semicolon-separated key=value pairs)
    param_string = ";".join([f"{k}={v}" for k, v in parameters.items()]) if parameters else ""
    
    # Call deploy-bicep.ps1 script
    script_name = OP_SCRIPTS["deploy-bicep"]
    script_path = _get_script_path(script_name)
    
    if not os.path.exists(script_path):
        return f"Error: Script '{script_name}' not found at {script_path}"
    
    script_params = {
        "ResourceGroup": resource_group,
        "TemplatePath": template_path
    }
    
    if param_string:
        script_params["Parameters"] = param_string
    
    deploy_result = _run_powershell_script(script_path, script_params)
    
    # Check if deployment was successful
    deployment_successful = (
        "Error" not in deploy_result and 
        "FAILED" not in deploy_result and
        "Failed" not in deploy_result and
        len(deploy_result.strip()) > 0
    )
    
    if deployment_successful:
        # Format deployment details
        output = [_format_deployment_details(resource_type, resource_group, parameters)]
        
        # Get resource ID for suggestions
        resource_id = _get_resource_id(resource_group, resource_type, parameters)
        
        # Check if NSP attachment is required
        if resource_type in NSP_MANDATORY_RESOURCES:
            output.append("\n" + "─" * 70)
            output.append("")
            output.append("⚠️  COMPLIANCE REQUIREMENT")
            output.append("═" * 70)
            output.append("")
            output.append("This resource requires NSP attachment to resolve:")
            output.append("   📋 [SFI-NS2.2.1] Secure PaaS Resources")
            output.append("")
            output.append("═" * 70)
            output.append("")
            output.append("🔒 Do you want to attach this resource to NSP?")
            output.append("")
            output.append("   Type 'yes: attach it to NSP' to proceed with NSP attachment")
            output.append("   Type 'no' to skip (not recommended - resource will not be compliant)")
            output.append("")
            output.append("If you choose 'yes', I will:")
            output.append("   1. ✓ Check for existing NSP in the resource group")
            output.append("   2. ✓ Create NSP if it doesn't exist")
            output.append("   3. ✓ Attach the resource to the NSP")
            output.append("")
        
        # Check if Log Analytics attachment is required
        if resource_type in LOG_ANALYTICS_MANDATORY_RESOURCES:
            output.append("\n" + "═" * 70)
            output.append("⚠️  COMPLIANCE REQUIREMENT")
            output.append("═" * 70)
            output.append("")
            output.append("This resource requires Log Analytics diagnostic settings to resolve:")
            output.append("   📋 [SFI-Monitoring] Resource Monitoring & Compliance")
            output.append("")
            output.append("═" * 70)
            output.append("")
            output.append("📊 Do you want to configure Log Analytics for this resource?")
            output.append("")
            output.append("   Type 'yes: attach it to Log Analytics' to proceed with Log Analytics configuration")
            output.append("   Type 'no' to skip (not recommended - resource will not have monitoring)")
            output.append("")
            output.append("If you choose 'yes', I will:")
            output.append("   1. ✓ Check for existing Log Analytics workspace in the resource group")
            output.append("   2. ✓ Create workspace if it doesn't exist")
            output.append("   3. ✓ Configure diagnostic settings for the resource")
            output.append("")
        
        return "\n".join(output)
    
    return deploy_result

# --- AZURE MCP TOOLS ---

@server.mcp.tool()
def azure_list_permissions(user_principal_name: str = None, force_refresh: bool = True) -> str:
    """
    Lists active Azure RBAC role assignments for resources and subscriptions.
    
    USE THIS TOOL when user asks to "list permissions" or "show permissions" without specifying the platform.
    This is the DEFAULT permission listing tool.
    
    Uses force_refresh=True by default to ensure recent role activations are captured.
    
    Args:
        user_principal_name: Optional user email. Defaults to current logged-in user.
        force_refresh: Whether to force refresh the role cache. Default is True.
    
    Returns:
        Table of Azure role assignments (Reader, Contributor, Owner, etc.)
    """
    script_name = OP_SCRIPTS["permissions"]
    script_path = _get_script_path(script_name)
    
    if not os.path.exists(script_path):
        return f"Error: Script '{script_name}' not found."

    params = {}
    if user_principal_name:
        params["UserPrincipalName"] = user_principal_name
    
    return _run_powershell_script(script_path, params)

@server.mcp.tool()
def azure_list_resources(resource_group_name: str = None) -> str:
    """
    Lists Azure resources (all resources or filtered by resource group).
    
    Args:
        resource_group_name: Optional resource group name to filter resources.
    
    Returns:
        Table of Azure resources with name, type, location, and resource group
    """
    script_name = OP_SCRIPTS["resources"]
    script_path = _get_script_path(script_name)
    if not os.path.exists(script_path):
        return f"Error: Script '{script_name}' not found."
    params = {}
    if resource_group_name:
        params["ResourceGroup"] = resource_group_name
    return _run_powershell_script(script_path, params)

@server.mcp.tool()
def azure_create_resource_group(resource_group_name: str, region: str, project_name: str) -> str:
    """Creates an Azure resource group with project tagging."""
    if not resource_group_name or not region or not project_name:
        return "Error: All parameters (resource_group_name, region, project_name) are required."
    
    script_name = OP_SCRIPTS["create-rg"]
    script_path = _get_script_path(script_name)
    if not os.path.exists(script_path):
        return f"Error: Script '{script_name}' not found."
    
    params = {
        "ResourceGroupName": resource_group_name,
        "Region": region,
        "ProjectName": project_name
    }
    return _run_powershell_script(script_path, params)

@server.mcp.tool()
def azure_check_nsp(resource_group: str) -> str:
    """
    Checks for Network Security Perimeters (NSP) in the specified resource group.
    Returns a list of NSPs found, or indicates if none exist.
    
    Args:
        resource_group: Resource group name to check
    
    Returns:
        JSON string with NSP information
    """
    if not resource_group or not resource_group.strip():
        return json.dumps({"error": "Resource group name is required"})
    
    ps_executable = "pwsh" if shutil.which("pwsh") else "powershell"
    check_nsp_script = _get_script_path("check-nsp.ps1")
    
    if not os.path.exists(check_nsp_script):
        return json.dumps({"error": "check-nsp.ps1 script not found"})
    
    result = run_command([
        ps_executable, "-File", check_nsp_script,
        "-ResourceGroupName", resource_group
    ])
    
    # Parse the result to extract NSP information
    found_match = re.search(r'NSP FOUND:\s*([a-zA-Z0-9_-]+)', result)
    if found_match:
        nsp_name = found_match.group(1).strip()
        return json.dumps({
            "count": 1,
            "nsps": [{"name": nsp_name}],
            "message": f"Found 1 NSP in '{resource_group}': {nsp_name}"
        })
    
    created_match = re.search(r"NSP '([a-zA-Z0-9_-]+)' created", result)
    if created_match:
        nsp_name = created_match.group(1).strip()
        return json.dumps({
            "count": 1,
            "nsps": [{"name": nsp_name}],
            "message": f"Created new NSP in '{resource_group}': {nsp_name}"
        })
    
    if "NSP NOT FOUND" in result or "not found" in result.lower():
        return json.dumps({
            "count": 0,
            "nsps": [],
            "message": f"No NSP found in resource group '{resource_group}'"
        })
    
    # Fallback: Try to extract NSP names from resource IDs
    nsp_names = []
    for line in result.split('\n'):
        if 'networkSecurityPerimeters' in line or '/networkSecurityPerimeters/' in line:
            name_match = re.search(r'/networkSecurityPerimeters/([a-zA-Z0-9_-]+)', line)
            if name_match and name_match.group(1) not in nsp_names:
                nsp_names.append(name_match.group(1))
    
    if nsp_names:
        return json.dumps({
            "count": len(nsp_names),
            "nsps": [{"name": name} for name in nsp_names],
            "message": f"Found {len(nsp_names)} NSP(s) in '{resource_group}'"
        })
    
    return json.dumps({
        "count": 0,
        "nsps": [],
        "raw_output": result,
        "message": "Could not parse NSP information from output"
    })

@server.mcp.tool()
def azure_attach_to_nsp(resource_group: str, nsp_name: str, resource_id: str) -> str:
    """
    Attaches a resource to a Network Security Perimeter (NSP).
    This resolves compliance requirement [SFI-NS2.2.1] Secure PaaS Resources.
    
    IMPORTANT: Only call this tool when:
    - User explicitly confirms the NSP attachment prompt (affirmative response), OR
    - User directly requests to attach a resource to NSP
    
    Do NOT call automatically after deployment without user interaction.
    
    Args:
        resource_group: Resource group name
        nsp_name: Name of the NSP to attach to
        resource_id: Full resource ID of the resource to attach
    
    Returns:
        Attachment result message
    """
    if not resource_group or not resource_group.strip():
        return "Error: Resource group name is required"
    
    if not nsp_name or not nsp_name.strip():
        return "Error: NSP name is required"
    
    if not resource_id or not resource_id.strip():
        return "Error: Resource ID is required"
    
    ps_executable = "pwsh" if shutil.which("pwsh") else "powershell"
    attach_nsp_script = _get_script_path("attach-nsp.ps1")
    
    if not os.path.exists(attach_nsp_script):
        return "Error: attach-nsp.ps1 script not found"
    
    result = run_command([
        ps_executable, "-File", attach_nsp_script,
        "-ResourceGroupName", resource_group,
        "-NSPName", nsp_name,
        "-ResourceId", resource_id
    ])
    
    if "Error" in result or "FAILED" in result:
        return f"Failed to attach resource to NSP '{nsp_name}':\n{result}"
    
    return f"✓ Resource attached to NSP '{nsp_name}' successfully\n\n[SFI-NS2.2.1] Compliance requirement resolved.\n\n{result}"

@server.mcp.tool()
def azure_check_log_analytics(resource_group: str) -> str:
    """
    Checks for Log Analytics Workspaces in the specified resource group.
    Returns a list of workspaces found, or indicates if none exist.
    If multiple workspaces exist, prompts user to select one.
    
    Args:
        resource_group: Resource group name to check
    
    Returns:
        JSON string with workspace information
    """
    if not resource_group or not resource_group.strip():
        return json.dumps({"error": "Resource group name is required"})
    
    ps_executable = "pwsh" if shutil.which("pwsh") else "powershell"
    check_law_script = _get_script_path("check-log-analytics.ps1")
    
    if not os.path.exists(check_law_script):
        return json.dumps({"error": "check-log-analytics.ps1 script not found"})
    
    result = run_command([
        ps_executable, "-File", check_law_script,
        "-ResourceGroupName", resource_group
    ])
    
    # Parse the result
    if "not found" in result.lower() or "does not exist" in result.lower():
        return json.dumps({
            "count": 0,
            "workspaces": [],
            "message": f"No Log Analytics Workspace found in resource group '{resource_group}'"
        })
    
    workspace_names = []
    if "MULTIPLE LOG ANALYTICS WORKSPACES FOUND" in result or "RequiresSelection" in result:
        for line in result.split('\n'):
            if '/workspaces/' in line.lower():
                match = re.search(r'/workspaces/([a-zA-Z0-9_-]+)', line)
                if match:
                    workspace_names.append(match.group(1))
    
    if workspace_names:
        return json.dumps({
            "count": len(workspace_names),
            "workspaces": [{"name": name} for name in workspace_names],
            "message": f"Found {len(workspace_names)} Log Analytics workspace(s)"
        })
    
    return json.dumps({
        "count": 0,
        "workspaces": [],
        "message": "Could not parse workspace information"
    })

@server.mcp.tool()
def azure_attach_diagnostic_settings(resource_group: str, workspace_id: str, resource_id: str) -> str:
    """
    Manually attaches diagnostic settings to a resource with a specified Log Analytics Workspace.
    Use this when multiple workspaces exist and user needs to select one.
    
    Args:
        resource_group: Resource group name
        workspace_id: Full resource ID of the Log Analytics Workspace
        resource_id: Full resource ID of the resource to attach diagnostic settings to
    """
    if not resource_group or not workspace_id or not resource_id:
        return "STOP: All parameters (resource_group, workspace_id, resource_id) are required."
    
    attach_law_script = _get_script_path("attach-log-analytics.ps1")
    if not os.path.exists(attach_law_script):
        return "Error: attach-log-analytics.ps1 not found."
    
    ps_executable = "pwsh" if shutil.which("pwsh") else "powershell"
    result = run_command([
        ps_executable, "-File", attach_law_script,
        "-ResourceGroupName", resource_group,
        "-WorkspaceId", workspace_id,
        "-ResourceId", resource_id
    ])
    
    return result

@server.mcp.tool()
def azure_get_bicep_requirements(resource_type: str) -> str:
    """(Bicep Path) Returns required/optional params for a Bicep template."""
    if resource_type not in TEMPLATE_MAP:
        return f"Unknown resource type. Supported:\n" + "\n".join([f"  - {t}" for t in TEMPLATE_MAP.keys()])
    
    template_path = _get_template_path(TEMPLATE_MAP[resource_type])
    if not os.path.exists(template_path):
        return f"Template file not found: {template_path}"
    
    params = _parse_bicep_parameters(template_path)
    req = [f"  {k}" for k, (r, _) in params.items() if r]
    opt = [f"  {k} (default: {d})" for k, (r, d) in params.items() if not r and d]
    
    msg = [f"Resource: {resource_type}"]
    if req:
        msg.append("\nRequired parameters:")
        msg.extend(req)
    if opt:
        msg.append("\nOptional parameters:")
        msg.extend(opt)
    
    return "\n".join(msg)

@server.mcp.tool()
def azure_create_resource(resource_type: str, resource_group: str, parameters: str = None) -> str:
    """
    Interactive Azure resource creation.
    
    Workflow:
    1. Validates resource type
    2. Requests missing required parameters from user
    3. Deploys resource using Bicep template
    
    Args:
        resource_type: Type of resource to create (storage-account, key-vault, openai, ai-search, ai-foundry, cosmos-db, sql-db, log-analytics, fabric-capacity)
        resource_group: Azure resource group name
        parameters: JSON string of resource-specific parameters (will prompt for missing required params)
    
    Returns:
        Deployment status
    """
    if not resource_type or not resource_type.strip():
        return "STOP: Resource type is required. Valid types: " + ", ".join(TEMPLATE_MAP.keys())
    
    if not resource_group or not resource_group.strip():
        return "STOP: Resource group name is required."
    
    parsed_params = {}
    if parameters:
        try:
            parsed_params = json.loads(parameters)
        except:
            return f"Error: Invalid JSON in parameters: {parameters}"
    
    # Validate parameters
    valid, msg, bicep_params = _validate_bicep_parameters(resource_type, parsed_params)
    
    if not valid:
        missing_list = msg.split(": ")[-1].split(", ")
        prompt = [f"Please provide the following parameters for '{resource_type}':"]
        prompt.extend([f"  - {p}" for p in missing_list])
        return "\n".join(prompt)
    
    # Get resource group location and add to parameters
    if "location" not in parsed_params:
        parsed_params["location"] = _get_rg_location(resource_group)
    
    # Deploy
    return _deploy_bicep(resource_group, resource_type, parsed_params)

@server.mcp.tool()
def azure_deploy_bicep_resource(resource_group: str, resource_type: str, parameters: Dict[str, str]) -> str:
    """
    Internal deployment function - validates and deploys a resource.
    
    Warning: Users should call azure_create_resource() instead for interactive parameter collection.
    
    This function:
    1. Validates all parameters against Bicep template
    2. Deploys the resource
    """
    if not resource_group or not resource_type or not parameters:
        return "Error: resource_group, resource_type, and parameters are all required."
    
    valid, msg, _ = _validate_bicep_parameters(resource_type, parameters)
    if not valid:
        return f"Validation failed: {msg}"
    
    if "location" not in parameters:
        parameters["location"] = _get_rg_location(resource_group)
    
    return _deploy_bicep(resource_group, resource_type, parameters)

