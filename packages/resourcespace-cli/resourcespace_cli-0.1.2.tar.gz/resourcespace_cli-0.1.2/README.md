# ResourceSpace CLI

[![PyPI version](https://badge.fury.io/py/resourcespace-cli.svg)](https://badge.fury.io/py/resourcespace-cli)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool for interacting with ResourceSpace digital asset management systems.

## Quick Start

```bash
# Install
pip install resourcespace-cli

# Configure
rs config set url https://your-resourcespace.com/api
rs config set key your-api-key
rs config set user your-username

# Start using
rs search "landscape photos"
rs download 12345
rs upload photo.jpg
```

## Features

- **Search & Discovery** - Search resources with filters, view details, list collections and types
- **Download** - Download single resources or batch download by search query
- **Upload** - Upload files with metadata, supports glob patterns and batch operations
- **Configuration** - Secure credential storage with .env file support
- **Flexible Output** - Human-readable tables or JSON for scripting
- **Progress Tracking** - Visual progress bars for batch operations

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `rs search` | Search for resources | `rs search "photo" --type 1` |
| `rs info` | Display resource details | `rs info 12345` |
| `rs download` | Download resources | `rs download 12345 -o ./` |
| `rs upload` | Upload files | `rs upload *.jpg --type 2` |
| `rs collections list` | List collections | `rs collections list` |
| `rs types list` | List resource types | `rs types list` |
| `rs config set` | Set configuration | `rs config set url https://...` |
| `rs config get` | View configuration | `rs config get` |
| `rs config clear` | Clear configuration | `rs config clear --all` |

### Global Options

- `--json` - Output results as JSON
- `--no-color` - Disable colored output
- `--version` - Show version information
- `--help` - Show help for any command

## Installation

**Using pip:**
```bash
pip install resourcespace-cli
```

**Using pipx (recommended for CLI tools):**
```bash
pipx install resourcespace-cli
```

**Development installation:**
```bash
git clone https://github.com/TidalStudio/ResourceSpace-CLI.git
cd ResourceSpace-CLI
pip install -e ".[dev]"
```

## Configuration

The CLI uses environment variables or a `.env` file for configuration:

| Variable | Description |
|----------|-------------|
| `RESOURCESPACE_API_URL` | Your ResourceSpace API endpoint |
| `RESOURCESPACE_API_KEY` | Your API key |
| `RESOURCESPACE_USER` | Your username |

Use `rs config set` commands for easy setup, or create a `.env` file manually.

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Command Reference](docs/commands.md)
- [Common Workflows](docs/workflows.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development Guide](docs/development.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
