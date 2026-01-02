"""Shared state management for Claude Code hooks.

This module provides a simple file-based state that persists across hook invocations
within the same Claude Code session.
"""

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from lore.core.models import Message


@dataclass
class HookState:
    """State shared across hook invocations in a session."""

    session_id: str
    project_root: str
    messages: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    git_commits: list[dict] = field(default_factory=list)  # Commits made during session
    pending_files: list[str] = field(default_factory=list)  # Files changed since last commit
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the state."""
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_tool_call(
        self,
        tool_name: str,
        tool_input: dict,
        tool_output: str | None = None,
    ) -> None:
        """Add a tool call to the state."""
        self.tool_calls.append(
            {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_file_change(self, file_path: str) -> None:
        """Add a changed file."""
        if file_path not in self.files_changed:
            self.files_changed.append(file_path)
        # Also track as pending (not yet committed to git)
        if file_path not in self.pending_files:
            self.pending_files.append(file_path)

    def record_git_commit(
        self,
        commit_hash: str,
        message: str = "",
        files: list[str] | None = None,
        is_amend: bool = False,
    ) -> None:
        """Record a git commit made during this session.

        Associates pending file changes with this commit.

        Args:
            commit_hash: The full git commit hash
            message: Commit message
            files: List of files in this commit (uses pending_files if None)
            is_amend: If True, updates the most recent commit instead of adding new
        """
        # Use provided files or current pending files
        committed_files = files if files is not None else list(self.pending_files)

        if is_amend and self.git_commits:
            # Update the most recent commit with the new hash
            last_commit = self.git_commits[-1]
            last_commit["commit_hash"] = commit_hash
            if message:
                last_commit["message"] = message
            last_commit["timestamp"] = datetime.now().isoformat()
            last_commit["amended"] = True
            # Update file list with any new pending files
            existing_files = set(last_commit.get("files", []))
            existing_files.update(committed_files)
            last_commit["files"] = sorted(list(existing_files))
        else:
            self.git_commits.append(
                {
                    "commit_hash": commit_hash,
                    "files": committed_files,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Clear pending files that were committed (for both new and amend cases)
        if files is None:
            self.pending_files = []
        else:
            self.pending_files = [f for f in self.pending_files if f not in files]

    def get_commit_for_files(self, files: list[str]) -> str | None:
        """Get the most recent git commit that includes any of the given files.

        Returns commit hash if found, None otherwise.
        """
        if not self.git_commits:
            return None

        # Search commits in reverse order (most recent first)
        for commit in reversed(self.git_commits):
            commit_files = set(commit.get("files", []))
            if commit_files.intersection(files):
                return commit.get("commit_hash")

        return None

    def get_latest_session_commit(self) -> str | None:
        """Get the most recent git commit made during this session."""
        if self.git_commits:
            return self.git_commits[-1].get("commit_hash")
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "project_root": self.project_root,
            "messages": self.messages,
            "tool_calls": self.tool_calls,
            "files_changed": self.files_changed,
            "git_commits": self.git_commits,
            "pending_files": self.pending_files,
            "started_at": self.started_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HookState":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            project_root=data.get("project_root", ""),
            messages=data.get("messages", []),
            tool_calls=data.get("tool_calls", []),
            files_changed=data.get("files_changed", []),
            git_commits=data.get("git_commits", []),
            pending_files=data.get("pending_files", []),
            started_at=data.get("started_at", datetime.now().isoformat()),
        )

    def get_messages_as_models(self) -> list[Message]:
        """Convert stored messages to Message models."""
        result = []
        for msg in self.messages:
            result.append(
                Message(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                )
            )
        return result


def _get_state_file_path(session_id: str) -> Path:
    """Get path to state file for a session."""
    # Use temp directory with session-specific file
    temp_dir = Path(tempfile.gettempdir()) / "lore"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / f"session-{session_id}.json"


def get_hook_state(session_id: str, project_root: str | None = None) -> HookState:
    """Get or create hook state for a session."""
    state_file = _get_state_file_path(session_id)

    if state_file.exists():
        try:
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)
                return HookState.from_dict(data)
        except (json.JSONDecodeError, OSError):
            pass

    # Create new state
    return HookState(
        session_id=session_id,
        project_root=project_root or str(Path.cwd()),
    )


def save_hook_state(state: HookState) -> None:
    """Save hook state to file."""
    state_file = _get_state_file_path(state.session_id)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)


def clear_hook_state(session_id: str) -> None:
    """Clear hook state for a session."""
    state_file = _get_state_file_path(session_id)
    if state_file.exists():
        state_file.unlink()


def add_tool_call(
    session_id: str,
    tool_name: str,
    tool_input: dict,
    tool_output: str | None = None,
    project_root: str | None = None,
) -> None:
    """Add a tool call to the session state."""
    state = get_hook_state(session_id, project_root=project_root)
    state.add_tool_call(tool_name, tool_input, tool_output)
    save_hook_state(state)


def add_file_change(
    session_id: str,
    file_path: str,
    project_root: str | None = None,
) -> None:
    """Add a changed file to the session state."""
    state = get_hook_state(session_id, project_root=project_root)
    state.add_file_change(file_path)
    save_hook_state(state)
