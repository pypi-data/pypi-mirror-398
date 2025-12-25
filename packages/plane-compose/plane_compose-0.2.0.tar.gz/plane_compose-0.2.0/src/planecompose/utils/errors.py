"""Shared error handling utilities for CLI commands.

Provides consistent, user-friendly error messages across all CLI commands.
"""
from rich.console import Console
from rich.panel import Panel

from planecompose.exceptions import (
    PlaneComposeError,
    APIError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    ConfigError,
    ValidationError,
    NetworkError,
)

console = Console()


def handle_api_error(error: Exception, context: str = "") -> None:
    """
    Handle API errors with helpful, user-friendly messages.
    
    Args:
        error: The exception that was raised
        context: Optional context about what operation was being performed
    """
    error_msg = str(error)
    
    if isinstance(error, AuthenticationError) or "401" in error_msg or "Unauthorized" in error_msg:
        _show_auth_error()
    elif isinstance(error, PermissionError) or "403" in error_msg or "Forbidden" in error_msg:
        _show_permission_error(context)
    elif isinstance(error, NotFoundError) or "404" in error_msg or "Not Found" in error_msg:
        _show_not_found_error(context)
    elif isinstance(error, RateLimitError) or "429" in error_msg:
        _show_rate_limit_error(error)
    elif isinstance(error, NetworkError) or "Connection" in error_msg:
        _show_network_error(error)
    elif isinstance(error, ConfigError):
        _show_config_error(error)
    elif isinstance(error, ValidationError):
        _show_validation_error(error)
    else:
        _show_generic_error(error)


def _show_auth_error() -> None:
    """Show authentication error message."""
    console.print("\n[red]✗ Authentication Failed (401)[/red]")
    console.print("\nYour API key is invalid or expired.")
    console.print("\n[yellow]Solution:[/yellow]")
    console.print("  Run [cyan]plane auth login[/cyan] to re-authenticate")
    console.print("\n[dim]Get your API key from: https://app.plane.so/<workspace-slug>/settings/account/api-tokens/[/dim]")


def _show_permission_error(context: str) -> None:
    """Show permission denied error message."""
    console.print("\n[red]✗ Permission Denied (403)[/red]")
    
    if context:
        console.print(f"\nYou don't have permission to {context}.")
    else:
        console.print("\nYou don't have permission for this operation.")
    
    console.print("\n[yellow]Solutions:[/yellow]")
    console.print("  • Verify you're a member/admin of the workspace")
    console.print("  • Use a workspace where you have proper permissions")
    console.print("  • Check with your workspace administrator")
    console.print("\nRun [cyan]plane auth whoami[/cyan] to verify your access")


def _show_not_found_error(context: str) -> None:
    """Show not found error message."""
    console.print("\n[red]✗ Not Found (404)[/red]")
    
    console.print("\nThe resource doesn't exist or you don't have access to it.")
    
    console.print("\n[yellow]Check:[/yellow]")
    console.print("  • Workspace name in plane.yaml is correct")
    console.print("  • Project key/UUID in plane.yaml is valid")
    console.print("  • You have access to this workspace/project")
    
    if "project" in context.lower() or not context:
        console.print("\n[dim]Tip: Run [cyan]plane schema push[/cyan] to create a new project[/dim]")


def _show_rate_limit_error(error: Exception) -> None:
    """Show rate limit error message."""
    console.print("\n[red]✗ Rate Limit Exceeded (429)[/red]")
    console.print("\nToo many API requests. Please wait and try again.")
    
    retry_after = getattr(error, 'retry_after', None)
    if retry_after:
        console.print(f"\n[yellow]Retry after:[/yellow] {retry_after} seconds")
    
    console.print("\n[yellow]Solutions:[/yellow]")
    console.print("  • Wait a minute before retrying")
    console.print("  • Run [cyan]plane rate stats[/cyan] to check usage")
    console.print("  • Reduce batch size or use --dry-run first")
    console.print("\n[dim]Rate limit: 50 requests/minute (configurable via PLANE_RATE_LIMIT_PER_MINUTE)[/dim]")


def _show_network_error(error: Exception) -> None:
    """Show network error message."""
    console.print("\n[red]✗ Network Error[/red]")
    console.print(f"\nCould not connect to Plane API: {error}")
    
    console.print("\n[yellow]Check:[/yellow]")
    console.print("  • Your internet connection")
    console.print("  • The API URL in plane.yaml (default: https://api.plane.so)")
    console.print("  • Any firewall or proxy settings")


def _show_config_error(error: Exception) -> None:
    """Show configuration error message."""
    console.print("\n[red]✗ Configuration Error[/red]")
    console.print(f"\n{error}")
    
    console.print("\n[yellow]Check:[/yellow]")
    console.print("  • plane.yaml exists and is valid YAML")
    console.print("  • Required fields (workspace, project.key) are set")
    console.print("  • Schema files in schema/ are valid")


def _show_validation_error(error: ValidationError) -> None:
    """Show validation error message."""
    console.print("\n[red]✗ Validation Error[/red]")
    
    if error.field:
        console.print(f"\nInvalid value for field: [cyan]{error.field}[/cyan]")
    
    console.print(f"\n{error.message}")
    
    if error.details:
        console.print("\n[dim]Details:[/dim]")
        for key, value in error.details.items():
            console.print(f"  {key}: {value}")


def _show_generic_error(error: Exception) -> None:
    """Show generic error message."""
    console.print(f"\n[red]✗ Error:[/red] {error}")
    console.print("\n[dim]If this error persists, please report it at:[/dim]")
    console.print("[dim]https://github.com/makeplane/compose/issues[/dim]")


def show_project_not_found(workspace: str, project_key: str, available_projects: list = None) -> None:
    """
    Show a helpful error when project key doesn't exist.
    
    Args:
        workspace: Workspace slug
        project_key: Project key that wasn't found
        available_projects: List of available projects (optional)
    """
    error_lines = [
        f"Project '[cyan]{project_key.upper()}[/cyan]' not found in workspace '[cyan]{workspace}[/cyan]'.",
        "",
        "[yellow]Available projects:[/yellow]",
    ]
    
    if available_projects:
        for p in available_projects[:10]:  # Limit to 10
            name = getattr(p, 'name', str(p))
            identifier = getattr(p, 'identifier', '')
            if identifier:
                error_lines.append(f"  • {name} ([cyan]{identifier}[/cyan])")
            else:
                error_lines.append(f"  • {name}")
        
        if len(available_projects) > 10:
            error_lines.append(f"  ... and {len(available_projects) - 10} more")
    else:
        error_lines.append("  [dim](no projects found)[/dim]")
    
    error_lines.extend([
        "",
        "[yellow]Solutions:[/yellow]",
        "  1. Fix the 'key' in plane.yaml to match an existing project",
        "  2. Or run [cyan]plane schema push[/cyan] to create the project",
    ])
    
    console.print()
    console.print(Panel(
        "\n".join(error_lines),
        title="[red]Project Not Found[/red]",
        border_style="red",
    ))


def show_success(message: str, details: list[str] = None) -> None:
    """
    Show a success message with optional details.
    
    Args:
        message: Main success message
        details: Optional list of detail lines
    """
    console.print(f"\n[bold green]✓ {message}[/bold green]")
    
    if details:
        for detail in details:
            console.print(f"  {detail}")


def show_warning(message: str, suggestions: list[str] = None) -> None:
    """
    Show a warning message with optional suggestions.
    
    Args:
        message: Warning message
        suggestions: Optional list of suggestions
    """
    console.print(f"\n[yellow]⚠ Warning:[/yellow] {message}")
    
    if suggestions:
        console.print("\n[dim]Suggestions:[/dim]")
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")

