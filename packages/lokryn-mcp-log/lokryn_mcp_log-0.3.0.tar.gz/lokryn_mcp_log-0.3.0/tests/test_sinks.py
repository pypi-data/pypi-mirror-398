"""Tests for log sinks."""

import io
import json
import tempfile
from pathlib import Path

import pytest

from lokryn_mcp_log import StdoutSink, FileSink
from lokryn_mcp_log.schema import log_pb2


def create_test_record() -> log_pb2.LogEntry:
    """Create a test log record."""
    return log_pb2.LogEntry(
        event_type=log_pb2.EVENT_TOOL_INVOCATION,
        outcome=log_pb2.OUTCOME_SUCCESS,
        severity=log_pb2.SEVERITY_INFO,
        actor_id="test-actor",
        component="test-component",
        environment="test",
        resource="tools/test",
        message="Test message",
        payload=b'{"key": "value"}',
        policy_tags=["SOC2"],
        sensitivity=log_pb2.SENSITIVITY_INTERNAL,
    )


class TestStdoutSink:
    """Tests for StdoutSink."""

    async def test_emit_writes_json(self):
        """Test that emit writes JSON to stdout."""
        stream = io.StringIO()
        sink = StdoutSink(stream=stream)
        record = create_test_record()

        await sink.emit(record)

        output = stream.getvalue()
        assert output.endswith("\n")

        data = json.loads(output)
        assert data["event_type"] == "EVENT_TOOL_INVOCATION"
        assert data["outcome"] == "OUTCOME_SUCCESS"
        assert data["actor_id"] == "test-actor"

    async def test_emit_pretty_print(self):
        """Test that pretty=True adds indentation."""
        stream = io.StringIO()
        sink = StdoutSink(stream=stream, pretty=True)
        record = create_test_record()

        await sink.emit(record)

        output = stream.getvalue()
        # Pretty printed JSON has newlines
        assert "\n" in output.strip()


class TestFileSink:
    """Tests for FileSink."""

    async def test_emit_writes_to_file(self):
        """Test that emit writes JSON to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = FileSink(path)
            record = create_test_record()

            await sink.emit(record)

            content = path.read_text()
            data = json.loads(content.strip())
            assert data["event_type"] == "EVENT_TOOL_INVOCATION"
            assert data["actor_id"] == "test-actor"

    async def test_emit_appends_to_file(self):
        """Test that emit appends to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = FileSink(path)
            record = create_test_record()

            await sink.emit(record)
            await sink.emit(record)

            lines = path.read_text().strip().split("\n")
            assert len(lines) == 2

    async def test_emit_creates_file(self):
        """Test that emit creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "test.jsonl"
            path.parent.mkdir(parents=True)
            sink = FileSink(path)
            record = create_test_record()

            await sink.emit(record)

            assert path.exists()
