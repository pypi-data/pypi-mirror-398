"""
Automation visualizer - Generate flowcharts from automation definitions.

Supports:
- Mermaid diagram syntax (text)
- PNG export via mermaid.ink
- HTML interactive viewer
- ASCII terminal output
"""

from __future__ import annotations
import base64
import zlib
import urllib.parse
from pathlib import Path
from typing import Any

from .models import AutomationDefinition


# =============================================================================
# MERMAID GENERATION
# =============================================================================

def generate_mermaid(automation: AutomationDefinition) -> str:
    """
    Generate Mermaid flowchart from automation definition.
    
    Args:
        automation: The automation to visualize
        
    Returns:
        Mermaid diagram syntax as string
    """
    lines = [
        "flowchart TD",
        "",
        "    %% Trigger",
        f"    Start([\"🎯 {automation.trigger_event}\"])",
    ]
    
    # Add filter node if 'when' conditions exist
    if automation.when:
        filter_conditions = _format_conditions(automation.when)
        lines.append(f"    Start --> Filter{{\"🔍 {filter_conditions}\"}}")
        lines.append("    Filter -->|No| Skip([\"⏭️ Skip\"])")
        lines.append("    Filter -->|Yes| Begin[\" \"]")
        prev_node = "Begin"
    else:
        prev_node = "Start"
    
    # Handle script-based automations
    if automation.script:
        lines.append("")
        lines.append("    %% Script execution")
        lines.append(f"    {prev_node} --> Script[\"📜 Script: {automation.script}\"]")
        lines.append("    Script --> Actions[\"⚡ Execute returned actions\"]")
        lines.append("    Actions --> Done([\"✅ Complete\"])")
    
    # Handle YAML actions
    elif automation.do:
        lines.append("")
        lines.append("    %% Conditions and Actions")
        
        action_nodes = []
        condition_count = 0
        otherwise_node = None
        
        for i, action_def in enumerate(automation.do):
            if isinstance(action_def, dict):
                action = action_def
            else:
                action = action_def.model_dump(exclude_none=True)
            
            condition = action.get("when")
            is_otherwise = action.get("otherwise", False)
            
            # Format the actions in this block
            actions_text = _format_action_block(action)
            node_id = f"A{i}"
            
            if condition:
                cond_id = f"C{condition_count}"
                condition_count += 1
                
                # Create condition node
                cond_text = _format_condition_display(condition)
                lines.append(f"    {prev_node} --> {cond_id}{{\"❓ {cond_text}\"}}")
                lines.append(f"    {cond_id} -->|Yes| {node_id}[\"{actions_text}\"]")
                
                action_nodes.append(node_id)
                prev_node = cond_id
                
            elif is_otherwise:
                # Save for last
                otherwise_node = (node_id, actions_text, prev_node)
                
            else:
                # Unconditional action
                lines.append(f"    {prev_node} --> {node_id}[\"{actions_text}\"]")
                action_nodes.append(node_id)
                prev_node = node_id
        
        # Add otherwise node at the end
        if otherwise_node:
            node_id, actions_text, from_node = otherwise_node
            lines.append(f"    {prev_node} -->|Otherwise| {node_id}[\"{actions_text}\"]")
            action_nodes.append(node_id)
        
        # Connect all action nodes to Done
        lines.append("")
        lines.append("    %% Completion")
        for node_id in action_nodes:
            lines.append(f"    {node_id} --> Done([\"✅ Complete\"])")
        
        if automation.when:
            lines.append("    Skip --> End([\"🔚 End\"])")
            lines.append("    Done --> End")
    
    # Add styling
    lines.extend([
        "",
        "    %% Styling",
        "    style Start fill:#10b981,stroke:#059669,color:#fff",
        "    style Done fill:#10b981,stroke:#059669,color:#fff",
    ])
    
    if automation.when:
        lines.append("    style Filter fill:#3b82f6,stroke:#2563eb,color:#fff")
        lines.append("    style Skip fill:#6b7280,stroke:#4b5563,color:#fff")
        lines.append("    style End fill:#6b7280,stroke:#4b5563,color:#fff")
    
    if automation.script:
        lines.append("    style Script fill:#8b5cf6,stroke:#7c3aed,color:#fff")
        lines.append("    style Actions fill:#f59e0b,stroke:#d97706,color:#fff")
    
    return "\n".join(lines)


def _format_conditions(when: dict[str, Any]) -> str:
    """Format 'when' conditions for display."""
    parts = []
    for key, value in when.items():
        if isinstance(value, list):
            parts.append(f"{key} in [{', '.join(str(v) for v in value)}]")
        else:
            parts.append(f"{key} = {value}")
    
    text = " AND ".join(parts)
    # Truncate if too long
    if len(text) > 40:
        text = text[:37] + "..."
    return text


def _format_condition_display(condition: str) -> str:
    """Format a condition string for display."""
    # Shorten common patterns
    condition = condition.replace("labels contains ", "has label: ")
    condition = condition.replace("labels contains_any: ", "has any: ")
    condition = condition.replace(" == ", " = ")
    
    # Truncate if too long
    if len(condition) > 35:
        condition = condition[:32] + "..."
    
    return condition


def _format_action_block(action: dict[str, Any]) -> str:
    """Format actions in a block for display."""
    parts = []
    
    action_icons = {
        "set": "📌",
        "assign": "👤",
        "add_label": "🏷️",
        "remove_label": "🗑️",
        "comment": "💬",
        "notify": "📢",
        "create": "➕",
    }
    
    for key in ["set", "assign", "add_label", "remove_label", "comment", "notify", "create"]:
        if key in action:
            icon = action_icons.get(key, "•")
            value = action[key]
            
            if key == "set" and isinstance(value, dict):
                set_parts = [f"{k}={v}" for k, v in value.items()]
                parts.append(f"{icon} {', '.join(set_parts)}")
            elif key == "notify" and isinstance(value, dict):
                target = value.get("channel") or value.get("to") or "?"
                parts.append(f"{icon} notify: {target}")
            elif key == "comment":
                preview = str(value)[:20] + "..." if len(str(value)) > 20 else value
                parts.append(f"{icon} comment")
            else:
                parts.append(f"{icon} {key}: {value}")
    
    text = "<br/>".join(parts) if parts else "No actions"
    return text


# =============================================================================
# PNG GENERATION
# =============================================================================

def get_mermaid_png_url(mermaid_code: str, theme: str = "dark") -> str:
    """
    Generate a mermaid.ink URL for PNG rendering.
    
    Args:
        mermaid_code: The Mermaid diagram code
        theme: Theme to use (dark, default, forest, neutral)
        
    Returns:
        URL to the rendered PNG
    """
    # Mermaid.ink uses base64 encoded JSON
    graph_def = {
        "code": mermaid_code,
        "mermaid": {
            "theme": theme
        }
    }
    
    import json
    json_str = json.dumps(graph_def)
    
    # Compress and base64 encode
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    
    return f"https://mermaid.ink/img/pako:{encoded}"


def get_mermaid_svg_url(mermaid_code: str, theme: str = "dark") -> str:
    """Generate a mermaid.ink URL for SVG rendering."""
    import json
    
    graph_def = {
        "code": mermaid_code,
        "mermaid": {
            "theme": theme
        }
    }
    
    json_str = json.dumps(graph_def)
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    
    return f"https://mermaid.ink/svg/pako:{encoded}"


async def download_png(mermaid_code: str, output_path: Path, theme: str = "dark") -> bool:
    """
    Download PNG from mermaid.ink.
    
    Args:
        mermaid_code: The Mermaid diagram code
        output_path: Where to save the PNG
        theme: Theme to use
        
    Returns:
        True if successful
    """
    import httpx
    
    url = get_mermaid_png_url(mermaid_code, theme)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            return True
        else:
            raise RuntimeError(f"Failed to generate PNG: {response.status_code}")


def download_png_sync(mermaid_code: str, output_path: Path, theme: str = "dark") -> bool:
    """Synchronous version of download_png."""
    import httpx
    
    url = get_mermaid_png_url(mermaid_code, theme)
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            return True
        else:
            raise RuntimeError(f"Failed to generate PNG: {response.status_code}")


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(automation: AutomationDefinition, mermaid_code: str) -> str:
    """
    Generate an interactive HTML page with the diagram.
    
    Args:
        automation: The automation definition
        mermaid_code: Pre-generated Mermaid code
        
    Returns:
        HTML content as string
    """
    # Escape for HTML
    import html
    mermaid_escaped = html.escape(mermaid_code).replace("\n", "\\n")
    
    # Build metadata
    trigger = automation.trigger_event
    filter_text = ""
    if automation.when:
        filter_text = ", ".join(f"{k}={v}" for k, v in automation.when.items())
    
    action_count = 0
    if automation.do:
        action_count = len(automation.do)
    elif automation.script:
        action_count = "Script"
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(automation.name)} - Automation Flow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            color: #60a5fa;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        h1 .icon {{
            font-size: 2.5rem;
        }}
        
        .description {{
            color: #94a3b8;
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }}
        
        .meta {{
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        
        .meta-card {{
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            min-width: 200px;
        }}
        
        .meta-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 0.5rem;
        }}
        
        .meta-value {{
            font-size: 1.1rem;
            font-weight: 500;
            color: #f1f5f9;
        }}
        
        .meta-card.trigger .meta-value {{
            color: #34d399;
        }}
        
        .meta-card.filter .meta-value {{
            color: #60a5fa;
        }}
        
        .meta-card.actions .meta-value {{
            color: #fbbf24;
        }}
        
        .diagram-container {{
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(71, 85, 105, 0.5);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 2rem;
            overflow-x: auto;
        }}
        
        .mermaid {{
            display: flex;
            justify-content: center;
        }}
        
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        
        .footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(71, 85, 105, 0.3);
            color: #64748b;
            font-size: 0.875rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .export-btn {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .export-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            h1 {{
                font-size: 1.5rem;
            }}
            
            .meta {{
                flex-direction: column;
            }}
            
            .meta-card {{
                min-width: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <span class="icon">🤖</span>
                {html.escape(automation.name)}
            </h1>
            <p class="description">{html.escape(automation.description or 'No description')}</p>
            
            <div class="meta">
                <div class="meta-card trigger">
                    <div class="meta-label">Trigger</div>
                    <div class="meta-value">🎯 {html.escape(trigger)}</div>
                </div>
                <div class="meta-card filter">
                    <div class="meta-label">Filter</div>
                    <div class="meta-value">🔍 {html.escape(filter_text) if filter_text else 'None'}</div>
                </div>
                <div class="meta-card actions">
                    <div class="meta-label">Actions</div>
                    <div class="meta-value">⚡ {action_count} {'branches' if isinstance(action_count, int) else ''}</div>
                </div>
            </div>
        </header>
        
        <div class="diagram-container">
            <pre class="mermaid">
{mermaid_code}
            </pre>
        </div>
        
        <footer>
            <span>Generated by Plane Automations</span>
            <button class="export-btn" onclick="exportSVG()">📥 Export SVG</button>
        </footer>
    </div>
    
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#3b82f6',
                primaryTextColor: '#f8fafc',
                primaryBorderColor: '#60a5fa',
                lineColor: '#64748b',
                secondaryColor: '#8b5cf6',
                tertiaryColor: '#1e293b',
                background: '#0f172a',
                mainBkg: '#1e293b',
                nodeBorder: '#475569',
                clusterBkg: '#1e293b',
                titleColor: '#f1f5f9',
                edgeLabelBackground: '#1e293b'
            }},
            flowchart: {{
                htmlLabels: true,
                curve: 'basis',
                padding: 20
            }}
        }});
        
        function exportSVG() {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{automation.name.lower().replace(" ", "-")}-flow.svg';
                a.click();
                URL.revokeObjectURL(url);
            }}
        }}
    </script>
</body>
</html>'''


# =============================================================================
# ASCII GENERATION
# =============================================================================

def generate_ascii(automation: AutomationDefinition) -> str:
    """
    Generate ASCII flowchart for terminal display.
    
    Args:
        automation: The automation to visualize
        
    Returns:
        ASCII art flowchart
    """
    lines = []
    width = 65
    
    # Header
    lines.append("╔" + "═" * width + "╗")
    title = f"🤖 {automation.name}"
    lines.append("║" + title.center(width) + "║")
    if automation.description:
        desc = automation.description[:width-4]
        lines.append("║" + desc.center(width) + "║")
    lines.append("╚" + "═" * width + "╝")
    lines.append("")
    
    # Trigger
    lines.append("  ┌" + "─" * 25 + "┐")
    lines.append("  │" + f"  🎯 TRIGGER".ljust(25) + "│")
    lines.append("  │" + f"  {automation.trigger_event}".ljust(25) + "│")
    lines.append("  └" + "─" * 12 + "┬" + "─" * 12 + "┘")
    lines.append("               │")
    lines.append("               ▼")
    
    # Filter
    if automation.when:
        filter_text = " & ".join(f"{k}={v}" for k, v in list(automation.when.items())[:2])
        if len(filter_text) > 20:
            filter_text = filter_text[:17] + "..."
        
        lines.append("  ┌" + "─" * 25 + "┐")
        lines.append("  │" + f"  🔍 FILTER".ljust(25) + "│")
        lines.append("  │" + f"  {filter_text}".ljust(25) + "│")
        lines.append("  └" + "─" * 12 + "┬" + "─" * 12 + "┘")
        lines.append("               │")
        lines.append("       ┌───────┴───────┐")
        lines.append("       │               │")
        lines.append("      Yes              No")
        lines.append("       │               │")
        lines.append("       ▼             [Skip]")
    
    lines.append("")
    
    # Actions
    if automation.script:
        lines.append("  ┌" + "─" * 40 + "┐")
        lines.append("  │" + f"  📜 SCRIPT".ljust(40) + "│")
        lines.append("  │" + f"  {automation.script}".ljust(40) + "│")
        lines.append("  └" + "─" * 40 + "┘")
    
    elif automation.do:
        lines.append("  ┌" + "─" * 55 + "┐")
        lines.append("  │" + "  CONDITIONS & ACTIONS".ljust(55) + "│")
        lines.append("  ├" + "─" * 55 + "┤")
        
        for i, action_def in enumerate(automation.do):
            if isinstance(action_def, dict):
                action = action_def
            else:
                action = action_def.model_dump(exclude_none=True)
            
            condition = action.get("when", "")
            is_otherwise = action.get("otherwise", False)
            
            # Condition line
            if condition:
                cond_display = condition[:40] + "..." if len(condition) > 40 else condition
                lines.append("  │" + f"  ❓ {cond_display}".ljust(55) + "│")
            elif is_otherwise:
                lines.append("  │" + f"  ↳ Otherwise:".ljust(55) + "│")
            
            # Action lines
            for key in ["set", "assign", "add_label", "notify", "comment"]:
                if key in action:
                    value = action[key]
                    if key == "set" and isinstance(value, dict):
                        for k, v in value.items():
                            lines.append("  │" + f"      → {k}: {v}".ljust(55) + "│")
                    elif key == "notify" and isinstance(value, dict):
                        target = value.get("channel") or value.get("to")
                        lines.append("  │" + f"      → notify: {target}".ljust(55) + "│")
                    else:
                        val_str = str(value)[:35]
                        lines.append("  │" + f"      → {key}: {val_str}".ljust(55) + "│")
            
            if i < len(automation.do) - 1:
                lines.append("  │" + " " * 55 + "│")
        
        lines.append("  └" + "─" * 55 + "┘")
    
    lines.append("")
    lines.append("               ▼")
    lines.append("          ✅ Complete")
    
    return "\n".join(lines)

