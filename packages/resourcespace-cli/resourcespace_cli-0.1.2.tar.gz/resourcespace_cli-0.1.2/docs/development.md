# Development Guide

Guide for contributing to the ResourceSpace CLI project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A ResourceSpace instance for testing (optional)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/TidalStudio/ResourceSpace-CLI.git
cd ResourceSpace-CLI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Unix/macOS:
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check CLI works
rs --version

# Run tests
pytest

# Run linter
ruff check src/
```

---

## Project Structure

```
ResourceSpace-CLI/
├── src/resourcespace_cli/
│   ├── __init__.py              # Version info
│   ├── main.py                  # CLI entry point
│   ├── client.py                # ResourceSpace API client
│   ├── config.py                # Configuration management
│   ├── exceptions.py            # Custom exception classes
│   ├── output.py                # Output formatting utilities
│   ├── commands/                # CLI command implementations
│   │   ├── search.py
│   │   ├── download.py
│   │   ├── upload.py
│   │   ├── info.py
│   │   ├── collections.py
│   │   ├── config.py
│   │   └── types.py
│   ├── api/                     # API function implementations
│   │   ├── search.py
│   │   ├── resources.py
│   │   ├── upload.py
│   │   └── types.py
│   └── utils/                   # Utility modules
│       ├── errors.py
│       ├── validation.py
│       └── files.py
├── tests/                       # Test files
├── docs/                        # Documentation
├── pyproject.toml               # Project configuration
└── README.md
```

---

## Development Tools

### Ruff (Linting & Formatting)

Ruff is used for both linting and code formatting.

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/

# Check formatting without changing
ruff format src/ --check
```

### Mypy (Type Checking)

The project uses strict type checking.

```bash
# Run type checker
python -m mypy src/

# Or with specific options
mypy --strict src/
```

### Pytest (Testing)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/resourcespace_cli

# Run specific test file
pytest tests/test_search.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_search.py::test_basic_search
```

---

## Code Style

### General Guidelines

1. **Type hints everywhere** - All functions should have type annotations
2. **Docstrings** - Public functions need docstrings
3. **Keep it simple** - Prefer clear, readable code over clever solutions
4. **Error handling** - Use custom exceptions from `exceptions.py`

### Example Function

```python
from resourcespace_cli.exceptions import ValidationError


def process_resource(resource_id: int, options: dict[str, str] | None = None) -> dict:
    """Process a resource with the given options.

    Args:
        resource_id: The ID of the resource to process.
        options: Optional processing options.

    Returns:
        A dictionary containing the processed resource data.

    Raises:
        ValidationError: If the resource_id is invalid.
    """
    if resource_id <= 0:
        raise ValidationError("Resource ID must be positive")

    # Implementation...
    return {"id": resource_id, "processed": True}
```

### Import Order

Imports should be ordered:
1. Standard library
2. Third-party packages
3. Local imports

Ruff will enforce this automatically.

---

## Adding a New Command

### 1. Create the Command File

Create a new file in `src/resourcespace_cli/commands/`:

```python
# src/resourcespace_cli/commands/mycommand.py
import click

from resourcespace_cli.config import get_config
from resourcespace_cli.client import ResourceSpaceClient
from resourcespace_cli.output import print_table, print_json


@click.command()
@click.argument("resource_id", type=int)
@click.pass_context
def mycommand(ctx: click.Context, resource_id: int) -> None:
    """Description of what mycommand does."""
    config = get_config()
    client = ResourceSpaceClient(config)

    result = client.my_api_call(resource_id)

    if ctx.obj.get("json"):
        print_json(result)
    else:
        print_table(result, columns=["id", "name"])
```

### 2. Register the Command

Add the command to `src/resourcespace_cli/main.py`:

```python
from resourcespace_cli.commands.mycommand import mycommand

# In the cli group
cli.add_command(mycommand)
```

### 3. Add Tests

Create `tests/test_mycommand.py`:

```python
from click.testing import CliRunner

from resourcespace_cli.main import cli


def test_mycommand_basic():
    runner = CliRunner()
    result = runner.invoke(cli, ["mycommand", "12345"])
    assert result.exit_code == 0
```

---

## Adding API Functions

API functions go in `src/resourcespace_cli/api/`:

```python
# src/resourcespace_cli/api/myfeature.py
from resourcespace_cli.client import ResourceSpaceClient


def get_something(client: ResourceSpaceClient, resource_id: int) -> dict:
    """Get something from the API.

    Args:
        client: The API client.
        resource_id: The resource ID.

    Returns:
        The API response as a dictionary.
    """
    return client.call_api("do_something", {"ref": resource_id})
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_search.py       # Search command tests
├── test_download.py     # Download command tests
├── test_upload.py       # Upload command tests
├── test_config.py       # Config command tests
├── test_client.py       # API client tests
└── test_validation.py   # Input validation tests
```

### Using Fixtures

Common fixtures are in `conftest.py`:

```python
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration."""
    monkeypatch.setenv("RESOURCESPACE_API_URL", "https://test.example.com/api")
    monkeypatch.setenv("RESOURCESPACE_API_KEY", "test-key")
    monkeypatch.setenv("RESOURCESPACE_USER", "test-user")
```

### Mocking HTTP Requests

Use `pytest-httpx` for mocking HTTP:

```python
def test_search(httpx_mock, runner, mock_config):
    httpx_mock.add_response(
        url="https://test.example.com/api",
        json=[{"ref": 1, "title": "Test"}]
    )

    result = runner.invoke(cli, ["search", "test"])
    assert result.exit_code == 0
```

---

## Pull Request Process

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make your changes** with tests
4. **Run quality checks**:
   ```bash
   ruff check src/
   ruff format src/
   mypy src/
   pytest
   ```
5. **Commit with clear messages**: `git commit -m "Add my feature"`
6. **Push to your fork**: `git push origin feature/my-feature`
7. **Open a Pull Request** on GitHub

### Commit Message Format

```
<type>: <short description>

<optional longer description>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

---

## Release Process

Releases are managed through GitHub:

1. Update version in `src/resourcespace_cli/__init__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will build and publish to PyPI

---

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [ResourceSpace API Documentation](https://www.resourcespace.com/knowledge-base/api)
