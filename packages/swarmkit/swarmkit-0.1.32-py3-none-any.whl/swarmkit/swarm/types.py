"""Type definitions for Swarm abstractions."""

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
)

from ..config import SandboxProvider, AgentConfig, WorkspaceMode
from ..retry import RetryConfig


# =============================================================================
# TYPE VARIABLES
# =============================================================================

T = TypeVar('T')

# =============================================================================
# FILE MAP
# =============================================================================

FileMap = Dict[str, Union[str, bytes]]

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SwarmConfig:
    """Configuration for Swarm instance.

    All fields are optional - TS SDK resolves defaults from environment:
    - agent defaults to SWARMKIT_API_KEY env var with 'claude' type
    - sandbox defaults to E2B with E2B_API_KEY env var
    """
    agent: Optional[AgentConfig] = None
    sandbox: Optional[SandboxProvider] = None
    tag: str = "swarm"
    concurrency: int = 4
    timeout_ms: int = 3_600_000  # 1 hour
    workspace_mode: WorkspaceMode = "knowledge"
    retry: Optional[RetryConfig] = None
    """Default retry configuration for all operations (per-operation config takes precedence)."""
    mcp_servers: Optional[Dict[str, Any]] = None
    """Default MCP servers for all operations (per-operation config takes precedence)."""


# Callback types for BestOf
OnCandidateCompleteCallback = Callable[[int, int, Literal["success", "error"]], None]
"""(item_index, candidate_index, status)"""

OnJudgeCompleteCallback = Callable[[int, int, str], None]
"""(item_index, winner_index, reasoning)"""


@dataclass
class BestOfConfig:
    """Configuration for bestOf operation."""
    judge_criteria: str
    n: Optional[int] = None
    task_agents: Optional[List[AgentConfig]] = None
    judge_agent: Optional[AgentConfig] = None
    mcp_servers: Optional[Dict[str, Any]] = None
    """MCP servers for candidates (defaults to operation mcp_servers)."""
    judge_mcp_servers: Optional[Dict[str, Any]] = None
    """MCP servers for judge (defaults to mcp_servers)."""
    on_candidate_complete: Optional[OnCandidateCompleteCallback] = None
    """Callback when a candidate completes."""
    on_judge_complete: Optional[OnJudgeCompleteCallback] = None
    """Callback when judge completes."""


# Callback types for Verify
OnWorkerCompleteCallback = Callable[[int, int, Literal["success", "error"]], None]
"""(item_index, attempt, status)"""

OnVerifierCompleteCallback = Callable[[int, int, bool, Optional[str]], None]
"""(item_index, attempt, passed, feedback)"""


@dataclass
class VerifyConfig:
    """Configuration for verify operation.

    Verify provides LLM-as-judge quality verification with retry loop.
    If verification fails, the worker is re-run with feedback from the verifier.
    """
    criteria: str
    """Verification criteria - what the output must satisfy."""
    max_attempts: int = 3
    """Maximum attempts with feedback (default: 3). Includes initial attempt."""
    verifier_agent: Optional[AgentConfig] = None
    """Optional: override agent for verifier."""
    verifier_mcp_servers: Optional[Dict[str, Any]] = None
    """MCP servers for verifier (defaults to operation mcp_servers)."""
    on_worker_complete: Optional[OnWorkerCompleteCallback] = None
    """Callback invoked after each worker completion (before verification)."""
    on_verifier_complete: Optional[OnVerifierCompleteCallback] = None
    """Callback invoked after each verifier completion."""


# =============================================================================
# METADATA
# =============================================================================

OperationType = Literal["map", "filter", "reduce", "bestof-cand", "bestof-judge", "verify"]


@dataclass
class BaseMeta:
    """Base metadata for all operations."""
    run_id: str
    operation: OperationType
    tag: str
    sandbox_id: str


@dataclass
class IndexedMeta(BaseMeta):
    """Metadata for indexed operations (map, filter, bestof-cand)."""
    index: int


@dataclass
class ReduceMeta(BaseMeta):
    """Metadata for reduce operation."""
    input_count: int
    input_indices: List[int]


@dataclass
class JudgeMeta(BaseMeta):
    """Metadata for bestOf judge."""
    candidate_count: int


@dataclass
class VerifyMeta(BaseMeta):
    """Metadata for verify operation."""
    attempts: int
    """Total verification attempts made."""


# =============================================================================
# PROMPT TYPES
# =============================================================================

PromptFn = Callable[[FileMap, int], str]
Prompt = Union[str, PromptFn]


# =============================================================================
# ITEM INPUT (for chaining)
# =============================================================================

# Forward reference - actual SwarmResult defined in results.py
# ItemInput can be a FileMap or a SwarmResult from a previous operation
ItemInput = Union[FileMap, Any]  # Any here will be SwarmResult at runtime


# =============================================================================
# SCHEMA TYPE
# =============================================================================

# Schema can be a Pydantic model, dataclass, or JSON Schema dict
SchemaType = Union[Type[Any], Dict[str, Any]]


# =============================================================================
# JUDGE DECISION
# =============================================================================

@dataclass
class JudgeDecision:
    """Fixed schema for bestOf judge output."""
    winner: int
    reasoning: str


@dataclass
class VerifyDecision:
    """Fixed schema for verify output."""
    passed: bool
    reasoning: str
    feedback: Optional[str] = None
