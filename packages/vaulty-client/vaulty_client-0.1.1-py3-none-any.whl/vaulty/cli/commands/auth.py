"""Authentication commands."""

import sys

import click

from ... import VaultyAPIError, VaultyClient
from ..config import CLIConfig
from ..utils import get_client, run_async


@click.group()
def auth_group():
    """Authentication commands."""


@auth_group.command()
@click.argument("token", required=False)
@click.option("--email", "-e", help="Email address (for JWT login)")
@click.option("--password", "-p", help="Password (prompted if not provided)")
@click.option("--token", "-t", "token_flag", help="API token (alternative to positional)")
@click.option("--token-env", help="Environment variable containing API token")
@click.option("--token-file", help="File containing API token")
@click.option("--project", help="Project name (for project-scoped tokens)")
@click.option("--base-url", "-u", help="Base URL for API (e.g., http://localhost:3001)")
def login(token, email, password, token_flag, token_env, token_file, project, base_url):
    """Login and store credentials and base URL.

    Default usage: vaulty login <token> [--base-url <url>]
    """
    import os

    config = CLIConfig()

    # Determine base URL (priority: --base-url > env var > default)
    if base_url:
        api_base_url = base_url
    elif os.getenv("VAULTY_API_URL"):
        api_base_url = os.getenv("VAULTY_API_URL")
    else:
        api_base_url = "https://api.vaulty.com"

    # Determine authentication method
    api_token = None

    if token:  # Positional argument (default)
        api_token = token
    elif token_flag:  # --token flag
        api_token = token_flag
    elif token_env:
        api_token = os.getenv(token_env)
        if not api_token:
            click.echo(f"Error: Environment variable {token_env} not set", err=True)
            sys.exit(1)
    elif token_file:
        try:
            with open(token_file) as f:
                api_token = f.read().strip()
        except FileNotFoundError:
            click.echo(f"Error: Token file not found: {token_file}", err=True)
            sys.exit(1)
    elif email:
        if not password:
            password = click.prompt("Password", hide_input=True)

        # Login with email/password to get JWT
        try:
            client = VaultyClient(base_url=api_base_url)
            token_response = run_async(client.customers.login(email, password))
            # Store JWT token and base URL
            config.save_jwt_token(
                token_response["access_token"], email=email, base_url=api_base_url
            )
            click.echo("Logged in successfully!")
            click.echo(f"Base URL: {api_base_url}")
            return
        except VaultyAPIError as e:
            click.echo(f"Error: {e.detail}", err=True)
            sys.exit(1)
    else:
        click.echo("Error: Must provide token, --email, --token-env, or --token-file", err=True)
        click.echo("Usage: vaulty login <token> [--base-url <url>]", err=True)
        sys.exit(2)

    # Store API token and base URL
    config.save_api_token(api_token, project=project, base_url=api_base_url)
    click.echo("Logged in successfully!")
    click.echo(f"Base URL: {api_base_url}")

    # Verify token and show info
    try:
        client = VaultyClient(api_token=api_token, base_url=api_base_url)
        customer = run_async(client.customers.get_current())
        click.echo(f"Authenticated as: {customer.email}")
        if project:
            click.echo(f"Project scope: {project}")
    except VaultyAPIError as e:
        click.echo(f"Warning: Could not verify token: {e.detail}", err=True)


@auth_group.command()
def logout():
    """Logout (clear stored credentials and base URL)."""
    config = CLIConfig()
    config.clear_credentials()
    click.echo("Logged out successfully!")


@auth_group.command()
def status():
    """Show current authentication status."""
    config = CLIConfig()
    auth_info = config.get_auth_info()

    if auth_info:
        click.echo(f"Type: {auth_info.get('type', 'unknown')}")
        if auth_info.get("base_url"):
            click.echo(f"Base URL: {auth_info['base_url']}")
        if auth_info.get("project"):
            click.echo(f"Project: {auth_info['project']}")
        click.echo("Status: Authenticated")
    else:
        click.echo("Status: Not authenticated")


@auth_group.command()
def info():
    """Show current token info (scope, project, base URL, etc.)."""
    try:
        client = get_client()
        customer = run_async(client.customers.get_current())
        click.echo(f"Email: {customer.email}")
        click.echo(f"Customer ID: {customer.id}")

        config = CLIConfig()
        auth_info = config.get_auth_info()
        if auth_info:
            if auth_info.get("base_url"):
                click.echo(f"Base URL: {auth_info['base_url']}")
            if auth_info.get("project"):
                click.echo(f"Project: {auth_info['project']}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@auth_group.command()
def validate():
    """Validate token (CI/CD friendly, exit code 0 if valid, 1 if invalid)."""
    try:
        client = get_client()
        run_async(client.customers.get_current())
        sys.exit(0)
    except Exception:
        sys.exit(1)
