"""
Azure SFI Agent - MCP Server
Main server file containing shared helpers and general tools.
Module-specific tools are organized in: azure_tools.py, ado_tools.py, fabric_tools.py
"""
from mcp.server.fastmcp import FastMCP
import subprocess
import os
import re
from typing import Optional

# Initialize the server (shared across all modules)
mcp = FastMCP("azure-agent")

# --- INSTRUCTIONS LOADING ---
AGENT_INSTRUCTIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AGENT_INSTRUCTIONS.md")

def load_agent_instructions() -> str:
    """Load the AGENT_INSTRUCTIONS.md file content if present."""
    if os.path.exists(AGENT_INSTRUCTIONS_FILE):
        try:
            with open(AGENT_INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Failed to read instructions: {e}"
    return "Instructions file not found."

def get_action_menu() -> str:
    return (
        "Available actions:\n"
        "1. List all active permissions (Live Fetch)\n"
        "2. List all accessible resources (optional resource group)\n"
        "3. Create resource group (requires: name, region, project name)\n"
        "4. Create Azure resources with SFI compliance\n"
        "   Usage: azure_create_resource(resource_type, resource_group, **parameters)\n"
        "   \n"
        "   Interactive workflow:\n"
        "   - Call with resource_type (e.g., 'storage-account')\n"
        "   - Agent will ask for missing required parameters\n"
        "   - Provide parameters when prompted\n"
        "   - Agent deploys resource\n"
        "   \n"
        "   Supported types: storage-account | key-vault | openai | ai-search | ai-foundry | cosmos-db | log-analytics | fabric-capacity | uami | nsp\n"
        "\n"
        "5. NSP Management (Manual)\n"
        "   - azure_check_nsp(resource_group) - Check for existing NSP\n"
        "   - azure_create_resource('nsp', resource_group, parameters) - Create new NSP\n"
        "   - azure_attach_to_nsp(resource_group, nsp_name, resource_id) - Attach resource to NSP\n"
        "   Note: If multiple NSPs exist, you'll be prompted to choose one\n"
        "\n"
        "6. Log Analytics Management (Manual)\n"
        "   - azure_check_log_analytics(resource_group) - Check for existing workspace\n"
        "   - azure_create_resource('log-analytics', resource_group, parameters) - Create new workspace\n"
        "   - azure_attach_diagnostic_settings(resource_group, workspace_id, resource_id) - Attach diagnostic settings\n"
        "   Note: If multiple workspaces exist, you'll be prompted to choose one\n"
        "\n"
        "7. Azure DevOps Operations\n"
        "   - ado_create_project(organization, project_name, repo_name) - Create ADO project\n"
        "   - ado_create_repo(organization, project_name, repo_name) - Create repository\n"
        "   - ado_create_branch(organization, project_name, repo_name, branch_name, base_branch) - Create branch\n"
        "   - ado_deploy_pipeline_yaml(...) - Deploy pipeline YAML to repo\n"
        "   - ado_create_pipeline(...) - Create pipeline from YAML\n"
        "\n"
        "8. Microsoft Fabric Operations\n"
        "   - fabric_create_workspace(capacity_id, workspace_name) - Create Fabric workspace\n"
        "   - fabric_attach_workspace_to_git(...) - Attach workspace to Azure DevOps Git\n"
        "   - fabric_list_permissions() - List Fabric workspace permissions"
    )

GREETING_PATTERN = re.compile(r"\b(hi|hello|hey|greetings|good (morning|afternoon|evening))\b", re.IGNORECASE)

def is_greeting(text: str) -> bool:
    return bool(GREETING_PATTERN.search(text))

def normalize(text: str) -> str:
    return text.lower().strip()

# --- SHARED HELPER FUNCTIONS ---
# These are used by all modules (Azure, ADO, Fabric)

def run_command(command: list, timeout: int = 120) -> str:
    """
    Generic command runner with timeout.
    Used by all modules for running Azure CLI, Git, and other commands.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds"
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e.stderr}"
    except Exception as e:
        return f"Error running command {' '.join(command)}: {str(e)}"

def _get_script_path(script_name: str) -> str:
    """Locates the script in the 'scripts' folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "scripts", script_name)

def _get_template_path(template_rel: str) -> str:
    """Locates the bicep/template file relative to server file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), template_rel)

def _run_powershell_script(script_path: str, params: dict = None) -> str:
    """
    Executes a PowerShell script with parameters.
    Used by all modules for executing .ps1 scripts.
    
    Args:
        script_path: Full path to the .ps1 script
        params: Dictionary of parameters to pass to the script
    
    Returns:
        Script output as string
    """
    import shutil
    
    ps_executable = "pwsh" if shutil.which("pwsh") else "powershell"
    cmd = [ps_executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
    
    if params:
        for key, value in params.items():
            cmd.extend([f"-{key}", str(value)])
    
    return run_command(cmd, timeout=180)

# --- INTENT PARSING HELPERS ---

def parse_intent(user_input: str) -> str:
    """Parses user input to determine intent."""
    txt = normalize(user_input)
    if is_greeting(txt) or "menu" in txt:
        return "greeting" if is_greeting(txt) else "menu"
    if any(k in txt for k in ["permission", "list role", "show role"]):
        return "permissions"
    if any(k in txt for k in ["list resource", "show resource", "resource list"]):
        return "resources"
    if "create" in txt and ("resource group" in txt or "rg" in txt):
        return "create-rg"
    if "create" in txt or "deploy" in txt:
        return "create"
    return "unknown"

def extract_resource_group(user_input: str) -> Optional[str]:
    """Extracts resource group name from user input."""
    match = re.search(r"(?:resource[-\s]?group|rg)[:\s]+([a-zA-Z0-9_-]+)", user_input, re.IGNORECASE)
    return match.group(1) if match else None

# --- GENERAL MCP TOOLS ---

@mcp.tool()
def show_agent_instructions() -> str:
    """Shows the agent instructions from AGENT_INSTRUCTIONS.md file."""
    return load_agent_instructions()

@mcp.tool()
def agent_dispatch(user_input: str) -> str:
    """High-level dispatcher for conversational commands."""
    intent = parse_intent(user_input)
    if intent in ("greeting", "menu"): return get_action_menu()
    if intent == "permissions": 
        # Import here to avoid circular dependency
        try:
            from .azure_tools import azure_list_permissions
        except ImportError:
            import azure_tools
            azure_list_permissions = azure_tools.azure_list_permissions
        return azure_list_permissions(force_refresh=True)
    if intent == "resources":
        try:
            from .azure_tools import azure_list_resources
        except ImportError:
            import azure_tools
            azure_list_resources = azure_tools.azure_list_resources
        rg = extract_resource_group(user_input)
        return azure_list_resources(rg) if rg else azure_list_resources()
    if intent == "create-rg":
        return (
            "Resource Group creation flow:\n\n"
            "Please provide:\n"
            "1. Resource Group Name\n"
            "2. Region (e.g., eastus, westus2, westeurope)\n"
            "3. Project Name (for tagging)\n\n"
            "Then call: azure_create_resource_group(resource_group_name, region, project_name)"
        )
    if intent == "create":
        return (
            "Azure Resource Creation (Interactive Mode)\n\n"
            "To create a resource, use: azure_create_resource(resource_type, ...)\n\n"
            "Example: azure_create_resource('storage-account')\n"
            "The agent will then ask you for required parameters interactively.\n\n"
            "Supported resource types:\n"
            "  - storage-account (ADLS Gen2 enabled by default)\n"
            "  - key-vault\n"
            "  - openai\n"
            "  - ai-search\n"
            "  - ai-foundry\n"
            "  - cosmos-db\n"
            "  - fabric-capacity\n"
            "  - nsp\n"
            "  - uami\n"
            "  - log-analytics\n\n"
            "Manual Compliance Tools:\n"
            "  NSP Management:\n"
            "    - azure_check_nsp() - Check for NSP (handles multiple NSPs)\n"
            "    - azure_create_resource('nsp', ...) - Create NSP if doesn't exist\n"
            "    - azure_attach_to_nsp() - Attach resource to NSP\n"
            "  Log Analytics Management:\n"
            "    - azure_check_log_analytics() - Check for workspace (handles multiple)\n"
            "    - azure_create_resource('log-analytics', ...) - Create workspace if doesn't exist\n"
            "    - azure_attach_diagnostic_settings() - Configure diagnostic settings\n\n"
            "Tip: You can provide all parameters at once if you know them:\n"
            "   azure_create_resource('storage-account', resource_group='my-rg', \n"
            "                        storageAccountName='mystg123', location='eastus', accessTier='Hot')"
        )
    return "Unrecognized command. " + get_action_menu()

# --- IMPORT TOOL MODULES AT MODULE LEVEL ---
# Must happen after helper functions are defined but at module load time
try:
    from . import azure_tools, ado_tools, fabric_tools
except ImportError:
    import azure_tools
    import ado_tools
    import fabric_tools

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
