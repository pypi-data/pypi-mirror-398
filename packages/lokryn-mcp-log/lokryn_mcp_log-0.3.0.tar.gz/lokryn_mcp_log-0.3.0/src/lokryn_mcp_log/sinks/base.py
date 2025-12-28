"""Base sink protocol."""

from typing import Protocol, runtime_checkable

from lokryn_mcp_log.schema import log_pb2


@runtime_checkable
class Sink(Protocol):
    """Protocol for log sinks.

    Sinks receive LogEntry messages and emit them somewhere.
    Implementations must be async.

    If emit() raises an exception, it propagates to the caller.
    This is intentional - the library does not swallow errors.
    """

    async def emit(self, record: log_pb2.LogEntry) -> None:
        """Emit a log record.

        Args:
            record: The log record to emit.

        Raises:
            Any exception from the underlying transport.
        """
        ...
