# Usage Examples

Practical examples demonstrating Veris AI SDK patterns, import strategies, and integration approaches.

## Quick Reference

**Purpose**: Real-world usage patterns and import flexibility demonstrations  
**Target Audience**: Developers implementing SDK integration  
**Source of Truth**: Example code shows working implementations

## Available Examples

**Semantic Tag**: `usage-examples`

| Example | Demonstrates | Key Concepts |
|---------|--------------|--------------|
| [`import_options.py`](import_options.py) | Flexible import patterns | Lazy imports, optional dependencies, conditional features |

## Import Strategies

**Semantic Tag**: `import-patterns`

The [`import_options.py`](import_options.py) example demonstrates five different approaches to importing and using the SDK:

### 1. Default Imports (Base Dependencies)
```python
from veris_ai import veris, JaegerClient
```
**Use Case**: Minimal installations, function mocking, trace querying  
**Dependencies**: Only `httpx`, `pydantic`, `requests`

### 2. Optional Features (Extra Dependencies)
```python
try:
    from veris_ai import instrument
    instrument(service_name="my-service")
except ImportError:
    print("Install with: pip install veris-ai[instrument]")
```
**Use Case**: Graceful degradation when tracing unavailable  
**Dependencies**: Requires `[instrument]` extra

### 3. Direct Submodule Imports
```python
from veris_ai.tool_mock import veris as mock_tool
```
**Use Case**: Maximum control over imported dependencies  
**Benefits**: Explicit imports, reduced memory footprint

### 4. FastAPI Integration with HTTP Transport
```python
if os.getenv("USE_FASTAPI") == "true":
    from fastapi import FastAPI
    app = FastAPI()
    veris.set_fastapi_mcp(fastapi=app, name="My API Server")
    veris.fastapi_mcp.mount_http()  # Mount with HTTP transport
```
**Use Case**: MCP server setup with HTTP transport for robust session management  
**Dependencies**: Requires `[fastapi]` extra (fastapi-mcp>=0.4.0)

## Integration Patterns

**Semantic Tag**: `integration-patterns`

### Decorator Usage
- **Mock Decorator**: `@veris.mock()` for simulation mode
- **Spy Decorator**: `@veris.spy()` for logging calls and responses
- **Stub Decorator**: `@veris.stub(return_value={})` for fixed responses

### Error Handling
- **Graceful Import Failures**: Try/catch blocks for optional features
- **Environment Validation**: Check required variables before initialization
- **Feature Detection**: Runtime capability checking

### Configuration Management  
- **Environment Variables**: `VERIS_API_KEY` for authentication, `VERIS_MOCK_TIMEOUT` for request timeout
- **Session Management**: Use `veris.set_session_id()` to enable mocking
- **Conditional Setup**: Feature flags for optional components
- **Service Configuration**: Dynamic service naming and endpoints

## Running Examples

**Semantic Tag**: `example-execution`

```bash
# Basic example execution
cd examples/
python import_options.py

# With API key for production
VERIS_API_KEY=your-api-key python import_options.py

# Testing with different feature flags
ENABLE_TRACING=true USE_FASTAPI=true python import_options.py
```

**Note**: To enable mocking in your code, call `veris.set_session_id("your-session-id")`.

w### Observability Environment (optional)

If you want traces exported while running examples, set the following before execution:

```bash
export OTEL_SERVICE_NAME="simulation-server"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://logfire-api.pydantic.dev"
export LOGFIRE_TOKEN="<your-token>"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=${LOGFIRE_TOKEN}"
```

## Development Notes

**Semantic Tag**: `example-development`

- **Self-contained**: Each example includes all necessary imports and setup
- **Environment Agnostic**: Examples work across development environments
- **Error Resilient**: Graceful handling of missing dependencies
- **Documentation**: Extensive comments explaining design decisions

**Adding New Examples**: Follow the pattern of demonstrating specific use cases with complete, runnable code and comprehensive error handling.

---

**Parent Documentation**: See [main README](../README.md) for installation and core usage patterns.  
**Module Details**: See [`src/veris_ai/README.md`](../src/veris_ai/README.md) for implementation architecture.