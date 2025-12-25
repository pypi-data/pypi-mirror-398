"""Schema management commands."""
import asyncio
import sys
import typer
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from planecompose.config.context import load_project_context, ProjectContext
from planecompose.backend.plane import PlaneBackend
from planecompose.utils.project import ensure_project_exists, update_plane_yaml_with_uuid
from planecompose.utils.logger import get_logger

logger = get_logger()

app = typer.Typer(help="Schema management commands")
console = Console()


# ============================================================================
# Helper Functions - DRY Principle
# ============================================================================

def _require_plane_yaml() -> ProjectContext:
    """
    Load project context, failing fast if plane.yaml is not found.
    
    This validates that we're in a Plane project before starting any
    expensive operations (like network calls or spinners).
    
    IMPORTANT: Only checks the CURRENT directory for plane.yaml.
    Does NOT search parent directories.
    
    Returns:
        ProjectContext: The loaded project context
        
    Raises:
        typer.Exit(1): If plane.yaml is not found in current directory
    """
    try:
        # Use the SAME logic as load_project_context() to avoid inconsistency
        return load_project_context()
    except FileNotFoundError as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        console.print("\n[dim]plane.yaml must exist in the current directory[/dim]")
        console.print(f"[dim]Current directory: {Path.cwd()}[/dim]")
        console.print("\n[yellow]To fix this:[/yellow]")
        console.print("  • [cyan]cd[/cyan] to a directory with plane.yaml")
        console.print("  • Run [cyan]plane init[/cyan] to initialize a new project")
        console.print("  • Run [cyan]plane clone <project-uuid>[/cyan] to clone an existing project\n")
        raise typer.Exit(1)


async def _load_project_with_backend(ctx: ProjectContext, auto_create: bool = False) -> tuple[ProjectContext, PlaneBackend]:
    """
    Connect to Plane backend using existing project context.
    
    This is a common pattern used by all schema commands.
    
    Args:
        ctx: Project context (already loaded by _require_plane_yaml)
        auto_create: Whether to auto-create the project if it doesn't exist (default: False)
    
    Returns:
        tuple[ProjectContext, PlaneBackend]: Connected context and backend
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Ensure project exists
        task = progress.add_task("🔍 Checking project...", total=None)
        project_uuid = await ensure_project_exists(
            workspace=ctx.config.workspace,
            project_key=ctx.config.project_key,
            project_uuid=ctx.config.project_uuid,
            project_name=ctx.config.project_name,
            api_key=ctx.api_key,
            api_url=ctx.config.api_url,
            auto_create=auto_create,
        )
        ctx.config.project_uuid = project_uuid
        
        # Connect to backend
        progress.update(task, description="🔌 Connecting to Plane...")
        backend = PlaneBackend()
        await backend.connect(ctx.config, ctx.api_key)
    
    return ctx, backend


def _display_create_table(title: str, items: list, row_func) -> None:
    """Display a table of items to be created."""
    if not items:
        return
    
    table = Table(title=f"{title} to Create")
    table.add_column("Name")
    table.add_column("Details", style="dim")
    
    for item in items:
        row_data = row_func(item)
        table.add_row(*row_data)
    
    console.print(table)
    console.print()


# ============================================================================
# CLI Commands - User-facing Interface
# ============================================================================

@app.command()
def validate():
    """Validate local schema files without connecting to Plane."""
    try:
        # Load project context (uses consistent error handling)
        ctx = _require_plane_yaml()
        
        console.print("\n[green]✓ Schema is valid![/green]\n")
        console.print(f"  [cyan]Types:[/cyan] {len(ctx.types)}")
        console.print(f"  [cyan]States:[/cyan] {len(ctx.states)}")
        console.print(f"  [cyan]Labels:[/cyan] {len(ctx.labels)}")
        console.print()
    except Exception as e:
        # Specific errors (like FileNotFoundError) are handled by _require_plane_yaml
        # This catches schema validation errors
        if "Exit" not in str(type(e)):
            console.print(f"\n[red]✗ Validation error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def push(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be pushed without making changes"),
    force: bool = typer.Option(False, "--force", "-f", help="Push without confirmation"),
):
    """
    Push schema to Plane.
    
    Creates the project if it doesn't exist, then pushes types, states, and labels.
    """
    asyncio.run(_push_schema(dry_run, force))


# ============================================================================
# Async Implementations - Business Logic
# ============================================================================

async def _push_schema(dry_run: bool, force: bool):
    """Async implementation of schema push."""
    try:
        # Load project context (fail fast if plane.yaml not found)
        ctx = _require_plane_yaml()
        
        # Connect to Plane backend (auto-create project if it doesn't exist)
        ctx, backend = await _load_project_with_backend(ctx, auto_create=True)
        
        # Fetch remote schema to compare
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📥 Fetching remote schema...", total=None)
            remote_types = await backend.list_types()
            remote_states = await backend.list_states()
            remote_labels = await backend.list_labels()
        
        # Calculate what needs to be created (set difference)
        remote_type_names = {t.name for t in remote_types}
        remote_state_names = {s.name for s in remote_states}
        remote_label_names = {l.name for l in remote_labels}
        
        types_to_create = [t for t in ctx.types if t.name not in remote_type_names]
        states_to_create = [s for s in ctx.states if s.name not in remote_state_names]
        labels_to_create = [l for l in ctx.labels if l.name not in remote_label_names]
        
        # Display push plan
        console.print("\n[bold]Schema Push Plan[/bold]\n")
        
        _display_create_table("Work Item Types", types_to_create, lambda t: [t.name, t.description or ""])
        _display_create_table("States", states_to_create, lambda s: [s.name, s.group])
        _display_create_table("Labels", labels_to_create, lambda l: [l.name, l.color or ""])
        
        total = len(types_to_create) + len(states_to_create) + len(labels_to_create)
        
        if total == 0:
            console.print("[green]✓ Everything up to date![/green]")
            console.print("All schema items already exist in Plane.\n")
            await backend.disconnect()
            return
        
        console.print(f"[bold]Summary:[/bold] {total} items to create\n")
        
        if dry_run:
            console.print("[yellow]Dry run mode - no changes applied[/yellow]")
            await backend.disconnect()
            return
        
        # Confirm before pushing
        if not force:
            from rich.prompt import Confirm
            if not Confirm.ask("Apply these changes?"):
                console.print("[yellow]Cancelled[/yellow]")
                await backend.disconnect()
                raise typer.Exit(0)
        
        # Push changes with tracking
        created_states = 0
        created_labels = 0
        created_types = 0
        failed_states = []
        failed_labels = []
        failed_types = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Create states first (required by work items)
            if states_to_create:
                task = progress.add_task(f"Creating {len(states_to_create)} states...", total=len(states_to_create))
                for state in states_to_create:
                    try:
                        remote_id = await backend.create_state(state)
                        ctx.state.states[state.name] = remote_id
                        created_states += 1
                    except Exception as e:
                        failed_states.append((state.name, str(e)))
                        logger.error(f"Failed to create state '{state.name}': {e}")
                    progress.update(task, advance=1)
                progress.remove_task(task)
            
            # Create labels
            if labels_to_create:
                task = progress.add_task(f"Creating {len(labels_to_create)} labels...", total=len(labels_to_create))
                for label in labels_to_create:
                    try:
                        remote_id = await backend.create_label(label)
                        ctx.state.labels[label.name] = remote_id
                        created_labels += 1
                    except Exception as e:
                        failed_labels.append((label.name, str(e)))
                        logger.error(f"Failed to create label '{label.name}': {e}")
                    progress.update(task, advance=1)
                progress.remove_task(task)
            
            # Create types
            if types_to_create:
                task = progress.add_task(f"Creating {len(types_to_create)} types...", total=len(types_to_create))
                for type_def in types_to_create:
                    try:
                        remote_id = await backend.create_type(type_def)
                        ctx.state.types[type_def.name] = remote_id
                        created_types += 1
                    except Exception as e:
                        failed_types.append((type_def.name, str(e)))
                        logger.error(f"Failed to create type '{type_def.name}': {e}")
                    progress.update(task, advance=1)
                progress.remove_task(task)
            
            # Save state
            task = progress.add_task("Saving state...", total=None)
            ctx.save_state()
            progress.remove_task(task)
        
        # Display summary
        console.print()
        console.print("[bold]Schema Push Summary[/bold]\n")
        
        if created_states > 0:
            console.print(f"[green]✓[/green] Created {created_states} states")
        if created_labels > 0:
            console.print(f"[green]✓[/green] Created {created_labels} labels")
        if created_types > 0:
            console.print(f"[green]✓[/green] Created {created_types} types")
        
        if failed_states:
            console.print(f"\n[red]✗[/red] Failed to create {len(failed_states)} states:")
            for name, error in failed_states[:5]:  # Show first 5
                console.print(f"  • {name}: {error[:80]}")
            if len(failed_states) > 5:
                console.print(f"  ... and {len(failed_states) - 5} more")
        
        if failed_labels:
            console.print(f"\n[red]✗[/red] Failed to create {len(failed_labels)} labels:")
            for name, error in failed_labels[:5]:
                console.print(f"  • {name}: {error[:80]}")
            if len(failed_labels) > 5:
                console.print(f"  ... and {len(failed_labels) - 5} more")
        
        if failed_types:
            console.print(f"\n[red]✗[/red] Failed to create {len(failed_types)} types:")
            for name, error in failed_types[:5]:
                console.print(f"  • {name}: {error[:80]}")
            if len(failed_types) > 5:
                console.print(f"  ... and {len(failed_types) - 5} more")
        
        total_created = created_states + created_labels + created_types
        total_failed = len(failed_states) + len(failed_labels) + len(failed_types)
        
        if total_failed == 0:
            console.print(f"\n[bold green]✓ Schema push complete![/bold green]")
            console.print(f"Successfully created all {total_created} items\n")
        else:
            console.print(f"\n[yellow]⚠ Schema push completed with errors[/yellow]")
            console.print(f"Created: {total_created}, Failed: {total_failed}\n")
        
        await backend.disconnect()
        
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        if "--debug" in sys.argv or "-v" in sys.argv:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def pull(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite without confirmation"),
):
    """
    Pull schema from Plane.
    
    Downloads types, states, and labels from Plane and writes to schema/ directory.
    Overwrites existing schema files.
    """
    asyncio.run(_pull_schema(force))


async def _pull_schema(force: bool):
    """Async implementation of schema pull."""
    import yaml
    import time
    
    try:
        # Load project context (fail fast if plane.yaml not found)
        ctx = _require_plane_yaml()
        
        # Connect to Plane backend
        ctx, backend = await _load_project_with_backend(ctx)
        
        # Check if schema files exist (prompt for overwrite)
        schema_dir = ctx.root_path / "schema"
        has_existing = (
            (schema_dir / "types.yaml").exists() or
            (schema_dir / "workflows.yaml").exists() or
            (schema_dir / "labels.yaml").exists()
        )
        
        if has_existing and not force:
            from rich.prompt import Confirm
            if not Confirm.ask("\n[yellow]Schema files exist. Overwrite?[/yellow]"):
                console.print("[yellow]Cancelled[/yellow]")
                await backend.disconnect()
                raise typer.Exit(0)
        
        # Fetch schema from Plane
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📋 Fetching types...", total=None)
            remote_types = await backend.list_types()
            
            progress.update(task, description="🔄 Fetching states...")
            remote_states = await backend.list_states()
            
            progress.update(task, description="🏷️  Fetching labels...")
            remote_labels = await backend.list_labels()
            
            progress.update(task, description="💾 Writing schema files...")
            
            # Write schema to files
            schema_dir.mkdir(exist_ok=True)
            
            # Write types.yaml
            types_yaml = []
            for t in remote_types:
                type_data = {
                    'name': t.name,
                    'description': t.description or '',
                }
                # Add logo_props if available (don't convert to icon)
                if hasattr(t, 'logo_props') and t.logo_props:
                    type_data['logo_props'] = {
                        'in_use': t.logo_props.in_use,
                        'emoji': t.logo_props.emoji,
                        'icon': t.logo_props.icon,
                    }
                if hasattr(t, 'fields') and t.fields:
                    type_data['properties'] = []
                    for prop in t.fields:
                        prop_data = {
                            'name': prop.name,
                            'type': prop.type,
                            'required': prop.required,
                        }
                        if hasattr(prop, 'is_multi') and prop.is_multi is not None:
                            prop_data['is_multi'] = prop.is_multi
                        if hasattr(prop, 'relation_type') and prop.relation_type:
                            prop_data['relation_type'] = prop.relation_type
                        if hasattr(prop, 'options') and prop.options:
                            prop_data['options'] = [{'value': opt} for opt in prop.options]
                        type_data['properties'].append(prop_data)
                types_yaml.append(type_data)
            
            with open(schema_dir / "types.yaml", 'w') as f:
                yaml.dump(types_yaml, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            # Write workflows.yaml (states)
            workflows_yaml = {
                'standard': {
                    'states': [],
                    'initial': 'backlog',
                    'terminal': ['done', 'cancelled'],
                }
            }
            for state in remote_states:
                workflows_yaml['standard']['states'].append({
                    'name': state.name,
                    'group': state.group,
                    'color': state.color or '#808080',
                })
            
            with open(schema_dir / "workflows.yaml", 'w') as f:
                yaml.dump(workflows_yaml, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            # Write labels.yaml
            labels_yaml = {'groups': {}}
            for label in remote_labels:
                group_name = 'general'
                if labels_yaml['groups'].get(group_name) is None:
                    labels_yaml['groups'][group_name] = {
                        'color': label.color or '#808080',
                        'labels': []
                    }
                labels_yaml['groups'][group_name]['labels'].append({'name': label.name})
            
            with open(schema_dir / "labels.yaml", 'w') as f:
                yaml.dump(labels_yaml, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        elapsed = time.time() - start_time
        elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{int(elapsed//60)}m {int(elapsed%60)}s"
        
        console.print()
        console.print(f"[green]✓[/green] Pulled schema from Plane")
        console.print(f"  [cyan]Types:[/cyan] {len(remote_types)} → schema/types.yaml")
        console.print(f"  [cyan]States:[/cyan] {len(remote_states)} → schema/workflows.yaml")
        console.print(f"  [cyan]Labels:[/cyan] {len(remote_labels)} → schema/labels.yaml")
        console.print(f"[dim]  Completed in {elapsed_str}[/dim]")
        console.print()
        
        await backend.disconnect()
        
    except Exception as e:
        if "Exit" not in str(type(e)):
            console.print(f"\n[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be synced without making changes"),
    force: bool = typer.Option(False, "--force", "-f", help="Sync without confirmation"),
):
    """
    Declarative schema sync - make remote match local EXACTLY.
    
    This command:
    - Creates types/states/labels that exist in local but not remote
    - Updates types/states/labels that differ between local and remote
    - ⚠️  DELETES types/states/labels that exist in remote but not local
    
    WARNING: This is a DECLARATIVE operation. Use with caution!
    For additive-only sync (no deletions), use 'plane schema push' instead.
    
    NOTE: Delete operations are not yet supported by the Plane API.
    This command will show what WOULD be deleted but won't actually delete.
    """
    asyncio.run(_sync_schema(dry_run, force))


async def _sync_schema(dry_run: bool, force: bool):
    """Async implementation of declarative schema sync."""
    try:
        # Load project context (fail fast if plane.yaml not found)
        ctx = _require_plane_yaml()
        
        # Connect to Plane backend
        ctx, backend = await _load_project_with_backend(ctx)
        
        # Fetch remote schema to compare
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📥 Fetching remote schema...", total=None)
            remote_types = await backend.list_types()
            remote_states = await backend.list_states()
            remote_labels = await backend.list_labels()
        
        # Build maps for comparison
        local_type_map = {t.name: t for t in ctx.types}
        remote_type_map = {t.name: t for t in remote_types}
        
        local_state_map = {s.name: s for s in ctx.states}
        remote_state_map = {s.name: s for s in remote_states}
        
        local_label_map = {l.name: l for l in ctx.labels}
        remote_label_map = {l.name: l for l in remote_labels}
        
        # Calculate changes
        types_to_create = [t for t in ctx.types if t.name not in remote_type_map]
        types_to_update = [t for t in ctx.types if t.name in remote_type_map]
        types_to_delete = [t for t in remote_types if t.name not in local_type_map]
        
        states_to_create = [s for s in ctx.states if s.name not in remote_state_map]
        states_to_update = [s for s in ctx.states if s.name in remote_state_map]
        states_to_delete = [s for s in remote_states if s.name not in local_state_map]
        
        labels_to_create = [l for l in ctx.labels if l.name not in remote_label_map]
        labels_to_update = [l for l in ctx.labels if l.name in remote_label_map]
        labels_to_delete = [l for l in remote_labels if l.name not in local_label_map]
        
        # Display sync plan
        console.print("\n[bold]Declarative Schema Sync Plan[/bold]\n")
        
        has_changes = False
        
        if types_to_create or types_to_update:
            console.print("[bold cyan]Types:[/bold cyan]")
            if types_to_create:
                console.print(f"  [green]+[/green] Create: {', '.join(t.name for t in types_to_create)}")
                has_changes = True
            if types_to_update:
                console.print(f"  [yellow]~[/yellow] Update: {', '.join(t.name for t in types_to_update)}")
                has_changes = True
            console.print()
        
        if types_to_delete:
            console.print("[bold red]Types to DELETE:[/bold red]")
            console.print(f"  [red]✗[/red] Would delete: {', '.join(t.name for t in types_to_delete)}")
            console.print(f"  [yellow]⚠️  Delete API not yet supported - these will NOT be deleted[/yellow]")
            console.print()
        
        if states_to_create or states_to_update:
            console.print("[bold cyan]States:[/bold cyan]")
            if states_to_create:
                console.print(f"  [green]+[/green] Create: {', '.join(s.name for s in states_to_create)}")
                has_changes = True
            if states_to_update:
                console.print(f"  [yellow]~[/yellow] Update: {', '.join(s.name for s in states_to_update)}")
                has_changes = True
            console.print()
        
        if states_to_delete:
            console.print("[bold red]States to DELETE:[/bold red]")
            console.print(f"  [red]✗[/red] Would delete: {', '.join(s.name for s in states_to_delete)}")
            console.print(f"  [yellow]⚠️  Delete API not yet supported - these will NOT be deleted[/yellow]")
            console.print()
        
        if labels_to_create or labels_to_update:
            console.print("[bold cyan]Labels:[/bold cyan]")
            if labels_to_create:
                console.print(f"  [green]+[/green] Create: {', '.join(l.name for l in labels_to_create)}")
                has_changes = True
            if labels_to_update:
                console.print(f"  [yellow]~[/yellow] Update: {', '.join(l.name for l in labels_to_update)}")
                has_changes = True
            console.print()
        
        if labels_to_delete:
            console.print("[bold red]Labels to DELETE:[/bold red]")
            console.print(f"  [red]✗[/red] Would delete: {', '.join(l.name for l in labels_to_delete)}")
            console.print(f"  [yellow]⚠️  Delete API not yet supported - these will NOT be deleted[/yellow]")
            console.print()
        
        if not has_changes and not (types_to_delete or states_to_delete or labels_to_delete):
            console.print("[green]✓ Schema already in sync![/green]\n")
            await backend.disconnect()
            return
        
        if dry_run:
            console.print("[yellow]Dry run mode - no changes applied[/yellow]\n")
            await backend.disconnect()
            return
        
        # Confirm before syncing
        if not force and has_changes:
            from rich.prompt import Confirm
            total_changes = len(types_to_create) + len(types_to_update) + len(states_to_create) + len(states_to_update) + len(labels_to_create) + len(labels_to_update)
            
            if not Confirm.ask(f"Apply {total_changes} changes to remote schema?"):
                console.print("[yellow]Cancelled[/yellow]")
                await backend.disconnect()
                raise typer.Exit(0)
        
        # Apply changes (create/update only - no delete support yet)
        if has_changes:
            console.print("\n[bold]Applying schema changes...[/bold]\n")
            
            # Push types
            for type_def in types_to_create:
                try:
                    await backend.create_type(type_def)
                    console.print(f"  [green]✓[/green] Created type: {type_def.name}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed type {type_def.name}: {e}")
            
            # Update types
            for type_def in types_to_update:
                try:
                    # Get remote ID
                    remote_type = remote_type_map.get(type_def.name)
                    if remote_type and hasattr(remote_type, 'remote_id'):
                        await backend.update_type(remote_type.remote_id, type_def)
                        console.print(f"  [green]✓[/green] Updated type: {type_def.name}")
                    else:
                        console.print(f"  [yellow]~[/yellow] Skipped type {type_def.name} (no remote ID)")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed type {type_def.name}: {e}")
            
            # Push states
            for state_def in states_to_create:
                try:
                    await backend.create_state(state_def)
                    console.print(f"  [green]✓[/green] Created state: {state_def.name}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed state {state_def.name}: {e}")
            
            # Update states
            for state_def in states_to_update:
                try:
                    remote_state = remote_state_map.get(state_def.name)
                    if remote_state and hasattr(remote_state, 'remote_id'):
                        await backend.update_state(remote_state.remote_id, state_def)
                        console.print(f"  [green]✓[/green] Updated state: {state_def.name}")
                    else:
                        console.print(f"  [yellow]~[/yellow] Skipped state {state_def.name} (no remote ID)")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed state {state_def.name}: {e}")
            
            # Push labels
            for label_def in labels_to_create:
                try:
                    await backend.create_label(label_def)
                    console.print(f"  [green]✓[/green] Created label: {label_def.name}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed label {label_def.name}: {e}")
            
            # Update labels
            for label_def in labels_to_update:
                try:
                    remote_label = remote_label_map.get(label_def.name)
                    if remote_label and hasattr(remote_label, 'remote_id'):
                        await backend.update_label(remote_label.remote_id, label_def)
                        console.print(f"  [green]✓[/green] Updated label: {label_def.name}")
                    else:
                        console.print(f"  [yellow]~[/yellow] Skipped label {label_def.name} (no remote ID)")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed label {label_def.name}: {e}")
            
            console.print()
            console.print("[green]✓ Schema sync complete (create/update)[/green]")
            
            if types_to_delete or states_to_delete or labels_to_delete:
                console.print("[yellow]⚠️  Deletions skipped (API support pending)[/yellow]")
            console.print()
        
        await backend.disconnect()
        
    except Exception as e:
        if "Exit" not in str(type(e)):
            console.print(f"\n[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def diff():
    """
    Compare local schema with remote schema.
    
    Shows what would change if you pushed local schema or pulled remote schema.
    """
    asyncio.run(_diff_schema())


async def _diff_schema():
    """Async implementation of schema diff."""
    try:
        # Load project context (fail fast if plane.yaml not found)
        ctx = _require_plane_yaml()
        
        # Connect to Plane backend
        ctx, backend = await _load_project_with_backend(ctx)
        
        # Fetch remote schema to compare
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("📋 Fetching remote schema...", total=None)
            remote_types = await backend.list_types()
            remote_states = await backend.list_states()
            remote_labels = await backend.list_labels()
        
        # Compare schemas
        console.print("\n[bold]Schema Comparison: Local ↔ Remote[/bold]\n")
        
        # Compare types
        local_type_names = {t.name for t in ctx.types}
        remote_type_names = {t.name for t in remote_types}
        
        only_local = local_type_names - remote_type_names
        only_remote = remote_type_names - local_type_names
        in_both = local_type_names & remote_type_names
        
        if only_local or only_remote or in_both:
            console.print("[bold cyan]Types:[/bold cyan]")
            if only_local:
                console.print(f"  [green]+[/green] Only in local: {', '.join(sorted(only_local))}")
            if only_remote:
                console.print(f"  [red]-[/red] Only in remote: {', '.join(sorted(only_remote))}")
            if in_both:
                console.print(f"  [dim]=[/dim] In both: {len(in_both)} types")
            console.print()
        
        # Compare states
        local_state_names = {s.name for s in ctx.states}
        remote_state_names = {s.name for s in remote_states}
        
        only_local = local_state_names - remote_state_names
        only_remote = remote_state_names - local_state_names
        in_both = local_state_names & remote_state_names
        
        if only_local or only_remote or in_both:
            console.print("[bold cyan]States:[/bold cyan]")
            if only_local:
                console.print(f"  [green]+[/green] Only in local: {', '.join(sorted(only_local))}")
            if only_remote:
                console.print(f"  [red]-[/red] Only in remote: {', '.join(sorted(only_remote))}")
            if in_both:
                console.print(f"  [dim]=[/dim] In both: {len(in_both)} states")
            console.print()
        
        # Compare labels
        local_label_names = {l.name for l in ctx.labels}
        remote_label_names = {l.name for l in remote_labels}
        
        only_local = local_label_names - remote_label_names
        only_remote = remote_label_names - local_label_names
        in_both = local_label_names & remote_label_names
        
        if only_local or only_remote or in_both:
            console.print("[bold cyan]Labels:[/bold cyan]")
            if only_local:
                console.print(f"  [green]+[/green] Only in local: {', '.join(sorted(only_local))}")
            if only_remote:
                console.print(f"  [red]-[/red] Only in remote: {', '.join(sorted(only_remote))}")
            if in_both:
                console.print(f"  [dim]=[/dim] In both: {len(in_both)} labels")
            console.print()
        
        # Summary
        has_diff = any([
            local_type_names != remote_type_names,
            local_state_names != remote_state_names,
            local_label_names != remote_label_names,
        ])
        
        if not has_diff:
            console.print("[green]✓ Schemas are in sync![/green]\n")
        else:
            console.print("[yellow]Actions:[/yellow]")
            console.print("  [cyan]plane schema push[/cyan] - Push local changes to remote")
            console.print("  [cyan]plane schema pull[/cyan] - Pull remote changes to local")
            console.print()
        
        await backend.disconnect()
        
    except Exception as e:
        if "Exit" not in str(type(e)):
            console.print(f"\n[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)
