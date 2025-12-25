# Jaeger Interface

Typed Python wrapper for the Jaeger Query Service HTTP API with client-side span filtering capabilities.

## Quick Reference

**Purpose**: Search and retrieve traces from Jaeger with minimal boilerplate  
**Core Component**: [`JaegerClient`](client.py) class with `search()` and `get_trace()` methods  
**Dependencies**: Uses `requests` and `pydantic` (included in base SDK)  
**Compatibility**: Jaeger v1.x REST endpoints, OpenSearch storage backends

## Installation

**Semantic Tag**: `jaeger-setup`

No additional dependencies required - included with base `veris-ai` package:
```bash
pip install veris-ai
```

---

## Basic Usage

**Semantic Tag**: `jaeger-client-usage`

```python
from veris_ai.jaeger_interface import JaegerClient

client = JaegerClient("http://localhost:16686")

# Search traces with filtering
traces = client.search(
    service="veris-agent",
    limit=10,
    tags={"veris.session_id": "session-123"},
    span_tags={"http.status_code": 500}
)

# Retrieve specific trace
if traces.data:
    detailed = client.get_trace(traces.data[0].traceID)
```

**Data Models**: See [`models.py`](models.py) for `Trace`, `Span`, and response type definitions.

---

## API Reference

**Semantic Tag**: `jaeger-api-methods`

### Core Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `search(service, **filters)` | Search traces with optional filtering | `SearchResponse` |
| `get_trace(trace_id)` | Retrieve single trace by ID | `GetTraceResponse` |

**Implementation**: See [`client.py`](client.py) for method signatures and error handling.

### Filtering Strategy

**Semantic Tag**: `filtering-logic`

```python
# Server-side filtering (efficient)
traces = client.search(
    service="my-service",
    tags={"error": "true"},  # AND logic: trace must match ALL tags
    operation="specific_op"
)

# Client-side filtering (granular)  
traces = client.search(
    service="my-service",
    span_tags={"http.status_code": [500, 503]},  # OR logic: ANY span match
    span_operations=["db_query", "api_call"]
)
```

**Filter Types**:
- **`tags`**: Trace-level filters (server-side, AND logic)
- **`span_tags`**: Span-level filters (client-side, OR logic)  
- **`span_operations`**: Operation name filters (client-side, OR logic)

---

## Architecture

**Semantic Tag**: `jaeger-architecture`

- **Client Implementation**: [`client.py`](client.py) - HTTP requests to Jaeger API
- **Data Models**: [`models.py`](models.py) - Pydantic models for type safety  
- **Compatibility**: Jaeger v1.x REST endpoints, OpenSearch backends

**Design Principle**: Thin wrapper maintaining Jaeger's native API structure while adding client-side span filtering capabilities.

---

**Parent Documentation**: See [module README](../README.md) for integration with other SDK components.