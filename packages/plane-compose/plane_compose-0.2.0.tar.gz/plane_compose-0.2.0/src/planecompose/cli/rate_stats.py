"""Display rate limit statistics."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from planecompose.backend.plane import PlaneBackend

console = Console()

app = typer.Typer(help="Rate limit statistics and monitoring")


def _get_rate_limiter():
    """Get the shared rate limiter instance from PlaneBackend."""
    return PlaneBackend._rate_limiter


@app.command(name="stats")
def stats():
    """Display current rate limit statistics."""
    stats = _get_rate_limiter().get_stats()
    
    # Create stats table
    table = Table(title="Rate Limit Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Requests", str(stats['total_requests']))
    table.add_row("Requests (Last Minute)", str(stats['requests_last_minute']))
    table.add_row("Requests (Last Hour)", str(stats['requests_last_hour']))
    table.add_row("Rate Limit (Minute)", f"{stats['limit_per_minute']}/min")
    table.add_row("Rate Limit (Hour)", f"{stats['limit_per_hour']}/hour")
    table.add_row("Utilization (Minute)", stats['utilization_minute'])
    table.add_row("Utilization (Hour)", stats['utilization_hour'])
    table.add_row("Total Wait Time", stats['total_wait_time'])
    table.add_row("Avg Wait per Request", stats['avg_wait_per_request'])
    
    console.print()
    console.print(table)
    console.print()
    
    # Calculate requests per second
    if stats['total_requests'] > 0:
        rpm = stats['limit_per_minute']
        rps = rpm / 60.0
        console.print(Panel(
            f"[bold]Rate Limit Configuration[/bold]\n\n"
            f"• Max requests/minute: [cyan]{stats['limit_per_minute']}[/cyan]\n"
            f"• Max requests/hour: [cyan]{stats['limit_per_hour']}[/cyan]\n"
            f"• Max requests/second: [cyan]{rps:.2f}[/cyan]\n"
            f"• Safety margin: [green]83%[/green] of Plane's 3600/hour limit\n"
            f"• Min interval: [cyan]{1/rps:.3f}s[/cyan] between requests",
            title="Configuration",
            border_style="blue",
        ))
    
    # Show warning if utilization is high (check per-minute utilization)
    utilization_pct = float(stats['utilization_minute'].rstrip('%'))
    if utilization_pct > 80:
        console.print("\n[yellow]⚠ Warning:[/yellow] Rate limit utilization is high (>80%)")
        console.print("[dim]Consider spreading operations over a longer time period[/dim]")
    elif utilization_pct > 50:
        console.print("\n[blue]ℹ️  Info:[/blue] Moderate rate limit usage")
    else:
        console.print("\n[green]✓[/green] Rate limit usage is healthy")


@app.command(name="reset")
def reset():
    """Reset rate limit statistics (does not reset actual rate limiting)."""
    _get_rate_limiter().reset()
    console.print("[green]✓[/green] Rate limit statistics reset")
    console.print("[dim]Note: This only resets counters, not the actual rate limiting[/dim]")
