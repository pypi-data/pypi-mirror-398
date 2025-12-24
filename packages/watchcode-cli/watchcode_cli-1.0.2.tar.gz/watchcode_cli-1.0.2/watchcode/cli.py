"""WatchCode CLI - Send Claude Code notifications to your Apple Watch."""

import sys
import json
import click
from typing import Optional

from .config import Config
from .client import RelayClient
from .hooks import HooksInstaller


@click.group()
@click.version_option(package_name="watchcode-cli")
def main():
    """WatchCode CLI - Send Claude Code notifications to your Apple Watch."""
    pass


@main.command()
def setup():
    """Interactive setup - configure WatchCode with your setup code."""
    config = Config()

    click.echo("WatchCode Setup")
    click.echo("=" * 50)
    click.echo()
    click.echo("To get your setup code:")
    click.echo("1. Open WatchCode on your Apple Watch")
    click.echo("2. Go to Settings")
    click.echo("3. Your setup code will be displayed (format: XXXX-XXXX-XXXX)")
    click.echo()

    # Prompt for setup code
    while True:
        setup_code = click.prompt("Enter your setup code", type=str).strip()

        # Validate format
        if config.validate_token_format(setup_code):
            break
        else:
            click.echo("Invalid setup code format. Expected: XXXX-XXXX-XXXX (12 alphanumeric characters)")

    # Save auth token (without dashes)
    clean_token = setup_code.replace("-", "").upper()
    config.set_auth_token(clean_token)

    click.echo()
    click.echo(f"Setup code saved: {config.format_token_display(clean_token)}")
    click.echo()

    # Ask to install hooks
    if click.confirm("Install Claude Code hooks?", default=True):
        installer = HooksInstaller()
        result = installer.install_hooks()

        if result["installed"]:
            click.echo(f"Installed hooks: {', '.join(result['installed'])}")
        if result["skipped"]:
            click.echo(f"Already installed: {', '.join(result['skipped'])}")

        click.echo()
        click.echo("Hooks installed successfully!")
    else:
        click.echo("Skipped hook installation. Run 'watchcode install-hooks' later.")

    click.echo()

    # Send test notification
    if click.confirm("Send test notification?", default=True):
        try:
            client = RelayClient(config)
            response = client.send_test_notification()

            if response.get("success"):
                click.echo("Test notification sent successfully!")
                click.echo("Check your Apple Watch for the notification.")
            elif response.get("queued"):
                click.echo("Network error: Test notification queued for later delivery.")
            else:
                click.echo(f"Error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            click.echo(f"Error sending test notification: {str(e)}", err=True)

    click.echo()
    click.echo("Setup complete! Claude Code notifications will now be sent to your Watch.")


@main.command()
def install_hooks():
    """Install Claude Code hooks for WatchCode."""
    installer = HooksInstaller()

    # Show current status
    status = installer.get_hook_status()
    click.echo("Current hook status:")
    for hook_type, installed in status.items():
        status_text = "INSTALLED" if installed else "NOT INSTALLED"
        click.echo(f"  {hook_type}: {status_text}")

    click.echo()

    if all(status.values()):
        click.echo("All hooks are already installed.")
        return

    # Install hooks
    if click.confirm("Install WatchCode hooks?", default=True):
        result = installer.install_hooks()

        click.echo()
        if result["installed"]:
            click.echo(f"Installed: {', '.join(result['installed'])}")
        if result["skipped"]:
            click.echo(f"Already installed: {', '.join(result['skipped'])}")

        click.echo()
        click.echo("Hooks installed successfully!")
    else:
        click.echo("Installation cancelled.")


@main.command()
def uninstall_hooks():
    """Uninstall Claude Code hooks for WatchCode."""
    installer = HooksInstaller()

    if click.confirm("Remove all WatchCode hooks?", default=False):
        result = installer.uninstall_hooks()

        if result["removed"]:
            click.echo(f"Removed hooks: {', '.join(result['removed'])}")
            click.echo("Hooks uninstalled successfully!")
        else:
            click.echo("No WatchCode hooks found.")
    else:
        click.echo("Uninstall cancelled.")


@main.command()
def test():
    """Send a test notification to your Apple Watch."""
    config = Config()

    if not config.is_configured():
        click.echo("WatchCode not configured. Run 'watchcode setup' first.", err=True)
        sys.exit(1)

    try:
        client = RelayClient(config)
        click.echo("Sending test notification...")

        response = client.send_test_notification()

        if response.get("success"):
            click.echo("Test notification sent successfully!")
            click.echo("Check your Apple Watch for the notification.")
        elif response.get("queued"):
            click.echo("Network error: Test notification queued for later delivery.")
            click.echo("Run 'watchcode flush' when online to send queued notifications.")
        else:
            click.echo(f"Error: {response.get('error', 'Unknown error')}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option("--event", required=True, help="Event type (e.g., stop, permission_request)")
@click.option("--requires-action", is_flag=True, help="Notification requires user action")
def notify(event: str, requires_action: bool):
    """Send notification from Claude Code hook (reads hook data from stdin)."""
    config = Config()

    if not config.is_configured():
        # Silently fail if not configured (hooks shouldn't break Claude Code)
        sys.exit(0)

    try:
        # Read hook input from stdin (JSON from Claude Code)
        hook_data = {}
        if not sys.stdin.isatty():
            try:
                stdin_content = sys.stdin.read()
                if stdin_content.strip():
                    hook_data = json.loads(stdin_content)
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON

        # Extract data from hook payload
        message = hook_data.get("message", f"Claude Code: {event}")
        session_id = hook_data.get("session_id", "unknown")

        # Build metadata
        metadata = {
            "hook_type": event,
            "timestamp": hook_data.get("timestamp"),
        }

        # Add tool-specific metadata for pre_tool_use
        if event == "pre_tool_use":
            metadata["tool_name"] = hook_data.get("tool_name")
            metadata["tool_input"] = hook_data.get("tool_input")

        # Send notification
        client = RelayClient(config)
        response = client.send_notification(
            event=event,
            message=message,
            session_id=session_id,
            requires_action=requires_action,
            metadata=metadata
        )

        # Don't print anything on success (hooks should be silent)
        if not response.get("success") and not response.get("queued"):
            # Only log errors to stderr
            click.echo(f"WatchCode error: {response.get('error')}", err=True)

    except Exception as e:
        # Log errors but don't break Claude Code
        click.echo(f"WatchCode error: {str(e)}", err=True)


@main.command()
def status():
    """Show WatchCode configuration status."""
    config = Config()
    installer = HooksInstaller()

    click.echo("WatchCode Status")
    click.echo("=" * 50)

    # Configuration status
    if config.is_configured():
        token = config.get_auth_token()
        click.echo(f"Configuration: CONFIGURED")
        click.echo(f"Setup code: {config.format_token_display(token)}")
        click.echo(f"Token storage: {config.get_storage_location()}")
        click.echo(f"Relay URL: {config.get_relay_url()}")
    else:
        click.echo("Configuration: NOT CONFIGURED")
        click.echo("Run 'watchcode setup' to configure.")

    click.echo()

    # Queue status
    queue = config.load_queue()
    click.echo(f"Queued notifications: {len(queue)}")

    if queue:
        click.echo("Run 'watchcode flush' to send queued notifications.")

    click.echo()

    # Hook status
    hook_status = installer.get_hook_status()
    click.echo("Installed hooks:")
    for hook_type, installed in hook_status.items():
        status_icon = "✓" if installed else "✗"
        click.echo(f"  {status_icon} {hook_type}")

    if not all(hook_status.values()):
        click.echo()
        click.echo("Run 'watchcode install-hooks' to install missing hooks.")


@main.command()
def flush():
    """Send queued offline notifications."""
    config = Config()

    if not config.is_configured():
        click.echo("WatchCode not configured. Run 'watchcode setup' first.", err=True)
        sys.exit(1)

    queue = config.load_queue()
    if not queue:
        click.echo("No queued notifications.")
        return

    click.echo(f"Flushing {len(queue)} queued notification(s)...")

    try:
        client = RelayClient(config)
        result = client.flush_queue()

        click.echo()
        click.echo(f"Sent: {result['sent']}/{result['total']}")

        if result['failed'] > 0:
            click.echo(f"Failed: {result['failed']}/{result['total']}")
            click.echo("Failed notifications remain queued.")
        else:
            click.echo("All notifications sent successfully!")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
