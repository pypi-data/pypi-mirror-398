"""Configuration management for WatchCode CLI."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import keyring
from keyring.errors import KeyringError


class Config:
    """Manages WatchCode configuration files."""

    DEFAULT_RELAY_URL = "https://watchcode-relay.sydneyworldbank.workers.dev"
    CONFIG_DIR = Path.home() / ".watchcode"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    QUEUE_FILE = CONFIG_DIR / "offline_queue.json"

    # Keychain service name for secure token storage
    KEYCHAIN_SERVICE = "com.watchcode.cli"
    KEYCHAIN_ACCOUNT = "auth_token"

    def __init__(self):
        """Initialize config manager."""
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.queue_file = self.QUEUE_FILE
        self._keychain_available = None

    def ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _is_keychain_available(self) -> bool:
        """Check if keychain is available on this system.

        Returns:
            True if keychain operations are supported.
        """
        if self._keychain_available is not None:
            return self._keychain_available

        try:
            # Try a simple keychain operation to test availability
            keyring.get_keyring()
            self._keychain_available = True
        except Exception:
            self._keychain_available = False

        return self._keychain_available

    def load(self) -> Dict[str, Any]:
        """Load configuration from file (non-sensitive settings only).

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
        """Save configuration to file (non-sensitive settings only).

        Args:
            config: Configuration dictionary to save.
        """
        self.ensure_config_dir()
        # Remove auth_token from config file (it goes to keychain)
        config_to_save = {k: v for k, v in config.items() if k != "auth_token"}
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=2)

    def _migrate_token_to_keychain(self) -> Optional[str]:
        """Migrate auth token from config.json to keychain.

        Returns:
            The migrated token, or None if no migration needed.
        """
        config = self.load()
        old_token = config.get("auth_token")

        if old_token and self._is_keychain_available():
            try:
                # Store in keychain
                keyring.set_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_ACCOUNT,
                    old_token
                )
                # Remove from config file
                if "auth_token" in config:
                    del config["auth_token"]
                    self.save(config)
                return old_token
            except KeyringError:
                # Keep in config file if keychain fails
                pass

        return old_token

    def get_auth_token(self) -> Optional[str]:
        """Get the auth token from secure storage (keychain).

        Falls back to config.json for backwards compatibility,
        and migrates to keychain on first access.

        Returns:
            Auth token string or None if not configured.
        """
        # Try keychain first
        if self._is_keychain_available():
            try:
                token = keyring.get_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_ACCOUNT
                )
                if token:
                    return token
            except KeyringError:
                pass

        # Check for token in config file (legacy or fallback)
        # and migrate to keychain if possible
        return self._migrate_token_to_keychain()

    def set_auth_token(self, token: str) -> None:
        """Set the auth token in secure storage (keychain).

        Args:
            token: The auth token to save (without dashes).
        """
        clean_token = token.replace("-", "").upper()

        # Store in keychain (preferred)
        if self._is_keychain_available():
            try:
                keyring.set_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_ACCOUNT,
                    clean_token
                )
            except KeyringError as e:
                # Fall back to config file
                config = self.load()
                config["auth_token"] = clean_token
                config["relay_url"] = config.get("relay_url", self.DEFAULT_RELAY_URL)
                config["version"] = 1
                # Note: save() strips auth_token, so we need direct write
                self.ensure_config_dir()
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                return
        else:
            # No keychain available, use config file
            config = self.load()
            config["auth_token"] = clean_token
            config["relay_url"] = config.get("relay_url", self.DEFAULT_RELAY_URL)
            config["version"] = 1
            self.ensure_config_dir()
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return

        # Update non-sensitive config
        config = self.load()
        config["relay_url"] = config.get("relay_url", self.DEFAULT_RELAY_URL)
        config["version"] = 1
        self.save(config)

    def delete_auth_token(self) -> bool:
        """Delete the auth token from secure storage.

        Returns:
            True if token was deleted successfully.
        """
        deleted = False

        # Delete from keychain
        if self._is_keychain_available():
            try:
                keyring.delete_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_ACCOUNT
                )
                deleted = True
            except KeyringError:
                pass

        # Also remove from config file if present
        config = self.load()
        if "auth_token" in config:
            del config["auth_token"]
            self.save(config)
            deleted = True

        return deleted

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

    def get_storage_location(self) -> str:
        """Get description of where auth token is stored.

        Returns:
            Human-readable storage location description.
        """
        if self._is_keychain_available():
            try:
                token = keyring.get_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_ACCOUNT
                )
                if token:
                    return "macOS Keychain"
            except KeyringError:
                pass

        config = self.load()
        if config.get("auth_token"):
            return f"config file ({self.config_file})"

        return "not configured"

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
