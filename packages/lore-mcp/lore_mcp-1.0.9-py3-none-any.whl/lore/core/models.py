"""Core data models for Lore."""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_lore_id() -> str:
    """Generate a short lore ID like 'lore-27202017280242'."""
    return f"lore-{uuid4().hex[:14]}"


class MessageRole(str, Enum):
    """Role of a message in conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class ImpactLevel(str, Enum):
    """Impact level of code changes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolCall(BaseModel):
    """Represents a tool call made by the assistant."""

    tool_name: str
    tool_input: dict
    tool_output: str | None = None


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: list[ToolCall] | None = None


class PromptRecord(BaseModel):
    """Stores the full conversation for a context commit."""

    context_id: str
    conversation: list[Message]
    total_tokens: int = 0
    model: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class ContextCommit(BaseModel):
    """A context commit representing AI work with intent and decisions."""

    # Identifiers
    context_id: str = Field(default_factory=generate_lore_id)
    git_commit_id: str | None = None

    # Project identification
    project_name: str = Field(default="", description="Project folder name")
    project_remote: str | None = Field(default=None, description="Git remote URL")

    # Core context
    intent: str = Field(..., description="Implementation intent (required)")
    assumptions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(
        default_factory=list, description="Keywords/alternatives from LLM response"
    )
    decision: str = Field(default="", description="Final decision made")

    # References
    prompt_ref: str = Field(default="", description="Path to prompt file")
    code_diff_ref: str | None = None

    # Metadata
    files_changed: list[str] = Field(default_factory=list)
    model: str = Field(default="")
    session_id: str = Field(default="")

    # Branching support
    branch_name: str = Field(default="main", description="Branch this commit belongs to")
    parent_context_id: str | None = Field(default=None, description="Parent commit in lineage")
    rollback_from_id: str | None = Field(default=None, description="If rollback, source commit")

    # Enrichment scoring (populated by 'lore enrich')
    quality_score: int | None = Field(default=None, ge=0, le=100, description="Code quality score")
    security_score: int | None = Field(default=None, ge=0, le=100, description="Security score")
    impact_level: str | None = Field(default=None, description="low/medium/high")
    enrichment_data: str | None = Field(default=None, description="JSON with detailed analysis")
    is_enriched: bool = Field(default=False, description="Whether enrichment analysis is complete")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)


class FileContextMapping(BaseModel):
    """Maps file lines to context commits for blame functionality."""

    id: int | None = None
    file_path: str
    line_start: int
    line_end: int
    context_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class GitCommitInfo(BaseModel):
    """Git commit information for linking."""

    commit_id: str
    commit_hash: str
    commit_message: str
    author: str
    created_at: datetime


class ExtractedContext(BaseModel):
    """Result of intent extraction from conversation."""

    intent: str
    assumptions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    decision: str = ""
    confidence: float = 0.0


class BlameResult(BaseModel):
    """Result of a blame query."""

    context_id: str
    intent: str
    decision: str
    prompt_summary: str = ""
    model: str = ""
    created_at: datetime
    files_changed: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Result of a context search."""

    context_id: str
    intent: str
    relevance_score: float
    files_changed: list[str] = Field(default_factory=list)
    created_at: datetime
    snippet: str = ""


class ContextBranch(BaseModel):
    """A branch of context commits."""

    branch_name: str
    head_context_id: str | None = None
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class RollbackInfo(BaseModel):
    """Information about a rollback operation."""

    new_context_id: str
    target_context_id: str
    rolled_back_commits: int
    created_at: datetime = Field(default_factory=datetime.now)


class DiffAnalysis(BaseModel):
    """Git diff analysis results."""

    lines_added: int = 0
    lines_removed: int = 0
    files_modified: int = 0
    change_type: str = ""  # refactor, feature, bugfix, config, test, docs
    complexity_delta: int = 0  # positive = more complex, negative = simpler


class QualityAnalysis(BaseModel):
    """Code quality analysis results."""

    structure_score: int = Field(default=0, ge=0, le=100)  # Code organization
    readability_score: int = Field(default=0, ge=0, le=100)  # Naming, comments
    safety_score: int = Field(default=0, ge=0, le=100)  # Error handling
    testing_score: int = Field(default=0, ge=0, le=100)  # Test coverage indicators
    issues: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class SecurityAnalysis(BaseModel):
    """Security analysis results."""

    risk_patterns: list[str] = Field(default_factory=list)
    improvement_patterns: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)
    score: int = Field(default=100, ge=0, le=100)  # 100 = no issues found


class EnrichmentData(BaseModel):
    """Detailed enrichment analysis data stored as JSON."""

    diff_analysis: DiffAnalysis = Field(default_factory=DiffAnalysis)
    quality_analysis: QualityAnalysis = Field(default_factory=QualityAnalysis)
    security_analysis: SecurityAnalysis = Field(default_factory=SecurityAnalysis)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)


def generate_exploration_id() -> str:
    """Generate a short exploration ID like 'explore-27202017280242'."""
    return f"explore-{uuid4().hex[:14]}"


class ExplorationLog(BaseModel):
    """A log entry for exploration/read-only sessions without file changes.

    Captures tool usage and decision-making context from sessions
    that don't modify files (e.g., code analysis, research, debugging).
    """

    # Identifiers
    exploration_id: str = Field(default_factory=generate_exploration_id)
    session_id: str = Field(default="")

    # Context
    intent: str = Field(..., description="What was being explored/analyzed")
    findings: list[str] = Field(default_factory=list, description="Key findings or conclusions")
    files_read: list[str] = Field(default_factory=list, description="Files that were read")

    # Tool usage summary
    tool_calls: list[dict] = Field(
        default_factory=list,
        description="Summary of tools used: [{tool_name, count, sample_inputs}]",
    )
    total_tool_calls: int = Field(default=0, description="Total number of tool calls")

    # Metadata
    model: str = Field(default="")
    branch_name: str = Field(default="main")
    created_at: datetime = Field(default_factory=datetime.now)


class ExplorationSearchResult(BaseModel):
    """Result of an exploration log search."""

    exploration_id: str
    intent: str
    files_read: list[str] = Field(default_factory=list)
    created_at: datetime
    tool_summary: str = ""
