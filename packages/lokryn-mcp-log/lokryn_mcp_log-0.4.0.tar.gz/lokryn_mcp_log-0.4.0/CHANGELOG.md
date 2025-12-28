# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2025-12-25

### Changed

- **Breaking: Schema Migration** - Updated to lokryn-compliance-log v0.2.0
  - `LogEntry` → `LogRequest` - All sinks now emit `LogRequest` messages
  - `payload` bytes field replaced with structured `MCPPayload` (tool name, arguments, resource URI are now proper fields)
  - Added `session_id`, `client_id`, `client_version`, `server_id`, `server_version` fields
  - Added `trace_id` and `span_id` for distributed tracing support
- **MCP-Specific Event Types** - Now uses dedicated event types from the schema:
  - `EVENT_MCP_INITIALIZE` for session initialization
  - `EVENT_TOOL_LIST`, `EVENT_TOOL_INVOCATION` for tool operations
  - `EVENT_RESOURCE_LIST`, `EVENT_RESOURCE_READ` for resource operations
  - `EVENT_PROMPT_LIST`, `EVENT_PROMPT_EXECUTION` for prompt operations
  - `EVENT_LOGOUT` for session close

### Removed

- Base64-encoded payload field - MCP data is now in the structured `mcp` field

## [0.3.0] - 2025-12-25

### Added

- **Protobuf Format** - `HTTPSink` now supports `format` parameter: `"json"` (default) or `"protobuf"`
- **HMAC Signing** - `HTTPSink` now supports optional HMAC-SHA256 request signing via the `hmac_key` parameter
- **FieldNotesSink** - Convenience sink for Field Notes integration
  - `FIELDNOTES_HMAC_KEY` env var for HMAC signing
  - `FIELDNOTES_FORMAT` env var to choose between `json` (default) or `protobuf`

## [0.1.0] - 2025-12-25

Initial release.

### Features

- **Session Proxy** - Wraps the MCP Python SDK's `ClientSession` to transparently log all operations
- **Compliance-Ready Logs** - Output conforms to the lokryn-compliance-log-schema, designed for SOC2, HIPAA, and PCI audit requirements
- **Built-in Sinks**
  - `StdoutSink` - JSON output to stdout (with optional pretty-printing)
  - `FileSink` - Append to JSONL files
  - `HTTPSink` - POST to any HTTP endpoint (e.g., Field Notes)
- **Custom Sinks** - Implement the `Sink` protocol for custom log destinations
- **Full Operation Coverage** - Logs `initialize`, `call_tool`, `list_tools`, `read_resource`, `list_resources`, `get_prompt`, `list_prompts`, and session close events

### Log Record Fields

Each log includes timestamp, actor ID, duration, correlation ID, input arguments, outcome, and error details.
