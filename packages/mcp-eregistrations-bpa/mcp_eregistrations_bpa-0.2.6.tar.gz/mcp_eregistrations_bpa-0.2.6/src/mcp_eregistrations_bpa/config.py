"""Configuration management for MCP server.

Loads configuration from environment variables and YAML config file.
Environment variables take precedence over config file values.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator

from mcp_eregistrations_bpa.exceptions import ConfigurationError

# XDG-compliant config directory
CONFIG_DIR = Path.home() / ".config" / "mcp-eregistrations-bpa"
CONFIG_FILE = "config.yaml"


class Config(BaseModel):
    """MCP server configuration."""

    bpa_instance_url: str
    keycloak_client_id: str = "mcp-eregistrations-bpa"
    # Optional: explicit Keycloak URL (if different from BPA instance)
    keycloak_url: str | None = None
    # Optional: Keycloak realm name (derived from discovery if not specified)
    keycloak_realm: str | None = None

    @field_validator("bpa_instance_url", "keycloak_url")
    @classmethod
    def validate_https(cls, v: str | None) -> str | None:
        """Validate that URLs use HTTPS."""
        if v is None:
            return None
        if not v:
            raise ValueError("URL cannot be empty")
        if v.startswith("http://"):
            raise ValueError(
                "URL must use HTTPS: "
                "Security requires encrypted connections. "
                "Update URL to use https:// scheme."
            )
        if not v.startswith("https://"):
            raise ValueError("URL must start with https://")
        return v.rstrip("/")  # Normalize: remove trailing slash

    @property
    def oidc_discovery_url(self) -> str:
        """Get the OIDC discovery URL.

        If keycloak_url and keycloak_realm are provided, constructs
        the standard Keycloak realm discovery URL. Otherwise, falls
        back to BPA instance URL for discovery.

        Returns:
            The URL for .well-known/openid-configuration discovery.
        """
        if self.keycloak_url and self.keycloak_realm:
            # Standard Keycloak realm URL pattern
            return f"{self.keycloak_url}/realms/{self.keycloak_realm}"
        elif self.keycloak_url:
            # Keycloak URL provided but no realm - use as base
            return self.keycloak_url
        else:
            # Default: assume OIDC discovery at BPA URL
            return self.bpa_instance_url


def _load_config_from_env() -> str | None:
    """Load BPA instance URL from environment variable.

    Returns:
        The URL if set, None otherwise.
    """
    return os.environ.get("BPA_INSTANCE_URL")


def _load_config_from_file(config_path: Path | None = None) -> dict[str, Any] | None:
    """Load configuration from YAML config file.

    Args:
        config_path: Optional path to config file. Defaults to standard location.

    Returns:
        Dict with config values if found, None otherwise.

    Raises:
        ConfigurationError: If config file exists but is malformed.
    """
    if config_path is None:
        config_path = CONFIG_DIR / CONFIG_FILE

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Malformed YAML in config file {config_path}: {e}"
        ) from e

    return data if data.get("bpa_instance_url") else None


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from environment and/or config file.

    Priority: Environment variable > Config file

    Args:
        config_path: Optional path to config file for testing.

    Returns:
        Validated Config object.

    Raises:
        ConfigurationError: If no configuration is found or validation fails.
    """
    # Try environment variable first (highest priority)
    url = _load_config_from_env()

    # Load file config for additional values
    file_config = _load_config_from_file(config_path)

    # Fall back to config file URL if env var not set
    if url is None and file_config:
        url = file_config.get("bpa_instance_url")

    # No configuration found
    if url is None:
        raise ConfigurationError(
            "BPA instance URL not configured. "
            "Set BPA_INSTANCE_URL environment variable or create config at "
            f"{CONFIG_DIR / CONFIG_FILE}"
        )

    # Build config with optional fields from env vars and file
    config_kwargs: dict[str, Any] = {"bpa_instance_url": url}

    # Helper to get config value (env var takes precedence over file)
    def get_config_value(env_var: str, file_key: str) -> str | None:
        value = os.environ.get(env_var)
        if value:
            return value
        if file_config:
            file_value = file_config.get(file_key)
            if isinstance(file_value, str):
                return file_value
        return None

    # Load optional Keycloak configuration
    client_id = get_config_value("KEYCLOAK_CLIENT_ID", "keycloak_client_id")
    if client_id:
        config_kwargs["keycloak_client_id"] = client_id

    keycloak_url = get_config_value("KEYCLOAK_URL", "keycloak_url")
    if keycloak_url:
        config_kwargs["keycloak_url"] = keycloak_url

    keycloak_realm = get_config_value("KEYCLOAK_REALM", "keycloak_realm")
    if keycloak_realm:
        config_kwargs["keycloak_realm"] = keycloak_realm

    # Validate and return config
    try:
        return Config(**config_kwargs)
    except ValueError as e:
        raise ConfigurationError(str(e)) from e
