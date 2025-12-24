"""HTTP client for WatchCode relay server with offline queue support."""

import httpx
from typing import Dict, Any, Optional
from .config import Config


class RelayClient:
    """Client for communicating with the WatchCode relay server."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize relay client.

        Args:
            config: Configuration manager instance (creates new one if not provided).
        """
        self.config = config or Config()
        self.timeout = 10.0  # 10 second timeout

    def send_notification(
        self,
        event: str,
        message: str,
        session_id: str,
        requires_action: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        retry_offline: bool = True
    ) -> Dict[str, Any]:
        """Send notification to relay server.

        Args:
            event: Event type (e.g., 'stop', 'permission_request').
            message: Notification message.
            session_id: Claude Code session ID.
            requires_action: Whether notification requires user action.
            metadata: Additional metadata for the notification.
            retry_offline: Whether to queue notification if offline.

        Returns:
            Response dictionary from server.

        Raises:
            ValueError: If auth token not configured.
            httpx.HTTPStatusError: If server returns error status.
        """
        auth_token = self.config.get_auth_token()
        if not auth_token:
            raise ValueError("WatchCode not configured. Run 'watchcode setup' first.")

        relay_url = self.config.get_relay_url()
        payload = {
            "auth_token": auth_token,
            "event": event,
            "message": message,
            "session_id": session_id,
            "requires_action": requires_action,
            "metadata": metadata or {}
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{relay_url}/notify",
                    json=payload
                )
                response.raise_for_status()
                return response.json()

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            # Network error - queue if retry_offline enabled
            if retry_offline:
                self.config.add_to_queue(payload)
                return {
                    "success": False,
                    "queued": True,
                    "error": f"Network error: {str(e)}. Notification queued."
                }
            raise

        except httpx.HTTPStatusError as e:
            # HTTP error - don't queue, just raise
            error_data = {}
            try:
                error_data = e.response.json()
            except Exception:
                pass
            raise ValueError(
                f"Relay server error ({e.response.status_code}): "
                f"{error_data.get('error', str(e))}"
            )

    def flush_queue(self) -> Dict[str, Any]:
        """Flush offline notification queue.

        Returns:
            Dictionary with flush results.
        """
        queue = self.config.load_queue()
        if not queue:
            return {"sent": 0, "failed": 0, "total": 0}

        sent = 0
        failed = 0
        failed_items = []

        for notification in queue:
            try:
                # Extract fields from queued notification
                self.send_notification(
                    event=notification["event"],
                    message=notification["message"],
                    session_id=notification["session_id"],
                    requires_action=notification.get("requires_action", False),
                    metadata=notification.get("metadata"),
                    retry_offline=False  # Don't re-queue
                )
                sent += 1
            except Exception as e:
                failed += 1
                failed_items.append(notification)

        # Keep only failed items in queue
        self.config.save_queue(failed_items)

        return {
            "sent": sent,
            "failed": failed,
            "total": len(queue)
        }

    def test_connection(self) -> bool:
        """Test connection to relay server.

        Returns:
            True if server is reachable.
        """
        relay_url = self.config.get_relay_url()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{relay_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    def send_test_notification(self) -> Dict[str, Any]:
        """Send a test notification.

        Returns:
            Response from server.
        """
        import time
        return self.send_notification(
            event="notification",
            message="Test notification from WatchCode CLI",
            session_id=f"test-{int(time.time())}",
            requires_action=False,
            metadata={"source": "watchcode-cli-test"}
        )
