# Commands Reference

This page provides a comprehensive reference for all PAB CLI commands.

## Authentication Commands

### `pab login`

Login to APCloudy with your API key.

**Usage:**
```bash
pab login [OPTIONS]
```

**Options:**
- `--api-key, -k TEXT`: APCloudy API key (optional, will prompt if not provided)

**Examples:**
```bash
# Interactive login (prompts for API key)
pab login

# Login with API key directly
pab login --api-key your_api_key_here
```

**Behavior:**
- If already logged in, asks if you want to logout and login with a different account
- Stores credentials securely in local configuration
- Validates the API key with APCloudy servers

### `pab logout`

Logout from APCloudy and clear stored credentials.

**Usage:**
```bash
pab logout
```

**Examples:**
```bash
pab logout
```

**Behavior:**
- Removes all stored authentication credentials
- Does not revoke the API key on the server

## Project Management Commands

### `pab projects`

List all available projects in your APCloudy account.

**Usage:**
```bash
pab projects
```

**Examples:**
```bash
pab projects
```

**Output:**
Displays a formatted table with:
- Project ID
- Project Name
- Status
- Creation Date

**Sample Output:**
```
Available projects: 3
┌────┬─────────────────┬────────┬─────────────────────┐
│ ID │ Name            │ Status │ Created At          │
├────┼─────────────────┼────────┼─────────────────────┤
│ 123│ ecommerce-scraper│ active │ 2025-01-15 10:30:00│
│ 456│ news-aggregator │ active │ 2025-01-10 14:20:00│
│ 789│ price-monitor   │ active │ 2025-01-05 09:15:00│
└────┴─────────────────┴────────┴─────────────────────┘
```

### `pab spiders`

List all spiders in a specific project.

**Usage:**
```bash
pab spiders PROJECT_ID
```

**Arguments:**
- `PROJECT_ID`: The ID of the project to list spiders for

**Examples:**
```bash
pab spiders 123
```

**Output:**
Displays a formatted table with:
- Spider ID
- Spider Name
- Start URL
- Creation Date

**Sample Output:**
```
Spiders in project 123: 2
┌────┬─────────────────┬──────────────────────┬─────────────────────┐
│ ID │ Name            │ Start URL            │ Created At          │
├────┼─────────────────┼──────────────────────┼─────────────────────┤
│ 1  │ product_spider  │ https://example.com  │ 2025-01-15 10:30:00│
│ 2  │ review_spider   │ https://reviews.com  │ 2025-01-16 11:45:00│
└────┴─────────────────┴──────────────────────┴─────────────────────┘
```

## Deployment Commands

### `pab deploy`

Deploy a Scrapy project to APCloudy.

**Usage:**
```bash
pab deploy PROJECT_ID
```

**Arguments:**
- `PROJECT_ID`: The ID of the APCloudy project to deploy to

**Examples:**
```bash
# Deploy current directory to project 123
pab deploy 123
```

**Behavior:**
- Must be run from within a Scrapy project directory
- Automatically detects `scrapy.cfg` file
- Creates a deployment package
- Uploads to the specified project
- Returns a deployment ID for tracking

**Requirements:**
- Must be authenticated (`pab login`)
- Must be in a valid Scrapy project directory
- Project must exist in your APCloudy account

## Utility Commands

### `pab --version`

Display the current version of PAB CLI.

**Usage:**
```bash
pab --version
```

**Examples:**
```bash
pab --version
```

### `pab --help`

Display help information for PAB CLI.

**Usage:**
```bash
pab --help
pab COMMAND --help
```

**Examples:**
```bash
# General help
pab --help

# Help for specific command
pab login --help
pab deploy --help
```

## Global Options

These options can be used with any command:

- `--help`: Show help message and exit
- `--version`: Show version and exit

## Exit Codes

PAB CLI uses standard exit codes:

- `0`: Success
- `1`: General error (authentication, network, validation, etc.)

## Authentication Requirements

The following commands require authentication:
- `pab projects`
- `pab spiders`
- `pab deploy`

If not authenticated, these commands will display an error message and exit with code 1.

## Error Handling

All commands include comprehensive error handling:

- **Network errors**: Connection issues, timeouts
- **Authentication errors**: Invalid API key, expired tokens
- **Validation errors**: Invalid project structure, missing files
- **API errors**: Server-side errors from APCloudy

Error messages are descriptive and provide guidance for resolution.

## Examples by Use Case

### First-time Setup
```bash
pab login --api-key your_api_key
pab projects
```

### Daily Development Workflow
```bash
cd my-scrapy-project
pab deploy 123
pab spiders 123
```

### Troubleshooting
```bash
pab logout
pab login
pab projects
```
