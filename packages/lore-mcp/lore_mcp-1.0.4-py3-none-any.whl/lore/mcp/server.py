"""MCP Server for Lore.

Thin client version - all operations go through Cloud API.
"""

import asyncio
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from lore.core.models import ContextCommit
from lore.storage.cloud import CloudAuthError, LoreCloudClient, UsageLimitError

# Create MCP server
mcp = FastMCP(
    name="lore",
    instructions=(
        "Version control for AI coding context. "
        "Use lore_commit to save context, lore_blame to find context for code, "
        "lore_search to search commits."
    ),
)


def _get_client() -> LoreCloudClient:
    """Get cloud client instance."""
    api_key = os.environ.get("LORE_API_KEY")
    if not api_key:
        raise CloudAuthError(
            "API key not configured. Set LORE_API_KEY environment variable "
            "or run: lore config set api_key YOUR_KEY"
        )
    return LoreCloudClient(api_key=api_key)


def _run_async(coro):
    """Run async function synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@mcp.tool()
def lore_commit(
    intent: str,
    files_changed: list[str] | None = None,
    decision: str = "",
    assumptions: list[str] | None = None,
    alternatives: list[str] | None = None,
) -> dict[str, Any]:
    """Create a context commit to record AI coding context.

    Args:
        intent: The primary goal or intent of the coding session
        files_changed: List of file paths that were modified
        decision: The decision or approach taken
        assumptions: Assumptions made during the session
        alternatives: Alternative approaches considered

    Returns:
        Dictionary with context_id and commit details
    """
    try:
        client = _get_client()

        commit = ContextCommit(
            intent=intent,
            files_changed=files_changed or [],
            decision=decision,
            assumptions=assumptions or [],
            alternatives=alternatives or [],
            model="claude",
        )

        result = _run_async(client.sync_commits([commit]))

        return {
            "success": True,
            "synced": result.get("synced", 1),
            "intent": intent,
            "files_changed": len(files_changed or []),
            "usage": result.get("usage", {}),
        }
    except CloudAuthError as e:
        return {"success": False, "error": str(e)}
    except UsageLimitError as e:
        return {
            "success": False,
            "error": "Usage limit exceeded",
            "current": e.current,
            "limit": e.limit,
            "upgrade_url": e.upgrade_url,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def lore_blame(
    file_path: str,
    line_number: int | None = None,
) -> dict[str, Any]:
    """Find the AI context that led to code changes.

    Args:
        file_path: Path to the file to query
        line_number: Optional specific line number

    Returns:
        Context information for the file/line
    """
    try:
        client = _get_client()
        results = _run_async(client.blame(file_path, line_number))

        if not results:
            return {
                "found": False,
                "message": f"No context found for {file_path}",
            }

        blame_results = []
        for r in results:
            blame_results.append(
                {
                    "context_id": r.context_id,
                    "intent": r.intent,
                    "decision": r.decision,
                    "model": r.model,
                    "created_at": r.created_at,
                }
            )

        return {
            "found": True,
            "file_path": file_path,
            "line_number": line_number,
            "results": blame_results,
        }
    except CloudAuthError as e:
        return {"found": False, "error": str(e)}
    except Exception as e:
        return {"found": False, "error": str(e)}


@mcp.tool()
def lore_search(
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Search context commits by intent or keywords.

    Args:
        query: Search query (matches intent, decision, alternatives)
        limit: Maximum number of results to return

    Returns:
        List of matching context commits
    """
    try:
        client = _get_client()
        results = _run_async(client.search(query, limit=limit))

        if not results:
            return {
                "found": False,
                "query": query,
                "message": "No matching contexts found",
            }

        search_results = []
        for r in results:
            search_results.append(
                {
                    "context_id": r.context_id,
                    "intent": r.intent,
                    "relevance_score": r.relevance_score,
                    "files_changed": r.files_changed,
                    "created_at": r.created_at,
                    "snippet": r.snippet,
                }
            )

        return {
            "found": True,
            "query": query,
            "count": len(search_results),
            "results": search_results,
        }
    except CloudAuthError as e:
        return {"found": False, "error": str(e)}
    except Exception as e:
        return {"found": False, "error": str(e)}


@mcp.tool()
def lore_init(force: bool = False) -> dict[str, Any]:
    """Initialize Lore by setting up Claude Code hooks.

    This configures automatic context capture in ~/.claude/settings.json.

    Args:
        force: Force re-setup even if hooks already configured

    Returns:
        Status of the initialization
    """
    import json
    from pathlib import Path

    claude_dir = Path.home() / ".claude"
    settings_file = claude_dir / "settings.json"

    hooks_config = {
        "PostToolUse": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": "uvx lore-mcp python -m lore.hooks.post_tool_use",
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
                        "command": "uvx lore-mcp python -m lore.hooks.on_stop",
                    }
                ],
            }
        ],
    }

    try:
        # Load existing settings
        settings = {}
        if settings_file.exists():
            with open(settings_file, encoding="utf-8") as f:
                settings = json.load(f)

        # Check if already configured
        if not force and "hooks" in settings:
            existing_hooks = settings.get("hooks", {})
            has_lore = any(
                "lore" in str(hook).lower()
                for hook_list in existing_hooks.values()
                for hook in hook_list
            )
            if has_lore:
                return {
                    "success": True,
                    "message": "Hooks already configured",
                    "path": str(settings_file),
                }

        # Add hooks
        if "hooks" not in settings:
            settings["hooks"] = {}

        for hook_type, hook_configs in hooks_config.items():
            if hook_type not in settings["hooks"]:
                settings["hooks"][hook_type] = []
            settings["hooks"][hook_type].extend(hook_configs)

        # Save settings
        claude_dir.mkdir(parents=True, exist_ok=True)
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        # Check API key status
        api_key = os.environ.get("LORE_API_KEY")

        return {
            "success": True,
            "message": "Hooks configured successfully",
            "path": str(settings_file),
            "api_key_configured": bool(api_key),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def lore_status() -> dict[str, Any]:
    """Get Lore status and usage information.

    Returns:
        Status information including plan and usage stats
    """
    try:
        client = _get_client()
        usage = _run_async(client.get_usage())
        health = _run_async(client.health_check())

        return {
            "connected": True,
            "plan": usage.get("plan", "free"),
            "usage": usage.get("usage", []),
            "user_id": health.get("user_id"),
        }
    except CloudAuthError as e:
        return {
            "connected": False,
            "error": str(e),
            "message": "Configure API key with: lore config set api_key YOUR_KEY",
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


def run_server() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run_server()
