a# Quick Start Guide

This guide will help you get started with PAB CLI in just a few minutes.

## Prerequisites

- PAB CLI installed (see [Installation Guide](installation.md))
- An APCloudy account
- Your APCloudy API key
- A Scrapy project ready for deployment

## Step 1: Login to APCloudy

First, authenticate with your APCloudy account:

```bash
pab login
```

You'll be prompted to enter your APCloudy API key. You can also provide it directly:

```bash
pab login --api-key YOUR_API_KEY
```

**Where to find your API key:**
1. Log into your APCloudy dashboard
2. Navigate to Account Settings
3. Go to API Keys section
4. Copy your API key

## Step 2: List Your Projects

View all available projects in your APCloudy account:

```bash
pab projects
```

This will display a table with:
- Project ID
- Project Name
- Status
- Creation Date

Example output:
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

## Step 3: Deploy Your Spider

Navigate to your Scrapy project directory and deploy:

```bash
cd /path/to/your/scrapy/project
pab deploy PROJECT_ID
```

Replace `PROJECT_ID` with the ID from the projects list. For example:

```bash
pab deploy 123
```

PAB CLI will:
1. Automatically detect your Scrapy project
2. Package your code
3. Upload it to APCloudy
4. Provide you with a deployment ID

Example output:
```
Deploying to project: 123
Successfully deployed! Deployment ID: dep_abc123xyz
```

## Step 4: Verify Deployment

You can list the spiders in your project to verify the deployment:

```bash
pab spiders 123
```

This shows all spiders available in the specified project.

## Common Workflow

Here's a typical workflow when working with PAB CLI:

```bash
# 1. Login (one-time setup)
pab login

# 2. Check available projects
pab projects

# 3. Navigate to your Scrapy project
cd my-scrapy-project

# 4. Deploy to a specific project
pab deploy 123

# 5. Verify spiders are available
pab spiders 123
```

## Project Structure Requirements

Your Scrapy project should have the standard structure:

```
my-scrapy-project/
├── scrapy.cfg
├── myproject/
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   └── spiders/
│       ├── __init__.py
│       └── my_spider.py
└── requirements.txt (optional)
```

## What Happens During Deployment?

1. **Project Detection**: PAB CLI scans for `scrapy.cfg` to identify your Scrapy project
2. **Packaging**: Creates a deployment package with your code
3. **Upload**: Securely uploads the package to APCloudy
4. **Processing**: APCloudy processes and deploys your spiders
5. **Confirmation**: You receive a deployment ID for tracking

## Next Steps

- Learn about all available [Commands](commands.md)
- Explore [Configuration Options](configuration.md)
- Check out [Examples](examples.md) for advanced usage
- Read [Troubleshooting](troubleshooting.md) if you encounter issues

## Need Help?

If you encounter any issues:
1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Verify your API key is correct
3. Ensure you're in a valid Scrapy project directory
4. Check your internet connection
