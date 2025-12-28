"""Stdout sink for debugging and development."""

import json
import sys
from typing import TextIO

from google.protobuf.json_format import MessageToDict

from lokryn_mcp_log.schema import log_pb2


class StdoutSink:
    """Emit logs to stdout as JSON.

    Useful for debugging and piping to other tools.
    """

    def __init__(self, stream: TextIO = sys.stdout, pretty: bool = False):
        """Initialize stdout sink.

        Args:
            stream: Output stream. Defaults to sys.stdout.
            pretty: If True, pretty-print JSON with indentation.
        """
        self._stream = stream
        self._indent = 2 if pretty else None

    async def emit(self, record: log_pb2.LogRequest) -> None:
        """Emit log record to stdout."""
        data = MessageToDict(record, preserving_proto_field_name=True)
        line = json.dumps(data, indent=self._indent, default=str)
        self._stream.write(line + "\n")
        self._stream.flush()
