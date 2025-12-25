"""
CLI commands for Plane automations.

Commands:
    plane automations list      - List all automations
    plane automations validate  - Validate automation files
    plane automations run       - Run automations
    plane automations test      - Test an automation
    plane automations new       - Create new automation from template
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

from planecompose.automations.engine import (
    AutomationEngine, 
    create_event, 
    create_sample_work_item,
)
from planecompose.automations.parser import load_automations, validate_automation
from planecompose.automations.runner import ScriptRunner
from planecompose.automations.actions import format_action
from planecompose.automations.visualizer import (
    generate_mermaid,
    generate_ascii,
    generate_html,
    get_mermaid_png_url,
    download_png_sync,
)


app = typer.Typer(
    name="automations",
    help="Manage and run automations",
    no_args_is_help=True,
)
console = Console()


def get_project_root() -> Path:
    """Get project root (directory with plane.yaml)."""
    cwd = Path.cwd()
    
    # Look for plane.yaml
    for parent in [cwd] + list(cwd.parents):
        if (parent / "plane.yaml").exists():
            return parent
    
    return cwd


def get_config() -> dict:
    """Load config from plane.yaml."""
    import yaml
    
    project_root = get_project_root()
    config_file = project_root / "plane.yaml"
    
    if config_file.exists():
        return yaml.safe_load(config_file.read_text()) or {}
    
    return {}


# =============================================================================
# LIST COMMAND
# =============================================================================

@app.command("list")
def list_automations():
    """List all automations in the project."""
    project_root = get_project_root()
    automations_dir = project_root / "automations"
    
    if not automations_dir.exists():
        console.print("[yellow]No automations/ directory found[/yellow]")
        console.print(f"Create it at: {automations_dir}")
        raise typer.Exit(1)
    
    automations = load_automations(automations_dir)
    
    if not automations:
        console.print("[yellow]No automations found in automations/[/yellow]")
        console.print("\nCreate one with: [cyan]plane automations new <name>[/cyan]")
        return
    
    # Build table
    table = Table(title="Automations", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Trigger", style="green")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="yellow")
    
    for auto in automations:
        trigger = auto.trigger_event
        auto_type = "script" if auto.script else "yaml"
        status = "[green]✓ enabled[/green]" if auto.enabled else "[dim]✗ disabled[/dim]"
        
        table.add_row(auto.name, trigger, auto_type, status)
    
    console.print(table)
    console.print(f"\n[dim]{len(automations)} automation(s) found[/dim]")


# =============================================================================
# VALIDATE COMMAND
# =============================================================================

@app.command("validate")
def validate():
    """Validate all automation definitions."""
    project_root = get_project_root()
    
    engine = AutomationEngine(project_root, config=get_config())
    count = engine.load()
    
    if count == 0:
        console.print("[yellow]No automations found to validate[/yellow]")
        return
    
    console.print(f"Validating {count} automation(s)...\n")
    
    results = engine.validate_all()
    has_errors = False
    
    for name, errors in results.items():
        if errors:
            console.print(f"[red]✗ {name}[/red]")
            for error in errors:
                console.print(f"  └─ {error}")
            has_errors = True
        else:
            console.print(f"[green]✓ {name}[/green]")
    
    if has_errors:
        console.print("\n[red]Validation failed[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green]All {count} automation(s) valid ✓[/green]")


# =============================================================================
# RUN COMMAND
# =============================================================================

@app.command("run")
def run(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n",
        help="Show what would happen without executing"
    ),
    once: bool = typer.Option(
        False, "--once",
        help="Check once and exit"
    ),
    watch: bool = typer.Option(
        False, "--watch", "-w",
        help="Watch for events continuously"
    ),
    automation: Optional[str] = typer.Option(
        None, "--automation", "-a",
        help="Run specific automation only"
    ),
):
    """Run automations against recent events."""
    project_root = get_project_root()
    config = get_config()
    
    engine = AutomationEngine(project_root, config=config)
    engine.dry_run = dry_run
    count = engine.load()
    
    if count == 0:
        console.print("[yellow]No automations found[/yellow]")
        raise typer.Exit(1)
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE[/yellow] - no changes will be made\n")
    
    if watch:
        console.print(f"[cyan]Watching for events...[/cyan] (Ctrl+C to stop)")
        console.print(f"Loaded {count} automation(s)\n")
        console.print("[dim]Polling every 30 seconds[/dim]\n")
        
        # Would implement polling loop here
        console.print("[yellow]Watch mode not yet implemented[/yellow]")
        console.print("Use --once for now")
        raise typer.Exit(1)
    
    # One-shot mode
    console.print(f"Checking for events... ({count} automation(s) loaded)\n")
    
    # For demo, show what automations would match sample events
    console.print("[dim]Note: Event polling not yet connected to Plane API[/dim]")
    console.print("[dim]Use 'plane automations test <name>' to test automations[/dim]\n")


# =============================================================================
# TEST COMMAND
# =============================================================================

@app.command("test")
def test(
    name: str = typer.Argument(
        ...,
        help="Name of automation to test"
    ),
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i",
        help="JSON file with test work item data"
    ),
    type: str = typer.Option(
        "bug", "--type", "-t",
        help="Work item type for sample data"
    ),
    labels: Optional[str] = typer.Option(
        None, "--labels", "-l",
        help="Comma-separated labels for sample data"
    ),
):
    """Test an automation with sample data."""
    project_root = get_project_root()
    config = get_config()
    
    engine = AutomationEngine(project_root, config=config)
    engine.dry_run = True  # Always dry-run for tests
    engine.load()
    
    # Find automation
    auto = engine.get(name)
    if not auto:
        console.print(f"[red]Automation not found: {name}[/red]")
        console.print("\nAvailable automations:")
        for a in engine.automations:
            console.print(f"  • {a.name}")
        raise typer.Exit(1)
    
    # Build test context
    if input_file:
        work_item = json.loads(input_file.read_text())
    else:
        label_list = labels.split(",") if labels else ["critical"]
        work_item = create_sample_work_item(
            type=type,
            labels=label_list,
        )
    
    # Show test setup
    console.print(Panel(
        f"[bold cyan]{auto.name}[/bold cyan]\n"
        f"[dim]{auto.description or 'No description'}[/dim]",
        title="Testing Automation"
    ))
    
    console.print("\n[bold]Input:[/bold]")
    console.print(f"  type: [cyan]{work_item.get('type')}[/cyan]")
    console.print(f"  labels: [cyan]{work_item.get('labels')}[/cyan]")
    console.print(f"  priority: [cyan]{work_item.get('priority', 'none')}[/cyan]")
    
    # Create test event
    event = create_event(
        auto.trigger_event,
        work_item,
    )
    
    # Check if it matches
    matched = engine.match(event)
    
    if auto not in matched:
        console.print("\n[yellow]⚠ Automation did not match the test data[/yellow]")
        if auto.when:
            console.print(f"  Conditions: {auto.when}")
        return
    
    # Execute
    console.print("\n[bold]Executing...[/bold]\n")
    
    result = asyncio.run(engine.execute(auto, event))
    
    if result.success:
        console.print("[green]Actions that would be executed:[/green]\n")
        
        if result.actions:
            for action in result.actions:
                action_str = format_action({action.action: action.data})
                console.print(f"  → {action_str}")
        else:
            console.print("  [dim]No actions returned[/dim]")
        
        console.print(f"\n[dim]Duration: {result.duration_ms}ms[/dim]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


# =============================================================================
# NEW COMMAND
# =============================================================================

@app.command("new")
def new(
    name: str = typer.Argument(
        ...,
        help="Name for the new automation"
    ),
    trigger: str = typer.Option(
        "work_item.created",
        "--trigger", "-t",
        help="Trigger event type"
    ),
    with_script: bool = typer.Option(
        False, "--script", "-s",
        help="Create with TypeScript script"
    ),
):
    """Create a new automation from template."""
    project_root = get_project_root()
    automations_dir = project_root / "automations"
    scripts_dir = automations_dir / "scripts"
    
    # Create directories if needed
    automations_dir.mkdir(exist_ok=True)
    
    # Sanitize name
    safe_name = name.lower().replace(" ", "-").replace("_", "-")
    yaml_file = automations_dir / f"{safe_name}.yaml"
    
    if yaml_file.exists():
        console.print(f"[red]Automation already exists: {yaml_file}[/red]")
        raise typer.Exit(1)
    
    if with_script:
        # Create with script template
        scripts_dir.mkdir(exist_ok=True)
        script_file = scripts_dir / f"{safe_name}.ts"
        
        yaml_content = f'''name: {name}
description: TODO - Add description

on: {trigger}

when:
  type: bug

script: ./scripts/{safe_name}.ts
'''
        
        script_content = '''/**
 * Automation: ''' + name + '''
 * 
 * Receives context with work item data, returns actions to execute.
 * 
 * See ./types.ts for full type definitions.
 */

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface Context {
  workItem: {
    id: string;
    title: string;
    description?: string;
    type: string;
    state: string;
    priority?: string;
    labels: string[];
    assignees: string[];
    properties: Record<string, unknown>;
  };
  trigger: {
    type: string;
    timestamp: string;
    changes?: Record<string, { from: unknown; to: unknown }>;
  };
  config: Record<string, unknown>;
}

type Action =
  | { set: Record<string, unknown> }
  | { assign: string | string[] }
  | { unassign: string | string[] }
  | { add_label: string | string[] }
  | { remove_label: string | string[] }
  | { comment: string }
  | { notify: { channel?: string; to?: string; message: string } };

// =============================================================================
// AUTOMATION LOGIC
// =============================================================================

export default function run(ctx: Context): Action[] {
  const { workItem } = ctx;
  
  // Your logic here
  if (workItem.labels.includes("critical")) {
    return [
      { set: { priority: "urgent" } },
      { comment: "Auto-escalated due to critical label" }
    ];
  }
  
  return [];
}
'''
        
        script_file.write_text(script_content)
        console.print(f"[green]✓[/green] Created {script_file.relative_to(project_root)}")
    else:
        # YAML-only template
        yaml_content = f'''name: {name}
description: TODO - Add description

on: {trigger}

when:
  type: bug

do:
  - when: labels contains "critical"
    set: {{ priority: urgent, state: in_progress }}
    notify:
      channel: "#alerts"
      message: "🚨 Critical bug: ${{{{ title }}}}"
    
  - when: labels contains "security"
    set: {{ priority: urgent }}
    add_label: security-review
    
  - otherwise:
    set: {{ state: backlog }}
    add_label: needs-triage
'''
    
    yaml_file.write_text(yaml_content)
    console.print(f"[green]✓[/green] Created {yaml_file.relative_to(project_root)}")
    
    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Edit the automation: [dim]{yaml_file}[/dim]")
    console.print(f"  2. Validate: [dim]plane automations validate[/dim]")
    console.print(f"  3. Test: [dim]plane automations test {safe_name}[/dim]")


# =============================================================================
# INFO COMMAND
# =============================================================================

@app.command("info")
def info():
    """Show automation system info and Deno status."""
    project_root = get_project_root()
    
    console.print("[bold]Plane Automations[/bold]\n")
    
    # Project info
    console.print(f"Project root: [cyan]{project_root}[/cyan]")
    
    automations_dir = project_root / "automations"
    if automations_dir.exists():
        automations = load_automations(automations_dir)
        console.print(f"Automations: [green]{len(automations)}[/green]")
    else:
        console.print("Automations: [yellow]directory not found[/yellow]")
    
    # Deno status
    runner = ScriptRunner(project_root)
    deno_ok, deno_info = runner.check_deno()
    
    console.print(f"\n[bold]Runtime:[/bold]")
    if deno_ok:
        console.print(f"  Deno: [green]✓ {deno_info}[/green]")
    else:
        console.print(f"  Deno: [red]✗ {deno_info}[/red]")
        console.print("\n  Install Deno:")
        console.print("    curl -fsSL https://deno.land/install.sh | sh")


# =============================================================================
# SHOW COMMAND
# =============================================================================

@app.command("show")
def show(
    name: str = typer.Argument(..., help="Automation name")
):
    """Show details of an automation."""
    project_root = get_project_root()
    
    engine = AutomationEngine(project_root, config=get_config())
    engine.load()
    
    auto = engine.get(name)
    if not auto:
        console.print(f"[red]Automation not found: {name}[/red]")
        raise typer.Exit(1)
    
    # Read source file
    if auto.source_file:
        content = Path(auto.source_file).read_text()
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
        
        console.print(Panel(
            syntax,
            title=f"[bold]{auto.name}[/bold]",
            subtitle=f"[dim]{auto.source_file}[/dim]"
        ))
    
    # If has script, show it too
    if auto.script:
        script_path = Path(auto.source_file).parent / auto.script
        if script_path.exists():
            console.print()
            script_content = script_path.read_text()
            script_syntax = Syntax(script_content, "typescript", theme="monokai", line_numbers=True)
            console.print(Panel(
                script_syntax,
                title=f"[bold]Script: {auto.script}[/bold]"
            ))


# =============================================================================
# VIZ COMMAND
# =============================================================================

@app.command("viz")
def visualize(
    name: str = typer.Argument(..., help="Automation name to visualize"),
    format: str = typer.Option(
        "ascii", "--format", "-f",
        help="Output format: ascii, mermaid, html, png"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path (default: stdout or auto-named file)"
    ),
    theme: str = typer.Option(
        "dark", "--theme", "-t",
        help="Theme for diagrams: dark, default, forest, neutral"
    ),
    open_browser: bool = typer.Option(
        False, "--open", "-O",
        help="Open HTML output in browser"
    ),
):
    """
    Visualize an automation as a flowchart.
    
    Examples:
        plane automations viz "Bug triage"              # ASCII in terminal
        plane automations viz "Bug triage" -f mermaid   # Mermaid markdown
        plane automations viz "Bug triage" -f html -O   # Open in browser
        plane automations viz "Bug triage" -f png -o flow.png  # Export PNG
    """
    project_root = get_project_root()
    
    engine = AutomationEngine(project_root, config=get_config())
    engine.load()
    
    # Find automation
    auto = engine.get(name)
    if not auto:
        console.print(f"[red]Automation not found: {name}[/red]")
        console.print("\nAvailable automations:")
        for a in engine.automations:
            console.print(f"  • {a.name}")
        raise typer.Exit(1)
    
    # Generate based on format
    format = format.lower()
    
    if format == "ascii":
        # ASCII output to terminal
        ascii_chart = generate_ascii(auto)
        console.print(ascii_chart)
        
    elif format == "mermaid":
        # Mermaid markdown
        mermaid_code = generate_mermaid(auto)
        
        if output:
            output.write_text(f"```mermaid\n{mermaid_code}\n```")
            console.print(f"[green]✓[/green] Mermaid saved to {output}")
        else:
            console.print(Panel(
                Syntax(mermaid_code, "text", theme="monokai"),
                title="[bold cyan]Mermaid Diagram[/bold cyan]",
                subtitle="[dim]Paste into GitHub, Notion, or any Mermaid renderer[/dim]"
            ))
            console.print("\n[dim]Tip: Use -o file.md to save, or pipe to clipboard[/dim]")
        
    elif format == "html":
        # Interactive HTML
        mermaid_code = generate_mermaid(auto)
        html_content = generate_html(auto, mermaid_code)
        
        if output:
            output_path = output
        else:
            safe_name = auto.name.lower().replace(" ", "-")
            output_path = project_root / f"{safe_name}-flow.html"
        
        output_path.write_text(html_content)
        console.print(f"[green]✓[/green] HTML saved to {output_path}")
        
        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{output_path.absolute()}")
            console.print("[dim]Opening in browser...[/dim]")
        else:
            console.print(f"[dim]Open with: open {output_path}[/dim]")
        
    elif format == "png":
        # PNG export via mermaid.ink
        mermaid_code = generate_mermaid(auto)
        
        if output:
            output_path = output
        else:
            safe_name = auto.name.lower().replace(" ", "-")
            output_path = project_root / f"{safe_name}-flow.png"
        
        console.print("[dim]Generating PNG via mermaid.ink...[/dim]")
        
        try:
            download_png_sync(mermaid_code, output_path, theme)
            console.print(f"[green]✓[/green] PNG saved to {output_path}")
            
            # Show file size
            size_kb = output_path.stat().st_size / 1024
            console.print(f"[dim]Size: {size_kb:.1f} KB[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error generating PNG: {e}[/red]")
            console.print("\n[yellow]Fallback: Use mermaid.ink URL[/yellow]")
            url = get_mermaid_png_url(mermaid_code, theme)
            console.print(f"[dim]{url[:80]}...[/dim]")
            raise typer.Exit(1)
    
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        console.print("Available formats: ascii, mermaid, html, png")
        raise typer.Exit(1)


@app.command("viz-all")
def visualize_all(
    format: str = typer.Option(
        "html", "--format", "-f",
        help="Output format: mermaid, html"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o",
        help="Output directory (default: ./automations/docs)"
    ),
):
    """
    Visualize all automations and generate documentation.
    
    Example:
        plane automations viz-all -f html -o docs/flows
    """
    project_root = get_project_root()
    
    engine = AutomationEngine(project_root, config=get_config())
    count = engine.load()
    
    if count == 0:
        console.print("[yellow]No automations found[/yellow]")
        return
    
    # Determine output directory
    if output_dir:
        out_dir = output_dir
    else:
        out_dir = project_root / "automations" / "docs"
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"Generating {format.upper()} for {count} automation(s)...\n")
    
    generated = []
    
    for auto in engine.automations:
        safe_name = auto.name.lower().replace(" ", "-")
        mermaid_code = generate_mermaid(auto)
        
        if format == "mermaid":
            out_file = out_dir / f"{safe_name}.md"
            content = f"# {auto.name}\n\n"
            content += f"{auto.description or 'No description'}\n\n"
            content += f"```mermaid\n{mermaid_code}\n```\n"
            out_file.write_text(content)
            
        elif format == "html":
            out_file = out_dir / f"{safe_name}.html"
            html_content = generate_html(auto, mermaid_code)
            out_file.write_text(html_content)
        
        else:
            console.print(f"[red]Unsupported format for viz-all: {format}[/red]")
            raise typer.Exit(1)
        
        generated.append(out_file)
        console.print(f"  [green]✓[/green] {auto.name} → {out_file.name}")
    
    console.print(f"\n[green]Generated {len(generated)} visualization(s) in {out_dir}[/green]")
    
    # Generate index if HTML
    if format == "html":
        index_path = out_dir / "index.html"
        index_content = _generate_index_html(engine.automations, generated)
        index_path.write_text(index_content)
        console.print(f"  [cyan]→[/cyan] Index: {index_path}")


def _generate_index_html(automations: list, files: list[Path]) -> str:
    """Generate an index HTML page linking to all visualizations."""
    import html as html_module
    
    items = ""
    for auto, file in zip(automations, files):
        items += f'''
        <a href="{file.name}" class="card">
            <div class="card-icon">🤖</div>
            <div class="card-content">
                <div class="card-title">{html_module.escape(auto.name)}</div>
                <div class="card-desc">{html_module.escape(auto.description or 'No description')}</div>
                <div class="card-meta">
                    <span class="trigger">🎯 {auto.trigger_event}</span>
                    <span class="type">{'📜 Script' if auto.script else '📄 YAML'}</span>
                </div>
            </div>
        </a>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automation Flows</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        h1 {{
            font-size: 2.5rem;
            color: #60a5fa;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: #94a3b8;
            margin-bottom: 2rem;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }}
        
        .card {{
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 16px;
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            display: flex;
            gap: 1rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            border-color: #3b82f6;
        }}
        
        .card-icon {{ font-size: 2.5rem; }}
        
        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 0.5rem;
        }}
        
        .card-desc {{
            color: #94a3b8;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}
        
        .card-meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
        }}
        
        .trigger {{ color: #34d399; }}
        .type {{ color: #fbbf24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Automation Flows</h1>
        <p class="subtitle">{len(automations)} automations configured</p>
        
        <div class="grid">
            {items}
        </div>
    </div>
</body>
</html>'''

