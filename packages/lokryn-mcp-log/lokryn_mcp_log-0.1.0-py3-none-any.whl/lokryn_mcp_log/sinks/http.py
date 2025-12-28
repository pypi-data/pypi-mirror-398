"""HTTP sink for remote log collection."""

from typing import Mapping

import httpx
from google.protobuf.json_format import MessageToDict

from lokryn_mcp_log.schema import log_pb2


class HTTPSink:
    """Emit logs to an HTTP endpoint.

    Sends POST requests with JSON body.
    Raises on non-2xx responses.
    """

    def __init__(
        self,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
        timeout: float = 10.0,
    ):
        """Initialize HTTP sink.

        Args:
            endpoint: URL to POST logs to.
            headers: Optional headers (e.g., for authentication).
            timeout: Request timeout in seconds.
        """
        self._endpoint = endpoint
        self._headers = dict(headers) if headers else {}
        self._headers.setdefault("Content-Type", "application/json")
        self._timeout = timeout

    async def emit(self, record: log_pb2.LogEntry) -> None:
        """Emit log record via HTTP POST.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            httpx.RequestError: On connection/timeout errors.
        """
        data = MessageToDict(record, preserving_proto_field_name=True)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._endpoint,
                headers=self._headers,
                json=data,
            )
            response.raise_for_status()
