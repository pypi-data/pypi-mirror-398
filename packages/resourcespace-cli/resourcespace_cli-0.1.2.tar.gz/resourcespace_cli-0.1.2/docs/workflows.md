# Common Workflows

Practical examples of common tasks using the ResourceSpace CLI.

## Getting Started

### Initial Setup

```bash
# Install the CLI
pip install resourcespace-cli

# Configure credentials
rs config set url https://dam.company.com/api
rs config set key your-api-key
rs config set user your-username

# Verify connection
rs types list
```

### Explore Your ResourceSpace

```bash
# See what resource types are available
rs types list

# See what collections exist
rs collections list

# Do a quick search
rs search "test"
```

---

## Searching for Resources

### Basic Search

```bash
# Simple keyword search
rs search "annual report"

# Search within a specific type
rs search "photo" --type 1

# Search within a collection
rs search "2024" --collection 5
```

### Paginated Results

```bash
# Get more results per page
rs search "landscape" --limit 100

# Navigate to page 2
rs search "landscape" --page 2 --limit 100
```

### Search and Process with JSON

```bash
# Get just the resource IDs
rs --json search "photo" | jq -r '.[].ref'

# Count results
rs --json search "document" | jq 'length'

# Get titles only
rs --json search "report" | jq -r '.[].title'
```

---

## Downloading Resources

### Download Single Resource

```bash
# Download to current directory
rs download 12345

# Download to specific folder
rs download 12345 --output ./downloads

# Stream to stdout (useful for piping)
rs download 12345 --stdout > my-file.jpg
```

### Batch Download

```bash
# Download all results from a search
rs download --search "landscape" --output ./landscapes

# Download from a specific collection
rs download --search "" --collection 5 --output ./collection-backup

# Download specific type
rs download --search "report" --type 2 --output ./reports
```

### Download with Processing

```bash
# Download and convert (example with ImageMagick)
rs download 12345 --stdout | convert - -resize 800x600 thumbnail.jpg

# Download and upload elsewhere
rs download 12345 --stdout | curl -X POST -F "file=@-" https://other-service.com/upload
```

---

## Uploading Resources

### Upload Single File

```bash
# Basic upload
rs upload photo.jpg

# Specify resource type
rs upload document.pdf --type 2

# Add to a collection
rs upload photo.jpg --collection 5
```

### Upload with Metadata

```bash
# Set a single field
rs upload photo.jpg --field "8=Photo Title"

# Set multiple fields
rs upload report.pdf --field "8=Annual Report" --field "3=Financial summary for 2024"

# Combine with type and collection
rs upload photo.jpg --type 1 --collection 10 --field "8=Sunset Photo"
```

### Batch Upload

```bash
# Upload all JPGs in current directory
rs upload *.jpg

# Upload recursively
rs upload photos/**/*.jpg

# Upload with type for all
rs upload *.pdf --type 2

# Upload to collection
rs upload images/*.png --collection 5
```

### Upload from File List

```bash
# Using find
find ./photos -name "*.jpg" | rs upload --stdin

# Using ls
ls *.pdf | rs upload --stdin --type 2

# From a text file
cat files-to-upload.txt | rs upload --stdin
```

---

## Working with Collections

### List Collections

```bash
# View all collections
rs collections list

# Get as JSON
rs --json collections list | jq '.[] | "\(.ref): \(.name) (\(.count) items)"'
```

### Search Within Collection

```bash
# Search in specific collection
rs search "photo" --collection 5

# Get all items in a collection (empty search)
rs search "" --collection 5 --limit 1000
```

### Upload to Collection

```bash
# Upload single file to collection
rs upload photo.jpg --collection 5

# Batch upload to collection
rs upload *.jpg --collection 5
```

---

## Scripting and Automation

### Basic Scripting Pattern

```bash
#!/bin/bash

# Search and download all matching resources
for id in $(rs --json search "quarterly" --type 2 | jq -r '.[].ref'); do
    rs download "$id" --output ./quarterly-reports
done
```

### Error Handling

```bash
#!/bin/bash

# Check if configured
if ! rs types list > /dev/null 2>&1; then
    echo "Error: ResourceSpace CLI not configured"
    echo "Run: rs config set url <url>"
    exit 1
fi

# Proceed with operations
rs search "document"
```

### Backup Workflow

```bash
#!/bin/bash

BACKUP_DIR="./backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Download all resources from each collection
for collection in $(rs --json collections list | jq -r '.[].ref'); do
    echo "Backing up collection $collection..."
    rs download --search "" --collection "$collection" --output "$BACKUP_DIR/collection-$collection"
done

echo "Backup complete: $BACKUP_DIR"
```

### Bulk Metadata Update (via re-upload)

```bash
#!/bin/bash

# Note: ResourceSpace API may support direct metadata updates
# This example shows a pattern for processing resources

rs --json search "needs-update" | jq -r '.[].ref' | while read id; do
    echo "Processing resource $id..."
    rs --json info "$id" > "/tmp/resource-$id.json"
    # Process as needed
done
```

---

## Integration Examples

### With jq (JSON Processing)

```bash
# Pretty print search results
rs --json search "photo" | jq '.'

# Extract specific fields
rs --json search "photo" | jq '[.[] | {id: .ref, title: .title}]'

# Filter results
rs --json search "document" | jq '[.[] | select(.title | contains("2024"))]'
```

### With xargs

```bash
# Download multiple resources in parallel
rs --json search "photo" | jq -r '.[].ref' | xargs -P 4 -I {} rs download {} --output ./photos
```

### With CI/CD

```yaml
# Example GitHub Actions step
- name: Upload assets to ResourceSpace
  env:
    RESOURCESPACE_API_URL: ${{ secrets.RS_URL }}
    RESOURCESPACE_API_KEY: ${{ secrets.RS_KEY }}
    RESOURCESPACE_USER: ${{ secrets.RS_USER }}
  run: |
    pip install resourcespace-cli
    rs upload ./dist/*.pdf --type 2 --collection 10
```

---

## Tips and Best Practices

1. **Use JSON output for scripting** - The `--json` flag provides structured data ideal for automation

2. **Check types before uploading** - Use `rs types list` to find the correct type ID

3. **Use collections for organization** - Upload related files to the same collection

4. **Batch operations are efficient** - Use glob patterns or `--stdin` for multiple files

5. **Handle pagination for large searches** - Default limit is 20, increase with `--limit`

6. **Test with dry runs** - Use `rs search` before `rs download --search` to verify results
