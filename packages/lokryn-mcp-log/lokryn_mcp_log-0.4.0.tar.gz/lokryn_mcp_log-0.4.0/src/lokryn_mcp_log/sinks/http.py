"""HTTP sink for remote log collection."""

import hashlib
import hmac
import json
import os
from typing import Literal, Mapping

import httpx
from google.protobuf.json_format import MessageToDict

from lokryn_mcp_log.schema import log_pb2


class HTTPSink:
    """Emit logs to an HTTP endpoint.

    Supports JSON or protobuf format, with optional HMAC-SHA256 signing.
    Raises on non-2xx responses.
    """

    def __init__(
        self,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
        timeout: float = 10.0,
        hmac_key: str | None = None,
        format: Literal["json", "protobuf"] = "json",
    ):
        """Initialize HTTP sink.

        Args:
            endpoint: URL to POST logs to.
            headers: Optional headers (e.g., for authentication).
            timeout: Request timeout in seconds.
            hmac_key: Optional HMAC-SHA256 key for request signing.
            format: Serialization format, "json" (default) or "protobuf".
        """
        if format not in ("json", "protobuf"):
            raise ValueError(f"Invalid format '{format}'. Must be 'json' or 'protobuf'.")

        self._endpoint = endpoint
        self._headers = dict(headers) if headers else {}
        self._timeout = timeout
        self._hmac_key = hmac_key
        self._format = format

        if format == "protobuf":
            self._headers.setdefault("Content-Type", "application/x-protobuf")
        else:
            self._headers.setdefault("Content-Type", "application/json")

    def _sign(self, body: bytes) -> str:
        """Generate HMAC-SHA256 signature for request body."""
        return hmac.new(
            self._hmac_key.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

    async def emit(self, record: log_pb2.LogRequest) -> None:
        """Emit log record via HTTP POST.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            httpx.RequestError: On connection/timeout errors.
        """
        if self._format == "protobuf":
            body = record.SerializeToString()
        else:
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

    Configuration via environment variables:
        FIELDNOTES_HMAC_KEY: Required. HMAC key for request signing.
        FIELDNOTES_FORMAT: Optional. "json" (default) or "protobuf".
    """

    BASE_URL = "https://fieldnotes.lokryn.com"

    def __init__(
        self,
        hmac_key: str | None = None,
        format: Literal["json", "protobuf"] | None = None,
        timeout: float = 10.0,
    ):
        """Initialize Field Notes sink.

        Args:
            hmac_key: HMAC key. If not provided, reads from FIELDNOTES_HMAC_KEY env var.
            format: "json" or "protobuf". If not provided, reads from FIELDNOTES_FORMAT
                env var, defaulting to "json".
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If no HMAC key is provided or found in environment.
            ValueError: If format is not "json" or "protobuf".
        """
        key = hmac_key or os.environ.get("FIELDNOTES_HMAC_KEY")
        if not key:
            raise ValueError(
                "HMAC key required. Pass hmac_key or set FIELDNOTES_HMAC_KEY env var."
            )

        fmt = format or os.environ.get("FIELDNOTES_FORMAT", "json")
        if fmt not in ("json", "protobuf"):
            raise ValueError(f"Invalid format '{fmt}'. Must be 'json' or 'protobuf'.")

        if fmt == "protobuf":
            endpoint = f"{self.BASE_URL}/v1/log/protobuf"
        else:
            endpoint = f"{self.BASE_URL}/v1/log"

        super().__init__(
            endpoint=endpoint,
            timeout=timeout,
            hmac_key=key,
            format=fmt,
        )
