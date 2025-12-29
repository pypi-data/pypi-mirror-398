"""Search command for Lore - Thin Client version."""

import asyncio
import os

import typer
from rich.console import Console

console = Console()


def search_command(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum results"),
) -> None:
    """Search contexts by natural language query."""
    from lore.storage.cloud import CloudAuthError, LoreCloudClient, UsageLimitError

    try:
        # Check API key
        api_key = os.environ.get("LORE_API_KEY")
        if not api_key:
            console.print("[red]Error:[/red] API key not configured")
            console.print("Set LORE_API_KEY environment variable or run:")
            console.print("  lore config set api_key YOUR_KEY")
            raise typer.Exit(1)

        client = LoreCloudClient(api_key=api_key)
        results = asyncio.run(client.search(query, limit=limit))

        if not results:
            console.print(f"[yellow]No results found for '{query}'[/yellow]")
            return

        console.print(f'\nFound {len(results)} results for "{query}":\n')

        for i, result in enumerate(results, 1):
            files_str = ", ".join(result.files_changed[:3])
            if len(result.files_changed) > 3:
                files_str += f" (+{len(result.files_changed) - 3} more)"

            console.print(
                f"[bold]{i}.[/bold] {result.context_id} "
                f"[dim](relevance: {result.relevance_score:.2f})[/dim]"
            )
            console.print(f"   [green]Intent:[/green] {result.intent}")
            if files_str:
                console.print(f"   [blue]Files:[/blue] {files_str}")
            console.print()

    except typer.Exit:
        raise
    except CloudAuthError as e:
        console.print(f"[red]Auth Error:[/red] {e}")
        raise typer.Exit(1) from None
    except UsageLimitError as e:
        console.print(f"[red]Usage Limit:[/red] {e.current}/{e.limit}")
        console.print(f"Upgrade at: {e.upgrade_url}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
