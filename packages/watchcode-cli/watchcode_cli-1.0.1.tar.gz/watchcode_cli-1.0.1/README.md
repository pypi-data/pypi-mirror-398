# WatchCode CLI

Send Claude Code notifications directly to your Apple Watch.

## What is WatchCode?

WatchCode lets you receive notifications from [Claude Code](https://claude.com/claude-code) on your Apple Watch - no iPhone required. Get instant alerts for permission requests, tool usage, errors, and more.

## Installation

```bash
pip install watchcode-cli
```

## Quick Start

1. **Install the WatchCode app on your Apple Watch** (available on the App Store)

2. **Get your setup code from the Watch app:**
   - Open WatchCode on your Watch
   - Go to Settings
   - Note your setup code (format: XXXX-XXXX-XXXX)

3. **Configure the CLI:**
   ```bash
   watchcode setup
   ```
   This will:
   - Prompt for your setup code
   - Install Claude Code hooks automatically
   - Send a test notification to verify setup

4. **Done!** Claude Code will now send notifications to your Watch.

## Commands

### `watchcode setup`
Interactive setup wizard. Configures WatchCode with your setup code, installs hooks, and sends a test notification.

```bash
watchcode setup
```

### `watchcode test`
Send a test notification to your Watch.

```bash
watchcode test
```

### `watchcode status`
Show configuration and hook status.

```bash
watchcode status
```

### `watchcode install-hooks`
Install Claude Code hooks for WatchCode (normally done during setup).

```bash
watchcode install-hooks
```

### `watchcode uninstall-hooks`
Remove WatchCode hooks from Claude Code.

```bash
watchcode uninstall-hooks
```

### `watchcode flush`
Manually send queued offline notifications.

```bash
watchcode flush
```

### `watchcode notify`
Send notification from Claude Code hook (used internally by hooks).

```bash
# Examples (normally called by Claude Code hooks)
watchcode notify --event stop
watchcode notify --event permission_request --requires-action
watchcode notify --event notification
```

## How It Works

WatchCode uses Claude Code's hook system to send notifications:

1. **Hook triggers** - Claude Code calls WatchCode hooks on events (permission requests, tool usage, etc.)
2. **Relay server** - WatchCode CLI sends notification to Cloudflare Worker relay
3. **APNs delivery** - Relay forwards to Apple Push Notification service
4. **Watch receives** - Your Apple Watch receives the notification instantly

## Supported Events

WatchCode supports all Claude Code hook types:

- **Stop** - When Claude Code stops execution
- **PreToolUse** - Before using a tool (optional confirmation)
- **PermissionRequest** - When Claude needs permission (requires action)
- **Notification** - General notifications
- **SessionStart** / **SessionEnd** - Session lifecycle events

## Offline Queue

If the relay server is unreachable, notifications are queued locally and automatically sent when connectivity is restored.

View queued notifications:
```bash
watchcode status
```

Manually flush queue:
```bash
watchcode flush
```

## Configuration

WatchCode stores configuration in `~/.watchcode/`:

- `config.json` - Setup code and relay URL
- `offline_queue.json` - Queued notifications (when offline)

Claude Code hooks are installed in `~/.claude/settings.json`.

## Privacy & Security

- **No data collection** - WatchCode only sends what's needed for notifications
- **Secure relay** - End-to-end encrypted via APNs
- **Auth tokens** - Setup codes authenticate your device (no passwords)
- **Open source** - Full source code available on GitHub

## Troubleshooting

### Notifications not appearing on Watch

1. Check configuration: `watchcode status`
2. Verify hooks are installed: `watchcode install-hooks`
3. Test notification: `watchcode test`
4. Check Watch is connected and WatchCode app is installed

### Network errors

If you see "Network error: Notification queued", the relay server is unreachable. Notifications will be queued and sent automatically when online. Run `watchcode flush` to retry manually.

### Invalid setup code

Setup codes are 12 alphanumeric characters (format: XXXX-XXXX-XXXX). Get your code from the WatchCode app on your Watch (Settings screen).

## Links

- **GitHub**: https://github.com/egor-gm/WatchCode
- **Issues**: https://github.com/egor-gm/WatchCode/issues
- **Watch App**: Available on the App Store

## License

MIT License - see LICENSE file for details.
