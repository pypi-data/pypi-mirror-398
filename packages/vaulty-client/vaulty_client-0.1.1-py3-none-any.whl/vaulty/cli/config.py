"""CLI configuration management."""

import base64
import json
import os
from pathlib import Path
from typing import Any

import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CLIConfig:
    """Manages CLI configuration and credentials."""

    def __init__(self):
        self.config_dir = Path.home() / ".vaulty"
        self.config_file = self.config_dir / "config.yaml"
        self.credentials_file = self.config_dir / "credentials.json"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _get_encryption_key(self) -> bytes:
        """Get encryption key for credentials (derived from machine ID)."""
        # Use machine-specific identifier (hostname + user)
        machine_id = f"{os.getenv('HOSTNAME', 'localhost')}-{os.getenv('USER', 'user')}"

        # Derive key using PBKDF2 with SHA256 hash
        from cryptography.hazmat.primitives import hashes

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"vaulty_cli_salt",  # Fixed salt for consistency
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return key

    def load(self) -> dict[str, Any]:
        """Load configuration from file or environment."""
        config = {}

        # Load from file
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Load credentials (encrypted) - includes stored base_url
        auth_info = self.get_auth_info()
        if auth_info:
            if auth_info.get("type") == "api_token":
                config["api_token"] = auth_info["token"]
                if auth_info.get("project"):
                    config["default_project"] = auth_info["project"]
                if auth_info.get("base_url"):
                    config["api_url"] = auth_info["base_url"]
            elif auth_info.get("type") == "jwt":
                config["jwt_token"] = auth_info["token"]
                if auth_info.get("base_url"):
                    config["api_url"] = auth_info["base_url"]

        # Override with environment variables (highest priority)
        if os.getenv("VAULTY_API_URL"):
            config["api_url"] = os.getenv("VAULTY_API_URL")
        if os.getenv("VAULTY_API_TOKEN"):
            config["api_token"] = os.getenv("VAULTY_API_TOKEN")
        if os.getenv("VAULTY_JWT_TOKEN"):
            config["jwt_token"] = os.getenv("VAULTY_JWT_TOKEN")

        # Default to production if no base_url set
        if not config.get("api_url"):
            config["api_url"] = "https://api.vaulty.com"

        return config

    def get_auth_info(self) -> dict[str, Any] | None:
        """Get authentication info from encrypted credentials file."""
        if not self.credentials_file.exists():
            return None

        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)

            encrypted = self.credentials_file.read_bytes()
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception:
            return None

    def _validate_token(self, token: str) -> bool:
        """Validate token format.

        Args:
            token: Token to validate

        Returns:
            True if token appears valid
        """
        if not token or len(token) < 10:
            return False
        # Basic validation - tokens should start with 'vaulty_' or be JWT-like
        return token.startswith("vaulty_") or len(token.split(".")) >= 2

    def save_api_token(self, token: str, project: str | None = None, base_url: str | None = None):
        """Save API token and base URL (encrypted).

        Args:
            token: API token to save
            project: Optional project name
            base_url: Optional base URL

        Raises:
            ValueError: If token format is invalid
        """
        if not self._validate_token(token):
            raise ValueError(
                "Invalid token format. Token should start with 'vaulty_' or be a valid JWT."
            )

        key = self._get_encryption_key()
        fernet = Fernet(key)

        credentials = {
            "type": "api_token",
            "token": token,
            "project": project,
            "base_url": base_url,
        }

        encrypted = fernet.encrypt(json.dumps(credentials).encode())
        self.credentials_file.write_bytes(encrypted)
        self.credentials_file.chmod(0o600)

    def save_jwt_token(self, token: str, email: str | None = None, base_url: str | None = None):
        """Save JWT token and base URL (encrypted).

        Args:
            token: JWT token to save
            email: Optional email address
            base_url: Optional base URL

        Raises:
            ValueError: If token format is invalid
        """
        if not self._validate_token(token):
            raise ValueError("Invalid JWT token format.")

        key = self._get_encryption_key()
        fernet = Fernet(key)

        credentials = {
            "type": "jwt",
            "token": token,
            "email": email,
            "base_url": base_url,
        }

        encrypted = fernet.encrypt(json.dumps(credentials).encode())
        self.credentials_file.write_bytes(encrypted)
        self.credentials_file.chmod(0o600)

    def clear_credentials(self):
        """Clear stored credentials."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
