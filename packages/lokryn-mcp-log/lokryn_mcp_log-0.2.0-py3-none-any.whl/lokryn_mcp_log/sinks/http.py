"""HTTP sink for remote log collection."""

import hashlib
import hmac
import json
import os
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
        hmac_key: str | None = None,
    ):
        """Initialize HTTP sink.

        Args:
            endpoint: URL to POST logs to.
            headers: Optional headers (e.g., for authentication).
            timeout: Request timeout in seconds.
            hmac_key: Optional HMAC-SHA256 key for request signing.
        """
        self._endpoint = endpoint
        self._headers = dict(headers) if headers else {}
        self._headers.setdefault("Content-Type", "application/json")
        self._timeout = timeout
        self._hmac_key = hmac_key

    def _sign(self, body: bytes) -> str:
        """Generate HMAC-SHA256 signature for request body."""
        return hmac.new(
            self._hmac_key.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

    async def emit(self, record: log_pb2.LogEntry) -> None:
        """Emit log record via HTTP POST.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            httpx.RequestError: On connection/timeout errors.
        """
        data = MessageToDict(record, preserving_proto_field_name=True)
        body = json.dumps(data).encode()

        headers = self._headers.copy()
        if self._hmac_key:
            headers["X-Signature"] = self._sign(body)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._endpoint,
                headers=headers,
                content=body,
            )
            response.raise_for_status()


class FieldNotesSink(HTTPSink):
    """Emit logs to Field Notes.

    Reads HMAC key from FIELDNOTES_HMAC_KEY environment variable.
    """

    DEFAULT_ENDPOINT = "https://fieldnotes.lokryn.com/ingest"

    def __init__(
        self,
        endpoint: str | None = None,
        hmac_key: str | None = None,
        timeout: float = 10.0,
    ):
        """Initialize Field Notes sink.

        Args:
            endpoint: Optional custom endpoint. Defaults to Field Notes ingest URL.
            hmac_key: HMAC key. If not provided, reads from FIELDNOTES_HMAC_KEY env var.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If no HMAC key is provided or found in environment.
        """
        key = hmac_key or os.environ.get("FIELDNOTES_HMAC_KEY")
        if not key:
            raise ValueError(
                "HMAC key required. Pass hmac_key or set FIELDNOTES_HMAC_KEY env var."
            )

        super().__init__(
            endpoint=endpoint or self.DEFAULT_ENDPOINT,
            timeout=timeout,
            hmac_key=key,
        )
