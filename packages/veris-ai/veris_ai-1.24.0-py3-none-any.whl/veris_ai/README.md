# Veris AI Module Architecture

This module contains the core implementation of the Veris AI Python SDK. Each component focuses on a specific aspect of tool mocking, tracing, and MCP integration.

## Quick Reference

**Purpose**: Core SDK implementation with modular architecture  
**Entry Point**: [`__init__.py`](__init__.py) handles lazy imports and public API exports  
**Source of Truth**: Individual module files contain implementation details

## Module Overview

**Semantic Tag**: `core-modules`

| Module | Purpose | Key Classes/Functions | Lines |
|--------|---------|----------------------|-------|
| [`tool_mock.py`](tool_mock.py) | Function mocking & FastAPI MCP | `VerisSDK`, `@mock`, `@stub`, `@spy` | 327 |
| [`utils.py`](utils.py) | Type utilities & JSON schema | `extract_json_schema()`, `convert_to_type()` | 272 |
| [`api_client.py`](api_client.py) | Centralized API client | `SimulatorAPIClient` | 62 |
| [`logging.py`](logging.py) | Tool call/response logging | `log_tool_call()`, `log_tool_response()` | 116 |
| [`models.py`](models.py) | Data models | Type definitions | 12 |
| [`jaeger_interface/`](jaeger_interface/) | Jaeger Query API wrapper | `JaegerClient` | See module README |

## Core Workflows

**Semantic Tag**: `implementation-flows`

### Mock Flow
1. **Decoration**: `@veris.mock()` captures function metadata
2. **Session Check**: Presence of session ID determines behavior  
3. **API Call**: POST to VERIS API endpoint `/v3/tool_mock` (auto-configured)
4. **Type Conversion**: Response converted using `extract_json_schema()`

**Implementation**: [`tool_mock.py:200-250`](tool_mock.py)

### Spy Flow  
1. **Pre-execution Logging**: Call details sent to `v3/log_tool_call?session_id={session_id}`
2. **Function Execution**: Original function runs normally
3. **Post-execution Logging**: Response sent to `v3/log_tool_response?session_id={session_id}`

**Implementation**: [`tool_mock.py:250-300`](tool_mock.py)


## Configuration

**Semantic Tag**: `module-config`

Environment variables are processed in [`api_client.py`](api_client.py):

- `VERIS_API_KEY`: API authentication key (optional, but recommended)
- `VERIS_MOCK_TIMEOUT`: Request timeout (default: 90s)
- `VERIS_API_URL`: Override default API endpoint (rarely needed - defaults to production)

### Observability (OTLP / Logfire)

When using the observability helpers (`init_observability`, `instrument_fastapi_app`), configure the following environment variables so traces export correctly and are attributed to the right service name:

- `OTEL_SERVICE_NAME` — e.g. `simulation-server` (keep consistent with any `VERIS_SERVICE_NAME` you use)
- `OTEL_EXPORTER_OTLP_ENDPOINT` — e.g. `https://logfire-api.pydantic.dev`
- `LOGFIRE_TOKEN` — API token for Logfire
- `OTEL_EXPORTER_OTLP_HEADERS` — e.g. `Authorization=Bearer <LOGFIRE_TOKEN>` (quote the value)

Minimal shell setup:

```bash
export OTEL_SERVICE_NAME="simulation-server"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://logfire-api.pydantic.dev"
export LOGFIRE_TOKEN="<your-token>"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=${LOGFIRE_TOKEN}"
```

Then in code:

```python
from veris_ai import init_observability, instrument_fastapi_app
init_observability()
app = FastAPI()
instrument_fastapi_app(app)
```

## Development Notes

**Semantic Tag**: `development-patterns`

- **Lazy Imports**: [`__init__.py`](__init__.py) minimizes startup dependencies
- **Type Safety**: Extensive use of Pydantic models and type hints
- **Error Handling**: Comprehensive exception handling with timeouts
- **Testing**: Module-specific tests in [`../tests/`](../tests/)

**Architecture Principle**: Each module is self-contained with minimal cross-dependencies, enabling selective imports and reduced memory footprint.

---

**Parent Documentation**: See [main README](../../README.md) for installation and usage patterns.