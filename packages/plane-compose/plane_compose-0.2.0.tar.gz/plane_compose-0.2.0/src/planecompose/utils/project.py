"""Project management utilities.

All API calls go through PlaneBackend - no direct SDK usage here.
"""
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()


def update_plane_yaml_with_uuid(project_path: Path, project_key: str, project_uuid: str) -> None:
    """Add UUID to plane.yaml without replacing the key."""
    plane_yaml_path = project_path / "plane.yaml"
    
    with open(plane_yaml_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Add uuid field, keep key as-is
    config_data['project']['uuid'] = project_uuid
    
    with open(plane_yaml_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"\n[dim]Updated plane.yaml with project UUID[/dim]")


async def ensure_project_exists(workspace: str, project_key: str, project_uuid: str | None, project_name: str, api_key: str, api_url: str, auto_create: bool = True) -> str:
    """
    Ensure project exists in Plane.
    
    All API calls go through PlaneBackend (no direct SDK usage).
    
    Args:
        workspace: Workspace slug
        project_key: Short identifier (e.g., "MYPROJ")
        project_uuid: Optional UUID if already known
        project_name: Project display name
        api_key: Plane API key
        api_url: Plane API URL
        auto_create: Whether to create project if it doesn't exist
    
    Returns: project UUID
    
    Raises:
        Exception: If project doesn't exist and can't be created
    """
    from planecompose.backend.plane import PlaneBackend
    
    # Use backend for all API calls (rate limiting is automatic)
    backend = PlaneBackend.create_client(api_url, api_key)
    
    # If we already have the UUID, try to verify it exists
    if project_uuid:
        try:
            project = await backend.retrieve_project(workspace, project_uuid)
            console.print(f"[green]✓[/green] Found project: {project.name}")
            return project_uuid
        except Exception:
            # UUID is stale/invalid - fall back to key lookup
            console.print(f"[dim]UUID in plane.yaml is stale, looking up by key instead...[/dim]")
    
    # Look up project by key
    try:
        projects = await backend.list_projects(workspace)
        existing = next((p for p in projects if p.identifier == project_key.upper()), None)
        
        if existing:
            console.print(f"[green]✓[/green] Found project: {existing.name} ({project_key.upper()})")
            return str(existing.id)
        
        # Project doesn't exist
        if not auto_create:
            _show_project_not_found_error(workspace, project_key, projects)
            raise Exception(f"Project '{project_key}' not found in workspace '{workspace}'")
        
        # Create new project
        console.print(f"\n[cyan]Project '{project_key.upper()}' not found. Creating...[/cyan]")
        
        new_project = await backend.create_project(
            workspace=workspace,
            name=project_name or project_key.upper(),
            identifier=project_key.upper(),
        )
        
        console.print(f"[green]✓[/green] Created project: {new_project.name}")
        console.print(f"[dim]  Identifier: {project_key.upper()}[/dim]")
        console.print(f"[dim]  UUID: {new_project.id}[/dim]")
        return str(new_project.id)
        
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e):
            console.print(f"\n[red]✗ Permission Denied[/red]")
            console.print(f"You don't have permission to create projects in workspace '{workspace}'")
            console.print(f"\n[yellow]Solutions:[/yellow]")
            console.print(f"  • Use a workspace where you have admin/member access")
            console.print(f"  • Ask workspace admin to create the project first")
            console.print(f"  • Use a different API key with proper permissions")
            raise
        raise


def _show_project_not_found_error(workspace: str, project_key: str, available_projects: list):
    """Show helpful error when project key doesn't exist."""
    console.print(f"\n[red]✗ Project Not Found[/red]\n")
    
    error_msg = f"""Project with identifier '[cyan]{project_key.upper()}[/cyan]' doesn't exist in workspace '[cyan]{workspace}[/cyan]'.

[yellow]Available projects in this workspace:[/yellow]"""
    
    if available_projects:
        for p in available_projects:
            error_msg += f"\n  • {p.name} ([cyan]{p.identifier}[/cyan])"
    else:
        error_msg += "\n  [dim](no projects found)[/dim]"
    
    error_msg += f"""

[yellow]Solutions:[/yellow]
  1. Fix the 'key' in plane.yaml to match an existing project
  2. Or run [cyan]plane schema push[/cyan] to create the project automatically"""
    
    console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))


def create_gitignore(project_path: Path) -> None:
    """Create .gitignore file if it doesn't exist."""
    gitignore_path = project_path / ".gitignore"
    
    if gitignore_path.exists():
        # Just append .plane/ if not already there
        content = gitignore_path.read_text()
        if ".plane/" not in content:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Plane CLI sync state\n.plane/\n")
    else:
        gitignore_content = """# Plane CLI sync state
.plane/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
"""
        gitignore_path.write_text(gitignore_content)
        console.print("  [green]✓[/green] Created .gitignore")

