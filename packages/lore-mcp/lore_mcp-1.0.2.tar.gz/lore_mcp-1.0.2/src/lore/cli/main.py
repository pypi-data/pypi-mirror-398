"""CLI entry point for Lore - Thin Client version."""

import asyncio
import os

import typer
from rich.console import Console

from lore import __version__
from lore.cli.commands import blame, commit, config, init, search, sync

app = typer.Typer(
    name="lore",
    help="Lore - Version control for AI coding context (Cloud)",
    no_args_is_help=True,
)

console = Console()

# Register config subcommand
app.add_typer(config.app, name="config", help="Manage configuration")


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"Lore v{__version__} (Cloud)")


# Register main commands
app.command(name="init")(init.init_command)
app.command(name="commit")(commit.commit_command)
app.command(name="blame")(blame.blame_command)
app.command(name="search")(search.search_command)
app.command(name="sync")(sync.sync_command)
app.command(name="usage")(sync.usage_command)


@app.command()
def status() -> None:
    """Show Lore cloud connection status."""
    from lore.storage.cloud import CloudAuthError, LoreCloudClient

    api_key = os.environ.get("LORE_API_KEY")
    if not api_key:
        console.print("[yellow]Not connected[/yellow]")
        console.print("Set LORE_API_KEY environment variable or run:")
        console.print("  lore config set api_key YOUR_KEY")
        return

    try:
        client = LoreCloudClient(api_key=api_key)
        usage = asyncio.run(client.get_usage())

        console.print("[green]Connected to Lore Cloud[/green]")
        console.print(f"  Plan: {usage.get('plan', 'free')}")

        for stat in usage.get("usage", []):
            action = stat.get("action", "unknown")
            current = stat.get("current_count", 0)
            limit = stat.get("limit_count", -1)
            limit_str = str(limit) if limit > 0 else "unlimited"
            console.print(f"  {action}: {current}/{limit_str}")

    except CloudAuthError as e:
        console.print(f"[red]Auth Error:[/red] {e}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def login() -> None:
    """Open dashboard to get API key."""
    import webbrowser
    url = "https://lore-dashboard.jadecon2655.workers.dev/api-keys"
    console.print(f"Opening {url}")
    webbrowser.open(url)
    console.print("\nAfter getting your API key, run:")
    console.print("  export LORE_API_KEY=your_key_here")


if __name__ == "__main__":
    app()
