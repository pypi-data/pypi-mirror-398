
4. **Use full Python path:**
   ```bash
   python -m pab_cli --help
   ```

### Permission Errors During Installation

**Problem:** Permission denied when installing PAB CLI.

**Solutions:**

1. **Install for current user only:**
   ```bash
   pip install --user pab-cli
   ```

2. **Use virtual environment:**
   ```bash
   python -m venv pab-env
   source pab-env/bin/activate  # Linux/macOS
   # pab-env\Scripts\activate   # Windows
   pip install pab-cli
   ```

3. **Use sudo (Linux/macOS only):**
   ```bash
   sudo pip install pab-cli
   ```

## Project Structure Issues

### Missing Dependencies

**Problem:** Deployment fails due to missing Python packages.

**Solutions:**

1. **Create requirements.txt:**
   ```bash
   pip freeze > requirements.txt
   ```

2. **Include required packages:**
   ```txt
   scrapy>=2.5.0
   requests>=2.25.0
   # Add other dependencies
   ```

3. **Test locally first:**
   ```bash
   pip install -r requirements.txt
   scrapy check
   ```

### Invalid Spider Code

**Problem:** Deployment succeeds but spiders don't work.

**Solutions:**

1. **Test spiders locally:**
   ```bash
   scrapy check
   scrapy crawl spider_name -s CLOSESPIDER_ITEMCOUNT=1
   ```

2. **Check spider syntax:**
   ```python
   # Ensure proper spider structure
   import scrapy
   
   class MySpider(scrapy.Spider):
       name = 'my_spider'
       start_urls = ['http://example.com']
       
       def parse(self, response):
           # Your parsing logic
           pass
   ```

3. **Validate settings.py:**
   - Check for syntax errors
   - Ensure all imports are available

## Performance Issues

### Slow Commands

**Problem:** PAB CLI commands take too long to execute.

**Solutions:**

1. **Check network latency:**
   ```bash
   ping api.apcloudy.com
   ```

2. **Reduce project size:**
   - Add `.gitignore` patterns
   - Exclude unnecessary files
   - Remove large datasets

3. **Use faster network:**
   - Switch to wired connection
   - Use different WiFi network

## Data/Configuration Issues

### Corrupted Configuration

**Problem:** Strange errors or unexpected behavior.

**Solutions:**

1. **Reset configuration:**
   ```bash
   # Windows
   del "%APPDATA%\pab\pab_config.json"
   
   # macOS/Linux
   rm ~/.pab/pab_config.json
   
   # Re-authenticate
   pab login
   ```

2. **Check configuration file:**
   ```bash
   # View configuration (remove sensitive data before sharing)
   cat ~/.pab/pab_config.json
   ```

## Getting Help

### Enable Debug Mode

For detailed error information:

```bash
# Set debug environment variable
export PAB_DEBUG=1
pab deploy PROJECT_ID
```

### Collect System Information

When reporting issues, include:

```bash
# System information
python --version
pip --version
pab --version

# Operating system
uname -a  # Linux/macOS
systeminfo  # Windows

# Network connectivity
curl -I https://api.apcloudy.com
```

### Log Files

PAB CLI logs are typically found in:
- **Windows**: `%APPDATA%\pab\logs\`
- **macOS/Linux**: `~/.pab/logs/`

### Common Error Patterns

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Connection refused" | Network/firewall issue | Check connectivity, proxy |
| "Invalid JSON response" | Server error | Retry later, check status |
| "File not found" | Wrong directory | Navigate to project root |
| "Permission denied" | File permissions | Fix file/directory permissions |
| "Invalid credentials" | Authentication issue | Re-login with correct API key |

### When to Contact Support

Contact PAB CLI support when:
- Issues persist after trying troubleshooting steps
- Error messages are unclear or undocumented
- You suspect a bug in PAB CLI
- You need help with advanced configuration

Include the following in your support request:
- PAB CLI version (`pab --version`)
- Operating system and version
- Complete error message
- Steps to reproduce the issue
- What you've already tried
# Troubleshooting

This guide helps you resolve common issues when using PAB CLI.

## Authentication Issues

### "Not authenticated" Error

**Problem:** Commands fail with "Not authenticated. Please run 'pab login' first."

**Solutions:**

1. **Login again:**
   ```bash
   pab login
   ```

2. **Check if credentials expired:**
   ```bash
   pab logout
   pab login --api-key your_api_key
   ```

3. **Verify API key is correct:**
   - Check your APCloudy dashboard for the correct API key
   - Ensure no extra spaces or characters

### Invalid API Key

**Problem:** Login fails with "Invalid API key" or authentication errors.

**Solutions:**

1. **Get a fresh API key:**
   - Log into APCloudy dashboard
   - Navigate to Account Settings → API Keys
   - Generate a new API key if needed

2. **Check API key format:**
   - API keys should be alphanumeric strings
   - No spaces at beginning or end
   - Case-sensitive

3. **Try direct API key login:**
   ```bash
   pab login --api-key YOUR_EXACT_API_KEY
   ```

### Permission Denied on Configuration

**Problem:** Cannot read/write configuration file.

**Solutions:**

**Windows:**
```cmd
# Run Command Prompt as Administrator
icacls "%APPDATA%\pab" /grant %USERNAME%:F
```

**macOS/Linux:**
```bash
chmod 700 ~/.pab
chmod 600 ~/.pab/pab_config.json
```

## Deployment Issues

### "Not in a Scrapy project directory"

**Problem:** Deploy command fails because PAB CLI can't find `scrapy.cfg`.

**Solutions:**

1. **Verify you're in the correct directory:**
   ```bash
   ls -la  # Should show scrapy.cfg file
   pwd     # Confirm current directory
   ```

2. **Navigate to project root:**
   ```bash
   cd /path/to/your/scrapy/project
   ls scrapy.cfg  # Should exist
   ```

3. **Check project structure:**
   ```
   your-project/
   ├── scrapy.cfg          ← Must be present
   ├── projectname/
   │   ├── __init__.py
   │   ├── spiders/
   │   └── ...
   ```

### "Project not found" Error

**Problem:** Cannot deploy to specified project ID.

**Solutions:**

1. **List available projects:**
   ```bash
   pab projects
   ```

2. **Verify project ID exists:**
   - Check the project ID in the output
   - Use exact ID number from the list

3. **Check project permissions:**
   - Ensure you have access to the project
   - Contact project owner if needed

### Deployment Timeout

**Problem:** Deployment hangs or times out.

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping api.apcloudy.com
   ```

2. **Retry deployment:**
   ```bash
   pab deploy PROJECT_ID
   ```

3. **Check project size:**
   - Large projects may take longer
   - Consider excluding unnecessary files

## Network Issues

### Connection Timeout

**Problem:** Commands fail with connection timeout errors.

**Solutions:**

1. **Check internet connectivity:**
   ```bash
   curl -I https://api.apcloudy.com
   ```

2. **Configure proxy if needed:**
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=https://proxy.company.com:8080
   ```

3. **Increase timeout (if needed):**
   ```bash
   export PAB_TIMEOUT=60
   ```

### SSL Certificate Errors

**Problem:** SSL/TLS certificate verification failures.

**Solutions:**

1. **Update certificates:**
   ```bash
   # macOS
   brew update && brew upgrade ca-certificates
   
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get upgrade ca-certificates
   
   # Windows - update Windows
   ```

2. **Python certificate update:**
   ```bash
   pip install --upgrade certifi
   ```

### Firewall/Corporate Network

**Problem:** Corporate firewall blocking connections.

**Solutions:**

1. **Configure proxy settings:**
   ```bash
   export HTTP_PROXY=http://proxy:port
   export HTTPS_PROXY=https://proxy:port
   export NO_PROXY=localhost,127.0.0.1
   ```

2. **Contact IT department:**
   - Request access to `api.apcloudy.com`
   - Port 443 (HTTPS) needs to be open

## Installation Issues

### Command Not Found

**Problem:** `pab` command not recognized after installation.

**Solutions:**

1. **Check if PAB CLI is installed:**
   ```bash
   pip list | grep pab-cli
   ```

2. **Reinstall PAB CLI:**
   ```bash
   pip uninstall pab-cli
   pip install pab-cli
   ```

3. **Check PATH:**
   ```bash
   # Find where pip installs scripts
   python -m site --user-base
   
   # Add to PATH if needed (add to ~/.bashrc or ~/.zshrc)
   export PATH="$PATH:$(python -m site --user-base)/bin"
   ```
