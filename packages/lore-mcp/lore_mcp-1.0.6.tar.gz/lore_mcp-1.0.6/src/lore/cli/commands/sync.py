"""Sync command for Lore - Thin Client version.

In the thin client version, syncing is automatic via hooks.
This command shows status and usage information.
"""

import asyncio
import os

import typer
from rich.console import Console
from rich.table import Table

from lore.storage.cloud import (
    CloudAuthError,
    LoreCloudClient,
)

console = Console()


def sync_command() -> None:
    """Show sync status.

    In the cloud version, syncing happens automatically via hooks.
    This command shows your current sync status and usage.
    """
    api_key = os.environ.get("LORE_API_KEY")

    if not api_key:
        console.print(
            "[yellow]Note:[/yellow] API key not configured.\n"
            "Set your API key: [cyan]export LORE_API_KEY=your_key[/cyan]\n"
            "Get an API key at: [link]https://lore-dashboard.jadecon2655.workers.dev/api-keys[/link]"
        )
        raise typer.Exit(1)

    try:
        client = LoreCloudClient(api_key=api_key)
        result = asyncio.run(client.get_usage())

        console.print("\n[green]✓[/green] Connected to Lore Cloud")
        console.print("[dim]Syncing is automatic via Claude Code hooks.[/dim]\n")

        plan = result.get("plan", "free")
        period = result.get("period", "")
        usage_data = result.get("usage", [])

        console.print(f"[bold]Plan:[/bold] {plan.capitalize()}")
        console.print(f"[bold]Period:[/bold] {period}\n")

        table = Table(show_header=True)
        table.add_column("Action")
        table.add_column("Used", justify="right")
        table.add_column("Limit", justify="right")

        for stat in usage_data:
            action = stat.get("action", "")
            current = stat.get("current_count", 0)
            limit_count = stat.get("limit_count", -1)
            limit_str = "∞" if limit_count == -1 else str(limit_count)

            table.add_row(action.capitalize(), str(current), limit_str)

        console.print(table)

    except CloudAuthError as e:
        console.print(f"[red]Authentication error:[/red] {e}")
        raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


def usage_command() -> None:
    """Show current cloud usage statistics."""
    api_key = os.environ.get("LORE_API_KEY")

    if not api_key:
        console.print(
            "[red]Error:[/red] API key not configured.\n"
            "Set your API key: [cyan]export LORE_API_KEY=your_key[/cyan]"
        )
        raise typer.Exit(1)

    client = LoreCloudClient(api_key=api_key)

    try:
        result = asyncio.run(client.get_usage())

        plan = result.get("plan", "free")
        period = result.get("period", "")
        usage_data = result.get("usage", [])

        console.print(f"\n[bold]Plan:[/bold] {plan.capitalize()}")
        console.print(f"[bold]Period:[/bold] {period}\n")

        table = Table(show_header=True)
        table.add_column("Action")
        table.add_column("Used", justify="right")
        table.add_column("Limit", justify="right")
        table.add_column("Remaining", justify="right")

        for stat in usage_data:
            action = stat.get("action", "")
            current = stat.get("current_count", 0)
            limit_count = stat.get("limit_count", -1)

            if limit_count == -1:
                remaining = "∞"
                limit_str = "∞"
            else:
                remaining = str(max(0, limit_count - current))
                limit_str = str(limit_count)

            table.add_row(
                action.capitalize(),
                str(current),
                limit_str,
                remaining,
            )

        console.print(table)

    except CloudAuthError as e:
        console.print(f"[red]Authentication error:[/red] {e}")
        raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
