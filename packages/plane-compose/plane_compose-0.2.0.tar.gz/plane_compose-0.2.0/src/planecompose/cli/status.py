"""Status command - show project sync status."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from planecompose.config.context import load_project_context
from planecompose.parser.work_yaml import parse_work_items

console = Console()


def status():
    """
    Show project sync status.
    
    Displays information about the current project, schema sync status,
    and pending work items.
    """
    try:
        ctx = load_project_context()
        
        # Project info
        console.print()
        uuid_info = f" ({ctx.config.project_uuid[:8]}...)" if ctx.config.project_uuid else " [dim](not synced yet)[/dim]"
        project_info = f"""[bold]Workspace:[/bold] {ctx.config.workspace}
[bold]Project:[/bold] {ctx.config.project_name or 'N/A'}
[bold]Project Key:[/bold] {ctx.config.project_key}{uuid_info}
[bold]Root:[/bold] {ctx.root_path}"""
        
        console.print(Panel(project_info, title="[cyan]Project Info[/cyan]", border_style="cyan"))
        console.print()
        
        # Schema status
        schema_table = Table(title="Schema Status", show_header=True)
        schema_table.add_column("Type", style="cyan")
        schema_table.add_column("Local", justify="right")
        schema_table.add_column("Synced", justify="right")
        schema_table.add_column("Status", justify="center")
        
        types_synced = len(ctx.state.types)
        states_synced = len(ctx.state.states)
        labels_synced = len(ctx.state.labels)
        
        types_total = len(ctx.types)
        states_total = len(ctx.states)
        labels_total = len(ctx.labels)
        
        schema_table.add_row(
            "Types",
            str(types_total),
            str(types_synced),
            "[green]✓[/green]" if types_synced == types_total else "[yellow]pending[/yellow]"
        )
        schema_table.add_row(
            "States",
            str(states_total),
            str(states_synced),
            "[green]✓[/green]" if states_synced == states_total else "[yellow]pending[/yellow]"
        )
        schema_table.add_row(
            "Labels",
            str(labels_total),
            str(labels_synced),
            "[green]✓[/green]" if labels_synced == labels_total else "[yellow]pending[/yellow]"
        )
        
        console.print(schema_table)
        console.print()
        
        # Work items status
        work_items = list(parse_work_items(ctx.work_path))
        
        work_table = Table(title="Work Items Status")
        work_table.add_column("Status", style="cyan")
        work_table.add_column("Count", justify="right")
        
        work_table.add_row("Pending (in inbox.yaml)", str(len(work_items)))
        work_table.add_row("Synced to Plane", str(len(ctx.state.work_items)))
        
        console.print(work_table)
        console.print()
        
        # Last sync info
        if ctx.state.last_sync:
            console.print(f"[dim]Last sync: {ctx.state.last_sync}[/dim]")
        else:
            console.print("[dim]Never synced[/dim]")
        console.print()
        
        # Suggestions
        has_pending_schema = (
            types_synced < types_total or
            states_synced < states_total or
            labels_synced < labels_total
        )
        
        if has_pending_schema or types_synced == 0:
            console.print("[bold]Next steps:[/bold]")
            if has_pending_schema or types_synced == 0:
                console.print("  • Run [cyan]plane schema push[/cyan] to sync schema")
            if work_items:
                console.print(f"  • Run [cyan]plane push[/cyan] to create {len(work_items)} work items")
            console.print()
        elif work_items:
            console.print("[bold]Next step:[/bold]")
            console.print(f"  • Run [cyan]plane push[/cyan] to create {len(work_items)} work items")
            console.print()
        else:
            console.print("[green]✓ Everything is up to date![/green]")
            console.print("\nAdd work items to [cyan]work/inbox.yaml[/cyan] to get started")
            console.print()
        
    except FileNotFoundError as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        console.print("\nRun [cyan]plane init[/cyan] to initialize a project")
        console.print()
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        console.print()
        raise typer.Exit(1)
