#!/usr/bin/env python3
"""Stop hook handler for Lore - Thin Client version.

Collects session data and syncs to cloud API.
"""

import asyncio
import json
import os
import sys

from lore.core.models import ContextCommit
from lore.hooks.state import clear_hook_state, get_hook_state
from lore.storage.cloud import CloudAuthError, LoreCloudClient, UsageLimitError


def main() -> None:
    """Handle stop hook - sync session to cloud."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        if not session_id:
            print(json.dumps({"continue": True}))
            return

        # Check for API key
        api_key = os.environ.get("LORE_API_KEY")
        if not api_key:
            print(json.dumps({"continue": True, "skipped": "no_api_key"}))
            return

        # Get session state
        state = get_hook_state(session_id, project_root=cwd)

        # Skip if no changes
        if not state.files_changed and not state.tool_calls:
            clear_hook_state(session_id)
            print(json.dumps({"continue": True, "skipped": "no_changes"}))
            return

        # Create simple intent from first message or default
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
            session_id=session_id,
        )

        # Sync to cloud
        client = LoreCloudClient(api_key=api_key)
        result = asyncio.run(client.sync_commits([commit]))

        # Clear session state
        clear_hook_state(session_id)

        print(json.dumps({
            "continue": True,
            "synced": result.get("synced", 1),
            "usage": result.get("usage", {}),
        }))

    except CloudAuthError as e:
        print(json.dumps({"continue": True, "error": str(e)}))
    except UsageLimitError as e:
        print(json.dumps({
            "continue": True,
            "error": "usage_limit",
            "current": e.current,
            "limit": e.limit,
        }))
    except Exception as e:
        print(json.dumps({"continue": True, "error": str(e)}))


if __name__ == "__main__":
    main()
