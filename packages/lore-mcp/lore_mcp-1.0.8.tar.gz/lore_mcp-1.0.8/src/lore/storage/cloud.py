"""Cloud storage client for Lore MCP SaaS."""

from __future__ import annotations

from typing import Any

import httpx

from lore.core.models import BlameResult, ContextCommit, SearchResult


class UsageLimitError(Exception):
    """Raised when usage limit is exceeded."""

    def __init__(self, data: dict):
        self.current = data.get("current", 0)
        self.limit = data.get("limit", 0)
        super().__init__(f"Usage limit exceeded: {self.current}/{self.limit}")


class CloudAuthError(Exception):
    """Raised when API key is invalid or missing."""

    pass


class LoreCloudClient:
    """Client for interacting with Lore Cloud API."""

    DEFAULT_BASE_URL = "https://ymwuecowpkiiewlcbhzg.supabase.co/functions/v1/lore-api"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the cloud client.

        Args:
            api_key: Lore API key (lore_xxxxx format)
            base_url: Optional custom API base URL
        """
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL

    def _get_api_key(self) -> str:
        """Get API key from instance or environment."""
        import os

        key = self.api_key or os.environ.get("LORE_API_KEY")
        if not key:
            raise CloudAuthError(
                "API key not configured. Set LORE_API_KEY environment variable "
                "or run: lore config set api_key YOUR_KEY"
            )
        return key

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "X-Lore-API-Key": self._get_api_key(),
            "Content-Type": "application/json",
        }

    async def sync_commits(self, commits: list[ContextCommit]) -> dict[str, Any]:
        """Sync context commits to cloud.

        Args:
            commits: List of ContextCommit objects to sync

        Returns:
            Dict with sync results including count and usage stats

        Raises:
            UsageLimitError: If monthly sync limit exceeded
            CloudAuthError: If API key is invalid
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/sync",
                headers=self._headers(),
                json={"commits": [self._commit_to_dict(c) for c in commits]},
            )

            if response.status_code == 401:
                raise CloudAuthError("Invalid API key")

            if response.status_code == 429:
                raise UsageLimitError(response.json())

            response.raise_for_status()
            return response.json()

    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search context commits in cloud.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of SearchResult objects
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers=self._headers(),
                json={"query": query, "limit": limit},
            )

            if response.status_code == 401:
                raise CloudAuthError("Invalid API key")

            if response.status_code == 429:
                raise UsageLimitError(response.json())

            response.raise_for_status()
            data = response.json()

            return [
                SearchResult(
                    context_id=r["context_id"],
                    intent=r["intent"],
                    relevance_score=1.0,  # Cloud doesn't return score
                    files_changed=r.get("files_changed", []),
                    created_at=r["created_at"],
                    snippet=r.get("decision", ""),
                )
                for r in data.get("results", [])
            ]

    async def blame(
        self,
        file_path: str,
        line_number: int | None = None,
    ) -> list[BlameResult]:
        """Find context for a file/line.

        Args:
            file_path: Path to the file
            line_number: Optional specific line number

        Returns:
            List of BlameResult objects
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload: dict[str, Any] = {"file_path": file_path}
            if line_number is not None:
                payload["line_number"] = line_number

            response = await client.post(
                f"{self.base_url}/blame",
                headers=self._headers(),
                json=payload,
            )

            if response.status_code == 401:
                raise CloudAuthError("Invalid API key")

            response.raise_for_status()
            data = response.json()

            results = []
            for r in data.get("results", []):
                commit_data = r.get("context_commits", {})
                if commit_data:
                    results.append(
                        BlameResult(
                            context_id=r["context_id"],
                            intent=commit_data.get("intent", ""),
                            decision=commit_data.get("decision", ""),
                            model=commit_data.get("model", ""),
                            created_at=commit_data.get("created_at"),
                            files_changed=commit_data.get("files_changed", []),
                        )
                    )
            return results

    async def get_usage(self) -> dict[str, Any]:
        """Get current usage statistics.

        Returns:
            Dict with plan and usage stats
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/usage",
                headers=self._headers(),
            )

            if response.status_code == 401:
                raise CloudAuthError("Invalid API key")

            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict[str, Any]:
        """Check API health and verify API key.

        Returns:
            Dict with status, user_id, and plan
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/health",
                headers=self._headers(),
            )

            if response.status_code == 401:
                raise CloudAuthError("Invalid API key")

            response.raise_for_status()
            return response.json()

    def _commit_to_dict(self, commit: ContextCommit) -> dict[str, Any]:
        """Convert ContextCommit to API-compatible dict."""
        return {
            "context_id": commit.context_id,
            "intent": commit.intent,
            "decision": commit.decision,
            "assumptions": commit.assumptions,
            "alternatives": commit.alternatives,
            "git_commit_id": commit.git_commit_id,
            "files_changed": commit.files_changed,
            "model": commit.model,
            "session_id": commit.session_id,
            "branch_name": commit.branch_name,
            "parent_context_id": commit.parent_context_id,
            "quality_score": commit.quality_score,
            "security_score": commit.security_score,
            "impact_level": commit.impact_level,
            "enrichment_data": commit.enrichment_data,
            "is_enriched": commit.is_enriched,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
            # Project identification
            "project_name": commit.project_name,
            "project_remote": commit.project_remote,
        }


# Sync wrapper for CLI usage
def sync_to_cloud(commits: list[ContextCommit], api_key: str | None = None) -> dict:
    """Synchronous wrapper for syncing commits to cloud.

    Args:
        commits: List of commits to sync
        api_key: Optional API key override

    Returns:
        Sync result dict
    """
    import asyncio

    client = LoreCloudClient(api_key=api_key)
    return asyncio.run(client.sync_commits(commits))


def search_cloud(query: str, limit: int = 20, api_key: str | None = None) -> list[SearchResult]:
    """Synchronous wrapper for cloud search.

    Args:
        query: Search query
        limit: Max results
        api_key: Optional API key override

    Returns:
        List of SearchResult objects
    """
    import asyncio

    client = LoreCloudClient(api_key=api_key)
    return asyncio.run(client.search(query, limit))


def get_cloud_usage(api_key: str | None = None) -> dict:
    """Synchronous wrapper for getting usage stats.

    Args:
        api_key: Optional API key override

    Returns:
        Usage statistics dict
    """
    import asyncio

    client = LoreCloudClient(api_key=api_key)
    return asyncio.run(client.get_usage())
