# Configuration

PAB CLI stores configuration and credentials in local files for secure and convenient access.

## Configuration Location

PAB CLI stores its configuration in different locations depending on your operating system:

- **Windows**: `%APPDATA%\pab\pab_config.json`
- **macOS**: `~/.pab/pab_config.json`
- **Linux**: `~/.pab/pab_config.json`

## Configuration File Structure

The configuration file is a JSON file with the following structure:

```json
{
  "credentials": {
    "username": "your_username",
    "access_token": "your_access_token",
    "refresh_token": "your_refresh_token",
    "api_key": "your_api_key"
  },
  "endpoint": "https://api.apcloudy.com",
  "settings": {
    "timeout": 30,
    "retries": 3
  }
}
```

## Configuration Options

### Credentials

These are managed automatically through the `pab login` command:

- `username`: Your APCloudy username
- `access_token`: OAuth access token for API requests
- `refresh_token`: Token used to refresh the access token
- `api_key`: Your APCloudy API key

### Endpoint

- `endpoint`: The APCloudy API endpoint URL (default: `https://api.apcloudy.com`)

### Settings

- `timeout`: Request timeout in seconds (default: 30)
- `retries`: Number of retry attempts for failed requests (default: 3)

## Manual Configuration

While most configuration is handled through PAB CLI commands, you can manually edit the configuration file if needed.

### Changing the API Endpoint

If you need to use a different APCloudy endpoint (e.g., for testing):

```json
{
  "endpoint": "https://staging-api.apcloudy.com"
}
```

### Adjusting Request Settings

You can modify timeout and retry settings:

```json
{
  "settings": {
    "timeout": 60,
    "retries": 5
  }
}
```

## Environment Variables

PAB CLI also supports configuration through environment variables:

- `PAB_API_KEY`: Your APCloudy API key
- `PAB_ENDPOINT`: API endpoint URL
- `PAB_TIMEOUT`: Request timeout in seconds
- `PAB_RETRIES`: Number of retry attempts

Environment variables take precedence over configuration file values.

**Example:**
```bash
export PAB_API_KEY=your_api_key_here
export PAB_ENDPOINT=https://staging-api.apcloudy.com
pab projects
```

## Security Considerations

### File Permissions

PAB CLI automatically sets appropriate file permissions on the configuration directory and file:

- Configuration directory: `700` (owner read/write/execute only)
- Configuration file: `600` (owner read/write only)

### Credential Storage

- Credentials are stored in JSON format
- The configuration file should be kept secure and not shared
- Use `pab logout` to clear stored credentials when needed

### API Key Protection

- Never commit your API key to version control
- Use environment variables in CI/CD environments
- Regularly rotate your API keys

## Troubleshooting Configuration

### Configuration File Corruption

If your configuration file becomes corrupted:

```bash
# Remove the configuration file
# Windows
del "%APPDATA%\pab\pab_config.json"
# macOS/Linux
rm ~/.pab/pab_config.json

# Re-authenticate
pab login
```

### Permission Issues

If you encounter permission errors:

```bash
# Windows (run as administrator)
icacls "%APPDATA%\pab" /grant %USERNAME%:F

# macOS/Linux
chmod 700 ~/.pab
chmod 600 ~/.pab/pab_config.json
```

### Multiple Accounts

To switch between multiple APCloudy accounts:

```bash
# Logout from current account
pab logout

# Login with different account
pab login --api-key different_api_key
```

## Advanced Configuration

### Custom Configuration Path

You can specify a custom configuration path using the `PAB_CONFIG_PATH` environment variable:

```bash
export PAB_CONFIG_PATH=/path/to/custom/config.json
pab login
```

### Proxy Configuration

If you're behind a corporate proxy, you can configure proxy settings in your system environment or use standard Python proxy environment variables:

```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
pab projects
```

## Configuration Commands

While there are no dedicated configuration commands, these commands affect configuration:

- `pab login`: Creates/updates credentials
- `pab logout`: Removes credentials
- All commands: Read configuration for operation

## Best Practices

1. **Keep credentials secure**: Don't share your configuration file
2. **Regular cleanup**: Use `pab logout` when switching accounts
3. **Environment variables**: Use env vars in automated environments
4. **Backup important settings**: Note any custom endpoint or timeout settings
5. **Monitor permissions**: Ensure configuration files have proper permissions
