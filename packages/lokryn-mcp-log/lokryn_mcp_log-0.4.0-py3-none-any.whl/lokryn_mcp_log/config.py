"""Configuration for logging proxy."""

from dataclasses import dataclass, field
from typing import Sequence
from uuid import uuid4

from lokryn_mcp_log.schema import SENSITIVITY_CONFIDENTIAL


@dataclass(frozen=True)
class LogConfig:
    """Configuration for the logging proxy.

    Attributes:
        actor_id: Identifier for the actor (session/agent/user). Auto-generated if not provided.
        environment: Deployment environment (e.g., "production", "staging", "development").
        component: Component name for logs. Defaults to "mcp-client".
        policy_tags: Compliance tags to attach to all logs (e.g., ["SOC2", "HIPAA"]).
        default_sensitivity: Default sensitivity level for logs.
        session_id: MCP session identifier. Auto-generated if not provided.
        client_id: Client identifier (optional).
        client_version: Client version (optional).
    """

    environment: str
    actor_id: str = field(default_factory=lambda: f"session_{uuid4().hex[:12]}")
    component: str = "mcp-client"
    policy_tags: Sequence[str] = field(default_factory=list)
    default_sensitivity: int = SENSITIVITY_CONFIDENTIAL
    session_id: str = field(default_factory=lambda: f"mcp_{uuid4().hex[:16]}")
    client_id: str = ""
    client_version: str = ""
