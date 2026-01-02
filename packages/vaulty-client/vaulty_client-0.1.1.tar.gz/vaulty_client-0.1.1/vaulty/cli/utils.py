"""CLI utilities."""

import asyncio
import os
import sys

import click

from .. import VaultyClient
from .config import CLIConfig


def get_client(
    token: str | None = None, base_url: str | None = None, non_interactive: bool = True
) -> VaultyClient:
    """Get Vaulty client from config or parameters.

    Args:
        token: API token (overrides stored credentials)
        base_url: Base URL (overrides stored/configured URL)
        non_interactive: Non-interactive mode (default: True)

    Returns:
        VaultyClient instance
    """
    config = CLIConfig()
    config_data = config.load()

    # Determine base URL (priority: parameter > env var > stored > default)
    if base_url:
        api_base_url = base_url.rstrip("/")
    elif os.getenv("VAULTY_API_URL"):
        api_base_url = os.getenv("VAULTY_API_URL").rstrip("/")
    elif config_data.get("api_url"):
        api_base_url = config_data["api_url"].rstrip("/")
    else:
        api_base_url = "https://api.vaulty.com"

    # Normalize base URL - remove trailing /api if present (paths include /api/v1/...)
    # Backend structure: Health at root (/health), API under /api/v1/...
    # So base_url should be at root (http://localhost:8000), not http://localhost:8000/api
    if api_base_url.endswith("/api"):
        api_base_url = api_base_url[:-4]
    elif api_base_url.endswith("/api/"):
        api_base_url = api_base_url[:-5]

    # Determine token (priority: parameter > env var > stored)
    api_token = None
    jwt_token = None

    if token:
        api_token = token
    elif os.getenv("VAULTY_API_TOKEN"):
        api_token = os.getenv("VAULTY_API_TOKEN")
    elif config_data.get("api_token"):
        api_token = config_data["api_token"]
    elif os.getenv("VAULTY_JWT_TOKEN"):
        jwt_token = os.getenv("VAULTY_JWT_TOKEN")
    elif config_data.get("jwt_token"):
        jwt_token = config_data["jwt_token"]

    if not api_token and not jwt_token:
        if non_interactive:
            raise ValueError(
                "No authentication token found. Set VAULTY_API_TOKEN or run 'vaulty login'"
            )
        raise ValueError("No authentication token found. Run 'vaulty login' first.")

    return VaultyClient(base_url=api_base_url, api_token=api_token, jwt_token=jwt_token)


async def get_project_from_token_scope(client: VaultyClient) -> dict[str, str] | None:
    """Extract project ID and name from token scope (for project-scoped tokens).

    For project-scoped tokens, extracts project ID from token scope and attempts
    to fetch the project name. The server's secrets route can fetch projects by ID,
    so we use that to get project information.

    For full-scope tokens, returns None (project must be specified explicitly).

    Args:
        client: VaultyClient instance

    Returns:
        Dict with 'id' and 'name' keys if token is project-scoped, None otherwise.
        'name' may be None if we can't fetch it, but 'id' will always be present.
    """
    try:
        # Try to get project from token scope by listing tokens
        tokens_result = await client.tokens.list(page=1, page_size=1)

        if tokens_result.items:
            token = tokens_result.items[0]
            scope = token.scope

            # Extract project ID from scope (format: project:p-xxxxx:read/write)
            if scope.startswith("project:"):
                parts = scope.split(":")
                if len(parts) >= 2:
                    project_id = parts[1]

                    # For project-scoped tokens, we have the project ID from the token scope
                    # The server's secrets route accepts project_name parameter, and if it matches
                    # the token's project_id, it will fetch the project by ID internally
                    # So we can use the project ID as the project name in API calls
                    # This maintains the standard approach of using project_name parameter
                    return {
                        "id": project_id,
                        "name": project_id,  # Use ID as name - server's secrets route accepts it
                    }

        return None
    except Exception:
        # If tokens.list fails, return None
        return None


def run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


def detect_cicd() -> bool:
    """Detect if running in CI/CD environment."""
    ci_vars = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "CIRCLECI",
    ]
    return any(os.getenv(var) for var in ci_vars)


def resolve_project(
    project: str | None, client: VaultyClient, required: bool = False
) -> str | None:
    """Resolve project name from various sources.

    Args:
        project: Explicitly provided project name
        client: VaultyClient instance
        required: Whether project is required (for full-scope tokens)

    Returns:
        Project name or None if not found and not required

    Raises:
        ValueError: If project is required but cannot be determined
    """
    if project:
        return project

    # Try environment variable
    project = os.getenv("VAULTY_PROJECT")
    if project:
        return project

    # Try to infer from token scope (for project-scoped tokens)
    project_info = run_async(get_project_from_token_scope(client))
    if project_info:
        return project_info.get("name") or project_info.get("id")

    if required:
        raise ValueError(
            "--project is required for full-scope tokens. "
            "For project-scoped tokens, project is auto-detected."
        )

    return None


def handle_cli_errors(func):
    """Decorator to handle common CLI errors.

    Usage:
        @handle_cli_errors
        def my_command(...):
            ...
    """
    import functools

    from .. import (
        VaultyAPIError,
        VaultyAuthenticationError,
        VaultyAuthorizationError,
        VaultyNotFoundError,
        VaultyRateLimitError,
        VaultyValidationError,
    )

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except VaultyNotFoundError as e:
            click.echo(f"Error: Resource not found - {e.detail or str(e)}", err=True)
            sys.exit(1)
        except VaultyAuthenticationError:
            click.echo("Error: Authentication failed. Please run 'vaulty login'", err=True)
            sys.exit(1)
        except VaultyAuthorizationError as e:
            click.echo(f"Error: Insufficient permissions - {e.detail or str(e)}", err=True)
            sys.exit(1)
        except VaultyValidationError as e:
            click.echo(f"Error: Validation failed - {e.detail or str(e)}", err=True)
            sys.exit(1)
        except VaultyRateLimitError as e:
            click.echo(
                f"Error: Rate limit exceeded. {e.detail or 'Please try again later.'}", err=True
            )
            sys.exit(1)
        except VaultyAPIError as e:
            click.echo(f"Error: {e.detail or str(e)}", err=True)
            sys.exit(1)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(2)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)

    return wrapper
