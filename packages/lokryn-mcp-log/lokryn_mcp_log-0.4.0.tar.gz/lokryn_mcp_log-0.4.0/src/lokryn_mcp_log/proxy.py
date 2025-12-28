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

from lokryn_mcp_log.schema import (
    log_pb2,
    EVENT_MCP_INITIALIZE,
    EVENT_LOGOUT,
    EVENT_TOOL_LIST,
    EVENT_TOOL_INVOCATION,
    EVENT_RESOURCE_LIST,
    EVENT_RESOURCE_READ,
    EVENT_PROMPT_LIST,
    EVENT_PROMPT_EXECUTION,
    OUTCOME_SUCCESS,
    OUTCOME_FAILURE_ERROR,
    SENSITIVITY_CONFIDENTIAL,
)
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
        self._server_id: str | None = None
        self._server_version: str | None = None

    def __getattr__(self, name: str) -> Any:
        """Forward unknown attributes to underlying session."""
        return getattr(self._session, name)

    async def _emit(
        self,
        event_type: int,
        outcome: int,
        resource: str,
        message: str,
        tool_name: str | None = None,
        tool_arguments: dict[str, Any] | None = None,
        resource_uri: str | None = None,
        duration_ms: float | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Build and emit a log record."""
        record = build_log_record(
            config=self._config,
            event_type=event_type,
            outcome=outcome,
            resource=resource,
            message=message,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            resource_uri=resource_uri,
            duration_ms=int(duration_ms) if duration_ms is not None else None,
            trace_id=trace_id,
            server_id=self._server_id,
            server_version=self._server_version,
        )
        await self._sink.emit(record)

    # -------------------------------------------------------------------------
    # Intercepted methods
    # -------------------------------------------------------------------------

    async def initialize(self, **kwargs: Any) -> Any:
        """Initialize the session with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.initialize(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Extract server info if available
            if hasattr(result, "serverInfo") and result.serverInfo:
                self._server_id = getattr(result.serverInfo, "name", None)
                self._server_version = getattr(result.serverInfo, "version", None)

            await self._emit(
                event_type=EVENT_MCP_INITIALIZE,
                outcome=OUTCOME_SUCCESS,
                resource="session/initialize",
                message="MCP session initialized",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_MCP_INITIALIZE,
                outcome=OUTCOME_FAILURE_ERROR,
                resource="session/initialize",
                message=f"Failed to initialize session: {e}",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def close(self) -> None:
        """Close the session with logging."""
        trace_id = uuid4().hex

        try:
            # Log before close since we may not be able to emit after
            await self._emit(
                event_type=EVENT_LOGOUT,
                outcome=OUTCOME_SUCCESS,
                resource="session/close",
                message="MCP session closed",
                duration_ms=0,
                trace_id=trace_id,
            )

            if hasattr(self._session, "close"):
                await self._session.close()

        except Exception:
            # Best effort - session may already be closed
            pass

    async def list_tools(self, **kwargs: Any) -> ListToolsResult:
        """List available tools with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_tools(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=EVENT_TOOL_LIST,
                outcome=OUTCOME_SUCCESS,
                resource="tools/list",
                message=f"Listed {len(result.tools)} tools",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_TOOL_LIST,
                outcome=OUTCOME_FAILURE_ERROR,
                resource="tools/list",
                message=f"Failed to list tools: {e}",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CallToolResult:
        """Call a tool with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.call_tool(name, arguments, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Determine outcome - check for tool-level error
            if result.isError:
                outcome = OUTCOME_FAILURE_ERROR
                message = f"Tool '{name}' returned error"
            else:
                outcome = OUTCOME_SUCCESS
                message = f"Tool '{name}' executed successfully"

            await self._emit(
                event_type=EVENT_TOOL_INVOCATION,
                outcome=outcome,
                resource=f"tools/{name}",
                message=message,
                tool_name=name,
                tool_arguments=arguments,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_TOOL_INVOCATION,
                outcome=OUTCOME_FAILURE_ERROR,
                resource=f"tools/{name}",
                message=f"Tool '{name}' failed: {e}",
                tool_name=name,
                tool_arguments=arguments,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def list_resources(self, **kwargs: Any) -> ListResourcesResult:
        """List available resources with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_resources(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=EVENT_RESOURCE_LIST,
                outcome=OUTCOME_SUCCESS,
                resource="resources/list",
                message=f"Listed {len(result.resources)} resources",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_RESOURCE_LIST,
                outcome=OUTCOME_FAILURE_ERROR,
                resource="resources/list",
                message=f"Failed to list resources: {e}",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def read_resource(self, uri: AnyUrl, **kwargs: Any) -> ReadResourceResult:
        """Read a resource with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()
        uri_str = str(uri)

        try:
            result = await self._session.read_resource(uri, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=EVENT_RESOURCE_READ,
                outcome=OUTCOME_SUCCESS,
                resource=uri_str,
                message=f"Read resource: {uri_str}",
                resource_uri=uri_str,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_RESOURCE_READ,
                outcome=OUTCOME_FAILURE_ERROR,
                resource=uri_str,
                message=f"Failed to read resource: {e}",
                resource_uri=uri_str,
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def list_prompts(self, **kwargs: Any) -> ListPromptsResult:
        """List available prompts with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.list_prompts(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=EVENT_PROMPT_LIST,
                outcome=OUTCOME_SUCCESS,
                resource="prompts/list",
                message=f"Listed {len(result.prompts)} prompts",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_PROMPT_LIST,
                outcome=OUTCOME_FAILURE_ERROR,
                resource="prompts/list",
                message=f"Failed to list prompts: {e}",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            raise

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> GetPromptResult:
        """Get a prompt with logging."""
        trace_id = uuid4().hex
        start = time.perf_counter()

        try:
            result = await self._session.get_prompt(name, arguments, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            await self._emit(
                event_type=EVENT_PROMPT_EXECUTION,
                outcome=OUTCOME_SUCCESS,
                resource=f"prompts/{name}",
                message=f"Got prompt: {name}",
                duration_ms=duration_ms,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                event_type=EVENT_PROMPT_EXECUTION,
                outcome=OUTCOME_FAILURE_ERROR,
                resource=f"prompts/{name}",
                message=f"Failed to get prompt '{name}': {e}",
                duration_ms=duration_ms,
                trace_id=trace_id,
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
    default_sensitivity: int = SENSITIVITY_CONFIDENTIAL,
    session_id: str | None = None,
    client_id: str = "",
    client_version: str = "",
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
        session_id: Optional MCP session ID. Generated if not provided.
        client_id: Optional client identifier.
        client_version: Optional client version.

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
        session_id=session_id or f"mcp_{uuid4().hex[:16]}",
        client_id=client_id,
        client_version=client_version,
    )
    return LoggingProxy(session=session, sink=sink, config=config)
