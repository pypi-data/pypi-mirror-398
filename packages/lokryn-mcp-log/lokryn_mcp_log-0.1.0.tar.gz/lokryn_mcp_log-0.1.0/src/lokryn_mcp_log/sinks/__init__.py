"""Log sinks for emitting audit records."""

from lokryn_mcp_log.sinks.base import Sink
from lokryn_mcp_log.sinks.stdout import StdoutSink
from lokryn_mcp_log.sinks.file import FileSink
from lokryn_mcp_log.sinks.http import HTTPSink

__all__ = [
    "Sink",
    "StdoutSink",
    "FileSink",
    "HTTPSink",
]
