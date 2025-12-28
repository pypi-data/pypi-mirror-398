# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-12-25

### Added

- **HMAC Signing** - `HTTPSink` now supports optional HMAC-SHA256 request signing via the `hmac_key` parameter
- **FieldNotesSink** - New convenience sink for Field Notes integration that reads HMAC key from `FIELDNOTES_HMAC_KEY` environment variable

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
