"""Push command - push work items to Plane.

PERFORMANCE OPTIMIZATIONS:
- Uses cached type/state/label lookups (O(1) instead of O(n) API calls)
- Pre-loads all caches in parallel at start
- Concurrent batch processing for multiple items
"""
import asyncio
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from planecompose.config.context import load_project_context
from planecompose.backend.plane import PlaneBackend
from planecompose.parser.work_yaml import parse_work_items, WorkItemWithMeta
from planecompose.utils.work_items import (
    get_tracking_key,
    calculate_content_hash,
    make_work_item_state,
)

# Batch size for concurrent operations (respect rate limits)
BATCH_SIZE = 5

console = Console()


def push(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be pushed without making changes"),
    force: bool = typer.Option(False, "--force", "-f", help="Push without confirmation"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Only push schema (not work items)"),
    work_only: bool = typer.Option(False, "--work-only", help="Only push work items (not schema)"),
):
    """
    Push schema and work items to Plane.
    
    By default, pushes both schema and work items.
    Use --work-only to skip schema (faster if schema unchanged).
    Use --schema-only to push only schema.
    
    Reads work items from work/inbox.yaml and creates them in Plane.
    """
    asyncio.run(_push(dry_run, force, schema_only, work_only))


async def _push(dry_run: bool, force: bool, schema_only: bool, work_only: bool):
    """Async implementation of push."""
    import time
    schema_time = 0
    
    try:
        # Push schema first (unless --work-only)
        if not work_only:
            schema_start = time.time()
            console.print("\n[bold cyan]Step 1: Pushing schema...[/bold cyan]")
            from planecompose.cli.schema import _push_schema
            await _push_schema(dry_run, force)
            schema_time = time.time() - schema_start
            
            if schema_only:
                # Schema-only mode, we're done
                return
            
            console.print("\n[bold cyan]Step 2: Pushing work items...[/bold cyan]")
        
        # Load project context
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading project...", total=None)
            
            try:
                ctx = load_project_context()
            except FileNotFoundError as e:
                console.print(f"\n[red]✗ Error:[/red] {e}")
                console.print("\nRun [cyan]plane init[/cyan] first to initialize a project")
                raise typer.Exit(1)
            
            progress.update(task, description="Connecting to Plane...")
            
            # Ensure project exists
            from planecompose.utils.project import ensure_project_exists, update_plane_yaml_with_uuid
            try:
                project_uuid = await ensure_project_exists(
                    workspace=ctx.config.workspace,
                    project_key=ctx.config.project_key,
                    project_uuid=ctx.config.project_uuid,
                    project_name=ctx.config.project_name,
                    api_key=ctx.api_key,
                    api_url=ctx.config.api_url,
                    auto_create=False,  # Don't auto-create during push
                )
                
                # Update UUID only if it's not set
                if not ctx.config.project_uuid:
                    update_plane_yaml_with_uuid(ctx.root_path, ctx.config.project_key, project_uuid)
                    ctx.config.project_uuid = project_uuid
                else:
                    # Use the project_uuid from the lookup for API calls
                    ctx.config.project_uuid = project_uuid
                
            except Exception as e:
                console.print()
                raise typer.Exit(1)
            
            backend = PlaneBackend()
            await backend.connect(ctx.config, ctx.api_key)
            
            progress.update(task, description="Loading work items...")
            all_items = list(parse_work_items(ctx.work_path, ctx.root_path))
            
            # Filter: only push new items or modified items
            items_to_push = []
            items_to_update = []
            
            for item_meta in all_items:
                item = item_meta.item
                tracking_key = get_tracking_key(item, item_meta.source_file, item_meta.index)
                
                # Check if item exists in state
                if tracking_key in ctx.state.work_items:
                    item_state = ctx.state.work_items[tracking_key]
                    current_hash = calculate_content_hash(item)
                    
                    # Check if content changed
                    if current_hash != item_state.content_hash:
                        items_to_update.append((item_meta, item_state.remote_id))
                    # else: already synced and unchanged, skip
                else:
                    # New item
                    items_to_push.append(item_meta)
        
        if not items_to_push and not items_to_update:
            console.print("\n[green]✓ All work items are already synced![/green]")
            
            if not all_items:
                console.print(f"\nAdd work items to [cyan]{ctx.work_path / 'inbox.yaml'}[/cyan]")
                console.print("\nExample:")
                console.print("  - title: Implement user authentication")
                console.print("    type: task")
                console.print("    priority: high")
                console.print("    labels: [backend, feature]\n")
            else:
                console.print(f"\n[dim]{len(all_items)} items already in Plane[/dim]")
            
            await backend.disconnect()
            return
        
        # Display push plan
        console.print("\n[bold]Work Items Push Plan[/bold]\n")
        
        if items_to_push:
            table = Table(title=f"{len(items_to_push)} Work Items to Create")
            table.add_column("Title", style="bold")
            table.add_column("Type", style="cyan")
            table.add_column("Priority", style="yellow")
            table.add_column("Labels", style="dim")
            
            for item_meta in items_to_push:
                item = item_meta.item
                labels_str = ", ".join(item.labels) if item.labels else ""
                table.add_row(
                    item.title[:50] + ("..." if len(item.title) > 50 else ""),
                    item.type,
                    item.priority or "none",
                    labels_str
                )
            
            console.print(table)
            console.print()
        
        if items_to_update:
            table = Table(title=f"{len(items_to_update)} Work Items to Update")
            table.add_column("Title", style="bold")
            table.add_column("Type", style="cyan")
            table.add_column("Status", style="yellow")
            
            for item_meta, _ in items_to_update:
                item = item_meta.item
                table.add_row(
                    item.title[:50] + ("..." if len(item.title) > 50 else ""),
                    item.type,
                    "modified"
                )
            
            console.print(table)
            console.print()
        
        if dry_run:
            console.print("[yellow]Dry run mode - no changes applied[/yellow]")
            await backend.disconnect()
            return
        
        # Confirm before pushing
        if not force:
            from rich.prompt import Confirm
            total_changes = len(items_to_push) + len(items_to_update)
            action = f"Create {len(items_to_push)}" if items_to_push else ""
            if items_to_push and items_to_update:
                action += f", update {len(items_to_update)}"
            elif items_to_update:
                action = f"Update {len(items_to_update)}"
            
            if not Confirm.ask(f"{action} work items in Plane?"):
                console.print("[yellow]Cancelled[/yellow]")
                await backend.disconnect()
                raise typer.Exit(0)
        
        # Push work items (create + update) with progress bar
        import time
        import logging
        
        start_time = time.time()
        
        # Suppress INFO logs during progress to keep output clean
        original_level = logging.getLogger("planecompose").level
        logging.getLogger("planecompose").setLevel(logging.WARNING)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            total_items = len(items_to_push) + len(items_to_update)
            task = progress.add_task(f"Syncing {total_items} work items...", total=total_items)
            
            created_count = 0
            updated_count = 0
            failed_count = 0
            
            # PERFORMANCE: Pre-load caches before creating items
            # This ensures all lookups are O(1) during creation
            await backend._ensure_caches_loaded()
            
            # Helper to create single item
            async def create_item(item_meta: WorkItemWithMeta):
                nonlocal created_count, failed_count
                item = item_meta.item
                try:
                    remote_id = await backend.create_work_item(item)
                    tracking_key = get_tracking_key(item, item_meta.source_file, item_meta.index)
                    ctx.state.work_items[tracking_key] = make_work_item_state(
                        remote_id, item, item_meta.source_file, item_meta.index
                    )
                    created_count += 1
                    return True
                except Exception as e:
                    console.print(f"\n[red]✗ Failed to create:[/red] {item.title}")
                    console.print(f"[dim]  Error: {e}[/dim]")
                    failed_count += 1
                    return False
            
            # Helper to update single item
            async def update_item(item_meta: WorkItemWithMeta, remote_id: str):
                nonlocal updated_count, failed_count
                item = item_meta.item
                try:
                    await backend.update_work_item(remote_id, item)
                    tracking_key = get_tracking_key(item, item_meta.source_file, item_meta.index)
                    ctx.state.work_items[tracking_key] = make_work_item_state(
                        remote_id, item, item_meta.source_file, item_meta.index
                    )
                    updated_count += 1
                    return True
                except Exception as e:
                    console.print(f"\n[red]✗ Failed to update:[/red] {item.title}")
                    console.print(f"[dim]  Error: {e}[/dim]")
                    failed_count += 1
                    return False
            
            # Process creates in batches (rate limiter handles throttling)
            for i in range(0, len(items_to_push), BATCH_SIZE):
                batch = items_to_push[i:i + BATCH_SIZE]
                # Sequential within batch to respect rate limits
                for item_meta in batch:
                    await create_item(item_meta)
                    progress.advance(task)
            
            # Process updates in batches
            for i in range(0, len(items_to_update), BATCH_SIZE):
                batch = items_to_update[i:i + BATCH_SIZE]
                for item_meta, remote_id in batch:
                    await update_item(item_meta, remote_id)
                    progress.advance(task)
            
            progress.update(task, description="Saving state...")
            ctx.save_state()
        
        # Restore log level
        logging.getLogger("planecompose").setLevel(original_level)
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{int(elapsed//60)}m {int(elapsed%60)}s"
        
        # Summary
        console.print()
        if schema_time > 0 and not work_only:
            schema_str = f"{schema_time:.1f}s" if schema_time < 60 else f"{int(schema_time//60)}m {int(schema_time%60)}s"
            console.print(f"[green]✓[/green] Pushed schema [dim]({schema_str})[/dim]")
        if created_count > 0:
            console.print(f"[green]✓[/green] Created {created_count} work items")
        if updated_count > 0:
            console.print(f"[green]✓[/green] Updated {updated_count} work items")
        if failed_count > 0:
            console.print(f"[red]✗[/red] {failed_count} items failed")
        
        total_time = schema_time + elapsed
        total_str = f"{total_time:.1f}s" if total_time < 60 else f"{int(total_time//60)}m {int(total_time%60)}s"
        console.print(f"[dim]  Total time: {total_str}[/dim]")
        console.print()
        
        await backend.disconnect()
        
    except Exception as e:
        _handle_error(e)
        raise typer.Exit(1)


def _handle_error(e: Exception):
    """Handle common errors with helpful messages."""
    error_msg = str(e)
    
    if "403" in error_msg or "Forbidden" in error_msg:
        console.print(f"\n[red]✗ Permission Denied (403)[/red]")
        console.print("\nYour API key doesn't have permission to create work items.")
        console.print("\n[yellow]Solutions:[/yellow]")
        console.print("  • Verify you're a member of the workspace")
        console.print("  • Check with your workspace administrator")
    
    elif "404" in error_msg or "Not Found" in error_msg:
        console.print(f"\n[red]✗ Not Found (404)[/red]")
        console.print("\nThe project doesn't exist.")
        console.print("\n[yellow]Try:[/yellow]")
        console.print("  • Run [cyan]plane schema push[/cyan] to create the project first")
    
    else:
        console.print(f"\n[red]✗ Error:[/red] {e}")
