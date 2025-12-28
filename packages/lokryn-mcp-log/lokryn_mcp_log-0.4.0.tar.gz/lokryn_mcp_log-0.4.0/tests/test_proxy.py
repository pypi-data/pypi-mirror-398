"""Tests for the LoggingProxy."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lokryn_mcp_log import LoggingProxy, LogConfig
from lokryn_mcp_log.schema import log_pb2


class MockSink:
    """Mock sink that collects log records for testing."""

    def __init__(self):
        self.records: list[log_pb2.LogRequest] = []

    async def emit(self, record: log_pb2.LogRequest) -> None:
        self.records.append(record)


@pytest.fixture
def mock_session():
    """Create a mock MCP ClientSession."""
    session = AsyncMock()
    session.list_tools.return_value = MagicMock(tools=[])
    session.call_tool.return_value = MagicMock(isError=False, content=[])
    session.list_resources.return_value = MagicMock(resources=[])
    session.read_resource.return_value = MagicMock(contents=[])
    session.list_prompts.return_value = MagicMock(prompts=[])
    session.get_prompt.return_value = MagicMock(messages=[])
    # MagicMock uses 'name' internally, so we configure it separately
    server_info = MagicMock()
    server_info.name = "test-server"
    server_info.version = "1.0.0"
    init_result = MagicMock()
    init_result.serverInfo = server_info
    session.initialize.return_value = init_result
    return session


@pytest.fixture
def sink():
    return MockSink()


@pytest.fixture
def config():
    return LogConfig(environment="test", actor_id="test-actor")


async def test_list_tools_logs_success(mock_session, sink, config):
    """Test that list_tools logs a success event."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_tools()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.event_type == log_pb2.EVENT_TOOL_LIST
    assert record.outcome == log_pb2.OUTCOME_SUCCESS
    assert record.resource == "tools/list"
    assert record.actor_id == "test-actor"
    assert record.environment == "test"


async def test_call_tool_logs_with_arguments(mock_session, sink, config):
    """Test that call_tool logs tool name and arguments."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.call_tool("add", {"a": 1, "b": 2})

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.resource == "tools/add"
    assert record.mcp.tool_name == "add"
    assert record.mcp.tool_arguments["a"] == 1


async def test_call_tool_logs_error_on_exception(mock_session, sink, config):
    """Test that call_tool logs failure when exception is raised."""
    mock_session.call_tool.side_effect = RuntimeError("Connection lost")
    proxy = LoggingProxy(mock_session, sink, config)

    with pytest.raises(RuntimeError):
        await proxy.call_tool("add", {"a": 1, "b": 2})

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.outcome == log_pb2.OUTCOME_FAILURE_ERROR
    assert "Connection lost" in record.message


async def test_call_tool_logs_tool_error(mock_session, sink, config):
    """Test that call_tool logs failure when tool returns error."""
    mock_session.call_tool.return_value = MagicMock(isError=True, content=[])
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.call_tool("add", {"a": 1, "b": 2})

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.outcome == log_pb2.OUTCOME_FAILURE_ERROR
    assert "error" in record.message.lower()


async def test_forwards_unknown_attributes(mock_session, sink, config):
    """Test that unknown attributes are forwarded to the session."""
    mock_session.some_other_method = AsyncMock(return_value="hello")
    proxy = LoggingProxy(mock_session, sink, config)

    result = await proxy.some_other_method()

    assert result == "hello"
    assert len(sink.records) == 0  # Not logged


async def test_initialize_logs_success(mock_session, sink, config):
    """Test that initialize logs a login event."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.initialize()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.event_type == log_pb2.EVENT_MCP_INITIALIZE
    assert record.outcome == log_pb2.OUTCOME_SUCCESS
    assert record.resource == "session/initialize"


async def test_list_resources_logs_success(mock_session, sink, config):
    """Test that list_resources logs a resource access event."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_resources()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.event_type == log_pb2.EVENT_RESOURCE_LIST
    assert record.outcome == log_pb2.OUTCOME_SUCCESS


async def test_list_prompts_logs_success(mock_session, sink, config):
    """Test that list_prompts logs a prompt list event."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_prompts()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.event_type == log_pb2.EVENT_PROMPT_LIST
    assert record.outcome == log_pb2.OUTCOME_SUCCESS


async def test_get_prompt_logs_with_name(mock_session, sink, config):
    """Test that get_prompt logs prompt name."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.get_prompt("my-prompt", {"arg": "value"})

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.resource == "prompts/my-prompt"
    assert record.event_type == log_pb2.EVENT_PROMPT_EXECUTION


async def test_policy_tags_included(mock_session, sink):
    """Test that policy tags are included in log records."""
    config = LogConfig(
        environment="production",
        actor_id="test-actor",
        policy_tags=["SOC2", "HIPAA"],
    )
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_tools()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert "SOC2" in record.policy_tags
    assert "HIPAA" in record.policy_tags


async def test_duration_ms_included(mock_session, sink, config):
    """Test that duration_ms is included in record."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_tools()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.duration_ms >= 0


async def test_trace_id_included(mock_session, sink, config):
    """Test that trace_id is included in record."""
    proxy = LoggingProxy(mock_session, sink, config)

    await proxy.list_tools()

    assert len(sink.records) == 1
    record = sink.records[0]
    assert len(record.trace_id) > 0
