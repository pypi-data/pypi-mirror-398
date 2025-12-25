# Configuration Guide

The ResourceSpace CLI requires three pieces of information to connect to your ResourceSpace instance:

1. **API URL** - Your ResourceSpace API endpoint
2. **API Key** - Your authentication key
3. **Username** - Your ResourceSpace username

## Quick Setup

The easiest way to configure the CLI is using the `config set` command:

```bash
rs config set url https://your-resourcespace.com/api
rs config set key your-api-key
rs config set user your-username
```

## Finding Your Credentials

### API URL

Your API URL is typically your ResourceSpace URL with `/api` appended:
- If your ResourceSpace is at `https://dam.company.com`
- Your API URL is `https://dam.company.com/api`

### API Key

1. Log into ResourceSpace as an administrator
2. Go to **Admin** > **System** > **API Configuration**
3. Find or generate your API key

### Username

Use the same username you use to log into ResourceSpace.

## Configuration Storage

### .env File

By default, configuration is stored in a `.env` file in the current directory. Example `.env` file:

```env
RESOURCESPACE_API_URL=https://dam.company.com/api
RESOURCESPACE_API_KEY=abc123def456
RESOURCESPACE_USER=admin
```

### Environment Variables

You can also set configuration via environment variables. These take precedence over `.env` file values:

```bash
export RESOURCESPACE_API_URL=https://dam.company.com/api
export RESOURCESPACE_API_KEY=abc123def456
export RESOURCESPACE_USER=admin
```

### Custom .env Location

To use a `.env` file in a different location, set the `RESOURCESPACE_ENV_PATH` environment variable:

```bash
export RESOURCESPACE_ENV_PATH=/path/to/custom/.env
```

## Configuration Variables

| Variable | Aliases | Description |
|----------|---------|-------------|
| `RESOURCESPACE_API_URL` | `url`, `api-url`, `api_url` | ResourceSpace API endpoint URL |
| `RESOURCESPACE_API_KEY` | `key`, `api-key`, `api_key` | API authentication key |
| `RESOURCESPACE_USER` | `user`, `username` | API username |

## Managing Configuration

### View Configuration

```bash
# Show all config (values masked for security)
rs config get

# Show specific value
rs config get url

# Show actual values (WARNING: exposes secrets in terminal)
rs config get --show-values
```

### Update Configuration

```bash
rs config set url https://new-server.com/api
rs config set key new-api-key
```

### Clear Configuration

```bash
# Clear a specific value
rs config clear url

# Clear all configuration
rs config clear --all

# Clear without confirmation prompt
rs config clear --all --yes
```

## Security Best Practices

1. **Never commit `.env` files** - Add `.env` to your `.gitignore`
2. **Use environment variables in CI/CD** - Set credentials as secrets in your CI system
3. **Limit API key permissions** - In ResourceSpace, configure API keys with minimal required permissions
4. **Don't use `--show-values` in scripts** - This exposes credentials in logs

## Verifying Configuration

After configuration, test the connection:

```bash
rs types list
```

If successful, you'll see a list of resource types. If not, check the [Troubleshooting Guide](troubleshooting.md).

## Example Configurations

### Development

```env
RESOURCESPACE_API_URL=http://localhost:8080/api
RESOURCESPACE_API_KEY=dev-key
RESOURCESPACE_USER=developer
```

### Production

```env
RESOURCESPACE_API_URL=https://dam.company.com/api
RESOURCESPACE_API_KEY=production-key
RESOURCESPACE_USER=api-user
```

### Multiple Environments

Use different `.env` files and switch between them:

```bash
# Point to development config
export RESOURCESPACE_ENV_PATH=./configs/dev.env
rs search "test"

# Point to production config
export RESOURCESPACE_ENV_PATH=./configs/prod.env
rs search "test"
```
