"""
CLI module for PAB - APCloudy deployment tool
"""

import sys

import click
from tabulate import tabulate

from .auth import AuthManager
from .deploy import DeployManager
from .config import ConfigManager
from .http_client import APCloudyClient
from .utils import (
    print_success,
    print_error,
    print_info,
    print_cyan,
    create_setup
)


@click.group()
@click.version_option()
def main():
    """PAB - Deploy Scrapy spiders to APCloudy"""
    pass


@main.command()
@click.option('--api-key', '-k', help='APCloudy API key')
def login(api_key):
    """Login to APCloudy"""
    try:
        config_manager = ConfigManager()

        if config_manager.is_authenticated():
            creds = config_manager.get_credentials()
            print_info(f"You are already logged in as: {creds['username']}")

            if click.confirm("Do you want to logout and login with a different account?"):
                config_manager.clear_credentials()
                print_info("Logged out successfully.")
            else:
                print_info("Login cancelled. Use 'pab logout' to logout first.")
                return

        if not api_key:
            api_key = click.prompt('APCloudy API key')

        endpoint = config_manager.get_endpoint()

        auth_manager = AuthManager(endpoint)
        user_info = auth_manager.authenticate(api_key)

        config_manager.save_credentials(
            user_info['username'],
            user_info['access_token'],
            user_info['refresh_token'],
            user_info['api_key']
        )

        print_success(f"Successfully logged in as {user_info['username']}")

    except Exception as e:
        print_error(f"Login failed: {str(e)}")
        sys.exit(1)


@main.command()
def logout():
    """Logout from APCloudy"""
    try:
        config_manager = ConfigManager()
        config_manager.clear_credentials()
        print_success("Successfully logged out")
    except Exception as e:
        print_error(f"Logout failed: {str(e)}")


@main.command()
@click.argument('project_id')
def deploy(project_id):
    """Deploy Scrapy spider to APCloudy"""
    try:
        config_manager = ConfigManager()
        if not config_manager.is_authenticated():
            print_error("Not authenticated. Please run 'pab login' first.")
            sys.exit(1)

        create_setup()
        deploy_manager = DeployManager(config_manager)

        print_info(f"Deploying to project: {project_id}")

        deployment_id = deploy_manager.deploy(project_id)
        print_success(f"Successfully deployed! Deployment ID: {deployment_id}")

    except Exception as e:
        print_error(f"Deployment failed: {str(e)}")
        sys.exit(1)


@main.command()
def projects():
    """List available projects"""
    try:
        config_manager = ConfigManager()
        if not config_manager.is_authenticated():
            print_error("Not authenticated. Please run 'pab login' first.")
            sys.exit(1)

        http_client = APCloudyClient(config_manager)
        projects_data = http_client.list_projects()

        if not projects_data:
            print_error("No projects found for your account.")
            return

        table_headers = ["ID", "Name", "Organization", "Created At"]
        table_data = [[proj.get('id'), proj.get('name'), proj.get('org'), proj.get('created_at')] for proj in projects_data]

        print_info(f"Available projects: {len(projects_data)}")
        print_cyan(tabulate(table_data, headers=table_headers, tablefmt="grid"))

    except Exception as e:
        print_error(f"Failed to list projects: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('project_id')
def spiders(project_id):
    """List spiders in a project"""
    try:
        config_manager = ConfigManager()
        if not config_manager.is_authenticated():
            print_error("Not authenticated. Please run 'pab login' first.")
            sys.exit(1)

        http_client = APCloudyClient(config_manager)
        spiders_data = http_client.list_spiders(project_id)

        if not spiders_data:
            print_info(f"No spiders found in project {project_id}.")
            return

        table_headers = ["ID", "Name", "Start URL", "Created At"]
        table_data = [[sp.get('id'), sp.get('name'), sp.get('start_url'), sp.get('created_at')] for sp in spiders_data]

        print_info(f"Spiders in project {project_id}: {len(spiders_data)}")
        print_cyan(tabulate(table_data, headers=table_headers, tablefmt="grid"))

    except Exception as e:
        print_error(f"Failed to list spiders: {str(e)}")
        sys.exit(1)


@main.command()
def status():
    """Show the current authentication status"""
    try:
        config_manager = ConfigManager()
        if config_manager.is_authenticated():
            creds = config_manager.get_credentials()
            print_success(f"Logged in as: {creds.get('username')}")
        else:
            print_info("Not authenticated. Run 'pab login' to authenticate.")
    except Exception as e:
        print_error(f"Failed to get status: {str(e)}")


if __name__ == '__main__':
    main()
