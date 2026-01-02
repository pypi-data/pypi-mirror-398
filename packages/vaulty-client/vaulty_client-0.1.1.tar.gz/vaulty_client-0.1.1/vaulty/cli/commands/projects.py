"""Project commands."""

import sys

import click

from ...cli.output import OutputFormatter
from ...cli.utils import get_client, run_async


@click.group()
def projects_group():
    """Project management commands."""


@projects_group.command("list")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=50, help="Items per page")
@click.option(
    "--format", "-f", default="table", type=click.Choice(["json", "yaml", "plain", "table"])
)
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def list_projects(page, page_size, format, token, base_url):
    """List all projects."""
    try:
        client = get_client(token=token, base_url=base_url)
        result = run_async(client.projects.list(page=page, page_size=page_size))

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


@projects_group.command("get")
@click.argument("name")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_project(name, format, token, base_url):
    """Get project details."""
    try:
        client = get_client(token=token, base_url=base_url)
        project = run_async(client.projects.get(name))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(project.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@projects_group.command("create")
@click.argument("name")
@click.option("--description", help="Project description")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def create_project(name, description, format, token, base_url):
    """Create project."""
    try:
        client = get_client(token=token, base_url=base_url)
        project = run_async(client.projects.create(name=name, description=description))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(project.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@projects_group.command("update")
@click.argument("name")
@click.option("--description", help="Project description")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def update_project(name, description, format, token, base_url):
    """Update project."""
    try:
        client = get_client(token=token, base_url=base_url)
        project = run_async(client.projects.update(name=name, description=description))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(project.dict()))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@projects_group.command("delete")
@click.argument("name")
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def delete_project(name, token, base_url):
    """Delete project."""
    try:
        client = get_client(token=token, base_url=base_url)
        run_async(client.projects.delete(name))
        click.echo("Project deleted successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
