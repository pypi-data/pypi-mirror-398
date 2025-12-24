"""Claude Code hooks installer for WatchCode."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class HooksInstaller:
    """Manages installation of Claude Code hooks."""

    CLAUDE_SETTINGS_DIR = Path.home() / ".claude"
    CLAUDE_SETTINGS_FILE = CLAUDE_SETTINGS_DIR / "settings.json"

    # Hook definitions for WatchCode
    WATCHCODE_HOOKS = {
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event stop"
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event pre_tool_use"
                    }
                ]
            }
        ],
        "Notification": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event notification"
                    }
                ]
            }
        ],
        "PermissionRequest": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event permission_request --requires-action"
                    }
                ]
            }
        ],
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event session_start"
                    }
                ]
            }
        ],
        "SessionEnd": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "watchcode notify --event session_end"
                    }
                ]
            }
        ]
    }

    def __init__(self):
        """Initialize hooks installer."""
        self.settings_dir = self.CLAUDE_SETTINGS_DIR
        self.settings_file = self.CLAUDE_SETTINGS_FILE

    def ensure_settings_dir(self) -> None:
        """Ensure Claude settings directory exists."""
        self.settings_dir.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> Dict[str, Any]:
        """Load Claude Code settings.

        Returns:
            Settings dictionary.
        """
        if not self.settings_file.exists():
            return {}

        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save Claude Code settings.

        Args:
            settings: Settings dictionary to save.
        """
        self.ensure_settings_dir()
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

    def get_installed_hooks(self) -> Dict[str, List]:
        """Get currently installed hooks.

        Returns:
            Dictionary of hook types to hook lists.
        """
        settings = self.load_settings()
        return settings.get("hooks", {})

    def is_watchcode_hook(self, hook: Dict[str, Any]) -> bool:
        """Check if a hook is a WatchCode hook.

        Args:
            hook: Hook configuration to check.

        Returns:
            True if this is a WatchCode hook.
        """
        if "hooks" not in hook:
            return False

        for h in hook["hooks"]:
            if h.get("type") == "command":
                command = h.get("command", "")
                if "watchcode notify" in command:
                    return True
        return False

    def install_hooks(self, hook_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Install WatchCode hooks.

        Args:
            hook_types: List of hook types to install (None = all).

        Returns:
            Dictionary with installation results.
        """
        settings = self.load_settings()

        if "hooks" not in settings:
            settings["hooks"] = {}

        if hook_types is None:
            hook_types = list(self.WATCHCODE_HOOKS.keys())

        installed = []
        skipped = []

        for hook_type in hook_types:
            if hook_type not in self.WATCHCODE_HOOKS:
                skipped.append(hook_type)
                continue

            # Get existing hooks for this type
            existing_hooks = settings["hooks"].get(hook_type, [])

            # Check if WatchCode hook already exists
            has_watchcode_hook = any(
                self.is_watchcode_hook(hook) for hook in existing_hooks
            )

            if has_watchcode_hook:
                skipped.append(hook_type)
                continue

            # Add WatchCode hooks (preserving existing hooks)
            watchcode_hooks = self.WATCHCODE_HOOKS[hook_type]
            settings["hooks"][hook_type] = existing_hooks + watchcode_hooks
            installed.append(hook_type)

        self.save_settings(settings)

        return {
            "installed": installed,
            "skipped": skipped,
            "total": len(hook_types)
        }

    def uninstall_hooks(self) -> Dict[str, Any]:
        """Uninstall WatchCode hooks.

        Returns:
            Dictionary with uninstallation results.
        """
        settings = self.load_settings()

        if "hooks" not in settings:
            return {"removed": [], "total": 0}

        removed = []

        for hook_type, hooks in settings["hooks"].items():
            # Filter out WatchCode hooks
            filtered_hooks = [
                hook for hook in hooks
                if not self.is_watchcode_hook(hook)
            ]

            if len(filtered_hooks) != len(hooks):
                settings["hooks"][hook_type] = filtered_hooks
                removed.append(hook_type)

            # Clean up empty hook types
            if not filtered_hooks:
                del settings["hooks"][hook_type]

        self.save_settings(settings)

        return {
            "removed": removed,
            "total": len(removed)
        }

    def get_hook_status(self) -> Dict[str, bool]:
        """Get installation status for each hook type.

        Returns:
            Dictionary mapping hook type to installation status.
        """
        settings = self.load_settings()
        hooks = settings.get("hooks", {})

        status = {}
        for hook_type in self.WATCHCODE_HOOKS.keys():
            hook_list = hooks.get(hook_type, [])
            status[hook_type] = any(
                self.is_watchcode_hook(hook) for hook in hook_list
            )

        return status
