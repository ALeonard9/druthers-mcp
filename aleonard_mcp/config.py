"""Environment-driven configuration for the MCP server."""

import os
from dataclasses import dataclass


@dataclass
class Settings:  # pylint: disable=too-many-instance-attributes
    """Runtime configuration, populated from the environment."""

    api_base_url: str = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
    # Either a pre-issued token, or email+password to exchange for one.
    api_token: str | None = os.getenv('API_TOKEN')
    api_email: str | None = os.getenv('API_EMAIL')
    api_password: str | None = os.getenv('API_PASSWORD')
    request_timeout: float = float(os.getenv('API_TIMEOUT', '15'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    lz: str | None = os.getenv('LZ')
    env: str = os.getenv('ENV', 'local')


def get_settings() -> Settings:
    """Return a fresh Settings snapshot from the current environment."""
    return Settings()
