"""Init command for Lore - Sets up global hooks."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console

console = Console()

HOOKS_CONFIG = {
    "PostToolUse": [
        {
            "matcher": "*",
            "hooks": [
                {
                    "type": "command",
                    "command": "uvx --from lore-mcp python -m lore.hooks.post_tool_use",
                }
            ],
        }
    ],
    "Stop": [
        {
            "matcher": "*",
            "hooks": [
                {
                    "type": "command",
                    "command": "uvx --from lore-mcp python -m lore.hooks.on_stop",
                }
            ],
        }
    ],
}


def get_claude_settings_path() -> Path:
    """Get path to Claude Code settings file."""
    return Path.home() / ".claude" / "settings.json"


def load_claude_settings() -> dict:
    """Load existing Claude settings or return empty dict."""
    settings_path = get_claude_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_claude_settings(settings: dict) -> None:
    """Save Claude settings."""
    settings_path = get_claude_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def setup_global_hooks() -> bool:
    """Add Lore hooks to global Claude settings.

    Returns:
        True if hooks were added, False if already configured.
    """
    settings = load_claude_settings()

    # Check if hooks already exist
    existing_hooks = settings.get("hooks", {})

    # Check if Lore hooks are already configured
    lore_configured = False
    for hook_type in ["PostToolUse", "Stop"]:
        for hook_config in existing_hooks.get(hook_type, []):
            for hook in hook_config.get("hooks", []):
                if "lore" in hook.get("command", "").lower():
                    lore_configured = True
                    break

    if lore_configured:
        return False

    # Merge hooks
    if "hooks" not in settings:
        settings["hooks"] = {}

    for hook_type, hook_configs in HOOKS_CONFIG.items():
        if hook_type not in settings["hooks"]:
            settings["hooks"][hook_type] = []
        settings["hooks"][hook_type].extend(hook_configs)

    save_claude_settings(settings)
    return True


def init_command(
    hooks: bool = typer.Option(True, "--hooks/--no-hooks", help="Set up global Claude hooks"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-setup even if already configured"
    ),
) -> None:
    """Initialize Lore for your system.

    Sets up global Claude Code hooks for automatic context capture.
    """
    console.print("\n[bold blue]🔮 Lore MCP Setup[/bold blue]\n")

    # Check API key
    api_key = os.environ.get("LORE_API_KEY")
    if api_key:
        console.print("[green]✓[/green] API key configured")
    else:
        console.print("[yellow]![/yellow] API key not set. Run:")
        console.print("  [dim]export LORE_API_KEY=lore_xxxxxxxx[/dim]")
        console.print(
            "  [dim]# Get your key at: https://lore-dashboard.jadecon2655.workers.dev/api-keys[/dim]\n"
        )

    # Set up hooks
    if hooks:
        if force or setup_global_hooks():
            console.print("[green]✓[/green] Global hooks configured")
            console.print("  [dim]Location: ~/.claude/settings.json[/dim]")
        else:
            console.print("[green]✓[/green] Hooks already configured")
    else:
        console.print("[dim]○[/dim] Hooks setup skipped (--no-hooks)")

    console.print("\n[bold green]Lore is ready![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Start a Claude Code session")
    console.print("  2. Your context will be automatically captured")
    console.print("  3. View at: [link]https://lore-dashboard.jadecon2655.workers.dev[/link]")
    console.print()
