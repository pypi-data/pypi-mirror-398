"""Claude Code hook handlers for Lore - Thin Client version."""

from lore.hooks.on_stop import main as handle_stop
from lore.hooks.post_tool_use import main as handle_post_tool_use
from lore.hooks.state import (
    HookState,
    add_file_change,
    add_tool_call,
    clear_hook_state,
    get_hook_state,
    save_hook_state,
)

__all__ = [
    # State management
    "HookState",
    "get_hook_state",
    "save_hook_state",
    "clear_hook_state",
    "add_file_change",
    "add_tool_call",
    # Handlers
    "handle_post_tool_use",
    "handle_stop",
]
