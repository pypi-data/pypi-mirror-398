# Vaulty Python SDK

High-level Python SDK and CLI for the Vaulty API.

## Features

- ✅ Type-safe API client with Pydantic models
- ✅ Full async/await support
- ✅ Automatic retry with exponential backoff
- ✅ Rate limit handling
- ✅ CLI tool for terminal usage
- ✅ CI/CD friendly defaults
- ✅ Support for full-scope and project-scoped tokens

## Installation

```bash
# SDK only
pip install vaulty

# SDK with CLI
pip install vaulty[cli]
```

## Quick Start

### Python SDK

```python
import asyncio
from vaulty import VaultyClient

async def main():
    # Initialize client
    client = VaultyClient(
        base_url="https://api.vaulty.com",
        api_token="vaulty_abc123..."
    )

    # Create project
    project = await client.projects.create(
        name="my-project",
        description="My awesome project"
    )

    # Create secret
    secret = await client.secrets.create(
        project_name="my-project",
        key="API_KEY",
        value="secret_value_123"
    )

    # Get secret value
    value = await client.secrets.get_value(
        project_name="my-project",
        key="API_KEY"
    )
    print(f"Secret value: {value.value}")

asyncio.run(main())
```

### CLI

```bash
# Login
vaulty login vaulty_abc123...

# Create project
vaulty projects create my-project --description "My project"

# Create secret
vaulty secrets create API_KEY "secret_value" --project my-project

# Get secret value
vaulty get_secret API_KEY --project my-project

# List secrets
vaulty secrets list --project my-project
```

## API Reference

### Client Initialization

```python
from vaulty import VaultyClient

# Initialize with API token
client = VaultyClient(
    base_url="https://api.vaulty.com",
    api_token="vaulty_abc123..."
)

# Initialize with custom base URL (for local development)
client = VaultyClient(
    base_url="http://localhost:3001",
    api_token="vaulty_abc123..."
)

# Initialize with email/password for JWT
client = VaultyClient(
    base_url="https://api.vaulty.com",
    email="user@example.com",
    password="password123"
)

# Load from environment variables
client = VaultyClient.from_env()  # Uses VAULTY_API_URL and VAULTY_API_TOKEN
```

### Projects

```python
# Create, list, get, update, delete projects
project = await client.projects.create(
    name="my-project",
    description="My awesome project"
)
projects_page = await client.projects.list(page=1, page_size=50)
project = await client.projects.get("my-project")
updated = await client.projects.update(
    name="my-project",
    description="Updated description"
)
await client.projects.delete("my-project")
```

### Secrets

```python
# Create, list, get, update, delete secrets
secret = await client.secrets.create(
    project_name="my-project",
    key="API_KEY",
    value="secret_value_123"
)
secrets_page = await client.secrets.list(
    project_name="my-project",
    page=1,
    page_size=50
)
secret = await client.secrets.get(
    project_name="my-project",
    key="API_KEY"
)
value_response = await client.secrets.get_value(
    project_name="my-project",
    key="API_KEY"
)
updated = await client.secrets.update(
    project_name="my-project",
    key="API_KEY",
    value="new_secret_value"
)
await client.secrets.delete(
    project_name="my-project",
    key="API_KEY"
)
```

### Tokens

```python
# Create full-scope or project-scoped tokens, list, delete
token = await client.tokens.create(
    name="My API Token",
    scope="full",
    expires_at=None
)
token = await client.tokens.create(
    name="Project Read Token",
    scope="read",
    project_id="p-abc123"
)
tokens_page = await client.tokens.list(page=1, page_size=50)
await client.tokens.delete("t-token123")
```

### Customers

```python
# Register, login, get current customer, update settings
customer = await client.customers.register(
    email="user@example.com",
    password="secure_password123"
)
token_response = await client.customers.login(
    email="user@example.com",
    password="secure_password123"
)
customer = await client.customers.get_current()
settings = await client.customers.update_settings(
    rate_limit_enabled=True,
    rate_limit_requests_per_minute=100
)
```

### Activities

```python
# List activities with filters and pagination
from datetime import datetime

activities_page = await client.activities.list(
    page=1,
    page_size=50,
    action="create_secret",
    method="POST",
    resource_id="s-abc123",
    search="API_KEY",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31)
)
```

### Health

```python
health = await client.health.check()
ready = await client.health.ready()
live = await client.health.live()
```

## Advanced Features

- **Automatic Retry**: Retries on transient errors (5xx, network errors) with exponential backoff
- **Rate Limit Handling**: Automatic backoff on rate limit errors
- **Context Managers**: Automatic cleanup with `async with`
- **Pagination Helpers**: `list_all()` iterates through all pages automatically
- **Type Safety**: Full Pydantic model support for request/response validation

## Base URL Management

### Priority Order
1. Explicit parameter: `--base-url` flag or `base_url` parameter
2. Environment variable: `VAULTY_API_URL`
3. Stored from login: Base URL stored when running `vaulty login <token> --base-url <url>`
4. Default: Production URL (`https://api.vaulty.com`)

### Usage
```bash
# Login with custom base URL (stores for future use)
vaulty login vaulty_abc123... --base-url http://localhost:3001

# All subsequent commands use stored base URL
vaulty get_secret HelloToken  # Uses http://localhost:3001
```

## Development

### Local Checks (Before Committing)

**CRITICAL**: Always run these checks locally before pushing! This prevents CI failures.

```bash
# Run all CI checks (matches GitHub Actions exactly)
./scripts/check.sh

# This runs:
# - ruff check .              (no auto-fix, matches CI)
# - ruff format --check .      (format check, matches CI)
# - mypy vaulty --ignore-missing-imports
# - pytest with coverage

# If checks fail, fix errors:
ruff check . --fix            # Auto-fix ruff errors
ruff format .                 # Auto-format code
./scripts/check.sh            # Verify fixes
```
mypy vaulty --ignore-missing-imports  # Type checking
pytest tests/ -v --cov=vaulty --cov-report=term-missing  # Tests

# Option 3: Use pre-commit hooks (runs automatically on commit)
pre-commit install              # Install hooks (one-time setup)
# Now every commit will run checks automatically
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=vaulty --cov-report=html
```

### Building for Distribution

```bash
# Install build tools
pip install build twine

# Build packages
python -m build

# Check package
python -m twine check dist/*

# Upload to TestPyPI (for testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
python -m twine upload dist/*
```

**Note**: Update version in `pyproject.toml` and `vaulty/__init__.py` before each release.

## CLI Commands

### Authentication

```bash
# Login with API token (default - simplest method)
vaulty login vaulty_abc123...
vaulty login vaulty_abc123... --base-url http://localhost:3001  # For local development

# Login with project-scoped token
vaulty login vaulty_project_token... --project my-project

# Login with email/password (JWT token)
vaulty login --email user@example.com

# Logout, status, info, validate
vaulty logout
vaulty auth status
vaulty auth info
vaulty auth validate  # CI/CD friendly: exit code 0 if valid, 1 if invalid
```

### Projects

```bash
vaulty projects list [--page 1] [--page-size 50]
vaulty projects get my-project
vaulty projects create my-project [--description "My project"]
vaulty projects update my-project [--description "Updated description"]
vaulty projects delete my-project
```

### Secrets

```bash
# Get secret value
vaulty get_secret HelloToken [--project my-project]
# Full scope: --project required | Project-scoped: --project optional (defaults to token's project)

# List secrets
vaulty secrets list [--project my-project] [--page 1] [--page-size 50]

# Create, update, delete
vaulty secrets create HelloToken "secret_value" [--project my-project]
vaulty secrets update HelloToken "new_value" [--project my-project]
vaulty secrets delete HelloToken [--project my-project]

# Export secrets (CI/CD friendly - 'env' format is default)
vaulty secrets export [--project my-project] [--prefix PROD_]
# Output: export KEY1=value1\nexport KEY2=value2
# Usage: source <(vaulty secrets export --project PROJECT)

# Check if secret exists (CI/CD friendly - exit code 0 if exists, 1 if not)
vaulty secrets exists HelloToken [--project my-project]
```

### Tokens

```bash
vaulty tokens list
vaulty tokens create "My Token" --scope full
vaulty tokens create "Project Read Token" --scope read --project-id p-abc123
vaulty tokens create "Project Write Token" --scope write --project-id p-abc123
vaulty tokens delete t-token123
```

### Activities

```bash
vaulty activities list [--action create_secret] [--method POST] [--resource-id s-abc123] [--search "API_KEY"] [--start-date 2025-01-01] [--end-date 2025-12-31] [--page 1] [--page-size 50]
```

### Customers

```bash
vaulty customers register --email user@example.com --password password123
vaulty customers get
vaulty customers settings update --rate-limit-enabled true --rate-limit-requests-per-minute 100
vaulty customers settings get
```

### Health

```bash
vaulty health
vaulty health ready
vaulty health live
```

### Output Formats

```bash
# JSON, YAML, plain (default), table (for lists)
vaulty get_secret HelloToken --format json
vaulty get_secret HelloToken --format plain  # Default for CI/CD
vaulty secrets list --project my-project --format table
```

## Token Scope Behavior

### Full Scope Tokens
- Access to all projects, secrets, tokens, activities owned by customer
- Must specify `--project` for project-scoped operations

### Project-Scoped Tokens
- Access only to assigned project (from token scope)
- `--project` is optional (defaults to token's project)
- Cannot access other projects (403 Forbidden)

### Examples

**Full scope token:**
```python
client = VaultyClient(api_token="vaulty_full_scope_token...")
secrets = await client.secrets.list("project-1")  # ✅ Works
secrets = await client.secrets.list("project-2")  # ✅ Works
```

**Project-scoped token (assigned to "my-project"):**
```python
client = VaultyClient(api_token="vaulty_project_token...")
secrets = await client.secrets.list()  # ✅ Works (uses "my-project" from token)
secrets = await client.secrets.list("my-project")  # ✅ Works (explicit)
secrets = await client.secrets.list("other-project")  # ❌ 403 Forbidden
```

**CLI with project-scoped token:**
```bash
vaulty secrets list  # ✅ Lists secrets from token's project (no --project needed!)
vaulty secrets list --project my-project  # ✅ Works if matches token's project
```

### Scope Comparison

| Operation | Full Scope | Project-Scoped (Read) | Project-Scoped (Write) |
|-----------|------------|----------------------|----------------------|
| List secrets in assigned project | ✅ | ✅ | ✅ |
| List secrets in other project | ✅ | ❌ (403) | ❌ (403) |
| Get secret from assigned project | ✅ | ✅ | ✅ |
| Create secret in assigned project | ✅ | ❌ (403) | ✅ |
| Update/Delete secret | ✅ | ❌ (403) | ✅ |
| List tokens | ✅ (all) | ✅ (project only) | ✅ (project only) |
| List activities | ✅ (all) | ✅ (project only) | ✅ (project only) |

## Error Handling

The SDK provides custom exceptions for different error types:

```python
from vaulty.exceptions import (
    VaultyError,
    VaultyAPIError,
    VaultyAuthenticationError,
    VaultyAuthorizationError,
    VaultyNotFoundError,
    VaultyValidationError,
    VaultyRateLimitError
)

try:
    secret = await client.secrets.get("my-project", "API_KEY")
except VaultyNotFoundError:
    print("Secret not found")
except VaultyRateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after}")
except VaultyAPIError as e:
    print(f"API error: {e}")
```

## Configuration

### Environment Variables

```bash
VAULTY_API_URL          # API base URL (default: https://api.vaulty.com)
VAULTY_API_TOKEN        # API token (full scope or project-scoped)
VAULTY_JWT_TOKEN        # JWT token (alternative to API token)
VAULTY_PROJECT          # Default project name (for project-scoped tokens)
VAULTY_FORMAT           # Default output format (json, yaml, plain, table)
VAULTY_NON_INTERACTIVE  # Force non-interactive mode (default: true)
```

### Client Configuration

```python
from vaulty import VaultyClient

# Configure client with custom settings
client = VaultyClient(
    base_url="https://api.vaulty.com",
    api_token="vaulty_abc123...",
    timeout=30.0,
    max_retries=3,
    retry_backoff_factor=2.0,
    rate_limit_retry=True
)
```

## CI/CD Integration

### Design Principles

1. **Non-Interactive by Default**: All commands work without user input
2. **Exit Codes**: Proper exit codes (0 = success, non-zero = failure)
3. **Plain Text Output**: Default to plain text for easy parsing
4. **Environment Variable Friendly**: Easy to use with `export` and `$()`
5. **No Prompts**: Never prompt for input in CI/CD environments
6. **Token-Based Auth**: Prefer API tokens over JWT for CI/CD

### Basic Usage

```bash
# Use environment variable for token
export VAULTY_API_TOKEN="vaulty_abc123..."
export VAULTY_API_URL="http://localhost:3001"  # Optional, for local development
export VAULTY_PROJECT="production"  # Optional, default project

# Quick secret retrieval (plain text is default)
export SECRET=$(vaulty get_secret KEY --project PROJECT)

# Export all secrets (format 'env' is default for export)
source <(vaulty secrets export --project PROJECT)

# Validate setup (silent checks)
vaulty auth validate && vaulty projects get PROJECT || exit 1

# Get multiple secrets
for key in DB_PASSWORD API_KEY SECRET_KEY; do
    export $key=$(vaulty get_secret $key --project PROJECT)
done
```

### CI/CD Examples

#### GitHub Actions

```yaml
- name: Get secrets
  env:
    VAULTY_API_TOKEN: ${{ secrets.VAULTY_API_TOKEN }}
    VAULTY_PROJECT: production
  run: |
    export DB_PASSWORD=$(vaulty get_secret DB_PASSWORD)
    export API_KEY=$(vaulty get_secret API_KEY)
```

#### GitLab CI

```yaml
script:
  - export DB_PASSWORD=$(vaulty get_secret DB_PASSWORD --project production --token "$VAULTY_API_TOKEN")
  - export API_KEY=$(vaulty get_secret API_KEY --project production --token "$VAULTY_API_TOKEN")
variables:
  VAULTY_API_TOKEN: $VAULTY_API_TOKEN
```

### Exit Codes

- `0`: Success
- `1`: General error (secret not found, authentication failed, etc.)
- `2`: Invalid arguments or configuration
- `3`: Network error
- `4`: API error (rate limit, server error, etc.)

## License

MIT
