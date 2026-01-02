"""Output formatting for CLI."""

import json
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table


class OutputFormatter:
    """Formats output for CLI commands."""

    def __init__(self, format: str = "plain"):
        self.format = format
        self.console = Console()

    def format_output(self, data: Any) -> str:
        """Format output based on format type.

        Args:
            data: Data to format

        Returns:
            Formatted string
        """
        if self.format == "json":
            return json.dumps(data, indent=2, default=str)
        if self.format == "yaml":
            return yaml.dump(data, default_flow_style=False, default_style=None)
        if self.format == "table":
            return self._format_table(data)
        # plain
        return self._format_plain(data)

    def _format_plain(self, data: Any) -> str:
        """Format as plain text."""
        if isinstance(data, dict):
            # For secret value responses, return just the value
            if "value" in data:
                return str(data["value"])
            # For list responses, return one item per line
            if "items" in data:
                if isinstance(data["items"], list) and len(data["items"]) > 0:
                    if isinstance(data["items"][0], dict):
                        # Extract key field if available
                        if "key" in data["items"][0]:
                            return "\n".join(str(item["key"]) for item in data["items"])
                        if "name" in data["items"][0]:
                            return "\n".join(str(item["name"]) for item in data["items"])
            return str(data)
        if isinstance(data, list):
            return "\n".join(str(item) for item in data)
        return str(data)

    def _format_table(self, data: Any) -> str:
        """Format as table."""
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
            if not items:
                return "No items found."

            # Determine columns from first item
            if isinstance(items[0], dict):
                columns = list(items[0].keys())
                table = Table()

                for col in columns:
                    table.add_column(col.replace("_", " ").title())

                for item in items:
                    table.add_row(*[str(item.get(col, "")) for col in columns])

                console = Console()
                with console.capture() as capture:
                    console.print(table)
                return capture.get()

        return self._format_plain(data)

    def format_env(self, data: Any, prefix: str = "VAULTY_SECRET_") -> str:
        """Format as environment variables.

        Args:
            data: Data to format
            prefix: Prefix for environment variable names

        Returns:
            Environment variable export statements
        """
        exports = []

        if isinstance(data, dict) and "items" in data:
            # List of secrets
            for item in data["items"]:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    key = item["key"]
                    value = item["value"]
                    var_name = f"{prefix}{key}"
                    exports.append(f"export {var_name}={value}")
        elif isinstance(data, dict) and "key" in data and "value" in data:
            # Single secret
            key = data["key"]
            value = data["value"]
            var_name = f"{prefix}{key}"
            exports.append(f"export {var_name}={value}")

        return "\n".join(exports)
