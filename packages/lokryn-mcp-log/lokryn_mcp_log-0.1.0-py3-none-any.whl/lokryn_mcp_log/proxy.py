"""Logging proxy for MCP ClientSession."""

import time
from typing import Any
from uuid import uuid4

from mcp.client.session import ClientSession
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
)
from pydantic import AnyUrl

from lokryn_mcp_log.schema import log_pb2
from lokryn_mcp_log.builder import build_log_record
from lokryn_mcp_log.config import LogConfig
from lokryn_mcp_log.sinks.base import Sink


class LoggingProxy:
    """Proxy that wraps a ClientSession and logs all operations.

    Uses composition - wraps the session and forwards calls.
    Methods we care about are intercepted and logged.
    All other attributes/methods are forwarded to the underlying session.

    Example:
        async with ClientSession(read, write) as session:
            await session.initialize()

            logged = LoggingProxy(
                session=session,
                sink=StdoutSink(),
                config=LogConfig(environment="production"),
            )

            # Use logged exactly like session
            result = await logged.call_tool("add", {"a": 1, "b": 2})
    """

    def __init__(
        self,
        session: ClientSession,
        sink: Sink,
        config: LogConfig,
    ):
        """Initialize logging proxy.

        Args:
            session: The MCP ClientSession to wrap.
            sink: Where to emit logs.
            config: Logging configuration.
        """
        self._session = session
        self._sink = sink
        self._config = config

    def __getattr__(self, name: str) -> Any:
        """Forward unknown attributes to underlying session."""
        return getattr(self._session, name)

    async def _emit(
        self,
        event_type: int,
        outcome: int,
        resource: str,
        message: str,
        payload: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Build and emit a log record."""
        record = build_log_record(
            config=self._config,
            event_type=event_type,
            outcome=outcome,
            resource=resource,
            message=message,
            payload=payload,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        await self._sink.emit(record)

    # -------------------------------------------------------------------------
    # Intercepted methods
    # -------------------------------------------------------------------------

    async def initialize(self, **kwargs: Any) -> Any:
        """Initialize the session with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.initialize(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Extract server info if available
            server_info = {}
            if hasattr(result, "serverInfo") and result.serverInfo:
                server_info = {
                    "server_name": getattr(result.serverInfo, "name", None),
                    "server_version": getattr(result.serverInfo, "version", None),
                }

            await self._emit(
                event_type=log_pb2.EVENT_LOGIN,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource="session/initialize",
                message="MCP session initialized",
                payload=server_info,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_LOGIN,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource="session/initialize",
                message=f"Failed to initialize session: {e}",
                payload={"error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def close(self) -> None:
        """Close the session with logging."""
        correlation_id = uuid4().hex

        try:
            # Log before close since we may not be able to emit after
            await self._emit(
                event_type=log_pb2.EVENT_LOGOUT,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource="session/close",
                message="MCP session closed",
                payload={},
                duration_ms=0,
                correlation_id=correlation_id,
            )

            if hasattr(self._session, "close"):
                await self._session.close()

        except Exception:
            # Best effort - session may already be closed
            pass

    async def list_tools(self, **kwargs: Any) -> ListToolsResult:
        """List available tools with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_tools(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=log_pb2.EVENT_TOOL_INVOCATION,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource="tools/list",
                message=f"Listed {len(result.tools)} tools",
                payload={"tool_count": len(result.tools)},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_TOOL_INVOCATION,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource="tools/list",
                message=f"Failed to list tools: {e}",
                payload={"error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CallToolResult:
        """Call a tool with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.call_tool(name, arguments, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Determine outcome - check for tool-level error
            if result.isError:
                outcome = log_pb2.OUTCOME_FAILURE_ERROR
                message = f"Tool '{name}' returned error"
            else:
                outcome = log_pb2.OUTCOME_SUCCESS
                message = f"Tool '{name}' executed successfully"

            await self._emit(
                event_type=log_pb2.EVENT_TOOL_INVOCATION,
                outcome=outcome,
                resource=f"tools/{name}",
                message=message,
                payload={
                    "tool_name": name,
                    "arguments": arguments,
                    "is_error": result.isError,
                },
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_TOOL_INVOCATION,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource=f"tools/{name}",
                message=f"Tool '{name}' failed: {e}",
                payload={
                    "tool_name": name,
                    "arguments": arguments,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def list_resources(self, **kwargs: Any) -> ListResourcesResult:
        """List available resources with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_resources(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=log_pb2.EVENT_RESOURCE_ACCESS,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource="resources/list",
                message=f"Listed {len(result.resources)} resources",
                payload={"resource_count": len(result.resources)},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_RESOURCE_ACCESS,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource="resources/list",
                message=f"Failed to list resources: {e}",
                payload={"error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def read_resource(self, uri: AnyUrl, **kwargs: Any) -> ReadResourceResult:
        """Read a resource with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()
        uri_str = str(uri)

        try:
            result = await self._session.read_resource(uri, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=log_pb2.EVENT_CONTEXT_ACCESS,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource=uri_str,
                message=f"Read resource: {uri_str}",
                payload={"uri": uri_str, "content_count": len(result.contents)},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_CONTEXT_ACCESS,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource=uri_str,
                message=f"Failed to read resource: {e}",
                payload={"uri": uri_str, "error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def list_prompts(self, **kwargs: Any) -> ListPromptsResult:
        """List available prompts with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_prompts(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=log_pb2.EVENT_PROMPT_EXECUTION,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource="prompts/list",
                message=f"Listed {len(result.prompts)} prompts",
                payload={"prompt_count": len(result.prompts)},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_PROMPT_EXECUTION,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource="prompts/list",
                message=f"Failed to list prompts: {e}",
                payload={"error": str(e), "error_type": type(e).__name__},
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> GetPromptResult:
        """Get a prompt with logging."""
        correlation_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.get_prompt(name, arguments, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=log_pb2.EVENT_PROMPT_EXECUTION,
                outcome=log_pb2.OUTCOME_SUCCESS,
                resource=f"prompts/{name}",
                message=f"Got prompt: {name}",
                payload={
                    "prompt_name": name,
                    "arguments": arguments,
                    "message_count": len(result.messages),
                },
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=log_pb2.EVENT_PROMPT_EXECUTION,
                outcome=log_pb2.OUTCOME_FAILURE_ERROR,
                resource=f"prompts/{name}",
                message=f"Failed to get prompt '{name}': {e}",
                payload={
                    "prompt_name": name,
                    "arguments": arguments,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise


def with_logging(
    session: ClientSession,
    sink: Sink,
    *,
    environment: str,
    actor_id: str | None = None,
    component: str = "mcp-client",
    policy_tags: list[str] | None = None,
    default_sensitivity: int = log_pb2.SENSITIVITY_INTERNAL,
) -> LoggingProxy:
    """Wrap a ClientSession with logging.

    Convenience function that creates LogConfig and LoggingProxy.

    Args:
        session: The MCP ClientSession to wrap.
        sink: Where to emit logs.
        environment: Deployment environment (required).
        actor_id: Optional actor ID. Generated if not provided.
        component: Component name. Defaults to "mcp-client".
        policy_tags: Optional compliance tags.
        default_sensitivity: Default sensitivity level.

    Returns:
        LoggingProxy wrapping the session.

    Example:
        logged = with_logging(
            session,
            sink=HTTPSink("https://logs.example.com/ingest"),
            environment="production",
            policy_tags=["SOC2", "PCI"],
        )
    """
    config = LogConfig(
        environment=environment,
        actor_id=actor_id or f"session_{uuid4().hex[:12]}",
        component=component,
        policy_tags=policy_tags or [],
        default_sensitivity=default_sensitivity,
    )
    return LoggingProxy(session=session, sink=sink, config=config)
