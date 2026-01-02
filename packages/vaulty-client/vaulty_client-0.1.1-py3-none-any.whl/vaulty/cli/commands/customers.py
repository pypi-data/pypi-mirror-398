"""Customer commands."""

import sys

import click

from ...cli.output import OutputFormatter
from ...cli.utils import get_client, run_async
from ...client import VaultyClient


@click.group()
def customers_group():
    """Customer management commands."""


@customers_group.command("register")
@click.option("--email", "-e", required=True, help="Email address")
@click.option("--password", "-p", required=True, help="Password (min 8 characters)")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def register_customer(email, password, format, base_url):
    """Register new customer."""
    try:
        import os

        api_base_url = base_url or os.getenv("VAULTY_API_URL", "https://api.vaulty.com")
        client = VaultyClient(base_url=api_base_url)
        customer = run_async(client.customers.register(email=email, password=password))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(customer.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@customers_group.command("get")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_customer(format, token, base_url):
    """Get current customer info."""
    try:
        client = get_client(token=token, base_url=base_url)
        customer = run_async(client.customers.get_current())

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(customer.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@customers_group.group("settings")
def settings_group():
    """Customer settings commands."""


@settings_group.command("get")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_settings(format, token, base_url):
    """Get customer settings."""
    try:
        client = get_client(token=token, base_url=base_url)
        settings = run_async(client.customers.get_settings())

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(settings.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@settings_group.command("update")
@click.option("--rate-limit-enabled", type=bool, help="Enable/disable rate limiting")
@click.option("--rate-limit-requests-per-minute", type=int, help="Rate limit for API requests")
@click.option(
    "--rate-limit-auth-attempts-per-minute", type=int, help="Rate limit for auth endpoints"
)
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def update_settings(
    rate_limit_enabled,
    rate_limit_requests_per_minute,
    rate_limit_auth_attempts_per_minute,
    format,
    token,
    base_url,
):
    """Update customer settings."""
    try:
        client = get_client(token=token, base_url=base_url)
        settings = run_async(
            client.customers.update_settings(
                rate_limit_enabled=rate_limit_enabled,
                rate_limit_requests_per_minute=rate_limit_requests_per_minute,
                rate_limit_auth_attempts_per_minute=rate_limit_auth_attempts_per_minute,
            )
        )

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(settings.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
