"""Build LogEntry records from MCP operations."""

import json
from typing import Any

from lokryn_mcp_log.schema import log_pb2
from lokryn_mcp_log.config import LogConfig


def build_log_record(
    config: LogConfig,
    event_type: int,
    outcome: int,
    resource: str,
    message: str,
    payload: dict[str, Any] | None = None,
    severity: int | None = None,
    sensitivity: int | None = None,
    correlation_id: str | None = None,
    duration_ms: float | None = None,
) -> log_pb2.LogEntry:
    """Build a LogEntry from operation data.

    Args:
        config: Logging configuration.
        event_type: Type of event.
        outcome: Outcome of the operation.
        resource: Resource identifier (tool name, URI, etc.).
        message: Human-readable message.
        payload: Optional structured payload (will be JSON-encoded).
        severity: Override default severity (derived from outcome if not provided).
        sensitivity: Override default sensitivity from config.
        correlation_id: Optional correlation ID for request tracing.
        duration_ms: Optional operation duration in milliseconds.

    Returns:
        Populated LogEntry ready for emission.
    """
    # Derive severity from outcome if not provided
    if severity is None:
        if outcome == log_pb2.OUTCOME_SUCCESS:
            severity = log_pb2.SEVERITY_INFO
        elif outcome == log_pb2.OUTCOME_FAILURE_ERROR:
            severity = log_pb2.SEVERITY_ERROR
        elif outcome in (log_pb2.OUTCOME_FAILURE_UNAUTHORIZED, log_pb2.OUTCOME_FAILURE_DENIED):
            severity = log_pb2.SEVERITY_WARNING
        else:
            severity = log_pb2.SEVERITY_INFO

    # Build payload bytes
    payload_dict = payload.copy() if payload else {}
    if correlation_id:
        payload_dict["correlation_id"] = correlation_id
    if duration_ms is not None:
        payload_dict["duration_ms"] = duration_ms

    payload_bytes = json.dumps(payload_dict, default=str).encode("utf-8")

    return log_pb2.LogEntry(
        event_type=event_type,
        outcome=outcome,
        severity=severity,
        actor_id=config.actor_id,
        component=config.component,
        environment=config.environment,
        resource=resource,
        message=message,
        payload=payload_bytes,
        policy_tags=list(config.policy_tags),
        sensitivity=sensitivity if sensitivity is not None else config.default_sensitivity,
    )
