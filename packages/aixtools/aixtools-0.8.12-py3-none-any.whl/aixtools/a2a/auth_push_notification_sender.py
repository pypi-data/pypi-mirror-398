"""Custom push notification sender that includes authentication headers."""

import logging

from a2a.server.tasks import BasePushNotificationSender
from a2a.types import PushNotificationConfig, Task

from aixtools.context import auth_token_var

logger = logging.getLogger(__name__)


class AuthenticatedPushNotificationSender(BasePushNotificationSender):  # pylint: disable=too-few-public-methods
    """
    Extended push notification sender that includes the Bearer token
    from the original request when sending notifications back to the client.

    Inherits from BasePushNotificationSender and only overrides the
    _dispatch_notification method to add authentication headers.
    """

    async def _dispatch_notification(self, task: Task, push_info: PushNotificationConfig) -> bool:
        """
        Dispatch a push notification with authentication headers.

        Args:
            task: The task object to send
            push_info: Push notification configuration

        Returns:
            True if notification was sent successfully, False otherwise
        """
        url = push_info.url
        try:
            headers = {}

            if push_info.token:
                headers["X-A2A-Notification-Token"] = push_info.token

            auth_token = auth_token_var.get()
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                logger.debug("Adding Authorization header to push notification for task %s", task.id)
            else:
                logger.warning(
                    "No auth token found in context for task %s. "
                    "Push notification may fail if endpoint requires authentication.",
                    task.id,
                )

            response = await self._client.post(
                url,
                json=task.model_dump(mode="json", exclude_none=True),
                headers=headers,
            )
            response.raise_for_status()
            logger.info("Push-notification sent for task_id=%s to URL: %s", task.id, url)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(
                "Error sending push-notification for task_id=%s to URL: %s.",
                task.id,
                url,
            )
            return False
        return True
