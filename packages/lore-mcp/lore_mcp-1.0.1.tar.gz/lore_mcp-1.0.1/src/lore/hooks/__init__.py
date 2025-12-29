"""Claude Code hook handlers for Lore."""

from lore.hooks.on_stop import handle_stop
from lore.hooks.post_tool_use import handle_post_tool_use
from lore.hooks.session_start import handle_session_start
from lore.hooks.state import (
    HookState,
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
    # Handlers
    "handle_session_start",
    "handle_post_tool_use",
    "handle_stop",
]
