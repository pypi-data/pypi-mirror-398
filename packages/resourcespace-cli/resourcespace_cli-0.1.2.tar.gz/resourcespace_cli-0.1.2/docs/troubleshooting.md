# Troubleshooting Guide

Solutions for common issues when using the ResourceSpace CLI.

## Configuration Issues

### "Configuration error: Missing required configuration"

**Problem:** The CLI can't find one or more required configuration values.

**Solution:**
```bash
# Check current configuration
rs config get

# Set missing values
rs config set url https://your-resourcespace.com/api
rs config set key your-api-key
rs config set user your-username
```

### Configuration not persisting

**Problem:** Configuration values disappear after setting them.

**Possible causes:**
1. `.env` file in wrong location
2. Environment variables overriding file values
3. File permissions issue

**Solution:**
```bash
# Check where .env is being written
ls -la .env

# Ensure you're in the right directory
pwd

# Or specify a custom location
export RESOURCESPACE_ENV_PATH=/path/to/your/.env
rs config set url https://...
```

### "Permission denied" when saving configuration

**Problem:** Cannot write to the `.env` file.

**Solution:**
```bash
# Check file permissions
ls -la .env

# Fix permissions (Unix/macOS)
chmod 600 .env

# Or use a different location
export RESOURCESPACE_ENV_PATH=~/.resourcespace/.env
mkdir -p ~/.resourcespace
rs config set url https://...
```

---

## Connection Issues

### "Connection error: Unable to connect to server"

**Problem:** Cannot reach the ResourceSpace server.

**Check:**
1. Is the URL correct?
2. Is the server running?
3. Are you behind a firewall or VPN?

**Solution:**
```bash
# Verify the URL
rs config get url

# Test connectivity (curl)
curl -I https://your-resourcespace.com/api

# Update URL if needed
rs config set url https://correct-url.com/api
```

### "SSL certificate verify failed"

**Problem:** SSL/TLS certificate issues.

**Possible causes:**
1. Self-signed certificate
2. Expired certificate
3. Certificate chain issues

**Solution:**
- Contact your ResourceSpace administrator to fix the certificate
- For testing only (not recommended for production):
  ```bash
  # Set environment variable to skip verification (INSECURE)
  export HTTPX_SSL_VERIFY=false
  rs types list
  ```

### Timeout errors

**Problem:** Operations timing out.

**Possible causes:**
1. Slow network connection
2. Large file uploads/downloads
3. Server under heavy load

**Solution:**
- Check your network connection
- Try again during off-peak hours
- For large files, consider batch processing smaller sets

---

## Authentication Issues

### "API error: Access denied" or "Authentication failed"

**Problem:** API key or credentials are invalid.

**Solution:**
```bash
# Verify your credentials
rs config get --show-values

# Re-enter your API key
rs config set key your-correct-api-key

# Verify username
rs config set user your-username

# Test the connection
rs types list
```

### "API error: User does not have permission"

**Problem:** The API user lacks permission for the requested operation.

**Solution:**
- Contact your ResourceSpace administrator
- Request appropriate permissions for:
  - Search/view resources
  - Download resources
  - Upload resources
  - Manage collections (if needed)

---

## Search Issues

### No results returned

**Problem:** Search returns empty results.

**Check:**
1. Spelling of search terms
2. Resource type filter
3. Collection filter

**Solution:**
```bash
# Try a broader search
rs search "*"

# Remove filters
rs search "photo"  # Without --type or --collection

# Check if resources exist
rs types list
rs collections list
```

### "Validation error: Search query must be 1-1000 characters"

**Problem:** Search query too long or empty.

**Solution:**
```bash
# Use a shorter query
rs search "annual report"

# For empty search (get all), use wildcard or empty quotes
rs search ""
rs search "*"
```

---

## Download Issues

### "Download error: Resource not found"

**Problem:** The resource ID doesn't exist.

**Solution:**
```bash
# Verify the resource exists
rs info 12345

# Search for the resource
rs search "filename"
```

### Downloaded file is corrupted or wrong type

**Problem:** File doesn't open correctly.

**Possible causes:**
1. Download interrupted
2. Wrong file extension
3. Server-side issue

**Solution:**
```bash
# Re-download the file
rs download 12345 --output ./new-download

# Check file info first
rs info 12345

# Try with --stdout to inspect
rs download 12345 --stdout | file -
```

### "File already exists"

**Problem:** A file with the same name exists in the output directory.

**Behavior:** The CLI automatically appends the resource ID to avoid conflicts.

**If you want to overwrite:**
```bash
# Delete existing file first
rm existing-file.jpg
rs download 12345
```

---

## Upload Issues

### "Upload error: File not found"

**Problem:** The specified file doesn't exist.

**Solution:**
```bash
# Check file exists
ls -la photo.jpg

# Use full path
rs upload /full/path/to/photo.jpg

# Check glob pattern
ls *.jpg  # See what matches
rs upload *.jpg
```

### "Upload error: Permission denied"

**Problem:** Cannot read the file.

**Solution:**
```bash
# Check file permissions
ls -la photo.jpg

# Fix permissions (Unix/macOS)
chmod 644 photo.jpg
```

### Upload fails with no clear error

**Problem:** Upload fails without specific error message.

**Check:**
1. File size limits on ResourceSpace server
2. Allowed file types on server
3. Server disk space

**Solution:**
- Contact ResourceSpace administrator for server limits
- Check file type is allowed
- Try uploading a smaller test file

### Metadata field not being set

**Problem:** `--field` option seems to have no effect.

**Solution:**
```bash
# Use numeric field IDs, not names
rs upload photo.jpg --field "8=My Title"  # 8 is the field ID

# Check field IDs in ResourceSpace admin panel
# Or use rs info on an existing resource to see field structure
rs --json info 12345 | jq '.metadata'
```

---

## Output Issues

### JSON output is malformed

**Problem:** JSON output can't be parsed.

**Check:**
1. You're using `--json` flag correctly
2. No other output mixed in

**Solution:**
```bash
# Ensure --json comes before the command
rs --json search "photo"  # Correct
rs search "photo" --json  # May not work as expected

# Redirect stderr separately
rs --json search "photo" 2>/dev/null | jq '.'
```

### Colors not displaying correctly

**Problem:** Terminal colors are garbled or not showing.

**Solution:**
```bash
# Disable colors
rs --no-color search "photo"

# Or set terminal type
export TERM=xterm-256color
```

---

## Exit Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 0 | Success | Operation completed successfully |
| 1 | General error | API error, validation error, file not found |
| 2 | Configuration error | Missing credentials, invalid configuration |

Use exit codes in scripts:
```bash
if rs search "photo"; then
    echo "Search succeeded"
else
    echo "Search failed with exit code $?"
fi
```

---

## Getting Help

### Check command help

```bash
rs --help
rs search --help
rs upload --help
```

### Enable verbose output

For debugging, examine the JSON output:
```bash
rs --json search "photo" 2>&1 | head -50
```

### Report Issues

If you encounter a bug or unexpected behavior:

1. Note the exact command you ran
2. Note the error message
3. Check your configuration (masked): `rs config get`
4. Report at: https://github.com/TidalStudio/ResourceSpace-CLI/issues
