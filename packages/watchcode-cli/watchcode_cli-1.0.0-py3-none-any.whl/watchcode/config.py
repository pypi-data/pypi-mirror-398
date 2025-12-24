"""Configuration management for WatchCode CLI."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manages WatchCode configuration files."""

    DEFAULT_RELAY_URL = "https://watchcode-relay.sydneyworldbank.workers.dev"
    CONFIG_DIR = Path.home() / ".watchcode"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    QUEUE_FILE = CONFIG_DIR / "offline_queue.json"

    def __init__(self):
        """Initialize config manager."""
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.queue_file = self.QUEUE_FILE

    def ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Dictionary containing configuration.
        """
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.

        Args:
            config: Configuration dictionary to save.
        """
        self.ensure_config_dir()
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_auth_token(self) -> Optional[str]:
        """Get the auth token from config.

        Returns:
            Auth token string or None if not configured.
        """
        config = self.load()
        return config.get("auth_token")

    def set_auth_token(self, token: str) -> None:
        """Set the auth token in config.

        Args:
            token: The auth token to save (without dashes).
        """
        config = self.load()
        config["auth_token"] = token.replace("-", "").upper()
        config["relay_url"] = config.get("relay_url", self.DEFAULT_RELAY_URL)
        config["version"] = 1
        self.save(config)

    def get_relay_url(self) -> str:
        """Get the relay URL from config.

        Returns:
            Relay URL string (defaults to production relay).
        """
        config = self.load()
        return config.get("relay_url", self.DEFAULT_RELAY_URL)

    def is_configured(self) -> bool:
        """Check if WatchCode is configured.

        Returns:
            True if auth token is configured.
        """
        return self.get_auth_token() is not None

    def load_queue(self) -> list:
        """Load offline notification queue.

        Returns:
            List of queued notifications.
        """
        if not self.queue_file.exists():
            return []

        try:
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_queue(self, queue: list) -> None:
        """Save offline notification queue.

        Args:
            queue: List of notifications to queue.
        """
        self.ensure_config_dir()
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def add_to_queue(self, notification: Dict[str, Any]) -> None:
        """Add a notification to the offline queue.

        Args:
            notification: Notification data to queue.
        """
        queue = self.load_queue()
        queue.append(notification)
        self.save_queue(queue)

    def clear_queue(self) -> None:
        """Clear the offline queue."""
        self.save_queue([])

    def format_token_display(self, token: str) -> str:
        """Format token for display with dashes (XXXX-XXXX-XXXX).

        Args:
            token: Raw token string (12 chars).

        Returns:
            Formatted token with dashes.
        """
        # Remove any existing dashes
        token = token.replace("-", "")
        # Add dashes every 4 characters
        if len(token) == 12:
            return f"{token[0:4]}-{token[4:8]}-{token[8:12]}"
        return token

    def validate_token_format(self, token: str) -> bool:
        """Validate token format.

        Args:
            token: Token to validate.

        Returns:
            True if token format is valid.
        """
        # Remove dashes
        clean_token = token.replace("-", "")
        # Check: 12 alphanumeric characters
        return len(clean_token) == 12 and clean_token.isalnum()
