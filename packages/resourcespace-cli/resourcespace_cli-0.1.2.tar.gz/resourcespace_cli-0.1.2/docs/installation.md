# Installation Guide

## Requirements

- Python 3.11 or higher
- pip or pipx package manager

## Installation Methods

### Using pip (simplest)

```bash
pip install resourcespace-cli
```

### Using pipx (recommended for CLI tools)

[pipx](https://pypa.github.io/pipx/) installs the CLI in an isolated environment while making it available globally:

```bash
pipx install resourcespace-cli
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/TidalStudio/ResourceSpace-CLI.git
cd ResourceSpace-CLI
pip install -e .
```

### Development Installation

For contributing or development work, install with dev dependencies:

```bash
git clone https://github.com/TidalStudio/ResourceSpace-CLI.git
cd ResourceSpace-CLI
pip install -e ".[dev]"
```

This includes:
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting

## Verifying Installation

After installation, verify the CLI is working:

```bash
rs --version
```

You should see the version number output.

## Next Steps

After installation, you need to configure the CLI with your ResourceSpace credentials:

```bash
rs config set url https://your-resourcespace.com/api
rs config set key your-api-key
rs config set user your-username
```

See the [Configuration Guide](configuration.md) for detailed setup instructions.

## Upgrading

### Using pip

```bash
pip install --upgrade resourcespace-cli
```

### Using pipx

```bash
pipx upgrade resourcespace-cli
```

## Uninstalling

### Using pip

```bash
pip uninstall resourcespace-cli
```

### Using pipx

```bash
pipx uninstall resourcespace-cli
```
