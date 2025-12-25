"""Pull command - fetch work items from Plane.

All API calls go through PlaneBackend - no direct SDK usage in CLI code.
"""
import asyncio
import typer
import yaml
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from planecompose.config.context import load_project_context
from planecompose.backend.plane import PlaneBackend

console = Console()


def pull(
    output: str = typer.Option(".plane/remote/items.yaml", "--output", "-o", help="Output file path"),
    merge: bool = typer.Option(False, "--merge", help="Merge with existing items in output file"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite without confirmation"),
    with_properties: bool = typer.Option(True, "--with-properties/--no-properties", help="Fetch custom property values (default: yes)"),
    work_only: bool = typer.Option(False, "--work-only", help="Pull only work items (skip schema)"),
):
    """
    Pull schema and work items from YOUR project (uses plane.yaml context).
    
    By default, pulls both schema and work items.
    Use --work-only to skip schema (faster).
    
    Fetches work items from your project and writes to .plane/remote/ by default.
    By default, fetches custom property values (use --no-properties to skip).
    
    For cloning someone else's project, use 'plane clone <uuid>' instead.
    """
    asyncio.run(_pull(output, merge, force, with_properties, work_only))


async def _pull(output_path: str, merge: bool, force: bool, with_properties: bool = True, work_only: bool = False):
    """Async implementation of pull."""
    import time
    
    start_time = time.time()
    schema_time = 0
    
    try:
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
            
            progress.update(task, description="📡 Connecting to Plane...")
            
            # Ensure project exists
            from planecompose.utils.project import ensure_project_exists
            try:
                project_uuid = await ensure_project_exists(
                    workspace=ctx.config.workspace,
                    project_key=ctx.config.project_key,
                    project_uuid=ctx.config.project_uuid,
                    project_name=ctx.config.project_name,
                    api_key=ctx.api_key,
                    api_url=ctx.config.api_url,
                    auto_create=False,
                )
                ctx.config.project_uuid = project_uuid
            except Exception as e:
                console.print()
                raise typer.Exit(1)
            
            backend = PlaneBackend()
            await backend.connect(ctx.config, ctx.api_key)
            
            # Pull schema first (unless --work-only)
            if not work_only:
                schema_start = time.time()
                progress.update(task, description="📋 Pulling schema...")
                
                # Fetch schema
                remote_types = await backend.list_types()
                remote_states = await backend.list_states()
                remote_labels = await backend.list_labels()
                
                # Write schema to files
                schema_dir = ctx.root_path / "schema"
                schema_dir.mkdir(exist_ok=True)
                
                # Write types.yaml
                types_yaml = []
                for t in remote_types:
                    type_data = {
                        'name': t.name,
                        'description': t.description,
                        'workflow': t.workflow or 'standard',
                    }
                    # Add logo_props if available
                    if t.logo_props:
                        lp = t.logo_props
                        if hasattr(lp, 'icon') and lp.icon:
                            type_data['icon'] = {
                                'name': lp.icon.get('name') if isinstance(lp.icon, dict) else getattr(lp.icon, 'name', None),
                                'color': lp.icon.get('background_color') if isinstance(lp.icon, dict) else getattr(lp.icon, 'background_color', None),
                            }
                        if hasattr(lp, 'emoji') and lp.emoji:
                            type_data['emoji'] = lp.emoji.get('value') if isinstance(lp.emoji, dict) else getattr(lp.emoji, 'value', None)
                    # Add fields (properties)
                    if t.fields:
                        type_data['properties'] = []
                        for prop in t.fields:
                            prop_type = prop.type.value if hasattr(prop.type, 'value') else str(prop.type)
                            prop_data = {
                                'name': prop.name,
                                'type': prop_type.lower(),
                                'required': prop.required,
                            }
                            if hasattr(prop, 'is_multi') and prop.is_multi is not None:
                                prop_data['is_multi'] = prop.is_multi
                            if hasattr(prop, 'relation_type') and prop.relation_type:
                                prop_data['relation_type'] = prop.relation_type
                            if hasattr(prop, 'options') and prop.options:
                                prop_data['options'] = list(prop.options)
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
                
                schema_time = time.time() - schema_start
            
            progress.update(task, description="📝 Fetching work items from Plane...")
            remote_items = await backend.list_work_items()
            
            # Fetch properties if requested (all via backend - rate limiting automatic)
            work_item_properties = {}
            raw_items_for_props = []  # For UUID lookup later
            
            if with_properties and remote_items:
                progress.update(task, description=f"⚙️  Fetching property definitions...")
                
                # Fetch types via backend (rate limiting automatic)
                types_sdk = await backend.list_types_raw()
                
                # Convert SDK objects to dicts for backend.build_property_maps()
                types_data = []
                for t in types_sdk:
                    type_dict = {
                        'id': str(t.id) if hasattr(t, 'id') else None,
                        'name': t.name if hasattr(t, 'name') else None,
                    }
                    types_data.append(type_dict)
                
                # Build property maps via backend
                property_maps = await backend.build_property_maps(types_data)
                
                if property_maps:
                    # Get raw items for property value fetching
                    raw_items_for_props = await backend.list_work_items_raw()
                    
                    # Estimate number of API calls
                    total_calls = sum(
                        len(property_maps.get(str(getattr(item, 'type_id', None)), {})) 
                        for item in raw_items_for_props if hasattr(item, 'type_id')
                    )
                    
                    if total_calls > 0:
                        est_time = f"~{total_calls/50:.0f}min" if total_calls > 50 else f"~{total_calls}s"
                        progress.update(task, description=f"⚙️  Fetching {total_calls} property values ({est_time})...")
                    
                    # Fetch property values via backend (rate limiting automatic)
                    work_item_properties = await backend.fetch_work_item_properties_batch(
                        raw_items_for_props, property_maps
                    )
        
        if not remote_items:
            console.print("\n[yellow]No work items found in Plane[/yellow]")
            await backend.disconnect()
            return
        
        # Display what will be pulled
        console.print(f"\n[bold]Found {len(remote_items)} work items in Plane[/bold]\n")
        
        table = Table(title="Work Items to Pull")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Type", style="yellow")
        table.add_column("State", style="green")
        
        for item in remote_items[:10]:  # Show first 10
            table.add_row(
                item.id or "—",
                item.title[:40] + ("..." if len(item.title) > 40 else ""),
                item.type,
                item.state or "—"
            )
        
        if len(remote_items) > 10:
            console.print(table)
            console.print(f"[dim]...and {len(remote_items) - 10} more[/dim]\n")
        else:
            console.print(table)
            console.print()
        
        # Determine output file
        output_file = ctx.root_path / output_path
        
        # Check if file exists
        existing_items = []
        if output_file.exists():
            if not force and not merge:
                from rich.prompt import Confirm
                if not Confirm.ask(f"[yellow]{output_path} exists. Overwrite?[/yellow]"):
                    console.print("[yellow]Cancelled[/yellow]")
                    await backend.disconnect()
                    raise typer.Exit(0)
            
            if merge:
                # Load existing items
                with open(output_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, list):
                        existing_items = data
        
        # Prepare items for output (clean format!)
        items_to_write = []
        
        if merge:
            # Start with existing items
            items_to_write.extend(existing_items)
        
        # raw_items_for_props is already fetched above if with_properties is True
        
        for idx, item in enumerate(remote_items):
            item_dict = {
                'title': item.title,
                'type': item.type,
            }
            
            # Add optional ID (for stable tracking)
            if item.id:
                item_dict = {'id': item.id, **item_dict}
            
            # Add other fields if present
            if item.description:
                item_dict['description'] = item.description
            if item.state:
                item_dict['state'] = item.state
            if item.priority:
                item_dict['priority'] = item.priority
            if item.labels:
                item_dict['labels'] = item.labels
            
            # Dates
            if item.start_date:
                item_dict['start_date'] = item.start_date
            if item.due_date:
                item_dict['due_date'] = item.due_date
            
            # Assignments
            if item.assignees:
                item_dict['assignees'] = item.assignees
            if item.watchers:
                item_dict['watchers'] = item.watchers
            
            # Relationships
            if item.parent:
                item_dict['parent'] = item.parent
            if item.blocked_by:
                item_dict['blocked_by'] = item.blocked_by
            if item.blocking:
                item_dict['blocking'] = item.blocking
            if item.duplicate_of:
                item_dict['duplicate_of'] = item.duplicate_of
            if item.relates_to:
                item_dict['relates_to'] = item.relates_to
            
            # Custom properties (from fetched data)
            if with_properties and raw_items_for_props and idx < len(raw_items_for_props):
                raw_item = raw_items_for_props[idx]
                if hasattr(raw_item, 'id'):
                    item_uuid = str(raw_item.id)
                    if item_uuid in work_item_properties and work_item_properties[item_uuid]:
                        item_dict['properties'] = work_item_properties[item_uuid]
            
            items_to_write.append(item_dict)
        
        # Write to file (clean YAML!)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            yaml.dump(
                items_to_write,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        
        # Update state to track pulled items
        for index, item in enumerate(remote_items):
            # We don't have remote_id from list, so we'll need to fetch or generate
            # For now, use a placeholder approach
            tracking_key = item.id if item.id else f"pulled:{item.title[:30]}"
            
            # Note: We can't get exact remote_id from list response without additional API calls
            # In production, you'd want to store this or fetch individually
            # For now, we'll track with what we have
            
        elapsed = time.time() - start_time
        elapsed_str = f"{elapsed:.1f}s" if elapsed < 60 else f"{int(elapsed//60)}m {int(elapsed%60)}s"
        
        console.print()
        if not work_only:
            schema_str = f"{schema_time:.1f}s" if schema_time < 60 else f"{int(schema_time//60)}m {int(schema_time%60)}s"
            console.print(f"[green]✓[/green] Pulled schema to [cyan]schema/[/cyan] [dim]({schema_str})[/dim]")
        console.print(f"[green]✓[/green] Pulled {len(remote_items)} work items to [cyan]{output_path}[/cyan]")
        if with_properties and work_item_properties:
            console.print(f"[green]✓[/green] Fetched custom properties for all items")
        console.print(f"[dim]  Total time: {elapsed_str}[/dim]")
        console.print()
        if work_only:
            console.print(f"[dim]💡 Tip: Use without --work-only to pull schema too[/dim]")
        elif not with_properties:
            console.print(f"[dim]💡 Tip: Use --with-properties to fetch custom property values[/dim]")
        console.print()
        
        await backend.disconnect()
        
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)

