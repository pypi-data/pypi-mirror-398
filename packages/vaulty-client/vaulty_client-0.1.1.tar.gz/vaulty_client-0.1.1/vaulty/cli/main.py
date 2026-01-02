"""CLI entry point."""

import sys

import click

from .. import __version__
from .commands import activities, auth, customers, health, projects, secrets, tokens


@click.group()
@click.version_option(version=__version__)
def cli():
    """Vaulty CLI - Manage secrets, projects, and tokens."""


# Add command groups
cli.add_command(auth.auth_group)
cli.add_command(projects.projects_group)
cli.add_command(secrets.secrets_group)
cli.add_command(tokens.tokens_group)
cli.add_command(activities.activities_group)
cli.add_command(customers.customers_group)
cli.add_command(health.health_group)


# Convenience shortcuts for common operations
@cli.command("login")
@click.argument("token", required=False)
@click.option("--email", "-e", help="Email address (for JWT login)")
@click.option("--password", "-p", help="Password (prompted if not provided)")
@click.option("--token", "-t", "token_flag", help="API token (alternative to positional)")
@click.option("--token-env", help="Environment variable containing API token")
@click.option("--token-file", help="File containing API token")
@click.option("--project", help="Project name (for project-scoped tokens)")
@click.option("--base-url", "-u", help="Base URL for API (e.g., http://localhost:8000)")
def login_shortcut(token, email, password, token_flag, token_env, token_file, project, base_url):
    """Login and store credentials (shortcut for 'auth login').

    Examples:
        vaulty login TOKEN
        vaulty login TOKEN --base-url http://localhost:8000
        vaulty login --email user@example.com
    """
    import os

    from .. import VaultyAPIError, VaultyClient
    from .config import CLIConfig
    from .utils import run_async

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


@cli.command("logout")
def logout_shortcut():
    """Logout and clear stored credentials (shortcut for 'auth logout').

    Examples:
        vaulty logout
    """
    from .config import CLIConfig

    config = CLIConfig()
    config.clear_credentials()
    click.echo("Logged out successfully!")


# Convenience shortcuts for common operations
@cli.command("get")
@click.argument("key")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_shortcut(key, project, format, token, base_url):
    """Get secret value (shortcut for 'secrets get').

    Examples:
        vaulty get API_KEY
        vaulty get API_KEY --project my-project
    """
    from .commands.secrets import get_secret

    get_secret(key, project, format, token, base_url)


@cli.command("g")
@click.argument("key")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def get_ultra_short(key, project, format, token, base_url):
    """Get secret value (ultra-short alias: 'g').

    Examples:
        vaulty g API_KEY
        vaulty g API_KEY --project my-project
    """
    from .commands.secrets import get_secret

    get_secret(key, project, format, token, base_url)


@cli.command("set")
@click.argument("key")
@click.argument("value", required=False)
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--prompt", is_flag=True, help="Prompt for value (hidden input)")
@click.option("--stdin", is_flag=True, help="Read value from stdin")
@click.option("--file", help="Read value from file")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def set_shortcut(key, value, project, prompt, stdin, file, format, token, base_url):
    """Set secret value (shortcut for 'secrets create').

    Examples:
        vaulty set API_KEY "secret-value"
        vaulty set API_KEY --prompt
        vaulty set API_KEY --stdin
    """
    import sys

    from .output import OutputFormatter
    from .utils import get_client, get_project_from_token_scope, run_async

    try:
        # Determine secret value
        if stdin:
            import sys as sys_module

            value = sys_module.stdin.read().strip()
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
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("key")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def delete_shortcut(key, project, token, base_url):
    """Delete secret (shortcut for 'secrets delete').

    Examples:
        vaulty delete API_KEY
        vaulty delete API_KEY --project my-project
    """
    import sys

    from .utils import get_client, get_project_from_token_scope, run_async

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


@cli.command("list")
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=50, help="Items per page")
@click.option("--format", "-f", default=None, type=click.Choice(["json", "yaml", "plain", "table"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def list_shortcut(project, page, page_size, format, token, base_url):
    """List secrets (shortcut for 'secrets list').

    Examples:
        vaulty list
        vaulty list --project my-project
    """
    # Import the actual implementation logic
    import sys

    from .output import OutputFormatter
    from .utils import detect_cicd, get_client, get_project_from_token_scope, run_async

    # Default format based on CI/CD detection
    if format is None:
        format = "plain" if detect_cicd() else "table"

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
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("update")
@click.argument("key")
@click.argument("value", required=False)
@click.option(
    "--project", "-p", help="Project name (required for full scope, optional for project-scoped)"
)
@click.option("--prompt", is_flag=True, help="Prompt for value (hidden input)")
@click.option("--stdin", is_flag=True, help="Read value from stdin")
@click.option("--file", help="Read value from file")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "plain"]))
@click.option("--token", "-t", help="API token (overrides stored credentials)")
@click.option("--base-url", "-u", help="Base URL (overrides stored/configured URL)")
def update_shortcut(key, value, project, prompt, stdin, file, format, token, base_url):
    """Update secret value (shortcut for 'secrets update').

    Examples:
        vaulty update API_KEY "new-value"
        vaulty update API_KEY --prompt
    """
    import sys

    from .output import OutputFormatter
    from .utils import get_client, get_project_from_token_scope, run_async

    try:
        # Determine secret value
        if stdin:
            import sys as sys_module

            value = sys_module.stdin.read().strip()
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
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
