"""Commit command for Lore - Thin Client version."""

import os

import typer
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def commit_command(
    message: str | None = typer.Option(None, "--message", "-m", help="Intent message"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-extract from current session"),
    session_id: str | None = typer.Option(
        None, "--session", "-s", help="Session ID for auto-extraction"
    ),
) -> None:
    """Create a context commit and sync to cloud."""
    from lore.core.models import ContextCommit
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

        # Auto-extraction mode
        if auto:
            sid = session_id or os.environ.get("CLAUDE_SESSION_ID", "")
            if not sid:
                console.print("[red]Error:[/red] No session ID provided")
                console.print("Use --session or set CLAUDE_SESSION_ID environment variable")
                raise typer.Exit(1)

            from lore.hooks.state import clear_hook_state, get_hook_state

            # Get project root from current dir
            project_root = os.getcwd()
            state = get_hook_state(sid, project_root=project_root)

            if not state.files_changed and not state.tool_calls:
                console.print("[yellow]Warning:[/yellow] No changes in session to commit")
                raise typer.Exit(0)

            # Simple intent extraction from first message
            intent = "AI coding session"
            if state.messages:
                first_msg = state.messages[0] if state.messages else None
                if first_msg and isinstance(first_msg, dict):
                    content = first_msg.get("content", "")
                    if isinstance(content, str) and len(content) > 10:
                        intent = content[:200] + "..." if len(content) > 200 else content

            # Create commit
            commit = ContextCommit(
                intent=intent,
                files_changed=state.files_changed,
                model="claude",
                session_id=sid,
            )

            # Sync to cloud
            import asyncio
            result = asyncio.run(client.sync_commits([commit]))

            # Clear session state
            clear_hook_state(sid)

            console.print(f"[green]✓[/green] Context synced to cloud")
            console.print(f"  Intent: {intent[:80]}...")
            console.print(f"  Files: {len(state.files_changed)}")
            console.print(f"  Usage: {result.get('usage', {})}")
            return

        # Interactive mode
        if interactive:
            intent = Prompt.ask("Intent")
            decision = Prompt.ask("Decision", default="")
            assumptions_str = Prompt.ask("Assumptions (comma-separated)", default="")
            assumptions = [a.strip() for a in assumptions_str.split(",") if a.strip()]
        elif message:
            intent = message
            decision = ""
            assumptions = []
        else:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  lore commit -m 'intent message'  # Manual with message")
            console.print("  lore commit -i                   # Interactive mode")
            console.print("  lore commit -a -s SESSION_ID     # Auto from session")
            raise typer.Exit(1)

        # Create commit
        commit = ContextCommit(
            intent=intent,
            decision=decision,
            assumptions=assumptions,
        )

        # Sync to cloud
        import asyncio
        result = asyncio.run(client.sync_commits([commit]))

        console.print(f"[green]✓[/green] Context synced to cloud")
        console.print(f"  Intent: {intent}")
        console.print(f"  Usage: {result.get('usage', {})}")

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
