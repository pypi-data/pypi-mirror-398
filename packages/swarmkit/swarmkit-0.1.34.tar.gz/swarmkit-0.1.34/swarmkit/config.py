"""Configuration types for SwarmKit SDK."""

from dataclasses import dataclass
from typing import List, Literal, Optional, Protocol, runtime_checkable


AgentType = Literal['codex', 'claude', 'gemini', 'qwen']
WorkspaceMode = Literal['knowledge', 'swe']
ReasoningEffort = Literal['low', 'medium', 'high', 'xhigh']
ValidationMode = Literal['strict', 'loose']


@dataclass
class SchemaOptions:
    """Validation options for schema validation.

    Args:
        mode: Validation mode - 'strict' (exact types) or 'loose' (coerce types, default)
    """
    mode: ValidationMode = 'loose'


@dataclass
class AgentConfig:
    """Agent configuration.

    All fields are optional - TS SDK resolves defaults from environment:
    - type defaults to 'claude'
    - api_key defaults to SWARMKIT_API_KEY env var

    Args:
        type: Agent type (codex, claude, gemini, qwen) - defaults to 'claude'
        api_key: SwarmKit API key from https://dashboard.swarmlink.ai (defaults to SWARMKIT_API_KEY env var)
        model: Model name (optional - uses agent's default if not specified)
        reasoning_effort: Reasoning effort for Codex models (optional)
        betas: Beta headers for Claude (Sonnet 4.5 only; e.g. ["context-1m-2025-08-07"] for 1M context)
    """
    type: Optional[AgentType] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    reasoning_effort: Optional[ReasoningEffort] = None
    betas: Optional[List[str]] = None


@runtime_checkable
class SandboxProvider(Protocol):
    """Sandbox provider protocol.

    Any sandbox provider must implement this protocol.
    Currently supported: E2BProvider

    To add a new provider:
    1. Create a class with `type` and `config` properties
    2. Add handling in bridge/src/adapter.ts
    """

    @property
    def type(self) -> str:
        """Provider type identifier (e.g., 'e2b')."""
        ...

    @property
    def config(self) -> dict:
        """Provider configuration dict for the bridge."""
        ...


@dataclass
class E2BProvider:
    """E2B sandbox provider configuration.

    Args:
        api_key: E2B API key (defaults to E2B_API_KEY env var)
        timeout_ms: Sandbox timeout in milliseconds (default: 3600000 = 1 hour)
    """
    api_key: Optional[str] = None
    timeout_ms: int = 3600000

    @property
    def type(self) -> Literal['e2b']:
        """Provider type."""
        return 'e2b'

    @property
    def config(self) -> dict:
        """Provider configuration dict."""
        result = {}
        if self.api_key:
            result['apiKey'] = self.api_key
        if self.timeout_ms:
            result['defaultTimeoutMs'] = self.timeout_ms
        return result
