"""Blame command for Lore - Thin Client version."""

import asyncio
import os

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def parse_file_line(file_spec: str) -> tuple[str, int | None, int | None]:
    """Parse file:line or file:start-end format."""
    if ":" not in file_spec:
        return file_spec, None, None

    parts = file_spec.rsplit(":", 1)
    file_path = parts[0]
    line_spec = parts[1]

    if "-" in line_spec:
        start, end = line_spec.split("-", 1)
        return file_path, int(start), int(end)
    else:
        line = int(line_spec)
        return file_path, line, line


def blame_command(
    file_spec: str = typer.Argument(..., help="File path (e.g., src/api.py:42)"),
) -> None:
    """Show context for a file or specific line."""
    from lore.storage.cloud import CloudAuthError, LoreCloudClient

    try:
        # Check API key
        api_key = os.environ.get("LORE_API_KEY")
        if not api_key:
            console.print("[red]Error:[/red] API key not configured")
            console.print("Set LORE_API_KEY environment variable or run:")
            console.print("  lore config set api_key YOUR_KEY")
            raise typer.Exit(1)

        client = LoreCloudClient(api_key=api_key)
        file_path, line_start, _ = parse_file_line(file_spec)

        results = asyncio.run(client.blame(file_path, line_start))

        if not results:
            console.print(f"[yellow]No context found for {file_spec}[/yellow]")
            return

        for result in results:
            created_at = (
                result.created_at
                if isinstance(result.created_at, str)
                else result.created_at.strftime("%Y-%m-%d %H:%M")
            )

            panel_content = f"""[bold]Intent:[/bold] {result.intent}
[bold]Decision:[/bold] {result.decision or '(none)'}
[bold]Model:[/bold] {result.model or 'unknown'}
[bold]Created:[/bold] {created_at}"""

            console.print(
                Panel(
                    panel_content,
                    title=f"Context: {result.context_id}",
                    border_style="blue",
                )
            )

    except typer.Exit:
        raise
    except CloudAuthError as e:
        console.print(f"[red]Auth Error:[/red] {e}")
        raise typer.Exit(1) from None
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid file specification: {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
