"""
Azure DevOps Tools
Contains all Azure DevOps-specific MCP tools and helper functions.
"""
import os
from typing import Optional

# Get shared server instance
try:
    from . import server
except ImportError:
    import server

# Use server.mcp directly for decorators
_get_script_path = server._get_script_path
_run_powershell_script = server._run_powershell_script

# --- ADO CONFIGURATION ---

# Pipeline template mappings
PIPELINE_TEMPLATE_MAP = {
    "codeql": "templates/codeql-pipeline.yml",
    "codeql-1es": "templates/codeql-1es-pipeline.yml",
    "codeql-prod": "templates/codeql-1es-pipeline.yml"
}

# Keywords for auto-detecting production pipelines
PIPELINE_TYPE_KEYWORDS = {
    "prod": ["1es", "prod", "production"],
    "non-prod": ["codeql", "standard", "dev", "test"]
}

# --- ADO HELPER FUNCTIONS ---

def _detect_pipeline_type(pipeline_name: str, pipeline_type: str) -> str:
    """
    Auto-detect pipeline type from pipeline name or explicit type.
    
    Rules:
    - If pipeline_name contains '1ES', 'prod', or 'production' → production (1ES)
    - Otherwise → standard non-production pipeline
    
    Args:
        pipeline_name: Name of the pipeline to create
        pipeline_type: Explicit type override (optional)
    
    Returns:
        Detected pipeline type: 'codeql', 'codeql-1es', or 'codeql-prod'
    """
    # Use explicit type if provided
    if pipeline_type and pipeline_type.strip():
        return pipeline_type.strip().lower()
    
    # Auto-detect from pipeline name
    name_lower = pipeline_name.lower() if pipeline_name else ""
    
    for keyword in PIPELINE_TYPE_KEYWORDS["prod"]:
        if keyword in name_lower:
            return "codeql-1es"  # Production template
    
    return "codeql"  # Default to non-production

def _get_pipeline_template(pipeline_type: str) -> str:
    """
    Get the template path for a given pipeline type.
    
    Args:
        pipeline_type: Type of pipeline (codeql, codeql-1es, codeql-prod)
    
    Returns:
        Template file path or default codeql template
    """
    return PIPELINE_TEMPLATE_MAP.get(pipeline_type, PIPELINE_TEMPLATE_MAP["codeql"])

# --- ADO MCP TOOLS ---

@server.mcp.tool()
def ado_create_project(organization: str = None, project_name: str = None, repo_name: str = None, description: str = None) -> str:
    """
    Creates an Azure DevOps project using AZ CLI via the PS1 script and sets the initial repo name.

    Behavior: Relies on the PS1 script output entirely (no extra verification).
    Required: organization (URL or org name), project_name, repo_name; description optional.
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (existing org URL where you're admin, e.g., https://dev.azure.com/<org>)")
    if not project_name or not project_name.strip():
        missing.append("project_name (name to keep/create)")
    if not repo_name or not repo_name.strip():
        missing.append("repo_name (initial repo name)")
    if missing:
        return (
            "ADO Project Creation\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            "\n\nOnly required inputs: organization, project_name, repo_name."
        )

    project_script = _get_script_path("create-devops-project.ps1")
    if not os.path.exists(project_script):
        return "Error: create-devops-project.ps1 not found"

    proj_params = {
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name
    }
    if description:
        proj_params["Description"] = description

    try:
        proj_out = _run_powershell_script(project_script, proj_params)
        return proj_out.strip()
    except Exception as e:
        return f"✗ Project/Repo operation crashed: {e}"

@server.mcp.tool()
def ado_create_repo(organization: str = None, project_name: str = None, repo_name: str = None) -> str:
    """
    Creates a new Azure DevOps Git repository via the PS1 script.

    Behavior: Relies on the PS1 script output entirely (no extra verification).
    Required: organization (URL or org name), project_name, repo_name.
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (existing org URL where you're project admin)")
    if not project_name or not project_name.strip():
        missing.append("project_name (existing project)")
    if not repo_name or not repo_name.strip():
        missing.append("repo_name (new repo name to keep/create)")
    if missing:
        return (
            "ADO Repo Creation\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            "\n\nOnly required inputs: organization, project_name, repo_name."
        )

    repo_script = _get_script_path("create-devops-repo.ps1")
    if not os.path.exists(repo_script):
        return "Error: create-devops-repo.ps1 not found"

    params = {
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name
    }

    try:
        out = _run_powershell_script(repo_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Repository operation crashed: {e}"

@server.mcp.tool()
def ado_list_projects(organization: str = None) -> str:
    """
    Lists all Azure DevOps projects in an organization.

    Behavior: Returns list of all projects with their details.
    Required: organization (URL or org name).
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    if not organization or not organization.strip():
        return (
            "ADO List Projects\n\n"
            "Please provide:\n"
            "  - organization (org URL to list projects from)\n\n"
            "Only required input: organization."
        )

    list_projects_script = _get_script_path("list-devops-projects.ps1")
    if not os.path.exists(list_projects_script):
        return "Error: list-devops-projects.ps1 not found"

    params = {
        "Organization": organization
    }

    try:
        out = _run_powershell_script(list_projects_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ List projects operation crashed: {e}"

@server.mcp.tool()
def ado_list_repos(organization: str = None, project_name: str = None) -> str:
    """
    Lists all Azure DevOps repositories in a project.

    Behavior: Returns list of all repos with their details.
    Required: organization (URL or org name), project_name.
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (org URL)")
    if not project_name or not project_name.strip():
        missing.append("project_name (project to list repos from)")
    if missing:
        return (
            "ADO List Repositories\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            "\n\nOnly required inputs: organization, project_name."
        )

    list_repos_script = _get_script_path("list-devops-repos.ps1")
    if not os.path.exists(list_repos_script):
        return "Error: list-devops-repos.ps1 not found"

    params = {
        "Organization": organization,
        "ProjectName": project_name
    }

    try:
        out = _run_powershell_script(list_repos_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ List repos operation crashed: {e}"

@server.mcp.tool()
def ado_create_branch(organization: str = None, project_name: str = None, 
                        repo_name: str = None, branch_name: str = None, 
                        base_branch: str = None) -> str:
    """
    Creates a new branch in an Azure DevOps repository from a base branch.

    Behavior: Creates branch from specified base branch (defaults to 'main').
    Branch name can be simple (e.g., 'dev') or folder-based (e.g., 'feature/myfeature').
    Required: organization, project_name, repo_name, branch_name, base_branch (defaults to 'main').
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (org URL)")
    if not project_name or not project_name.strip():
        missing.append("project_name (existing project)")
    if not repo_name or not repo_name.strip():
        missing.append("repo_name (existing repo)")
    if not branch_name or not branch_name.strip():
        missing.append("branch_name (new branch name, e.g., 'dev' or 'feature/myfeature')")
    if not base_branch or not base_branch.strip():
        missing.append("base_branch (branch to create from, usually 'main')")
    if missing:
        return (
            "ADO Create Branch\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            "\n\nOnly required inputs: organization, project_name, repo_name, branch_name, base_branch."
        )

    branch_script = _get_script_path("create-devops-branch.ps1")
    if not os.path.exists(branch_script):
        return "Error: create-devops-branch.ps1 not found"

    params = {
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name,
        "BranchName": branch_name,
        "BaseBranch": base_branch
    }

    try:
        out = _run_powershell_script(branch_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Branch creation operation crashed: {e}"

@server.mcp.tool()
def ado_deploy_pipeline_yaml(organization: str = None, project_name: str = None, 
                        repo_name: str = None, pipeline_type: str = None,
                        branch: str = None, folder_path: str = None) -> str:
    """
    Deploys a pipeline YAML template from agent/templates to an Azure DevOps repository.
    
    Template Auto-Selection:
    - Available types: codeql (non-prod), codeql-1es (prod), codeql-prod (prod)
    - System auto-detects based on keywords: '1ES', 'prod', 'production'
    - More pipeline types can be added to PIPELINE_TEMPLATE_MAP
    
    Workflow:
    1. Auto-selects template based on pipeline_type or keywords
    2. Clones the repo at specified branch
    3. Copies template to specified folder path
    4. Commits and pushes to repository
    
    Args:
        organization: Azure DevOps organization URL
        project_name: Existing project name
        repo_name: Existing repository name
        pipeline_type: Pipeline type ('codeql' for non-prod, 'codeql-1es' or 'codeql-prod' for production)
        branch: Branch to deploy to (defaults to 'main')
        folder_path: Folder in repo to deploy YAML (defaults to 'pipelines')
    
    Returns:
        Deployment status and YAML location
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (org URL)")
    if not project_name or not project_name.strip():
        missing.append("project_name (existing project)")
    if not repo_name or not repo_name.strip():
        missing.append("repo_name (existing repo)")
    if not pipeline_type or not pipeline_type.strip():
        missing.append(f"pipeline_type (available: {', '.join(PIPELINE_TEMPLATE_MAP.keys())})")
    if not branch or not branch.strip():
        missing.append("branch (branch to deploy to, usually 'main')")
    if not folder_path or not folder_path.strip():
        missing.append("folder_path (folder in repo, e.g., 'pipelines')")
    
    if missing:
        return (
            "Deploy Pipeline YAML\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            f"\n\nAvailable pipeline types:\n" +
            "\n".join([f"  - {k}: {v}" for k, v in PIPELINE_TEMPLATE_MAP.items()])
        )

    # Auto-detect and get template
    detected_type = _detect_pipeline_type(pipeline_type, pipeline_type)
    template_basename = os.path.basename(PIPELINE_TEMPLATE_MAP.get(detected_type, PIPELINE_TEMPLATE_MAP["codeql"]))
    
    deploy_script = _get_script_path("deploy-pipeline-yaml.ps1")
    if not os.path.exists(deploy_script):
        return "Error: deploy-pipeline-yaml.ps1 not found"

    params = {
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name,
        "TemplateName": template_basename.replace(".yml", ""),
        "Branch": branch,
        "FolderPath": folder_path
    }

    try:
        out = _run_powershell_script(deploy_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Deploy YAML operation crashed: {e}"

@server.mcp.tool()
def ado_create_pipeline(organization: str = None, project_name: str = None,
                          repo_name: str = None, pipeline_name: str = None,
                          branch: str = None, pipeline_type: str = None) -> str:
    """
    Creates an Azure DevOps pipeline from YAML file in repository.
    
    Template Auto-Selection:
    - Detects pipeline type from pipeline_name or pipeline_type parameter
    - Keywords: '1ES', 'prod', 'production' → selects production (1ES) pipeline
    - Otherwise → selects standard non-production pipeline
    - Auto-constructs yaml_path as: pipelines/{detected_template}.yml
    
    Available Pipeline Types:
    - codeql: Standard CodeQL pipeline (non-production)
    - codeql-1es: 1ES pipeline template (production, requires pool params)
    - More types can be added to PIPELINE_TEMPLATE_MAP
    
    Workflow:
    1. Auto-detects pipeline type from pipeline_name keywords
    2. Constructs yaml_path automatically
    3. Checks if YAML exists in repository
    4. Creates pipeline referencing the YAML
    
    Args:
        organization: Azure DevOps organization URL
        project_name: Existing project name
        repo_name: Existing repository name
        pipeline_name: Name for pipeline (keywords '1ES'/'prod' trigger production template)
        branch: Branch containing YAML (defaults to 'main')
        pipeline_type: Optional explicit type override (codeql, codeql-1es)
    
    Returns:
        Pipeline creation status and URL
    """
    # Normalize organization to URL if just the org name is provided
    if organization and not organization.strip().lower().startswith("http"):
        organization = f"https://dev.azure.com/{organization.strip()}"

    # Auto-detect pipeline type if not explicitly provided
    if pipeline_name and not pipeline_type:
        pipeline_type = _detect_pipeline_type(pipeline_name, "")
    elif not pipeline_type:
        pipeline_type = "codeql"  # default

    missing = []
    if not organization or not organization.strip():
        missing.append("organization (org URL)")
    if not project_name or not project_name.strip():
        missing.append("project_name (existing project)")
    if not repo_name or not repo_name.strip():
        missing.append("repo_name (existing repo)")
    if not pipeline_name or not pipeline_name.strip():
        missing.append("pipeline_name (include '1ES' or 'prod' for production pipelines)")
    if not branch or not branch.strip():
        missing.append("branch (branch with YAML, usually 'main')")
    
    if missing:
        # Provide intelligent suggestion based on detected type
        suggestion = f"\n\nDetected pipeline type: {pipeline_type}"
        if "1es" in pipeline_type or "prod" in pipeline_type:
            suggestion += "\nThis is a PRODUCTION pipeline (1ES template with pool parameters required)"
        else:
            suggestion += "\nThis is a NON-PRODUCTION pipeline (standard template)"
        
        return (
            "Create Azure DevOps Pipeline\n\n"
            "Please provide:\n"
            + "\n".join([f"  - {m}" for m in missing]) +
            suggestion +
            f"\n\nAvailable types: {', '.join(PIPELINE_TEMPLATE_MAP.keys())}"
        )

    # Auto-construct yaml_path based on detected pipeline type
    template_basename = os.path.basename(PIPELINE_TEMPLATE_MAP.get(pipeline_type, PIPELINE_TEMPLATE_MAP["codeql"]))
    yaml_path = f"pipelines/{template_basename}"

    pipeline_script = _get_script_path("create-devops-pipeline.ps1")
    if not os.path.exists(pipeline_script):
        return "Error: create-devops-pipeline.ps1 not found"

    params = {
        "Organization": organization,
        "ProjectName": project_name,
        "RepoName": repo_name,
        "PipelineName": pipeline_name,
        "Branch": branch,
        "YamlPath": yaml_path
    }

    try:
        out = _run_powershell_script(pipeline_script, params)
        return out.strip()
    except Exception as e:
        return f"✗ Create pipeline operation crashed: {e}"

