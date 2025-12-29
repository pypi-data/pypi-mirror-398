# PAB - APCloudy Deployment Tool

[![PyPI version](https://badge.fury.io/py/pab-cli.svg)](https://badge.fury.io/py/pab-cli)
[![Documentation Status](https://readthedocs.org/projects/pab-cli/badge/?version=latest)](https://pab-cli.readthedocs.io/en/latest/?badge=latest)
[![Python Support](https://img.shields.io/pypi/pyversions/pab-cli.svg)](https://pypi.org/project/pab-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/fawadss1/pab-cli.svg)](https://github.com/fawadss1/pab-cli/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/fawadss1/pab-cli.svg)](https://github.com/fawadss1/pab-cli/issues)

PAB is a command-line tool for deploying Scrapy spiders to APCloudy, similar to how `shub` works with Scrapinghub. It provides an easy way to manage and deploy your web scraping projects to the APCloudy platform.

## 📖 Documentation

For comprehensive documentation, visit: **[https://pab-cli.readthedocs.io/](https://pab-cli.readthedocs.io/en/latest/)**

## Features

- 🚀 Easy deployment of Scrapy spiders to APCloudy
- 🔐 Secure authentication and credential management
- 📦 Automatic project packaging and upload
- 📋 Project and spider management
- 🔄 Real-time deployment status tracking
- 🌟 Cross-platform support (Windows, macOS, Linux)

## Installation

You can install PAB using pip:

```bash
pip install pab-cli
```

Or install from source:

```bash
git clone https://github.com/fawadss1/pab-cli.git
cd pab-cli
pip install -e .
```

## Quick Start

### 1. Login to APCloudy

```bash
pab login
```

This will prompt you for your APCloudy API key and save it securely.

### 2. List Available Projects

```bash
pab projects
```

This will show you all available projects with their IDs.

### 3. Deploy a Spider

Navigate to your Scrapy project directory and run:

```bash
pab deploy <project-id>
```

For example:
```bash
pab deploy 5465
```

PAB will automatically package your project and deploy it to the specified project on APCloudy.

You can also specify additional options:

```bash
pab deploy 5465 --version v0.2.4 --target /path/to/project
```

## Commands

### Authentication

- `pab login` - Login to APCloudy with API key
- `pab logout` - Logout from APCloudy
- `pab status` - Show current authentication status

### Deployment

- `pab deploy <project-id>` - Deploy current project to specified APCloudy project
- `pab deploy <project-id> --version <version>` - Deploy with specific version tag
- `pab deploy <project-id> --target <path>` - Deploy from specific directory

### Project Management

- `pab projects` - List all available projects
- `pab spiders <project-id>` - List spiders in a project

## Configuration

PAB stores configuration in:
- Windows: `%APPDATA%\pab\pab_config.json`
- macOS/Linux: `~/.pab/pab_config.json`

## Examples

### Basic Usage

```bash
# Login to APCloudy
pab login

# List available projects to get project IDs
pab projects

# Deploy to project ID 5465
pab deploy 5465

# Check authentication status
pab status

# List spiders in a project
pab spiders 5465
```

### Advanced Usage

```bash
# Deploy with specific version
pab deploy 5465 --version production-2024

# Deploy from different directory
pab deploy 5465 --target /path/to/project

# Deploy with custom version and target
pab deploy 5465 --version v1.2.3 --target /my/scrapy/project
```

## API Endpoints

PAB communicates with APCloudy using the following API endpoints:

- `POST /api/cli/auth/authenticate` - API key authentication
- `POST /api/cli/auth/refresh` - Token refresh
- `GET /api/cli/projects` - List projects
- `POST /api/cli/projects/{id}/deploy` - Deploy spider
- `GET /api/cli/projects/{id}/spiders` - List spiders
- `GET /api/cli/deployments/{id}/status` - Deployment status

## Requirements

- Python 3.7+
- Scrapy 2.0+
- Valid APCloudy account and API key

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact:
- Email: Fawadstar6@gmail.com
- GitHub: [@fawadss1](https://github.com/fawadss1)

## Changelog

### v0.2.0 (2025-11-10)
- **Pre-deployment Validation**: Added comprehensive spider validation before deployment
  - Syntax error detection using Python's `compile()` function
  - Undefined variable detection with AST-based static analysis
  - Import error validation to catch missing modules and import failures
  - Spider structure validation for Scrapy-specific requirements
- **Smart Validation**: Script files in `scripts/` directory are skipped during import validation to avoid false positives from API calls
- **Package Validation**: Added package size validation to prevent uploading empty (0-byte) packages
- **Enhanced Error Reporting**: Improved error messages with file paths and line numbers for easier debugging
- **Code Optimization**: Removed unused imports and variables for cleaner codebase
- **Builtin Support**: Fixed validator to correctly recognize Python builtins (len, str, int, Exception, etc.)
- **Token Refresh Handling**: Improved HTTP client to read file content into memory for reliable token refresh retries
- **Debug Logging**: Added detailed logging during package creation for better troubleshooting

### v0.1.0 (2025-08-06)
- Initial release
- Basic authentication and deployment functionality
- Project and spider management
- Cross-platform support

---

**Made with ❤️ by Fawad Ali for AskPablos**
