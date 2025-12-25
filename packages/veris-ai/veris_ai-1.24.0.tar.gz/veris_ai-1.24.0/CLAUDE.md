# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Veris AI Python SDK - a package that provides simulation capabilities through decorator-based function mocking and FastAPI MCP (Model Context Protocol) integration. The core functionality revolves around:
- `VerisSDK` class in `src/veris_ai/tool_mock.py:27` - enables environment-aware execution where functions can be mocked in simulation mode, spied on, or executed normally in production
- `@veris.spy()` decorator - executes original functions while logging calls and responses via logging endpoints
- `convert_to_type()` function in `src/veris_ai/utils.py:5` - handles sophisticated type conversion from mock responses
- `FastApiMCPParams` model in `src/veris_ai/models.py:1` - provides configuration for integrating FastAPI applications with the Model Context Protocol
- `set_fastapi_mcp()` method in `src/veris_ai/tool_mock.py:54` - configures FastAPI MCP server with automatic OAuth2-based session management
- Logging utilities in `src/veris_ai/logging.py` - provide async and sync functions for logging tool calls and responses to VERIS endpoints
- `SimulatorAPIClient` class in `src/veris_ai/api_client.py` - centralized client for making requests to VERIS simulation endpoints with automatic authentication

## Development Commands

This project uses `uv` as the package manager and follows modern Python tooling practices.

### Setup
```bash
# Install base package
uv add veris-ai

# Install with development dependencies
uv add "veris-ai[dev]"

# Install with FastAPI MCP integration
uv add "veris-ai[fastapi]"

# Install with all extras
uv add "veris-ai[dev,fastapi,observability,agents]"

# Set Python version (requires 3.11+)
pyenv local 3.11.0
```

### Code Quality (Primary: Ruff)
```bash
# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code  
ruff format .

# Check formatting only
ruff format --check .
```

### Type Checking
```bash
# Run static type checking
mypy src/veris_ai tests
```

### Testing
```bash
# Run all tests with coverage
pytest tests/ --cov=veris_ai --cov-report=xml --cov-report=term-missing

# Run specific test file
pytest tests/test_tool_mock.py

# Run tests with verbose output
pytest -v tests/
```

### Building
```bash
# Build package distributions
uv build
```

## Code Architecture

### Core Components

**VerisSDK Class** (`src/veris_ai/tool_mock.py:27`)
- Main SDK class that provides decorator functionality:
  - `@veris.mock()`: Dynamic mocking that calls external endpoints for responses
  - `@veris.stub()`: Simple stubbing with fixed return values
  - `@veris.spy()`: Logging decorator that executes original function and logs the call/response
- Session-based activation: Uses session ID presence to determine mocking behavior
- HTTP communication with mock endpoints via `httpx` (for mock decorator)
- Context extraction for session management via context variables
- Delegates type conversion to the utils module
- Automatic API endpoint configuration with production defaults

**API Surface** (`src/veris_ai/__init__.py:5`)
- Exports single `veris` instance for public use
- Clean, minimal API design

**Type Conversion Utilities** (`src/veris_ai/utils.py:1`)
- `convert_to_type()` function handles sophisticated type conversion from mock responses
- Supports primitives, lists, dictionaries, unions, and custom types
- Modular design with separate conversion functions for each type category
- Uses Python's typing system for runtime type checking

**FastAPI MCP Integration** (`src/veris_ai/models.py:1`)
- `FastApiMCPParams` Pydantic model for configuring FastAPI MCP server integration
- Comprehensive configuration options including:
  - Custom server naming and descriptions
  - HTTP client configuration (base URL, headers, timeout)
  - Operation filtering (include/exclude by operation ID or tag)
  - Response schema documentation controls
  - Authentication configuration

### Environment Configuration

Environment variables:
- `VERIS_API_KEY`: API authentication key for VERIS services (optional, but recommended for production)
- `VERIS_MOCK_TIMEOUT`: Request timeout in seconds (optional, default: 90.0)

**Note**: The SDK automatically connects to the production VERIS API endpoint (`https://simulation.api.veris.ai/`). Only override `VERIS_API_URL` if you need to use a custom endpoint (rarely needed).

### Session-Based Activation

The SDK activates mocking based on session ID presence:
- **With session ID**: Routes calls to mock/simulator endpoint
- **Without session ID**: Executes original function
- Session IDs can be set manually via `veris.set_session_id()` or extracted automatically from OAuth2 tokens in FastAPI MCP integration

### Type System

The SDK handles sophisticated type conversion from mock responses:
- Type conversion is handled by the `convert_to_type()` function in `src/veris_ai/utils.py`
- Supports primitives, lists, dictionaries, unions, and custom types
- Modular design with separate handlers for different type categories
- Uses Python's typing system for runtime type checking

## Testing Strategy

**Test Structure**:
- `tests/conftest.py:1`: Pytest fixtures for environment mocking and context objects
- `tests/test_tool_mock.py:1`: Unit tests for the VerisSDK class and mock decorator functionality
- `tests/test_utils.py:1`: Comprehensive tests for type conversion utilities

**Key Test Fixtures**:
- `mock_context`: Provides mock context with session ID
- `simulation_env`: Sets up simulation mode with session ID  
- `production_env`: Sets up production mode without session ID

**Test Coverage Areas**:
- Environment-based behavior switching
- HTTP client interactions and error handling
- Type conversion scenarios (parametrized tests)
- Configuration validation

## Code Quality Standards

**Ruff Configuration** (80+ rules enabled):
- Line length: 100 characters
- Target: Python 3.11+
- Google-style docstring convention
- Comprehensive rule set covering style, bugs, security, and complexity
- Relaxed rules for test files (allows more flexibility in tests)

**Development Tools**:
- **Ruff**: Primary linter and formatter (replaces flake8, black, isort)
- **MyPy**: Static type checking
- **Pytest**: Testing with async support and coverage
- **Pre-commit**: Git hooks for code quality

## CI/CD Pipeline

**Testing Workflow** (`.github/workflows/test.yml`):
- Runs on Python 3.11, 3.12, 3.13
- Code quality checks (Ruff lint/format)
- Type checking (MyPy)  
- Unit tests with coverage

**Release Workflow** (`.github/workflows/release.yml`):
- Manual trigger for releases
- Semantic versioning with conventional commits
- Automated PyPI publishing
- Uses `uv build` for package building

## Key Implementation Details

- **Decorator Pattern**: Functions are wrapped to intercept calls in simulation mode
  - `@veris.mock()`: Sends function metadata to external endpoint for dynamic responses
  - `@veris.stub()`: Returns predetermined values without external calls
  - `@veris.spy()`: Executes original function while logging calls and responses
- **Session Management**: Extracts session ID from context for request correlation
- **API Client**: Centralized `SimulatorAPIClient` handles all API communication
  - Automatic endpoint configuration with production defaults
  - Built-in authentication via `VERIS_API_KEY` header
  - Configurable timeout with `VERIS_MOCK_TIMEOUT`
- **Error Handling**: Comprehensive HTTP and type conversion error handling
- **Async Support**: Built with async/await pattern throughout
- **Type Safety**: Full type hints and runtime type conversion validation
- **Modular Architecture**: Type conversion logic separated into utils module for better maintainability

### FastAPI MCP Integration

The `set_fastapi_mcp()` method provides:
- **Automatic Session Handling**: OAuth2-based session ID extraction from bearer tokens
- **Context Management**: Session IDs are stored in context variables for cross-request correlation
- **Auth Config Merging**: User-provided auth configs are merged with internal session handling
- **MCP Server Access**: Configured server available via `veris.fastapi_mcp` property

Key implementation aspects:
- Creates internal OAuth2PasswordBearer scheme for token extraction
- Dependency injection for automatic session context setting
- Preserves user auth configurations while adding session management
- SSE (Server-Sent Events) support for streaming responses

## Documentation Handling Guidelines

### Dual‑Use Overview

* **Humans**: READMEs must be narrative‑driven, intuitive, and structured for readability, with inline cross‑links to related READMEs or code modules for deeper context.
* **LLM Agents**: Treat these same READMEs as semantic routers. Use linked references and tags within the document to locate the most relevant code, tests, and workflows — never treat the README as the ultimate logic source.
* **Shared Goal**: Documentation must actively fight codebase complexity. Instead of growing endlessly, it should simplify, subtract redundancy, and delegate details to lower‑level READMEs in the hierarchy.

---

### When to Update Documentation

Trigger updates upon significant changes including:

* Major features, refactors, or architectural/schematic changes
* Workflow updates or dependencies added/removed
* Changes affecting user interactions or onboarding

**Heuristic**: If the change alters how a human would interact or mentally model the system — or how the LLM navigates it — it calls for a README update.

Updates should simplify where possible: remove outdated or redundant content, and delegate specifics via cross‑links (e.g., *See [Auth Module README](./auth/README.md) for details on authentication flows*).

---

### LLM‑Driven Continuous Documentation

1. **End‑of‑session reflection**: At task completion, the LLM should summarize the work and, if needed, update the README with clarifications or new links to relevant modules.
2. **Parallel instance memory**: Maintain awareness of session context across LLM instances to keep documentation aligned with ongoing workflows.
3. **LLM as thought partner**: Propose not only wording edits but also simplifications and delegation opportunities — e.g., linking to an existing module README rather than duplicating logic.
4. **Complexity management**: Treat every update as a chance to prune. The README should remain a high‑level, navigable entry point, not a catch‑all.

---

### Structure & Format

Each meaningful workspace or module must include a `README.md` designed to operate like a **hub page** in an IDE‑backed website:

* **Quick Reference**: Purpose, setup, usage, and high‑level architecture.
* **Linked Context**: Cross‑links to deeper READMEs, design docs, or code directories.
* **Semantic Anchors**: Inline cues (e.g., tags, headings, links) that help the LLM map concepts to code without requiring redundant prose.

> Example:
> *“For transaction processing, see [Transactions README](./transactions/README.md). For error handling logic, see [Error Handling README](./errors/README.md).”*

The human and LLM share the same document: humans follow the narrative, while the LLM uses references and anchors to navigate the codebase semantically.

---

### Workflow Roles

#### LLM Responsibilities

* Detect README drift by comparing live code to described behavior.
* Perform updates with an emphasis on pruning duplication and linking to existing READMEs.
* Use end‑of‑session summaries to suggest or implement simplifications.
* Ensure docs remain aligned with code without ballooning in size.

#### Human Responsibilities

* Review LLM‑driven updates for clarity, accuracy, and usability.
* Refactor prose when needed to keep explanations intuitive.
* Validate that cross‑links resolve correctly and are helpful for navigation.

---

### Key Principles

| Principle                  | Description                                                               |
| -------------------------- | ------------------------------------------------------------------------- |
| **Code is truth**          | Source code is definitive; README is a semantic guide, not the authority. |
| **Documentation evolves**  | Updates happen with real usage, not on a fixed schedule.                  |
| **Simplicity over sprawl** | Fight complexity by pruning, delegating, and cross‑linking.               |
| **One README, two roles**  | The same README serves both humans and LLMs through cross‑referencing.    |
| **Real‑world grounding**   | Updates reflect actual changes in workflows and architecture.             |
| **Human validation**       | LLM edits require human review to ensure usability and accuracy.          |
