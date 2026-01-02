"""Config command for Lore."""

import typer
from rich.console import Console

app = typer.Typer(help="Manage Lore configuration")
console = Console()


@app.command("list")
def list_config() -> None:
    """List all configuration values."""
    from lore.core import get_config_manager

    try:
        manager = get_config_manager()
        if not manager.is_initialized:
            console.print("[red]Error:[/red] Lore not initialized")
            raise typer.Exit(1)

        config = manager.list_all()
        console.print_json(data=config)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command("get")
def get_config(
    key: str = typer.Argument(..., help="Config key (e.g., auto_commit.enabled)"),
) -> None:
    """Get a configuration value."""
    from lore.core import get_config_manager

    try:
        manager = get_config_manager()
        if not manager.is_initialized:
            console.print("[red]Error:[/red] Lore not initialized")
            raise typer.Exit(1)

        value = manager.get(key)
        console.print(f"{key} = {value}")

    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value."""
    from lore.core import get_config_manager

    try:
        manager = get_config_manager()
        if not manager.is_initialized:
            console.print("[red]Error:[/red] Lore not initialized")
            raise typer.Exit(1)

        manager.set(key, value)
        console.print(f"[green]✓[/green] Set {key} = {value}")

    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
