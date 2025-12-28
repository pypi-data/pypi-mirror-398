# lokryn-mcp-log

Compliance-grade audit logging for MCP (Model Context Protocol) client operations.

## What It Does

Wraps the official MCP Python SDK's `ClientSession` and logs every operation—tool calls, resource access, prompt executions—in a format that satisfies SOC2, HIPAA, and PCI audit requirements.

Logs conform to the lokryn-compliance-log-schema, an open standard for audit logging (schema vendored in this package, will be extracted to separate PyPI package).

## Installation

```bash
pip install lokryn-mcp-log
```

Or with uv:

```bash
uv add lokryn-mcp-log
```

## Quick Start

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from lokryn_mcp_log import with_logging, StdoutSink

server_params = StdioServerParameters(command="python", args=["server.py"])

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Wrap with logging
            logged = with_logging(
                session,
                sink=StdoutSink(),
                environment="development",
            )

            # Use exactly like normal
            await logged.call_tool("add", {"a": 1, "b": 2})
```

## Sinks

### StdoutSink

```python
from lokryn_mcp_log import StdoutSink

sink = StdoutSink()           # JSON to stdout
sink = StdoutSink(pretty=True) # Pretty-printed
```

### FileSink

```python
from lokryn_mcp_log import FileSink

sink = FileSink("/var/log/mcp-audit.jsonl")
```

### HTTPSink

```python
from lokryn_mcp_log import HTTPSink

# JSON format (default)
sink = HTTPSink(
    endpoint="https://your-log-collector.com/ingest",
    headers={"Authorization": "Bearer <token>"},
)

# Protobuf format
sink = HTTPSink(
    endpoint="https://your-log-collector.com/ingest/proto",
    format="protobuf",
)

# With HMAC signing
sink = HTTPSink(
    endpoint="https://your-log-collector.com/ingest",
    hmac_key="your-secret-key",
)
```

### Custom Sink

Implement the `Sink` protocol:

```python
from lokryn_mcp_log.schema import log_pb2

class MySink:
    async def emit(self, record: log_pb2.LogRequest) -> None:
        # Your logic here
        pass
```

## Configuration

```python
from lokryn_mcp_log import with_logging
from lokryn_mcp_log.schema import log_pb2

logged = with_logging(
    session,
    sink=my_sink,
    environment="production",           # Required
    actor_id="agent-001",                # Optional, auto-generated if omitted
    component="my-agent",                # Defaults to "mcp-client"
    policy_tags=["SOC2", "HIPAA"],       # Optional compliance tags
    default_sensitivity=log_pb2.SENSITIVITY_CONFIDENTIAL,
)
```

## What Gets Logged

| Operation | Event Type | Resource |
|-----------|------------|----------|
| `initialize()` | `EVENT_LOGIN` | `session/initialize` |
| `list_tools()` | `EVENT_TOOL_INVOCATION` | `tools/list` |
| `call_tool(name, args)` | `EVENT_TOOL_INVOCATION` | `tools/{name}` |
| `list_resources()` | `EVENT_RESOURCE_ACCESS` | `resources/list` |
| `read_resource(uri)` | `EVENT_CONTEXT_ACCESS` | `{uri}` |
| `list_prompts()` | `EVENT_PROMPT_EXECUTION` | `prompts/list` |
| `get_prompt(name)` | `EVENT_PROMPT_EXECUTION` | `prompts/{name}` |
| (session close) | `EVENT_LOGOUT` | `session/close` |

Each log includes:
- Timestamp
- Actor ID (session/agent identifier)
- Duration (milliseconds)
- Correlation ID (for tracing)
- Input arguments
- Outcome (success/failure)
- Error details (on failure)

## Error Handling

This is a library, not a service. If the sink fails, the exception propagates to your code. Handle it as appropriate for your use case.

## Field Notes Integration

Send logs directly to [Field Notes](https://lokryn.com/field-notes) for tamper-evident storage and querying:

```python
from lokryn_mcp_log import FieldNotesSink

# Configure via environment variables:
# FIELDNOTES_HMAC_KEY=your-secret-key
# FIELDNOTES_FORMAT=json  (or "protobuf")

sink = FieldNotesSink()

# Or pass explicitly
sink = FieldNotesSink(hmac_key="your-secret-key", format="protobuf")
```

## License

AGPL-3.0. Commercial license available—contact license@lokryn.com.

## Links

- [lokryn-compliance-log-schema](https://github.com/lokryn-llc/compliance-log-schema)
- [Field Notes](https://lokryn.com/field-notes)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
