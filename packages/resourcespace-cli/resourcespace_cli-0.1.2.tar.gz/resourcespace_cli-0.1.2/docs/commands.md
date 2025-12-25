# Command Reference

Complete reference for all ResourceSpace CLI commands.

## Global Options

These options work with all commands:

| Option | Description |
|--------|-------------|
| `--json` | Output results as JSON instead of formatted tables |
| `--no-color` | Disable colored terminal output |
| `--version` | Show version information |
| `--help` | Show help message |

## Configuration Commands

### rs config set

Set a configuration value.

```bash
rs config set <KEY> <VALUE>
```

**Arguments:**
- `KEY` - Configuration key (url, key, user, or full names)
- `VALUE` - Value to set

**Key aliases:**
| Alias | Full Key |
|-------|----------|
| `url`, `api-url`, `api_url` | `RESOURCESPACE_API_URL` |
| `key`, `api-key`, `api_key` | `RESOURCESPACE_API_KEY` |
| `user`, `username` | `RESOURCESPACE_USER` |

**Examples:**
```bash
rs config set url https://dam.company.com/api
rs config set key abc123def456
rs config set user admin
rs config set RESOURCESPACE_API_URL https://dam.company.com/api
```

### rs config get

View configuration values.

```bash
rs config get [KEY] [OPTIONS]
```

**Arguments:**
- `KEY` (optional) - Specific key to view. If omitted, shows all values.

**Options:**
- `--show-values`, `-s` - Display actual values instead of masked values

**Examples:**
```bash
rs config get                    # Show all (masked)
rs config get url                # Show specific value
rs config get --show-values      # Show all with actual values
```

### rs config clear

Clear configuration values.

```bash
rs config clear [KEY] [OPTIONS]
```

**Arguments:**
- `KEY` (optional) - Specific key to clear

**Options:**
- `--all`, `-a` - Clear all configuration values
- `--yes`, `-y` - Skip confirmation prompt

**Examples:**
```bash
rs config clear url              # Clear specific key
rs config clear --all            # Clear all (with confirmation)
rs config clear --all --yes      # Clear all (no confirmation)
```

---

## Search & Discovery Commands

### rs search

Search for resources in ResourceSpace.

```bash
rs search <QUERY> [OPTIONS]
```

**Arguments:**
- `QUERY` (required) - Search query string (1-1000 characters)

**Options:**
- `--type TYPE_ID` - Filter by resource type ID
- `--collection COLLECTION_ID` - Filter by collection ID
- `--page PAGE` - Page number (default: 1, minimum: 1)
- `--limit LIMIT` - Results per page (default: 20, maximum: 1000)

**Output (default):**
- Rich table with columns: ID, Title, Preview URL

**Output (JSON):**
```json
[
  {
    "ref": 12345,
    "title": "Resource Title",
    "preview_url": "https://..."
  }
]
```

**Examples:**
```bash
rs search "landscape"
rs search "photo" --type 1
rs search "document" --collection 5
rs search "image" --page 2 --limit 50
rs --json search "landscape" | jq '.[0].ref'
```

### rs info

Display detailed information about a resource.

```bash
rs info <RESOURCE_ID>
```

**Arguments:**
- `RESOURCE_ID` (required) - Resource ID to display

**Output sections:**
1. **Basic Information** - Type, created date, filename, extension, file size
2. **Preview URL** - Direct link to preview image
3. **Metadata Fields** - All custom metadata with values
4. **Available Sizes** - Image variants/sizes available
5. **Alternative Files** - Additional file formats
6. **Collections** - Collections containing this resource

**Examples:**
```bash
rs info 12345
rs --json info 12345 | jq '.metadata'
```

### rs collections list

List all available collections.

```bash
rs collections list
```

**Output (default):**
- Table with columns: ID, Name, Resource Count

**Output (JSON):**
```json
[
  {
    "ref": 1,
    "name": "Collection Name",
    "count": 42
  }
]
```

**Examples:**
```bash
rs collections list
rs --json collections list | jq '.[].name'
```

### rs types list

List all available resource types.

```bash
rs types list
```

**Output (default):**
- Table with columns: ID, Name

**Output (JSON):**
```json
[
  {
    "ref": 1,
    "name": "Photo"
  },
  {
    "ref": 2,
    "name": "Document"
  }
]
```

**Examples:**
```bash
rs types list
rs --json types list | jq '.[] | "\(.ref): \(.name)"'
```

---

## File Operation Commands

### rs download

Download resources from ResourceSpace.

```bash
rs download [RESOURCE_ID] [OPTIONS]
```

**Arguments:**
- `RESOURCE_ID` (optional) - Resource ID to download (required unless using `--search`)

**Options:**
- `--output DIR`, `-o DIR` - Output directory (default: current directory)
- `--stdout` - Stream file contents to stdout (single resource only)
- `--search QUERY` - Batch download all resources matching the search query

**Behavior:**
- Shows progress bar during download
- Filename extracted from resource metadata or URL
- If file exists, appends resource ID to avoid conflicts
- Batch mode downloads all matching resources with progress tracking

**Examples:**
```bash
# Single resource
rs download 12345
rs download 12345 --output ./downloads
rs download 12345 --stdout > image.jpg

# Batch download
rs download --search "landscape" --output ./landscapes
rs download --search "2024" --type 2 --output ./docs
```

**Output (default):**
- Progress bar and success message with file path

**Output (JSON):**
```json
{
  "status": "success",
  "resource_id": 12345,
  "file_path": "/path/to/downloaded/file.jpg",
  "size": 1048576
}
```

### rs upload

Upload files to ResourceSpace.

```bash
rs upload <FILES>... [OPTIONS]
```

**Arguments:**
- `FILES` (required) - File paths or glob patterns (multiple allowed)

**Options:**
- `--type ID`, `-t ID` - Resource type ID (default: 1)
- `--collection ID`, `-c ID` - Add uploaded resources to this collection
- `--field FIELD`, `-f FIELD` - Set metadata field (format: `field_id=value`, repeatable)
- `--stdin` - Read file paths from stdin (one path per line)

**Behavior:**
- Supports glob patterns (`*.jpg`, `**/*.pdf`)
- Shows progress bar for batch uploads
- Returns resource ID(s) on success
- Can pipe file paths from other commands

**Examples:**
```bash
# Single file
rs upload photo.jpg
rs upload document.pdf --type 2

# With metadata
rs upload photo.jpg --field "8=Photo Title" --field "3=Description here"

# Add to collection
rs upload report.pdf --type 2 --collection 5

# Batch upload
rs upload *.jpg
rs upload photos/**/*.jpg --type 1 --collection 10

# From stdin
find . -name "*.pdf" | rs upload --stdin --type 2
ls *.jpg | rs upload --stdin
```

**Output (default):**
- Resource ID assigned to uploaded file
- For batch: summary of succeeded/failed uploads

**Output (JSON):**
```json
{
  "status": "success",
  "resource_id": 12346,
  "filename": "photo.jpg"
}
```

Batch upload JSON:
```json
{
  "succeeded": [
    {"resource_id": 12346, "filename": "photo1.jpg"},
    {"resource_id": 12347, "filename": "photo2.jpg"}
  ],
  "failed": [
    {"filename": "corrupt.jpg", "error": "Upload failed"}
  ],
  "total": 3,
  "succeeded_count": 2,
  "failed_count": 1
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (API error, validation error, file not found) |
| 2 | Configuration error (missing or invalid credentials) |

## Tips

- Use `--json` output for scripting and automation
- Combine with `jq` for powerful JSON processing
- Use `--help` on any command for quick reference
- Resource IDs are numeric - use `rs search` to find them
- Field IDs for `--field` option are numeric - check your ResourceSpace admin panel
