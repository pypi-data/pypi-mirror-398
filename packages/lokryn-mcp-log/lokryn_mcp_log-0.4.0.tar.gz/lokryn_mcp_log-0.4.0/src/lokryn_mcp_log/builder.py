"""Build LogRequest records from MCP operations."""

from typing import Any

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import ParseDict

from lokryn_mcp_log.schema import (
    log_pb2,
    OUTCOME_SUCCESS,
    OUTCOME_FAILURE_ERROR,
    OUTCOME_FAILURE_UNAUTHORIZED,
    OUTCOME_FAILURE_DENIED,
    SEVERITY_INFO,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
)
from lokryn_mcp_log.config import LogConfig


def _dict_to_struct(data: dict[str, Any] | None) -> Struct | None:
    """Convert a Python dict to a protobuf Struct."""
    if not data:
        return None
    struct = Struct()
    ParseDict(data, struct)
    return struct


def build_log_record(
    config: LogConfig,
    event_type: int,
    outcome: int,
    resource: str,
    message: str,
    tool_name: str | None = None,
    tool_arguments: dict[str, Any] | None = None,
    resource_uri: str | None = None,
    severity: int | None = None,
    sensitivity: int | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    duration_ms: int | None = None,
    server_id: str | None = None,
    server_version: str | None = None,
) -> log_pb2.LogRequest:
    """Build a LogRequest from operation data.

    Args:
        config: Logging configuration.
        event_type: Type of event.
        outcome: Outcome of the operation.
        resource: Resource identifier (tool name, URI, etc.).
        message: Human-readable message.
        tool_name: Name of the tool being called (for tool invocations).
        tool_arguments: Arguments passed to the tool.
        resource_uri: URI of the resource being accessed.
        severity: Override default severity (derived from outcome if not provided).
        sensitivity: Override default sensitivity from config.
        trace_id: Trace ID for distributed tracing.
        span_id: Span ID for distributed tracing.
        duration_ms: Operation duration in milliseconds.
        server_id: MCP server identifier.
        server_version: MCP server version.

    Returns:
        Populated LogRequest ready for emission.
    """
    # Derive severity from outcome if not provided
    if severity is None:
        if outcome == OUTCOME_SUCCESS:
            severity = SEVERITY_INFO
        elif outcome == OUTCOME_FAILURE_ERROR:
            severity = SEVERITY_ERROR
        elif outcome in (OUTCOME_FAILURE_UNAUTHORIZED, OUTCOME_FAILURE_DENIED):
            severity = SEVERITY_WARNING
        else:
            severity = SEVERITY_INFO

    # Build the request
    request = log_pb2.LogRequest(
        event_type=event_type,
        outcome=outcome,
        severity=severity,
        sensitivity=sensitivity if sensitivity is not None else config.default_sensitivity,
        actor_id=config.actor_id,
        component=config.component,
        environment=config.environment,
        resource=resource,
        message=message,
        session_id=config.session_id,
        policy_tags=list(config.policy_tags),
    )

    # Set optional top-level fields
    if trace_id:
        request.trace_id = trace_id
    if span_id:
        request.span_id = span_id
    if duration_ms is not None:
        request.duration_ms = int(duration_ms)
    if config.client_id:
        request.client_id = config.client_id
    if config.client_version:
        request.client_version = config.client_version
    if server_id:
        request.server_id = server_id
    if server_version:
        request.server_version = server_version

    # Build MCP payload if we have MCP-specific data
    if tool_name or tool_arguments or resource_uri:
        mcp_payload = log_pb2.MCPPayload()
        if tool_name:
            mcp_payload.tool_name = tool_name
        if tool_arguments:
            mcp_payload.tool_arguments.CopyFrom(_dict_to_struct(tool_arguments))
        if resource_uri:
            mcp_payload.resource_uri = resource_uri
        request.mcp.CopyFrom(mcp_payload)

    return request
