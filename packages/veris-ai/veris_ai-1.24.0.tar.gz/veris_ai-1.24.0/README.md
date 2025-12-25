# Veris AI Python SDK

[![PyPI version](https://badge.fury.io/py/veris-ai.svg)](https://badge.fury.io/py/veris-ai)
[![Downloads](https://static.pepy.tech/badge/veris-ai)](https://pepy.tech/project/veris-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Tool mocking and MCP server integration for AI agent simulation. For more information visit [veris.ai](https://veris.ai).

## Quick Start

Install the SDK:

```bash
uv add veris-ai --extra fastapi --extra agents
```

### Minimal Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from agents import Agent, function_tool, Runner
from veris_ai import veris

app = FastAPI()

# 1. Define tools with @veris.mock() - returns simulated responses during simulation
@function_tool
@veris.mock()
def get_user(user_id: str) -> dict:
    """Get user information."""
    return db.get_user(user_id)

# 2. Create an agent with the tools
agent = Agent(name="Assistant", model="gpt-4", tools=[get_user])

# 3. Expose an endpoint that invokes the agent
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    result = await Runner.run(agent, req.message)
    return {"response": result.final_output}

# 4. Set up the MCP server
veris.set_fastapi_mcp(fastapi=app)
veris.fastapi_mcp.mount_http()
```

Your FastAPI app now exposes an MCP server at `/mcp`. During Veris simulations, decorated tools return simulated responses; in production, they execute normally.

## Installation

```bash
# Base package
uv add veris-ai

# With FastAPI MCP support
uv add veris-ai --extra fastapi

# With OpenAI agents support
uv add veris-ai --extra agents

# All extras
uv add veris-ai --extra dev --extra fastapi --extra agents
```

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `VERIS_MOCK_TIMEOUT` | Tool mocking request timeout (seconds) | `90.0` |

---

## MCP Server

The SDK wraps [fastapi-mcp](https://github.com/tadata-org/fastapi_mcp) to expose your FastAPI endpoints as MCP tools with automatic session handling.

### Basic Setup

```python
from fastapi import FastAPI
from veris_ai import veris

app = FastAPI()

# Minimal setup
veris.set_fastapi_mcp(fastapi=app)
veris.fastapi_mcp.mount_http()
```

### Configuration Options

```python
veris.set_fastapi_mcp(
    fastapi=app,

    # Server metadata
    name="My API Server",
    description="API for user management",

    # Filter which endpoints become MCP tools
    include_operations=["get_user", "update_user"],  # Only these operation IDs
    # OR
    exclude_operations=["internal_cleanup"],          # All except these
)
```

**Filtering Rules:**
- Cannot use both `include_operations` and `exclude_operations`

### Accessing the MCP Server

The MCP server is available at `/mcp` on your FastAPI base URL:
- Local: `http://localhost:8000/mcp`
- Production: `https://your-api.com/mcp`

---

## Tool Mocking

Decorators control function behavior during simulations.

### @veris.mock()

Returns simulated responses when a session is active:

```python
from veris_ai import veris

@veris.mock()
async def get_account_balance(account_id: str) -> dict:
    """Get account balance."""
    return await bank_api.get_balance(account_id)
```

**Options:**

```python
@veris.mock(
    mode="tool",           # "tool" (default) or "function"
    expects_response=True, # Whether to wait for mock response
    cache_response=False,  # Cache responses for identical calls
)
```

### @veris.spy()

Executes the original function and logs the call/response:

```python
@veris.spy()
async def process_payment(amount: float, recipient: str) -> dict:
    """Process a payment - logs but executes normally."""
    return await payment_api.send(amount, recipient)
```

### @veris.stub()

Returns a fixed value during simulations:

```python
@veris.stub(return_value={"status": "success", "id": "test-123"})
async def create_order(items: list) -> dict:
    """Create order - returns stub in simulation."""
    return await order_api.create(items)
```

### Decorator Behavior Summary

| Decorator | Session Active | No Session |
|-----------|---------------|------------|
| `@veris.mock()` | Returns simulated response | Executes normally |
| `@veris.spy()` | Executes and logs | Executes normally |
| `@veris.stub()` | Returns fixed value | Executes normally |

---

## Simulation Context

When building custom agents (not using the OpenAI Agents SDK), wrap your agent execution in a context manager to activate simulation mode:

```python
from fastapi import FastAPI
from veris_ai import veris

app = FastAPI()

@veris.mock()
async def search_web(query: str) -> str:
    """Search the web."""
    return await search_api.query(query)

@app.post("/chat")
async def chat(message: str):
    # Wrap agent execution to enable tool mocking during simulations
    async with veris.target_context_async("my_agent"):
        result = await my_custom_agent.run(message)
    return {"response": result}

veris.set_fastapi_mcp(fastapi=app)
veris.fastapi_mcp.mount_http()
```

A sync version is also available:

```python
with veris.target_context("my_agent"):
    result = my_sync_agent.run(message)
```

**When to use:**
- Custom agent implementations that don't use `veris.Runner` or OpenAI's `Runner`
- Direct LLM API calls with tool execution loops
- Any code where decorated tools should be mocked during simulations

**Note:** The Veris `Runner` (below) handles this automatically—you only need explicit context managers for custom implementations.

---

## Veris Runner

For [OpenAI Agents](https://github.com/openai/openai-agents-python), use the Veris `Runner` to intercept tool calls without modifying tool code.

### Installation

```bash
uv add veris-ai --extra agents
```

### Basic Usage

```python
from veris_ai import Runner
from agents import Agent, function_tool

@function_tool
def calculator(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

agent = Agent(
    name="Assistant",
    model="gpt-4",
    tools=[calculator],
)

# Use Veris Runner instead of OpenAI's Runner
result = await Runner.run(agent, "What's 10 + 5?")
```

### Selective Tool Interception

```python
from veris_ai import Runner, VerisConfig

# Only intercept specific tools
config = VerisConfig(include_tools=["calculator", "search"])
result = await Runner.run(agent, "Calculate 2+2", veris_config=config)

# Or exclude specific tools
config = VerisConfig(exclude_tools=["get_weather"])
result = await Runner.run(agent, "Check weather", veris_config=config)
```

### Per-Tool Configuration

```python
from veris_ai import Runner, VerisConfig, ToolCallOptions, ResponseExpectation

config = VerisConfig(
    tool_options={
        "calculator": ToolCallOptions(
            response_expectation=ResponseExpectation.REQUIRED,
            cache_response=True,
        ),
        "search": ToolCallOptions(
            response_expectation=ResponseExpectation.NONE,
        ),
    }
)

result = await Runner.run(agent, "Calculate and search", veris_config=config)
```

---

## Development

```bash
# Install with dev dependencies
uv add veris-ai --extra dev

# Lint and format
ruff check --fix .
ruff format .

# Run tests
pytest tests/ --cov=veris_ai

# Type check
mypy src/veris_ai
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
