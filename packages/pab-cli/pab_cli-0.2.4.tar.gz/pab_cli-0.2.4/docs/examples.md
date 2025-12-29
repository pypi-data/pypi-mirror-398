# Examples

This page provides practical examples of using PAB CLI in various scenarios.

## Basic Usage Examples

### First-Time Setup

Complete setup flow for new users:

```bash
# Install PAB CLI
pip install pab-cli

# Login to APCloudy
pab login
# Enter your API key when prompted

# Check available projects
pab projects

# Deploy your first spider
cd my-scrapy-project
pab deploy 123
```

### Daily Development Workflow

Typical workflow for spider development:

```bash
# Start development session
cd my-scrapy-project

# Test spider locally first
scrapy crawl my_spider

# Deploy to APCloudy when ready
pab deploy 123

# Verify deployment
pab spiders 123
```

## Project Management Examples

### Working with Multiple Projects

```bash
# List all projects to see available options
pab projects

# Deploy different spiders to different projects
cd ecommerce-scraper
pab deploy 123  # Deploy to ecommerce project

cd ../news-scraper
pab deploy 456  # Deploy to news project

cd ../monitoring-scraper
pab deploy 789  # Deploy to monitoring project
```

### Project Information Gathering

```bash
# Get overview of all projects
pab projects

# Check spiders in specific projects
pab spiders 123
pab spiders 456
pab spiders 789

# Compare project contents
echo "Ecommerce project spiders:"
pab spiders 123
echo -e "\nNews project spiders:"
pab spiders 456
```

## Authentication Examples

### Switching Between Accounts

```bash
# Check current login status
pab projects  # This will show projects for current account

# Switch to different account
pab logout
pab login --api-key different_account_key

# Verify new account
pab projects
```

### Using Environment Variables

```bash
# Set API key in environment
export PAB_API_KEY=your_api_key_here

# Login will use the environment variable
pab login

# Or use directly with commands
PAB_API_KEY=your_key pab projects
```

## Advanced Deployment Examples

### Deploying Multiple Projects

Shell script for deploying multiple projects:

```bash
#!/bin/bash
# deploy_all.sh

projects=(
    "/path/to/ecommerce-scraper:123"
    "/path/to/news-scraper:456"
    "/path/to/price-monitor:789"
)

for project in "${projects[@]}"; do
    IFS=':' read -r path project_id <<< "$project"
    echo "Deploying $path to project $project_id"
    cd "$path"
    pab deploy "$project_id"
    echo "---"
done
```

### Conditional Deployment

Deploy only if tests pass:

```bash
#!/bin/bash
# smart_deploy.sh

PROJECT_ID=$1
if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <project_id>"
    exit 1
fi

# Run tests first
echo "Running tests..."
if scrapy check; then
    echo "Tests passed, deploying..."
    pab deploy "$PROJECT_ID"
    echo "Deployment complete!"
else
    echo "Tests failed, deployment aborted."
    exit 1
fi
```

## CI/CD Integration Examples

### GitHub Actions

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to APCloudy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install pab-cli
        pip install -r requirements.txt
    
    - name: Deploy to APCloudy
      env:
        PAB_API_KEY: ${{ secrets.PAB_API_KEY }}
      run: |
        pab login
        pab deploy ${{ secrets.PROJECT_ID }}
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - deploy

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - scrapy check

deploy:
  stage: deploy
  script:
    - pip install pab-cli
    - pab login
    - pab deploy $PROJECT_ID
  variables:
    PAB_API_KEY: $API_KEY
    PROJECT_ID: "123"
  only:
    - main
```

## Error Handling Examples

### Robust Deployment Script

```bash
#!/bin/bash
# robust_deploy.sh

PROJECT_ID=$1
MAX_RETRIES=3
RETRY_COUNT=0

deploy_with_retry() {
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        echo "Deployment attempt $((RETRY_COUNT + 1))..."
        
        if pab deploy "$PROJECT_ID"; then
            echo "Deployment successful!"
            return 0
        else
            echo "Deployment failed, retrying..."
            RETRY_COUNT=$((RETRY_COUNT + 1))
            sleep 5
        fi
    done
    
    echo "Deployment failed after $MAX_RETRIES attempts"
    return 1
}

# Check if logged in
if ! pab projects > /dev/null 2>&1; then
    echo "Not logged in, please run 'pab login' first"
    exit 1
fi

# Deploy with retry logic
deploy_with_retry
```

### Validation Before Deployment

```bash
#!/bin/bash
# validate_and_deploy.sh

PROJECT_ID=$1

# Validation checks
echo "Running pre-deployment validation..."

# Check if we're in a Scrapy project
if [ ! -f "scrapy.cfg" ]; then
    echo "Error: Not in a Scrapy project directory"
    exit 1
fi

# Check if authenticated
if ! pab projects > /dev/null 2>&1; then
    echo "Error: Not authenticated with APCloudy"
    exit 1
fi

# Check if project exists
if ! pab projects | grep -q "$PROJECT_ID"; then
    echo "Error: Project $PROJECT_ID not found"
    exit 1
fi

# All checks passed, deploy
echo "Validation passed, deploying..."
pab deploy "$PROJECT_ID"
```

## Monitoring and Logging Examples

### Deployment with Logging

```bash
#!/bin/bash
# deploy_with_logging.sh

PROJECT_ID=$1
LOG_FILE="deployment_$(date +%Y%m%d_%H%M%S).log"

{
    echo "=== Deployment started at $(date) ==="
    echo "Project ID: $PROJECT_ID"
    echo "Working directory: $(pwd)"
    echo "PAB CLI version: $(pab --version)"
    echo ""
    
    pab deploy "$PROJECT_ID"
    
    echo ""
    echo "=== Deployment finished at $(date) ==="
} 2>&1 | tee "$LOG_FILE"

echo "Deployment log saved to: $LOG_FILE"
```

### Health Check After Deployment

```bash
#!/bin/bash
# deploy_and_verify.sh

PROJECT_ID=$1

echo "Deploying to project $PROJECT_ID..."
if pab deploy "$PROJECT_ID"; then
    echo "Deployment successful!"
    
    echo "Verifying spiders..."
    pab spiders "$PROJECT_ID"
    
    echo "Deployment verification complete!"
else
    echo "Deployment failed!"
    exit 1
fi
```

## Development Workflow Examples

### Feature Branch Deployment

```bash
#!/bin/bash
# feature_deploy.sh

FEATURE_BRANCH=$(git branch --show-current)
PROJECT_ID=$1

if [ "$FEATURE_BRANCH" = "main" ]; then
    echo "Deploying main branch to production project..."
    pab deploy "$PROJECT_ID"
else
    echo "Deploying feature branch '$FEATURE_BRANCH' to staging..."
    # Use staging project ID
    pab deploy 999
fi
```

### Development Environment Setup

```bash
#!/bin/bash
# setup_dev_env.sh

echo "Setting up PAB CLI development environment..."

# Create virtual environment
python -m venv pab-dev
source pab-dev/bin/activate  # Linux/macOS
# pab-dev\Scripts\activate  # Windows

# Install PAB CLI
pip install pab-cli

# Login to development environment
export PAB_ENDPOINT=https://staging-api.apcloudy.com
pab login

echo "Development environment ready!"
echo "Use 'source pab-dev/bin/activate' to activate"
```

## Troubleshooting Examples

### Connection Testing

```bash
#!/bin/bash
# test_connection.sh

echo "Testing PAB CLI connection..."

# Test authentication
if pab projects > /dev/null 2>&1; then
    echo "✓ Authentication successful"
else
    echo "✗ Authentication failed"
    echo "Try running 'pab login' first"
    exit 1
fi

# Test project access
PROJECT_COUNT=$(pab projects 2>/dev/null | grep "Available projects:" | cut -d: -f2 | tr -d ' ')
echo "✓ Found $PROJECT_COUNT projects"

echo "Connection test complete!"
```

These examples cover common use cases and can be adapted to your specific needs. For more complex scenarios, combine these patterns or refer to the [Commands Reference](commands.md) for detailed options.
