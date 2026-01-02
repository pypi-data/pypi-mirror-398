"""Health check commands."""

import sys

import click

from ... import VaultyClient
from ...cli.output import OutputFormatter
from ...cli.utils import run_async


@click.group()
def health_group():
    """Health check commands."""


@health_group.command()
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def health(format, base_url):
    """Health check."""
    try:
        import os

        api_base_url = base_url or os.getenv("VAULTY_API_URL", "https://api.vaulty.com")
        client = VaultyClient(base_url=api_base_url)
        health_status = run_async(client.health.check())

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(health_status))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@health_group.command("ready")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def ready(format, base_url):
    """Readiness check."""
    try:
        import os

        api_base_url = base_url or os.getenv("VAULTY_API_URL", "https://api.vaulty.com")
        client = VaultyClient(base_url=api_base_url)
        ready_status = run_async(client.health.ready())

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(ready_status))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@health_group.command("live")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def live(format, base_url):
    """Liveness check."""
    try:
        import os

        api_base_url = base_url or os.getenv("VAULTY_API_URL", "https://api.vaulty.com")
        client = VaultyClient(base_url=api_base_url)
        live_status = run_async(client.health.live())

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(live_status))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
