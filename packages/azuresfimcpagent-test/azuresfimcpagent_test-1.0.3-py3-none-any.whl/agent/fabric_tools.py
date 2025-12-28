"""
Microsoft Fabric Tools
Contains all Fabric-specific MCP tools and helper functions.
"""
import os

# Get shared server instance
try:
    from . import server
except ImportError:
    import server

# Use server.mcp directly for decorators
_get_script_path = server._get_script_path
_run_powershell_script = server._run_powershell_script

# --- FABRIC MCP TOOLS ---

@server.mcp.tool()
def fabric_list_permissions(user_principal_name: str = None) -> str:
    """
    Lists Fabric workspace permissions for the current user.
    Shows workspace name, role, and access level.
    
    DO NOT USE THIS TOOL unless user explicitly asks for "Fabric permissions" or "Fabric workspace permissions".
    For general "list permissions" requests, use azure_list_permissions() instead.
    
    Args:
        user_principal_name: Optional user email. Defaults to current logged-in user.
    
    Returns:
        List of Fabric workspaces with permission levels
    """
    fabric_script = _get_script_path("list-fabric-permissions.ps1")
    
    if not os.path.exists(fabric_script):
        return "Error: list-fabric-permissions.ps1 not found"

    params = {}
    if user_principal_name:
        params["UserPrincipalName"] = user_principal_name
    
    return _run_powershell_script(fabric_script, params)

@server.mcp.tool()
def fabric_create_workspace(capacity_id: str = None, workspace_name: str = None, 
                           description: str = "") -> str:
    """
    Creates a Microsoft Fabric workspace in a capacity.
    
    Workflow:
    1. Validates capacity ID and workspace name
    2. Creates workspace using Fabric REST API
    3. Associates workspace with specified capacity
    
    Args:
        capacity_id: Full resource ID of the Fabric capacity (e.g., /subscriptions/.../resourceGroups/.../providers/Microsoft.Fabric/capacities/...)
        workspace_name: Name for the new workspace
        description: Optional description for the workspace
    
    Returns:
        Workspace creation status with workspace ID and details
    """
    missing = []
    if not capacity_id:
        missing.append("capacity_id (full resource ID)")
    if not workspace_name:
        missing.append("workspace_name")
    
    if missing:
        return "Missing required parameters:\n" + "\n".join([f"  - {m}" for m in missing])
    
    workspace_script = _get_script_path("create-fabric-workspace.ps1")
    if not os.path.exists(workspace_script):
        return "Error: create-fabric-workspace.ps1 not found"
    
    params = {
        "CapacityId": capacity_id,
        "WorkspaceName": workspace_name,
        "Description": description
    }
    
    try:
        out = _run_powershell_script(workspace_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Create workspace operation failed: {e}"

@server.mcp.tool()
def fabric_attach_workspace_to_git(workspace_id: str = None, organization: str = None,
                                   project_name: str = None, repo_name: str = None,
                                   branch_name: str = None, directory_name: str = "/") -> str:
    """
    Attaches a Microsoft Fabric workspace to an Azure DevOps Git repository.
    
    Workflow:
    1. Validates workspace ID and Git connection details
    2. Connects workspace to specified Azure DevOps repository
    3. Enables Git integration for workspace items
    
    Args:
        workspace_id: Fabric workspace ID (GUID)
        organization: Azure DevOps organization URL or name
        project_name: Azure DevOps project name
        repo_name: Azure DevOps repository name
        branch_name: Git branch name (e.g., 'main')
        directory_name: Directory path in repository (defaults to '/')
    
    Returns:
        Git connection status with workspace and repository details
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not workspace_id:
        missing.append("workspace_id (Fabric workspace GUID)")
    if not organization:
        missing.append("organization (Azure DevOps org URL)")
    if not project_name:
        missing.append("project_name (Azure DevOps project)")
    if not repo_name:
        missing.append("repo_name (Azure DevOps repository)")
    if not branch_name:
        missing.append("branch_name (Git branch, e.g., 'main')")
    
    if missing:
        return "Missing required parameters:\n" + "\n".join([f"  - {m}" for m in missing])
    
    git_script = _get_script_path("attach-fabric-git.ps1")
    if not os.path.exists(git_script):
        return "Error: attach-fabric-git.ps1 not found"
    
    params = {
        "WorkspaceId": workspace_id,
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name,
        "BranchName": branch_name,
        "DirectoryName": directory_name
    }
    
    try:
        out = _run_powershell_script(git_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Git integration operation failed: {e}"

