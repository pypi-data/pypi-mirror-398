"""Pytest fixtures for lokryn-mcp-log tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lokryn_mcp_log import LogConfig
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

    # list_tools
    session.list_tools.return_value = MagicMock(tools=[])

    # call_tool
    session.call_tool.return_value = MagicMock(isError=False, content=[])

    # list_resources
    session.list_resources.return_value = MagicMock(resources=[])

    # read_resource
    session.read_resource.return_value = MagicMock(contents=[])

    # list_prompts
    session.list_prompts.return_value = MagicMock(prompts=[])

    # get_prompt
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
    """Create a mock sink for testing."""
    return MockSink()


@pytest.fixture
def config():
    """Create a test configuration."""
    return LogConfig(environment="test", actor_id="test-actor")
