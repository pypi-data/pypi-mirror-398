# API Reference

This page provides detailed documentation for PAB CLI's internal modules and classes.

## CLI Module (`pab_cli.cli`)

The main command-line interface module that defines all PAB CLI commands.

### Functions

#### `main()`
Main CLI entry point using Click command group.

**Usage:**
```python
from pab_cli.cli import main
main()
```

#### `login(api_key)`
Authenticate with APCloudy using API key.

**Parameters:**
- `api_key` (str, optional): APCloudy API key

**Example:**
```bash
pab login --api-key your_api_key
```

#### `logout()`
Clear stored authentication credentials.

**Example:**
```bash
pab logout
```

#### `deploy(project_id)`
Deploy Scrapy project to APCloudy.

**Parameters:**
- `project_id` (str): Target project ID on APCloudy

**Example:**
```bash
pab deploy 123
```

#### `projects()`
List all available projects in user's APCloudy account.

**Returns:**
Displays formatted table of projects with ID, name, status, and creation date.

#### `spiders(project_id)`
List all spiders in a specific project.

**Parameters:**
- `project_id` (str): Project ID to list spiders for

**Returns:**
Displays formatted table of spiders with ID, name, start URL, and creation date.

## Authentication Module (`pab_cli.auth`)

Handles authentication with APCloudy API.

### Classes

#### `AuthManager`

Manages authentication operations including login and token refresh.

**Constructor:**
```python
AuthManager(endpoint: str)
```

**Parameters:**
- `endpoint` (str): APCloudy API endpoint URL

**Methods:**

##### `authenticate(api_key: str) -> dict`
Authenticate using API key and retrieve user information.

**Parameters:**
- `api_key` (str): User's APCloudy API key

**Returns:**
- `dict`: User information including username, tokens, and API key

**Raises:**
- `AuthenticationError`: If authentication fails
- `NetworkError`: If network request fails

**Example:**
```python
from pab_cli.auth import AuthManager

auth_manager = AuthManager("https://api.apcloudy.com")
user_info = auth_manager.authenticate("your_api_key")
print(user_info['username'])
```

##### `refresh_token(refresh_token: str) -> dict`
Refresh access token using refresh token.

**Parameters:**
- `refresh_token` (str): Valid refresh token

**Returns:**
- `dict`: New access and refresh tokens

## Configuration Module (`pab_cli.config`)

Manages PAB CLI configuration and credential storage.

### Classes

#### `ConfigManager`

Handles configuration file operations and credential management.

**Constructor:**
```python
ConfigManager()
```

**Methods:**

##### `is_authenticated() -> bool`
Check if user is currently authenticated.

**Returns:**
- `bool`: True if authenticated, False otherwise

##### `get_credentials() -> dict`
Retrieve stored user credentials.

**Returns:**
- `dict`: Stored credentials including username, tokens, and API key

**Raises:**
- `ConfigurationError`: If no credentials found

##### `save_credentials(username: str, access_token: str, refresh_token: str, api_key: str)`
Store user credentials securely.

**Parameters:**
- `username` (str): User's APCloudy username
- `access_token` (str): OAuth access token
- `refresh_token` (str): OAuth refresh token
- `api_key` (str): User's API key

##### `clear_credentials()`
Remove all stored credentials.

##### `get_endpoint() -> str`
Get configured API endpoint.

**Returns:**
- `str`: API endpoint URL

**Example:**
```python
from pab_cli.config import ConfigManager

config = ConfigManager()
if config.is_authenticated():
    creds = config.get_credentials()
    print(f"Logged in as: {creds['username']}")
```

## Deployment Module (`pab_cli.deploy`)

Handles project deployment to APCloudy.

### Classes

#### `DeployManager`

Manages the deployment process including packaging and uploading.

**Constructor:**
```python
DeployManager(config_manager: ConfigManager)
```

**Parameters:**
- `config_manager` (ConfigManager): Configured ConfigManager instance

**Methods:**

##### `deploy(project_id: str) -> str`
Deploy current Scrapy project to specified APCloudy project.

**Parameters:**
- `project_id` (str): Target project ID

**Returns:**
- `str`: Deployment ID for tracking

**Raises:**
- `DeploymentError`: If deployment fails
- `ProjectNotFoundError`: If project directory is invalid

**Example:**
```python
from pab_cli.deploy import DeployManager
from pab_cli.config import ConfigManager

config = ConfigManager()
deploy_manager = DeployManager(config)
deployment_id = deploy_manager.deploy("123")
print(f"Deployed with ID: {deployment_id}")
```

## HTTP Client Module (`pab_cli.http_client`)

Provides HTTP client for APCloudy API communication.

### Classes

#### `APCloudyClient`

HTTP client for interacting with APCloudy API.

**Constructor:**
```python
APCloudyClient(config_manager: ConfigManager)
```

**Parameters:**
- `config_manager` (ConfigManager): Configured ConfigManager instance

**Methods:**

##### `list_projects() -> list`
Retrieve list of user's projects.

**Returns:**
- `list`: List of project dictionaries

##### `list_spiders(project_id: str) -> list`
Retrieve list of spiders in a project.

**Parameters:**
- `project_id` (str): Project ID

**Returns:**
- `list`: List of spider dictionaries

##### `upload_project(project_id: str, project_data: bytes) -> str`
Upload project package to APCloudy.

**Parameters:**
- `project_id` (str): Target project ID
- `project_data` (bytes): Project package data

**Returns:**
- `str`: Deployment ID

## Package Module (`pab_cli.package`)

Handles project packaging for deployment.

### Functions

#### `create_package(project_path: str) -> bytes`
Create deployment package from Scrapy project.

**Parameters:**
- `project_path` (str): Path to Scrapy project directory

**Returns:**
- `bytes`: Packaged project data

**Raises:**
- `PackageError`: If packaging fails
- `InvalidProjectError`: If project structure is invalid

## Exception Classes (`pab_cli.exceptions`)

Custom exception classes for PAB CLI.

### `PABError`
Base exception class for all PAB CLI errors.

### `AuthenticationError`
Raised when authentication fails.

### `ConfigurationError`
Raised when configuration is invalid or missing.

### `DeploymentError`
Raised when deployment operations fail.

### `NetworkError`
Raised when network operations fail.

### `ProjectNotFoundError`
Raised when Scrapy project cannot be found or is invalid.

### `PackageError`
Raised when project packaging fails.

## Utility Functions (`pab_cli.utils`)

Utility functions and helpers.

### Functions

#### `print_success(message: str)`
Print success message in green color.

#### `print_error(message: str)`
Print error message in red color.

#### `print_info(message: str)`
Print informational message in blue color.

#### `print_cyan(message: str)`
Print message in cyan color.

#### `create_setup()`
Create setup.py file if it doesn't exist.

**Example:**
```python
from pab_cli.utils import print_success, print_error

print_success("Deployment completed!")
print_error("Authentication failed!")
```

## Version Module (`pab_cli.version`)

Contains version information.

### Constants

#### `__version__`
Current version of PAB CLI.

**Example:**
```python
from pab_cli import __version__
print(f"PAB CLI version: {__version__}")
```

## Usage Examples

### Basic API Usage

```python
from pab_cli.config import ConfigManager
from pab_cli.auth import AuthManager
from pab_cli.deploy import DeployManager

# Setup configuration
config = ConfigManager()

# Authenticate if needed
if not config.is_authenticated():
    auth = AuthManager(config.get_endpoint())
    user_info = auth.authenticate("your_api_key")
    config.save_credentials(
        user_info['username'],
        user_info['access_token'],
        user_info['refresh_token'],
        user_info['api_key']
    )

# Deploy project
deploy_manager = DeployManager(config)
deployment_id = deploy_manager.deploy("123")
print(f"Deployment ID: {deployment_id}")
```

### Error Handling

```python
from pab_cli.exceptions import AuthenticationError, DeploymentError
from pab_cli.deploy import DeployManager
from pab_cli.config import ConfigManager

try:
    config = ConfigManager()
    deploy_manager = DeployManager(config)
    deployment_id = deploy_manager.deploy("123")
except AuthenticationError:
    print("Please login first: pab login")
except DeploymentError as e:
    print(f"Deployment failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

This API reference provides comprehensive documentation for developers who want to extend PAB CLI or integrate it into their own applications.
