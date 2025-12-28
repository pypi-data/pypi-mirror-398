"""File sink for persistent local logging."""

import json
from pathlib import Path

import aiofiles
from google.protobuf.json_format import MessageToDict

from lokryn_mcp_log.schema import log_pb2


class FileSink:
    """Emit logs to a file as newline-delimited JSON.

    Each log record is written as a single JSON line (JSONL format).
    File is opened in append mode.
    """

    def __init__(self, path: str | Path):
        """Initialize file sink.

        Args:
            path: Path to the log file. Created if it doesn't exist.
        """
        self._path = Path(path)

    async def emit(self, record: log_pb2.LogRequest) -> None:
        """Emit log record to file."""
        data = MessageToDict(record, preserving_proto_field_name=True)
        line = json.dumps(data, default=str)

        async with aiofiles.open(self._path, mode="a") as f:
            await f.write(line + "\n")
