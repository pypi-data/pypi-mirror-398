"""Authentication commands."""
import typer
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

app = typer.Typer(help="Authentication commands")
console = Console()

CONFIG_DIR = Path.home() / ".config" / "plane-cli"
TOKEN_FILE = CONFIG_DIR / "credentials"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> tuple[str, str]:
    """
    Load server URL and API key from configuration.
    
    Returns:
        tuple: (server_url, api_key)
        
    Raises:
        typer.Exit: If not authenticated
    """
    # Try to read from config file first (new format)
    server_url = "https://api.plane.so"  # default
    api_key = None
    
    if CONFIG_FILE.exists():
        try:
            config_data = json.loads(CONFIG_FILE.read_text())
            server_url = config_data.get("server_url", "https://api.plane.so")
            api_key = config_data.get("api_key")
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Fall back to TOKEN_FILE for backward compatibility
    if not api_key and TOKEN_FILE.exists():
        api_key = TOKEN_FILE.read_text().strip()
    
    if not api_key:
        console.print("[red]✗ Not authenticated[/red]")
        console.print("\nRun [cyan]plane auth login[/cyan] to authenticate")
        raise typer.Exit(1)
    
    return server_url, api_key


@app.command()
def login():
    """
    Authenticate with Plane using an API key.
    
    Get your API key from: https://app.plane.so/<workspace-slug>/settings/account/api-tokens/
    """
    console.print("\n[cyan]Plane CLI Authentication[/cyan]")
    console.print("[dim]Get your API key from: https://app.plane.so/<workspace-slug>/settings/account/api-tokens/[/dim]\n")
    
    # Prompt for server URL first
    server_url = Prompt.ask(
        "Enter your Plane server URL",
        default="api.plane.so"
    )
    
    # If empty string, use default
    if not server_url or server_url.strip() == "":
        server_url = "api.plane.so"
    
    # Ensure URL has https:// prefix
    if not server_url.startswith("http://") and not server_url.startswith("https://"):
        server_url = f"https://{server_url}"
    
    console.print(f"[dim]Using server: {server_url}[/dim]\n")
    
    api_key = Prompt.ask("Enter your Plane API key", password=True)
    
    if not api_key or len(api_key) < 20:
        console.print("[red]✗[/red] Invalid API key format")
        raise typer.Exit(1)
    
    # Test the API key
    try:
        from plane import PlaneClient
        client = PlaneClient(base_url=server_url, api_key=api_key)
        me = client.users.get_me()
        
        # Save the configuration
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save to config file (new format)
        config_data = {
            "server_url": server_url,
            "api_key": api_key
        }
        CONFIG_FILE.write_text(json.dumps(config_data, indent=2))
        CONFIG_FILE.chmod(0o600)
        
        # Also save to TOKEN_FILE for backward compatibility
        TOKEN_FILE.write_text(api_key)
        TOKEN_FILE.chmod(0o600)
        
        # Show success with user info
        console.print(f"\n[green]✓ Authenticated successfully![/green]")
        console.print(f"\n[bold]Logged in as:[/bold]")
        console.print(f"  Email: {me.email if hasattr(me, 'email') else 'N/A'}")
        console.print(f"  Name: {me.display_name if hasattr(me, 'display_name') else 'N/A'}")
        console.print(f"  Server: {server_url}")
        
    except Exception as e:
        console.print(f"\n[red]✗ Authentication failed:[/red] {e}")
        console.print("[yellow]Please check your server URL and API key, then try again[/yellow]")
        raise typer.Exit(1)


@app.command()
def logout():
    """Remove stored credentials."""
    removed = False
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        removed = True
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        removed = True
    
    if removed:
        console.print("[green]✓[/green] Logged out successfully")
        console.print("[dim]Run 'plane auth login' to authenticate again[/dim]")
    else:
        console.print("[yellow]No credentials stored[/yellow]")


@app.command()
def whoami():
    """Show current authentication status and user information."""
    server_url, api_key = load_config()
    
    try:
        from plane import PlaneClient
        client = PlaneClient(base_url=server_url, api_key=api_key)
        me = client.users.get_me()
        
        # Display user info in a panel
        info_text = f"""[bold]Email:[/bold] {me.email if hasattr(me, 'email') else 'N/A'}
[bold]Name:[/bold] {me.display_name if hasattr(me, 'display_name') else 'N/A'}
[bold]User ID:[/bold] {me.id if hasattr(me, 'id') else 'N/A'}
[bold]Server:[/bold] {server_url}

[dim]API Key:[/dim] [dim]{api_key[:10]}...{api_key[-4:]}[/dim]"""
        
        console.print()
        console.print(Panel(info_text, title="[green]✓ Authenticated[/green]", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        console.print("\n[yellow]Your API key may be invalid or expired[/yellow]")
        console.print("Run [cyan]plane auth login[/cyan] to re-authenticate")
        raise typer.Exit(1)
