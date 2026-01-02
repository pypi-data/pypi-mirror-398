#!/usr/bin/env python3
"""Post tool use hook handler for Lore - Thin Client version.

Tracks file changes during AI coding session.
"""

import json
import os
import sys

from lore.hooks.state import add_file_change, add_tool_call


def main() -> None:
    """Handle post tool use hook - track changes."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        session_id = input_data.get("session_id", "")
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        cwd = input_data.get("cwd", os.getcwd())

        if not session_id:
            print(json.dumps({"continue": True}))
            return

        # Track tool call
        add_tool_call(session_id, tool_name, tool_input, project_root=cwd)

        # Track file changes for write/edit tools
        if tool_name in ("Write", "Edit", "MultiEdit"):
            file_path = tool_input.get("file_path", "")
            if file_path:
                add_file_change(session_id, file_path, project_root=cwd)

        print(json.dumps({"continue": True}))

    except Exception as e:
        # Always continue even on error
        print(json.dumps({"continue": True, "error": str(e)}))


if __name__ == "__main__":
    main()
