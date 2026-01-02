"""Secret commands."""

import sys

import click

from ... import (
    VaultyAPIError,
    VaultyAuthenticationError,
    VaultyAuthorizationError,
    VaultyNotFoundError,
    VaultyRateLimitError,
    VaultyValidationError,
)
from ...cli.output import OutputFormatter
from ...cli.utils import detect_cicd, get_client, get_project_from_token_scope, run_async


@click.group()
def secrets_group():
    """Secret management commands."""


@secrets_group.command("get")
@click.argument("key")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_secret(key, project, format, token, base_url):
    """Get secret value (decrypted).

    Defaults to plain text output for CI/CD.
    """
    # Default format based on CI/CD detection
    if format is None:
        format = "plain" if detect_cicd() else "json"

    try:
        client = get_client(token=token, base_url=base_url)

        # Determine project name
        # For project-scoped tokens, project is optional (auto-inferred)
        # For full scope tokens, project is required
        if not project:
            # Try to get from config or environment
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        value_response = run_async(client.secrets.get_value(project_name=project, key=key))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(value_response.dict()))
    except VaultyNotFoundError:
        click.echo(f"Error: Secret '{key}' not found in project '{project}'", err=True)
        sys.exit(1)
    except VaultyAuthenticationError:
        click.echo("Error: Authentication failed. Please run 'vaulty login'", err=True)
        sys.exit(1)
    except VaultyAuthorizationError:
        click.echo(
            f"Error: Insufficient permissions to access secret '{key}' in project '{project}'",
            err=True,
        )
        sys.exit(1)
    except VaultyValidationError as e:
        click.echo(f"Error: Validation failed - {e.detail or str(e)}", err=True)
        sys.exit(1)
    except VaultyRateLimitError as e:
        click.echo(f"Error: Rate limit exceeded. {e.detail or 'Please try again later.'}", err=True)
        sys.exit(1)
    except VaultyAPIError as e:
        click.echo(f"Error: {e.detail or str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("list")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=50, help="Items per page")
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain", "table"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def list_secrets(project, page, page_size, format, token, base_url):
    """List secrets in project.

    For full scope tokens: --project is REQUIRED
    For project-scoped tokens: --project is OPTIONAL (defaults to token's project)
    """
    # Default format based on CI/CD detection
    if format is None:
        format = "plain" if detect_cicd() else "table"

    try:
        client = get_client(token=token, base_url=base_url)

        # Determine project name
        # For project-scoped tokens, project is optional (auto-inferred)
        # For full scope tokens, project is required
        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        result = run_async(
            client.secrets.list(project_name=project, page=page, page_size=page_size)
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
    except VaultyAuthenticationError:
        click.echo("Error: Authentication failed. Please run 'vaulty login'", err=True)
        sys.exit(1)
    except VaultyAuthorizationError:
        click.echo(
            f"Error: Insufficient permissions to list secrets in project '{project}'", err=True
        )
        sys.exit(1)
    except VaultyNotFoundError as e:
        click.echo(f"Error: {e.detail or 'Project not found'}", err=True)
        sys.exit(1)
    except VaultyAPIError as e:
        click.echo(f"Error: {e.detail or str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("create")
@click.argument("key")
@click.argument("value", required=False)
@click.option("--project", "-p", help="Project name")
@click.option("--prompt", is_flag=True, help="Prompt for value (hidden input)")
@click.option("--stdin", is_flag=True, help="Read value from stdin")
@click.option("--file", help="Read value from file")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def create_secret(key, value, project, prompt, stdin, file, format, token, base_url):
    """Create secret."""
    try:
        # Determine secret value
        if stdin:
            import sys

            value = sys.stdin.read().strip()
        elif file:
            with open(file) as f:
                value = f.read().strip()
        elif prompt:
            value = click.prompt("Value", hide_input=True)
        elif not value:
            click.echo("Error: Must provide value, --prompt, --stdin, or --file", err=True)
            sys.exit(2)

        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                client = get_client(token=token, base_url=base_url)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        client = get_client(token=token, base_url=base_url)
        secret = run_async(client.secrets.create(project_name=project, key=key, value=value))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(secret.dict()))
    except VaultyNotFoundError:
        click.echo(f"Error: Secret '{key}' or project '{project}' not found", err=True)
        sys.exit(1)
    except VaultyAuthenticationError:
        click.echo("Error: Authentication failed. Please run 'vaulty login'", err=True)
        sys.exit(1)
    except VaultyValidationError as e:
        click.echo(f"Error: Validation failed - {e.detail or str(e)}", err=True)
        sys.exit(1)
    except VaultyAPIError as e:
        click.echo(f"Error: {e.detail or str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("update")
@click.argument("key")
@click.argument("value", required=False)
@click.option("--project", "-p", help="Project name")
@click.option("--prompt", is_flag=True, help="Prompt for value (hidden input)")
@click.option("--stdin", is_flag=True, help="Read value from stdin")
@click.option("--file", help="Read value from file")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def update_secret(key, value, project, prompt, stdin, file, format, token, base_url):
    """Update secret value."""
    try:
        # Determine secret value
        if stdin:
            import sys

            value = sys.stdin.read().strip()
        elif file:
            with open(file) as f:
                value = f.read().strip()
        elif prompt:
            value = click.prompt("Value", hide_input=True)
        elif not value:
            click.echo("Error: Must provide value, --prompt, --stdin, or --file", err=True)
            sys.exit(2)

        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                client = get_client(token=token, base_url=base_url)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        client = get_client(token=token, base_url=base_url)
        secret = run_async(client.secrets.update(project_name=project, key=key, value=value))

        formatter = OutputFormatter(format=format)
        click.echo(formatter.format_output(secret.dict()))
    except VaultyNotFoundError:
        click.echo(f"Error: Secret '{key}' or project '{project}' not found", err=True)
        sys.exit(1)
    except VaultyAuthenticationError:
        click.echo("Error: Authentication failed. Please run 'vaulty login'", err=True)
        sys.exit(1)
    except VaultyValidationError as e:
        click.echo(f"Error: Validation failed - {e.detail or str(e)}", err=True)
        sys.exit(1)
    except VaultyAPIError as e:
        click.echo(f"Error: {e.detail or str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("delete")
@click.argument("key")
@click.option("--project", "-p", help="Project name")
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def delete_secret(key, project, token, base_url):
    """Delete secret."""
    try:
        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                client = get_client(token=token, base_url=base_url)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        client = get_client(token=token, base_url=base_url)
        run_async(client.secrets.delete(project_name=project, key=key))
        click.echo("Secret deleted successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("export")
@click.option("--project", "-p", help="Project name")
@click.option("--prefix", default="VAULTY_SECRET_", help="Prefix for environment variable names")
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def export_secrets(project, prefix, token, base_url):
    """Export all secrets as environment variables (CI/CD friendly)."""
    try:
        client = get_client(token=token, base_url=base_url)

        # Determine project name
        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    click.echo(
                        "Error: --project is required for full-scope tokens. For project-scoped tokens, project is auto-detected.",
                        err=True,
                    )
                    sys.exit(2)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        # Fetch all secrets with pagination (API max page_size is 100)
        all_secrets = []
        page = 1
        page_size = 100

        while True:
            result = run_async(
                client.secrets.list(project_name=project, page=page, page_size=page_size)
            )
            all_secrets.extend(result.items)
            if not result.has_next:
                break
            page += 1

        result.items = all_secrets

        # Get all secrets with values
        secrets_with_values = []
        for secret in result.items:
            try:
                value_response = run_async(
                    client.secrets.get_value(project_name=project, key=secret.key)
                )
                secrets_with_values.append({"key": secret.key, "value": value_response.value})
            except Exception:
                pass

        formatter = OutputFormatter(format="env")
        click.echo(formatter.format_env({"items": secrets_with_values}, prefix=prefix))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@secrets_group.command("exists")
@click.argument("key")
@click.option("--project", "-p", help="Project name")
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def exists_secret(key, project, token, base_url):
    """Check if secret exists (CI/CD friendly, exit code 0 if exists, 1 if not)."""
    try:
        client = get_client(token=token, base_url=base_url)

        # Determine project name
        if not project:
            import os

            project = os.getenv("VAULTY_PROJECT")
            if not project:
                # Try to infer from token scope (for project-scoped tokens)
                project_info = run_async(get_project_from_token_scope(client))
                if not project_info:
                    sys.exit(1)
                # Use project name if available, otherwise use project ID
                project = project_info.get("name") or project_info.get("id")

        run_async(client.secrets.get(project_name=project, key=key))
        sys.exit(0)
    except Exception:
        sys.exit(1)


# Add get_secret as standalone command (for convenience)
@click.command("get_secret")
@click.argument("key")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_secret_command(key, project, format, token, base_url):
    """Get secret value (decrypted). Alias for 'secrets get'."""
    get_secret(key, project, format, token, base_url)


# Register standalone command
secrets_group.add_command(get_secret_command, name="get_secret")
