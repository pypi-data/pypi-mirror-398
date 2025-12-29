ll pab# Installation

This guide will help you install PAB CLI on your system.

## Requirements

- Python 3.7 or higher
- pip (Python package installer)
- An APCloudy account with API access

## Install from PyPI (Recommended)

The easiest way to install PAB CLI is using pip from the Python Package Index:

```bash
pip install pab-cli
```

### Upgrade to Latest Version

To upgrade to the latest version:

```bash
pip install --upgrade pab-cli
```

## Install from Source

If you want to install the development version or contribute to the project:

```bash
git clone https://github.com/fawadss1/pab-cli.git
cd pab-cli
pip install -e .
```

## Verify Installation

To verify that PAB CLI is installed correctly, run:

```bash
pab --version
```

You should see the version number displayed.

## Platform-Specific Notes

### Windows

If you're using Windows, you might need to add Python Scripts directory to your PATH:

```cmd
# Add to PATH (adjust Python version as needed)
set PATH=%PATH%;C:\Python39\Scripts
```

### macOS

On macOS, you might need to use `pip3` instead of `pip`:

```bash
pip3 install pab-cli
```

### Linux

On some Linux distributions, you might need to install additional packages:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip

# CentOS/RHEL/Fedora
sudo yum install python3-pip
# or
sudo dnf install python3-pip
```

## Virtual Environment (Recommended)

It's recommended to install PAB CLI in a virtual environment to avoid conflicts:

```bash
# Create virtual environment
python -m venv pab-env

# Activate virtual environment
# On Windows:
pab-env\Scripts\activate
# On macOS/Linux:
source pab-env/bin/activate

# Install PAB CLI
pip install pab-cli
```

## Troubleshooting Installation

### Permission Errors

If you encounter permission errors, try:

```bash
pip install --user pab-cli
```

### SSL Certificate Errors

If you encounter SSL certificate errors:

```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org pab-cli
```

### Command Not Found

If the `pab` command is not found after installation:

1. Make sure the Python Scripts directory is in your PATH
2. Try running with the full path: `python -m pab_cli`
3. Reinstall with `--force-reinstall` flag

## Next Steps

Once installed, proceed to the [Quick Start Guide](quickstart.md) to learn how to use PAB CLI.
