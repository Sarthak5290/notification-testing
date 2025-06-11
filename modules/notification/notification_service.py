from typing import Dict, List, Optional

from modules.notification.errors import NotificationTemplateNotFoundError, NotificationValidationError
from modules.notification.internal.notification_reader import NotificationReader
from modules.notification.internal.notification_util import NotificationUtil
from modules.notification.internal.notification_writer import NotificationWriter
from modules.notification.types import (
    CreateNotificationParams,
    DeviceToken,
    Notification,
    NotificationSearchParams,
    NotificationStatus,
    NotificationTemplate,
    NotificationType,
)
from modules.logger.logger import Logger


class NotificationService:
    @staticmethod
    def create_notification(params: CreateNotificationParams) -> Notification:
        """Create a new notification"""
        return NotificationWriter.create_notification(params)

    @staticmethod
    def send_notification_to_account(
        account_id: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None
    ) -> Notification:
        """Send notification to all devices of an account"""
        # Get device tokens for the account
        device_tokens = NotificationReader.get_active_device_tokens_by_account_id(account_id)
        
        if not device_tokens:
            raise NotificationValidationError(f"No active device tokens found for account {account_id}")
        
        # Create notification record
        create_params = CreateNotificationParams(
            account_id=account_id,
            title=title,
            body=body,
            notification_type=NotificationType.PUSH,
            device_tokens=device_tokens,
            data=data,
            image_url=image_url
        )
        
        notification = NotificationWriter.create_notification(create_params)
        
        try:
            # TODO: Add FCM sending logic here when Firebase is configured
            Logger.info(message=f"Created notification {notification.id} for account {account_id}")
            
            # Mark as sent for now
            NotificationWriter.mark_notification_as_sent(notification.id)
            
            return notification
            
        except Exception as e:
            # Mark notification as failed
            NotificationWriter.mark_notification_as_failed(notification.id, str(e))
            raise

    @staticmethod
    def get_notification_by_id(notification_id: str) -> Notification:
        """Get notification by ID"""
        return NotificationReader.get_notification_by_id(notification_id)

    @staticmethod
    def get_notifications(params: NotificationSearchParams) -> List[Notification]:
        """Get notifications with filtering and pagination"""
        return NotificationReader.get_notifications(params)

    @staticmethod
    def get_notifications_for_account(
        account_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a specific account"""
        return NotificationReader.get_notifications_by_account_id(account_id, limit, offset)

    @staticmethod
    def mark_notification_as_sent(notification_id: str) -> Notification:
        """Mark notification as sent"""
        return NotificationWriter.mark_notification_as_sent(notification_id)

    @staticmethod
    def mark_notification_as_failed(notification_id: str, error_message: str) -> Notification:
        """Mark notification as failed"""
        return NotificationWriter.mark_notification_as_failed(notification_id, error_message)

    @staticmethod
    def mark_notification_as_delivered(notification_id: str) -> Notification:
        """Mark notification as delivered"""
        return NotificationWriter.mark_notification_as_delivered(notification_id)

    @staticmethod
    def mark_notification_as_clicked(notification_id: str) -> Notification:
        """Mark notification as clicked"""
        return NotificationWriter.mark_notification_as_clicked(notification_id)

    @staticmethod
    def register_device_token(account_id: str, token: str, platform: str) -> DeviceToken:
        """Register device token for an account"""
        # Validate token format
        NotificationUtil.validate_device_tokens([token])
        
        # Validate platform
        valid_platforms = ["ios", "android", "web"]
        if platform not in valid_platforms:
            raise NotificationValidationError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
        
        return NotificationWriter.register_device_token(account_id, token, platform)

    @staticmethod
    def deactivate_device_token(token: str) -> bool:
        """Deactivate a device token"""
        return NotificationWriter.deactivate_device_token(token)

    @staticmethod
    def get_device_tokens_for_account(account_id: str, platform: Optional[str] = None) -> List[DeviceToken]:
        """Get device tokens for an account"""
        return NotificationReader.get_device_tokens_by_account_id(account_id, platform)

    @staticmethod
    def create_notification_template(
        name: str,
        title_template: str,
        body_template: str,
        default_data: Optional[Dict] = None
    ) -> NotificationTemplate:
        """Create a new notification template"""
        return NotificationWriter.create_notification_template(name, title_template, body_template, default_data)

    @staticmethod
    def get_notification_template_by_id(template_id: str) -> NotificationTemplate:
        """Get notification template by ID"""
        return NotificationReader.get_template_by_id(template_id)

    @staticmethod
    def get_notification_template_by_name(name: str) -> NotificationTemplate:
        """Get notification template by name"""
        return NotificationReader.get_template_by_name(name)

    @staticmethod
    def get_all_notification_templates() -> List[NotificationTemplate]:
        """Get all notification templates"""
        return NotificationReader.get_all_templates()

    @staticmethod
    def update_notification_template(
        template_id: str,
        name: Optional[str] = None,
        title_template: Optional[str] = None,
        body_template: Optional[str] = None,
        default_data: Optional[Dict] = None
    ) -> NotificationTemplate:
        """Update notification template"""
        return NotificationWriter.update_notification_template(
            template_id, name, title_template, body_template, default_data
        )

    @staticmethod
    def delete_notification_template(template_id: str) -> bool:
        """Delete notification template"""
        return NotificationWriter.delete_notification_template(template_id)

    @staticmethod
    def get_notification_count_for_account(account_id: str) -> int:
        """Get total notification count for an account"""
        return NotificationReader.get_notification_count_by_account_id(account_id)

    @staticmethod
    def get_unread_notification_count_for_account(account_id: str) -> int:
        """Get unread notification count for an account"""
        return NotificationReader.get_unread_notification_count_by_account_id(account_id)

    @staticmethod
    def cleanup_old_notifications(days_old: int = 90) -> int:
        """Clean up old notifications"""
        deleted_count = NotificationWriter.cleanup_old_notifications(days_old)
        Logger.info(message=f"Cleaned up {deleted_count} old notifications")
        return deleted_count

    @staticmethod
    def send_bulk_notification(
        account_ids: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Notification]:
        """Send notification to multiple accounts"""
        results = {}
        
        for account_id in account_ids:
            try:
                notification = NotificationService.send_notification_to_account(
                    account_id=account_id,
                    title=title,
                    body=body,
                    data=data,
                    image_url=image_url
                )
                results[account_id] = notification
                
            except Exception as e:
                Logger.error(message=f"Failed to send notification to account {account_id}: {str(e)}")
                # Continue with other accounts
                continue
        
        return results
    