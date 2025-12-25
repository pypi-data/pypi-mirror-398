"""Clone command - clone a Plane project by UUID.

All API calls go through PlaneBackend - no direct SDK usage in CLI code.
"""
import asyncio
import typer
import yaml
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


def clone(
    project_uuid: str = typer.Argument(..., help="Project UUID to clone"),
    directory: str = typer.Option(None, "--directory", "-d", help="Directory to clone into (default: project name)"),
    workspace: str = typer.Option(None, "--workspace", "-w", help="Workspace slug (required if not in project metadata)"),
    with_properties: bool = typer.Option(False, "--with-properties", help="Clone work item property values (slower, requires many API calls)"),
):
    """
    Clone a Plane project by UUID (fast by default).
    
    Creates a new local workspace with:
    - plane.yaml (project configuration)
    - schema/ (types, workflows, labels with property definitions)
    - .plane/remote/items.yaml (all work items)
    
    By default, work item property VALUES are NOT cloned (schema definitions are).
    Use --with-properties to clone property values (can be very slow for large projects).
    
    This is like 'git clone' - use it to get someone else's project.
    For your own project, use 'plane pull' instead.
    
    Example:
        plane clone abc-123-uuid-456 --workspace myteam
    """
    asyncio.run(_clone(project_uuid, directory, workspace, with_properties))


async def _clone(project_uuid: str, directory: str | None, workspace: str | None, with_properties: bool = False):
    """Async implementation of clone.
    
    All API calls go through PlaneBackend (rate limiting is automatic).
    """
    import time
    from planecompose.backend.plane import PlaneBackend
    
    start_time = time.time()
    phase_times = {}
    
    try:
        # Load configuration (server URL and API key)
        from planecompose.cli.auth import load_config
        server_url, api_key = load_config()
        
        console.print(f"\n[bold cyan]Cloning project {project_uuid}...[/bold cyan]")
        if not with_properties:
            console.print("[dim]  (Use --with-properties to clone work item property values)[/dim]\n")
        else:
            console.print("[dim]  (Cloning with property values - this may take longer)[/dim]\n")
        
        # Validate workspace
        if not workspace:
            console.print("\n[red]✗ Error:[/red] --workspace is required")
            console.print("Example: plane clone abc-123 --workspace myteam")
            raise typer.Exit(1)
        
        # Create backend (all API calls go through this)
        backend = PlaneBackend.create_client(server_url, api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            phase_start = time.time()
            task = progress.add_task("Connecting to Plane...", total=None)
            
            # Fetch project details
            progress.update(task, description="📡 Fetching project details...")
            
            try:
                project = await backend.retrieve_project(workspace, project_uuid)
                phase_times['connect'] = time.time() - phase_start
            except Exception as e:
                console.print(f"\n[red]✗ Error:[/red] Could not fetch project")
                console.print(f"[dim]{e}[/dim]")
                console.print("\n[yellow]Make sure:[/yellow]")
                console.print("  • The project UUID is correct")
                console.print("  • You have access to this project")
                console.print("  • The workspace slug is correct")
                raise typer.Exit(1)
            
            # Determine directory name
            if not directory:
                # Use project identifier or name
                directory = project.identifier.lower() if project.identifier else project.name.lower().replace(' ', '-')
            
            target_dir = Path.cwd() / directory
            
            if target_dir.exists():
                from rich.prompt import Confirm
                if not Confirm.ask(f"[yellow]Directory '{directory}' exists. Overwrite?[/yellow]"):
                    console.print("[yellow]Cancelled[/yellow]")
                    raise typer.Exit(0)
            
            # Create directory structure
            progress.update(task, description="Creating directory structure...")
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "schema").mkdir(exist_ok=True)
            (target_dir / "work").mkdir(exist_ok=True)
            (target_dir / ".plane" / "remote").mkdir(parents=True, exist_ok=True)
            
            # Create plane.yaml
            progress.update(task, description="Writing configuration...")
            plane_yaml = {
                'workspace': workspace,
                'project': {
                    'key': project.identifier,
                    'uuid': project_uuid,
                    'name': project.name,
                },
                'defaults': {
                    'type': 'task',
                    'workflow': 'standard',
                }
            }
            
            with open(target_dir / "plane.yaml", 'w') as f:
                yaml.dump(plane_yaml, f, default_flow_style=False, sort_keys=False)
            
            # Fetch and write schema (with rich metadata)
            phase_start = time.time()
            progress.update(task, description="📋 Fetching work item types...")
            
            # Use backend to fetch types (rate limiting is automatic)
            types_sdk = await backend.list_types_raw(workspace, project_uuid)
            
            # Convert SDK objects to dicts for consistent processing
            types_data = []
            for t in types_sdk:
                type_dict = {
                    'id': str(t.id) if hasattr(t, 'id') else None,
                    'name': t.name if hasattr(t, 'name') else None,
                    'description': t.description if hasattr(t, 'description') else None,
                    'is_epic': t.is_epic if hasattr(t, 'is_epic') else False,
                    'is_default': t.is_default if hasattr(t, 'is_default') else False,
                    'level': t.level if hasattr(t, 'level') else 0,
                }
                # Handle logo_props (SDK may return object or dict)
                if hasattr(t, 'logo_props') and t.logo_props:
                    lp = t.logo_props
                    if hasattr(lp, 'model_dump'):
                        type_dict['logo_props'] = lp.model_dump()
                    elif isinstance(lp, dict):
                        type_dict['logo_props'] = lp
                    else:
                        type_dict['logo_props'] = {
                            'icon': getattr(lp, 'icon', None),
                            'emoji': getattr(lp, 'emoji', None),
                            'in_use': getattr(lp, 'in_use', None),
                        }
                types_data.append(type_dict)
            
            # Build property maps early so we can use them when writing schema
            # Set config temporarily so backend methods work
            from planecompose.core.models import ProjectConfig
            backend._config = ProjectConfig(
                workspace=workspace,
                project_key=project.identifier,
                project_uuid=project_uuid,
                project_name=project.name,
            )
            backend._project_id = project_uuid
            
            progress.update(task, description=f"📋 Building property maps for {len(types_data)} types...")
            property_maps = await backend.build_property_maps(types_data)
            phase_times['types'] = time.time() - phase_start
            
            types_yaml = {}
            for wit in types_data:
                if not wit.get('name'):  # Skip unnamed types
                    continue
                    
                type_config = {
                    'description': wit.get('description') or f"{wit.get('name')} work item",
                    'workflow': 'standard',
                }
                
                # Add rich metadata
                if wit.get('logo_props'):
                    logo = wit['logo_props']
                    if logo.get('icon'):
                        type_config['icon'] = {
                            'name': logo['icon'].get('name'),
                            'color': logo['icon'].get('background_color'),
                        }
                    if logo.get('in_use') == 'emoji' and logo.get('emoji'):
                        type_config['emoji'] = logo['emoji'].get('value')
                
                if wit.get('is_epic'):
                    type_config['is_epic'] = True
                if wit.get('level', 0) > 0:
                    type_config['level'] = wit['level']
                if wit.get('is_default'):
                    type_config['is_default'] = True
                
                # Add properties from property_maps (which includes options)
                wit_id = wit.get('id')
                if wit_id and wit_id in property_maps and property_maps[wit_id]:
                    type_config['properties'] = []
                    for prop_id, prop_info in property_maps[wit_id].items():
                        # Convert PropertyType enum to string
                        prop_type = prop_info['type']
                        if hasattr(prop_type, 'value'):
                            prop_type = prop_type.value
                        prop_type = str(prop_type).lower()
                        
                        prop_config = {
                            'name': prop_info['name'],
                            'type': prop_type,
                            'required': False,  # We don't have this info in property_maps
                        }
                        
                        # Add options list for OPTION type properties
                        if 'option' in prop_type and prop_info.get('options'):
                            # Convert {uuid: name} dict to [name] list
                            options_list = list(prop_info['options'].values())
                            if options_list:
                                prop_config['options'] = options_list
                        
                        # Add is_multi flag
                        if prop_info.get('is_multi'):
                            prop_config['is_multi'] = True
                        
                        # Add relation_type for RELATION properties (user vs issue)
                        if 'relation' in prop_type and prop_info.get('relation_type'):
                            prop_config['relation_type'] = prop_info['relation_type']
                        
                        type_config['properties'].append(prop_config)
                
                types_yaml[wit['name']] = type_config
            
            with open(target_dir / "schema" / "types.yaml", 'w') as f:
                yaml.dump(types_yaml, f, default_flow_style=False, sort_keys=False)
            
            # Fetch states (via backend - rate limiting automatic)
            phase_start = time.time()
            progress.update(task, description="🔄 Fetching workflow states...")
            states_list = await backend.list_states_raw(workspace, project_uuid)
            
            if not states_list:
                # SDK validation may fail, use defaults
                console.print("[yellow]⚠ Warning:[/yellow] Could not fetch states, using defaults")
                from types import SimpleNamespace
                states_list = [
                    SimpleNamespace(id='default-1', name='backlog', group='backlog', color='#94a3b8'),
                    SimpleNamespace(id='default-2', name='todo', group='unstarted', color='#3b82f6'),
                    SimpleNamespace(id='default-3', name='in_progress', group='started', color='#f59e0b'),
                    SimpleNamespace(id='default-4', name='done', group='completed', color='#22c55e'),
                ]
            
            # Group states by workflow (for now just use 'standard')
            workflows_yaml = {
                'standard': {
                    'states': [],
                    'initial': 'backlog',
                    'terminal': ['done', 'cancelled'],
                }
            }
            
            for state in states_list:
                workflows_yaml['standard']['states'].append({
                    'name': state.name,
                    'group': state.group,
                    'color': state.color or '#808080',
                })
            
            with open(target_dir / "schema" / "workflows.yaml", 'w') as f:
                yaml.dump(workflows_yaml, f, default_flow_style=False, sort_keys=False)
            phase_times['states'] = time.time() - phase_start
            
            # Fetch labels (via backend - rate limiting automatic)
            phase_start = time.time()
            progress.update(task, description="🏷️  Fetching labels...")
            labels_list = await backend.list_labels_raw(workspace, project_uuid)
            
            labels_yaml = {'groups': {}}
            for label in labels_list:
                # Simple grouping by first word or 'general'
                group_name = 'general'
                if labels_yaml['groups'].get(group_name) is None:
                    labels_yaml['groups'][group_name] = {
                        'color': label.color or '#808080',
                        'labels': []
                    }
                labels_yaml['groups'][group_name]['labels'].append({'name': label.name})
            
            with open(target_dir / "schema" / "labels.yaml", 'w') as f:
                yaml.dump(labels_yaml, f, default_flow_style=False, sort_keys=False)
            phase_times['labels'] = time.time() - phase_start
            
            # Fetch work items (via backend - rate limiting automatic)
            phase_start = time.time()
            progress.update(task, description="📝 Fetching work items...")
            work_items_list = await backend.list_work_items_raw()
            
            # Build state, label, and type maps for reverse lookup
            state_map = {str(s.id): s.name for s in states_list}
            label_map = {str(l.id): l.name for l in labels_list}
            # Build type map: UUID -> type name
            type_map = {wit['id']: wit['name'] for wit in types_data if 'id' in wit and 'name' in wit}
            
            # property_maps already built earlier, reuse it
            
            phase_times['work_items'] = time.time() - phase_start
            
            # Fetch properties in batch (OPTIONAL - can be very slow!)
            work_item_properties = {}
            if with_properties and property_maps:
                phase_start = time.time()
                total_calls = sum(len(property_maps.get(str(item.type_id), {})) for item in work_items_list if hasattr(item, 'type_id'))
                
                progress.update(task, description=f"⚙️  Fetching property values ({total_calls} API calls, ~{total_calls/50:.0f}min)...")
                work_item_properties = await backend.fetch_work_item_properties_batch(
                    work_items_list, property_maps
                )
                phase_times['properties'] = time.time() - phase_start
            
            # Convert to clean YAML format (FAST - no API calls here!)
            items_list = []
            total_items = len(work_items_list)
            progress.update(task, description=f"Processing {total_items} work items...")
            
            for item in work_items_list:
                # Get type name from type_id
                type_name = 'task'
                if hasattr(item, 'type_id') and item.type_id:
                    type_name = type_map.get(str(item.type_id), 'task')
                
                item_dict = {
                    'title': item.name,
                    'type': type_name,
                }
                
                # Add sequence ID for stable tracking
                if hasattr(item, 'sequence_id') and item.sequence_id:
                    item_dict = {'id': f"{project.identifier}-{item.sequence_id}", **item_dict}
                
                if hasattr(item, 'description_html') and item.description_html:
                    item_dict['description'] = item.description_html
                if hasattr(item, 'state') and item.state:
                    state_name = state_map.get(str(item.state))
                    if state_name:
                        item_dict['state'] = state_name
                if hasattr(item, 'priority') and item.priority:
                    item_dict['priority'] = item.priority
                if hasattr(item, 'labels') and item.labels:
                    label_names = [label_map[str(lid)] for lid in item.labels if str(lid) in label_map]
                    if label_names:
                        item_dict['labels'] = label_names
                
                # Dates
                if hasattr(item, 'start_date') and item.start_date:
                    item_dict['start_date'] = item.start_date
                if hasattr(item, 'target_date') and item.target_date:  # Plane API uses "target_date"
                    item_dict['due_date'] = item.target_date
                
                # Parent relationship
                if hasattr(item, 'parent_id') and item.parent_id:
                    item_dict['parent'] = str(item.parent_id)
                
                # Assignees
                if hasattr(item, 'assignees') and item.assignees:
                    assignees = [str(a) for a in item.assignees]
                    if assignees:
                        item_dict['assignees'] = assignees
                
                # Dependencies & Relationships
                if hasattr(item, 'blocked_issues') and item.blocked_issues:
                    blocked_by = [str(b) for b in item.blocked_issues]
                    if blocked_by:
                        item_dict['blocked_by'] = blocked_by
                
                if hasattr(item, 'blocker_issues') and item.blocker_issues:
                    blocking = [str(b) for b in item.blocker_issues]
                    if blocking:
                        item_dict['blocking'] = blocking
                
                if hasattr(item, 'duplicate_to') and item.duplicate_to:
                    item_dict['duplicate_of'] = str(item.duplicate_to)
                
                if hasattr(item, 'related_issues') and item.related_issues:
                    relates_to = [str(r) for r in item.related_issues]
                    if relates_to:
                        item_dict['relates_to'] = relates_to
                
                # Add pre-fetched properties (if any)
                if hasattr(item, 'id'):
                    item_id = str(item.id)
                    if item_id in work_item_properties and work_item_properties[item_id]:
                        item_dict['properties'] = work_item_properties[item_id]
                
                items_list.append(item_dict)
            
            with open(target_dir / ".plane" / "remote" / "items.yaml", 'w') as f:
                yaml.dump(items_list, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            # Create empty work/inbox.yaml
            inbox_content = """# Add your work items here
# Items in .plane/remote/ are read-only (pulled from Plane)
# Use 'plane import' to bring specific items into this file

[]
"""
            (target_dir / "work" / "inbox.yaml").write_text(inbox_content)
            
            # Create state.json
            state_json = {
                "last_sync": None,
                "types": {},
                "states": {},
                "labels": {},
                "work_items": {}
            }
            
            import json
            with open(target_dir / ".plane" / "state.json", 'w') as f:
                json.dump(state_json, f, indent=2)
            
            # Create .gitignore
            (target_dir / ".gitignore").write_text(".plane/\n")
        
        # Success message with timing breakdown
        total_time = time.time() - start_time
        total_str = f"{total_time:.1f}s" if total_time < 60 else f"{int(total_time//60)}m {int(total_time%60)}s"
        
        # Build timing breakdown
        timing_lines = []
        if 'types' in phase_times:
            timing_lines.append(f"  📋 Types: {phase_times['types']:.1f}s")
        if 'states' in phase_times:
            timing_lines.append(f"  🔄 States: {phase_times['states']:.1f}s")
        if 'labels' in phase_times:
            timing_lines.append(f"  🏷️  Labels: {phase_times['labels']:.1f}s")
        if 'work_items' in phase_times:
            timing_lines.append(f"  📝 Work Items: {phase_times['work_items']:.1f}s")
        if 'properties' in phase_times:
            timing_lines.append(f"  ⚙️  Properties: {phase_times['properties']:.1f}s")
        timing_breakdown = "\n".join(timing_lines) if timing_lines else ""
        
        property_note = ""
        if not with_properties:
            property_note = "\n[dim]💡 Tip: Use --with-properties to clone work item property values[/dim]"
        
        console.print()
        console.print(Panel(
            f"[green]✓[/green] Successfully cloned project: [bold]{project.name}[/bold]\n\n"
            f"Directory: [cyan]{directory}/[/cyan]\n"
            f"Project: [dim]{project.identifier} ({project_uuid[:8]}...)[/dim]\n"
            f"Work items: [dim]{len(items_list)} items in .plane/remote/items.yaml[/dim]\n"
            f"Time: [dim]{total_str}[/dim]\n\n"
            f"[bold]Timing Breakdown:[/bold]\n{timing_breakdown}"
            f"{property_note}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  1. [cyan]cd {directory}[/cyan]\n"
            f"  2. Review items in [cyan].plane/remote/items.yaml[/cyan]\n"
            f"  3. Add your own items to [cyan]work/inbox.yaml[/cyan]\n"
            f"  4. [cyan]plane push[/cyan] to sync your changes",
            title="Clone Complete",
            title_align="left",
            border_style="green",
        ))
        console.print()
        
    except Exception as e:
        if "Exit" not in str(type(e)):
            console.print(f"\n[red]✗ Error:[/red] {e}")
        raise typer.Exit(1)

