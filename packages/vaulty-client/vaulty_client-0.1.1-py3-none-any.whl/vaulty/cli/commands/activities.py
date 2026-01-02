"""Activity commands."""

import sys
from datetime import datetime

import click

from ...cli.output import OutputFormatter
from ...cli.utils import get_client, run_async


@click.group()
def activities_group():
    """Activity management commands."""


@activities_group.command("list")
@click.option("--action", help="Filter by action (e.g., create_secret)")
@click.option("--method", help="Filter by HTTP method (e.g., POST)")
@click.option("--resource-id", help="Filter by resource ID")
@click.option("--search", help="Search term")
@click.option("--start-date", help="Filter activities after this date (YYYY-MM-DD)")
@click.option("--end-date", help="Filter activities before this date (YYYY-MM-DD)")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=50, help="Items per page")
@click.option(
    "--format", "-f", default="table", type=click.Choice(["json", "yaml", "plain", "table"])
)
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def list_activities(
    action,
    method,
    resource_id,
    search,
    start_date,
    end_date,
    page,
    page_size,
    format,
    token,
    base_url,
):
    """List activities with filters."""
    try:
        client = get_client(token=token, base_url=base_url)

        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)

        result = run_async(
            client.activities.list(
                page=page,
                page_size=page_size,
                action=action,
                method=method,
                resource_id=resource_id,
                search=search,
                start_date=start_dt,
                end_date=end_dt,
            )
        )

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
