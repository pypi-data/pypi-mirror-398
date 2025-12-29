"""Sync command for cloud synchronization."""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from lore.core.config import get_config_manager
from lore.storage.cloud import (
    CloudAuthError,
    LoreCloudClient,
    UsageLimitError,
)
from lore.storage.sqlite import ContextStorage

console = Console()


def sync_command(
    all_commits: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Sync all commits (not just unsynced)",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-l",
        help="Maximum commits to sync per batch",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be synced without syncing",
    ),
) -> None:
    """Sync local commits to Lore Cloud.

    Requires an API key. Set with: lore config set cloud.api_key YOUR_KEY
    """
    import asyncio
    import os

    config_manager = get_config_manager()
    config = config_manager.load()
    api_key = config.api_key or os.environ.get("LORE_API_KEY")

    if not api_key:
        console.print(
            "[red]Error:[/red] API key not configured.\n"
            "Set your API key with: [cyan]lore config set cloud.api_key YOUR_KEY[/cyan]\n"
            "Get an API key at: [link]https://lore.dev/api-keys[/link]"
        )
        raise typer.Exit(1)

    storage = ContextStorage(config_manager.db_path)

    # Get commits to sync
    if all_commits:
        commits = storage.list_commits(limit=limit)
    else:
        # TODO: Add synced_at tracking to only sync new commits
        commits = storage.list_commits(limit=limit)

    if not commits:
        console.print("[yellow]No commits to sync.[/yellow]")
        return

    if dry_run:
        console.print(f"[cyan]Would sync {len(commits)} commit(s):[/cyan]")
        table = Table(show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("Intent")
        table.add_column("Created")

        for commit in commits[:10]:
            table.add_row(
                commit.context_id[:12] + "...",
                commit.intent[:50] + ("..." if len(commit.intent) > 50 else ""),
                commit.created_at.strftime("%Y-%m-%d %H:%M") if commit.created_at else "N/A",
            )

        if len(commits) > 10:
            table.add_row("...", f"(+{len(commits) - 10} more)", "")

        console.print(table)
        return

    # Sync to cloud
    client = LoreCloudClient(api_key=api_key)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Syncing {len(commits)} commit(s)...", total=None)

        try:
            result = asyncio.run(client.sync_commits(commits))
            progress.update(task, completed=True)

            synced = result.get("synced", 0)
            usage = result.get("usage", {})

            console.print(f"\n[green]✓[/green] Synced {synced} commit(s) to cloud")

            if usage:
                current = usage.get("current", 0)
                limit_count = usage.get("limit", -1)
                if limit_count > 0:
                    percentage = (current / limit_count) * 100
                    color = "green" if percentage < 70 else "yellow" if percentage < 90 else "red"
                    console.print(
                        f"  Usage: [{color}]{current}/{limit_count}[/{color}] syncs this month"
                    )

        except CloudAuthError as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Authentication error:[/red] {e}")
            console.print("Check your API key with: [cyan]lore config get api_key[/cyan]")
            raise typer.Exit(1) from None

        except UsageLimitError as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Usage limit exceeded:[/red] {e.current}/{e.limit} syncs")
            console.print(f"Upgrade your plan at: [link]{e.upgrade_url}[/link]")
            raise typer.Exit(1) from None

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Sync failed:[/red] {e}")
            raise typer.Exit(1) from None


def usage_command() -> None:
    """Show current cloud usage statistics."""
    import asyncio
    import os

    config_manager = get_config_manager()
    config = config_manager.load()
    api_key = config.api_key or os.environ.get("LORE_API_KEY")

    if not api_key:
        console.print(
            "[red]Error:[/red] API key not configured.\n"
            "Set your API key with: [cyan]lore config set cloud.api_key YOUR_KEY[/cyan]"
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
