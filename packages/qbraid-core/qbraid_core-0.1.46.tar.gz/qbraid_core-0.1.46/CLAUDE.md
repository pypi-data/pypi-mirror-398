# qBraid Core Development Protocol

This document describes the development workflow, testing practices, and repository structure for the qBraid Core project.

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Development Workflow](#development-workflow)
3. [Testing with Tox](#testing-with-tox)
4. [Writing Unit Tests](#writing-unit-tests)
5. [Code Quality Standards](#code-quality-standards)
6. [Coverage Requirements](#coverage-requirements)
7. [Commit Workflow](#commit-workflow)

---

## Repository Structure

```
qbraid-core/
├── qbraid_core/           # Main source code
│   ├── services/          # Service implementations
│   │   ├── chat/          # Chat service client
│   │   ├── environments/  # Environment management
│   │   ├── mcp/          # MCP WebSocket client and router
│   │   ├── quantum/      # Quantum job submission and management
│   │   └── storage/      # Storage service client
│   ├── system/           # System utilities (executables, packages, versions)
│   └── *.py              # Core modules (config, client, sessions, etc.)
├── tests/                # Test suite mirroring source structure
│   ├── mcp/             # MCP tests
│   ├── quantum/         # Quantum service tests
│   └── ...
├── docs/                # Sphinx documentation
├── bin/                 # Executable scripts
├── pyproject.toml       # Project metadata and dependencies
├── tox.ini             # Test environment configuration
└── pytest.ini          # Pytest configuration (if separate from pyproject.toml)
```

### Key Directories

- **qbraid_core/services/**: Service client implementations for various qBraid cloud services
- **qbraid_core/system/**: System-level utilities for package management, executable discovery, etc.
- **tests/**: Comprehensive test suite with structure mirroring source code
- **docs/**: Sphinx documentation with API references

---

## Development Workflow

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd qbraid-core

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with all extras
pip install -e ".[test,runner,environments,mcp,docs]"
```

### 2. Make Changes

- Follow existing code patterns and style
- Add type hints to all function signatures
- Write docstrings for all public functions and classes
- Update tests to cover new functionality

### 3. Run Tests Locally

```bash
# Run full test suite
tox -e unit-tests

# Run specific test file
pytest tests/mcp/test_client.py

# Run with coverage report
pytest --cov=qbraid_core --cov-report=term
```

### 4. Check Code Quality

```bash
# Run all linters and formatters
tox -e format-check

# Auto-fix formatting issues
tox -e linters
```

### 5. Commit and Push

```bash
git add <files>
git commit -m "descriptive commit message"
git push origin <branch-name>
```

---

## Testing with Tox

Tox is used to manage test environments and ensure consistency. Key commands:

### Run Unit Tests

```bash
tox -e unit-tests
```

**What it does:**
- Installs the package with test, runner, environments, and mcp extras
- Runs pytest with coverage reporting
- Generates coverage.xml in build/coverage/
- Current target: 80%+ overall coverage

**Environment variables** (optional):
```bash
export QBRAID_API_KEY="your_api_key"       # For remote tests
export QBRAID_RUN_REMOTE_TESTS="true"      # Enable remote integration tests
export JUPYTERHUB_USER="username"          # For JupyterHub tests
```

### Run Format Checks

```bash
tox -e format-check
```

**What it does:**
- Runs pylint for code quality checks
- Runs isort to check import sorting
- Runs black to check code formatting
- Runs mypy for type checking
- Runs ruff for additional linting
- Checks copyright headers

**Target:** All checks must pass (10.00/10 score)

### Auto-fix Formatting

```bash
tox -e linters
```

**What it does:**
- Runs isort to sort imports
- Runs black to format code
- Fixes copyright headers automatically

### Individual Linters

```bash
tox -e pylint      # Run pylint only
tox -e black       # Run black only
tox -e isort       # Run isort only
tox -e mypy        # Run mypy only
tox -e ruff        # Run ruff only
tox -e headers     # Check copyright headers only
```

### Build Documentation

```bash
tox -e docs
```

**What it does:**
- Uses Sphinx to build HTML documentation
- Output: docs/build/html/

---

## Writing Unit Tests

### General Principles

1. **Test file naming**: Mirror source structure (e.g., `qbraid_core/services/mcp/client.py` → `tests/mcp/test_client.py`)
2. **Test function naming**: Use descriptive names starting with `test_`
3. **One concept per test**: Each test should verify one specific behavior
4. **Arrange-Act-Assert pattern**: Organize tests clearly
5. **Use fixtures**: Define reusable test components with pytest fixtures
6. **Mock external dependencies**: Use unittest.mock or pytest-mock

### Testing Async Code

For async functions, use `pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result == expected_value
```

### Mocking Patterns

#### Basic Mocking with unittest.mock

```python
from unittest.mock import Mock, AsyncMock, patch

def test_with_mock():
    """Test using Mock objects."""
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked_value"

    result = mock_obj.method()

    assert result == "mocked_value"
    mock_obj.method.assert_called_once()
```

#### Async Mocking

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_mock():
    """Test async functions with AsyncMock."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(return_value='{"result": "success"}')

    await mock_ws.send("test")
    response = await mock_ws.recv()

    mock_ws.send.assert_called_once_with("test")
    assert response == '{"result": "success"}'
```

#### Monkeypatching with pytest

```python
@pytest.mark.asyncio
async def test_with_monkeypatch(monkeypatch):
    """Test using monkeypatch for module-level patching."""
    import qbraid_core.services.mcp.client as client_module

    # Patch a module constant
    monkeypatch.setattr(client_module, "WEBSOCKETS_AVAILABLE", False)

    # Patch a function
    mock_connect = AsyncMock()
    monkeypatch.setattr(client_module.websockets, "connect", mock_connect)

    # Test code that uses the patched values
    # ...
```

#### Mocking WebSocket Connections

Example from `tests/mcp/test_client.py`:

```python
@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.ping = AsyncMock()
    mock_ws.close = AsyncMock()

    # Mock async iterator for receiving messages
    async def async_iter():
        messages = ['{"method": "test1"}', '{"method": "test2"}']
        for msg in messages:
            yield msg

    mock_ws.__aiter__ = lambda self: async_iter()
    return mock_ws

@pytest.mark.asyncio
async def test_websocket_communication(mock_websocket, monkeypatch):
    """Test WebSocket send/receive."""
    import qbraid_core.services.mcp.client as client_module

    # Patch the websockets.connect to return our mock
    monkeypatch.setattr(
        client_module,
        "websockets",
        Mock(connect=AsyncMock(return_value=mock_websocket))
    )

    # Create client and test
    client = MCPWebSocketClient(websocket_url="wss://test.example.com")
    await client.connect()
    await client.send({"method": "test"})

    # Verify mock was called correctly
    mock_websocket.send.assert_called_once()
```

#### Mocking with Side Effects

```python
@pytest.mark.asyncio
async def test_retry_on_failure(mock_websocket):
    """Test retry behavior on failure."""
    # First call fails, second succeeds
    mock_websocket.send.side_effect = [
        Exception("Send failed"),
        None  # Success on second call
    ]

    # Test code that handles retry logic
    # ...
```

### Pytest Fixtures

Define reusable test components:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def client():
    """Create a test client instance."""
    return MCPWebSocketClient(
        websocket_url="wss://test.example.com/mcp",
        name="test"
    )

@pytest.fixture
def client_with_callback():
    """Create a client with a message callback."""
    callback = Mock()
    client = MCPWebSocketClient(
        websocket_url="wss://test.example.com/mcp",
        on_message=callback,
        name="test"
    )
    return client, callback

# Use fixtures in tests
def test_client_initialization(client):
    """Test client is initialized correctly."""
    assert client.name == "test"
    assert client._is_connected is False
```

### Testing Error Cases

Always test both success and failure paths:

```python
@pytest.mark.asyncio
async def test_connection_timeout(client, monkeypatch):
    """Test connection timeout handling."""
    async def mock_wait_for(coro, timeout):
        raise asyncio.TimeoutError()

    monkeypatch.setattr("asyncio.wait_for", mock_wait_for)

    with pytest.raises(ConnectionError):
        await client.connect()

@pytest.mark.asyncio
async def test_connection_success(client, mock_websocket, monkeypatch):
    """Test successful connection."""
    monkeypatch.setattr(
        "websockets.connect",
        AsyncMock(return_value=mock_websocket)
    )

    await client.connect()

    assert client.is_connected is True
```

### Coverage Best Practices

1. **Aim for 80%+ coverage** overall
2. **Test all public APIs** thoroughly
3. **Test error paths** and edge cases
4. **Exclude known unTestable code** using `# pragma: no cover` sparingly
5. **Review coverage reports** in `build/coverage/coverage.xml`

**Check coverage:**
```bash
pytest --cov=qbraid_core --cov-report=term
```

**View detailed HTML report:**
```bash
pytest --cov=qbraid_core --cov-report=html
open build/coverage/index.html
```

---

## Code Quality Standards

### Style Guidelines

1. **Line length**: Maximum 100 characters
2. **Import sorting**: Use isort with black profile
3. **Code formatting**: Use black
4. **Type hints**: Required for all function signatures
5. **Docstrings**: Required for all public functions and classes

### Docstring Format

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    More detailed description if needed, explaining the purpose,
    behavior, and any important notes.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        ConnectionError: When connection fails

    Example:
        >>> result = example_function("test", 42)
        >>> assert result is True
    """
    # Implementation
    pass
```

### Type Hints

Always include type hints:

```python
from typing import Optional, Dict, List, Any, Callable

def process_data(
    data: Dict[str, Any],
    callback: Optional[Callable[[str], None]] = None,
    timeout: float = 30.0
) -> List[str]:
    """Process data with optional callback."""
    # Implementation
    pass
```

### Error Handling

Provide clear, actionable error messages:

```python
if not WEBSOCKETS_AVAILABLE:
    raise ImportError(
        "MCP WebSocket client requires the 'websockets' package. "
        "Install it with: pip install qbraid-core[mcp]"
    )
```

---

## Coverage Requirements

### Overall Target

- **Minimum**: 80% coverage
- **Goal**: 85%+ coverage

### Current Coverage (as of last run)

- **Overall**: 80.44%
- **MCP package**: 93.5%
  - client.py: 88%
  - discovery.py: 100%
  - router.py: 100%

### Excluded from Coverage

The following are automatically excluded (see `pyproject.toml`):

```python
# Excluded patterns in pyproject.toml [tool.coverage.report]
- raise NotImplementedError
- return NotImplemented
- except ImportError:
- def __repr__
- if __name__ == .__main__.:
- if TYPE_CHECKING:
- logger.debug
- logger.info
- __all__
- def __getattr__
- def __dir__
- # pragma: no cover
- pass
```

### Viewing Coverage Reports

**Terminal report:**
```bash
pytest --cov=qbraid_core --cov-report=term
```

**HTML report (detailed):**
```bash
pytest --cov=qbraid_core --cov-report=html
open build/coverage/index.html
```

**XML report (for CI/CD):**
```bash
pytest --cov=qbraid_core --cov-report=xml
# Output: build/coverage/coverage.xml
```

---

## Commit Workflow

### Branch Strategy

1. **Main branch**: `main` - stable production code
2. **Feature branches**: `feature/<name>` - new features
3. **Fix branches**: `fix/<name>` - bug fixes
4. **Release branches**: `release/<version>` - release preparation

### Before Committing

1. **Run tests**: `tox -e unit-tests`
2. **Check formatting**: `tox -e format-check`
3. **Auto-fix issues**: `tox -e linters` (if needed)
4. **Review changes**: `git diff`

### Commit Message Format

Use clear, descriptive commit messages:

```
<type>: <short summary>

<detailed description if needed>

<footer with issue references>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `style`: Code style changes (formatting, etc.)
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat: Add WebSocket client for MCP server communication

Implements MCPWebSocketClient with connection management,
heartbeat, and automatic reconnection logic.

Resolves #123
```

```
fix: Handle websockets import error gracefully

Add WEBSOCKETS_AVAILABLE flag and helpful error message
directing users to install qbraid-core[mcp] extra.

Fixes #456
```

### Pull Request Checklist

Before opening a PR:

- [ ] All tests pass (`tox -e unit-tests`)
- [ ] Format checks pass (`tox -e format-check`)
- [ ] Coverage maintained or improved (80%+ overall)
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear and descriptive

---

## Optional Dependencies

The project uses optional extras for different use cases:

```bash
# Core only (minimal dependencies)
pip install qbraid-core

# With quantum job runner
pip install qbraid-core[runner]

# With environment management
pip install qbraid-core[environments]

# With MCP WebSocket client
pip install qbraid-core[mcp]

# All extras (for development)
pip install qbraid-core[test,runner,environments,mcp,docs]
```

**Extras definition** (from `pyproject.toml`):
- `runner`: numpy, psutil
- `environments` (alias: `envs`): jupyter_client, ipython, pydantic, pyyaml, ipykernel
- `mcp`: websockets>=11.0
- `test`: pytest, pytest-cov, pytest-asyncio
- `docs`: sphinx and related documentation packages

---

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
```bash
# Solution: Install with test extras
pip install -e ".[test]"
```

**Issue**: Coverage report not generated
```bash
# Solution: Ensure pytest-cov is installed
pip install pytest-cov
```

**Issue**: Format check fails
```bash
# Solution: Auto-fix with linters
tox -e linters
```

**Issue**: Tox environment errors
```bash
# Solution: Recreate tox environments
tox -r -e unit-tests
```

**Issue**: WebSocket tests fail
```bash
# Solution: Install mcp extra
pip install -e ".[mcp]"
```

---

## Additional Resources

- **Main Documentation**: https://docs.qbraid.com/core
- **API Documentation**: https://qbraid.github.io/qbraid-core/
- **Issue Tracker**: https://github.com/qBraid/community/issues
- **Discord Community**: https://discord.gg/KugF6Cnncm

---

## Quick Reference

```bash
# Common commands
tox -e unit-tests              # Run all tests with coverage
tox -e format-check            # Check code quality (all linters)
tox -e linters                 # Auto-fix formatting issues
pytest tests/mcp/              # Run specific test directory
pytest -k test_client          # Run tests matching pattern
pytest --cov-report=html       # Generate HTML coverage report

# Development setup
pip install -e ".[test,mcp]"  # Install with test and MCP extras
git checkout -b feature/my-feature  # Create feature branch

# Before committing
tox -e unit-tests && tox -e format-check
```
