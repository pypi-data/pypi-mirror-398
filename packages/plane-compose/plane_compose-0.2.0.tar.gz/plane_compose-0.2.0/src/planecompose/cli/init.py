"""Initialize command - creates a new Plane project structure."""
import typer
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from planecompose.utils.project import create_gitignore

console = Console()


def init(
    path: Path = typer.Argument(Path("."), help="Path to initialize"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace slug"),
    project_key: str = typer.Option(None, "--project", "-p", help="Project identifier/key"),
):
    """
    Initialize a new Plane project structure.
    
    Creates plane.yaml, schema files, and work directory.
    Project will be created in Plane when you run 'plane schema push'.
    """
    project_path = path.resolve()
    
    # Check if already initialized
    if (project_path / "plane.yaml").exists():
        if not Confirm.ask("[yellow]plane.yaml exists. Overwrite?[/yellow]"):
            raise typer.Exit(1)
    
    # Get workspace and project info
    if not workspace:
        console.print("\n[cyan]Enter your Plane workspace slug[/cyan]")
        console.print("[dim]Find this in your Plane URL: plane.so/{workspace}[/dim]")
        workspace = Prompt.ask("Workspace")
    
    if not project_key:
        console.print("\n[cyan]Enter a project identifier[/cyan]")
        console.print("[dim]Use a short key like 'MYPROJ' or 'API'[/dim]")
        console.print("[dim]The project will be created when you run 'plane schema push'[/dim]")
        project_key = Prompt.ask("Project identifier")
    
    console.print(f"\n[bold]Initializing Plane project in {project_path}[/bold]\n")
    
    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "schema").mkdir(exist_ok=True)
    (project_path / "work").mkdir(exist_ok=True)
    (project_path / ".plane").mkdir(exist_ok=True)
    
    # Generate project name from directory
    project_name = project_path.name.replace("-", " ").replace("_", " ").title()
    
    # Create plane.yaml
    plane_yaml_content = f"""# Plane CLI Configuration
workspace: {workspace}
project:
  key: {project_key}  # Short identifier (e.g., "MYPROJ")
  # uuid: <will-be-added-automatically>  # Project UUID from Plane
  name: {project_name}

defaults:
  type: task
  workflow: standard
"""
    (project_path / "plane.yaml").write_text(plane_yaml_content)
    console.print("  [green]✓[/green] Created plane.yaml")
    
    # Create schema/types.yaml
    types_yaml = """# Work Item Type Definitions
task:
  description: A single unit of work
  workflow: standard
  fields:
    - name: title
      type: string
      required: true
    - name: priority
      type: enum
      options: [none, low, medium, high, urgent]

bug:
  description: A defect requiring fix
  workflow: standard
  fields:
    - name: title
      type: string
      required: true
    - name: severity
      type: enum
      options: [cosmetic, minor, major, critical]
      required: true
"""
    (project_path / "schema" / "types.yaml").write_text(types_yaml)
    console.print("  [green]✓[/green] Created schema/types.yaml")
    
    # Create schema/workflows.yaml
    workflows_yaml = """# Workflow Definitions
standard:
  states:
    - name: backlog
      group: unstarted
      color: "#858585"
    - name: todo
      group: unstarted
      color: "#3b82f6"
    - name: in_progress
      group: started
      color: "#f59e0b"
    - name: in_review
      group: started
      color: "#8b5cf6"
    - name: done
      group: completed
      color: "#22c55e"
    - name: cancelled
      group: cancelled
      color: "#ef4444"
  initial: backlog
  terminal: [done, cancelled]
"""
    (project_path / "schema" / "workflows.yaml").write_text(workflows_yaml)
    console.print("  [green]✓[/green] Created schema/workflows.yaml")
    
    # Create schema/labels.yaml
    labels_yaml = """# Label Definitions
groups:
  area:
    color: "#3b82f6"
    labels:
      - name: frontend
      - name: backend
      - name: infrastructure
  
  type:
    color: "#8b5cf6"
    labels:
      - name: feature
      - name: bug
      - name: tech-debt
"""
    (project_path / "schema" / "labels.yaml").write_text(labels_yaml)
    console.print("  [green]✓[/green] Created schema/labels.yaml")
    
    # Create work/inbox.yaml
    inbox_yaml = """# Add work items here, then run 'plane push' to create them in Plane
# Items will be created as work items in your project

# Example:
# - title: Implement user authentication
#   type: task
#   priority: high
#   labels: [backend, feature]
#   state: todo
#   description: Add OAuth2 authentication

[]
"""
    (project_path / "work" / "inbox.yaml").write_text(inbox_yaml)
    console.print("  [green]✓[/green] Created work/inbox.yaml")
    
    # Create .plane/state.json
    state_json = """{
  "last_sync": null,
  "types": {},
  "states": {},
  "labels": {},
  "work_items": {}
}"""
    (project_path / ".plane" / "state.json").write_text(state_json)
    console.print("  [green]✓[/green] Created .plane/state.json")
    
    # Create .gitignore
    create_gitignore(project_path)
    
    # Show next steps
    console.print("\n[bold green]✓ Project initialized successfully![/bold green]\n")
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. [cyan]plane auth login[/cyan] - Authenticate (if not already done)")
    console.print("  2. [cyan]plane schema push[/cyan] - Create project and push schema")
    console.print("  3. Edit [cyan]work/inbox.yaml[/cyan] - Add work items")
    console.print("  4. [cyan]plane push[/cyan] - Push work items to Plane")
    console.print("\n[dim]Tip: Customize schema files before pushing![/dim]")
