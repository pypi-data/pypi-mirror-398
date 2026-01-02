"""Token commands."""

import sys

import click

from ...cli.output import OutputFormatter
from ...cli.utils import get_client, run_async


@click.group()
def tokens_group():
    """Token management commands."""


@tokens_group.command("list")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=50, help="Items per page")
@click.option(
    "--format", "-f", default="table", type=click.Choice(["json", "yaml", "plain", "table"])
)
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def list_tokens(page, page_size, format, token, base_url):
    """List all tokens."""
    try:
        client = get_client(token=token, base_url=base_url)
        result = run_async(client.tokens.list(page=page, page_size=page_size))

        formatter = OutputFormatter(format=format)
        output = formatter.format_output(
            {
                "items": [item.dict() for item in result.items],
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
                "total_pages": result.total_pages,
                "has_next": result.has_next,
                "has_previous": result.has_previous,
            }
        )
        click.echo(output)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tokens_group.command("create")
@click.argument("name")
@click.option(
    "--scope",
    required=True,
    help="Token scope (full, read, write, or project:{project_id}:read/write)",
)
@click.option("--description", help="Token description")
@click.option("--password", help="Customer password (required for first token if no DEK exists)")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def create_token(name, scope, description, password, format, token, base_url):
    """Create API token."""
    try:
        client = get_client(token=token, base_url=base_url)
        token_response = run_async(
            client.tokens.create(scope=scope, description=description or name, password=password)
        )

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(token_response.dict()))

        if token_response.token:
            click.echo(f"\nToken: {token_response.token}", err=True)
            click.echo("⚠️  Save this token now - it won't be shown again!", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@tokens_group.command("delete")
@click.argument("token_id")
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def delete_token(token_id, token, base_url):
    """Delete token."""
    try:
        client = get_client(token=token, base_url=base_url)
        run_async(client.tokens.delete(token_id))
        click.echo("Token deleted successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
