from datetime import datetime
from typing import Dict, List, Optional

from bson.objectid import ObjectId
from pymongo import ReturnDocument

from modules.notification.errors import NotificationNotFoundError, NotificationTemplateNotFoundError
from modules.notification.internal.notification_util import NotificationUtil
from modules.notification.internal.store.notification_model import (
    DeviceTokenModel,
    NotificationModel,
    NotificationTemplateModel,
)
from modules.notification.internal.store.notification_repository import (
    DeviceTokenRepository,
    NotificationRepository,
    NotificationTemplateRepository,
)
from modules.notification.types import (
    CreateNotificationParams,
    DeviceToken,
    Notification,
    NotificationStatus,
    NotificationTemplate,
)


class NotificationWriter:
    @staticmethod
    def create_notification(params: CreateNotificationParams) -> Notification:
        """Create a new notification"""
        # Validate notification data
        NotificationUtil.validate_notification_data(params.title, params.body)
        
        # Validate and sanitize device tokens
        valid_tokens = NotificationUtil.validate_device_tokens(params.device_tokens)
        
        # Validate topic if provided
        if params.topic:
            NotificationUtil.validate_topic_name(params.topic)
        
        # Parse scheduled time if provided
        scheduled_at = None
        if params.scheduled_at:
            try:
                scheduled_at = datetime.fromisoformat(params.scheduled_at.replace('Z', '+00:00'))
            except ValueError:
                scheduled_at = None
        
        # Sanitize custom data
        sanitized_data = None
        if params.data:
            sanitized_data = NotificationUtil.sanitize_notification_data(params.data)
        
        # Create notification model
        notification_bson = NotificationModel(
            id=None,
            account_id=params.account_id,
            title=params.title,
            body=params.body,
            notification_type=params.notification_type,
            status=NotificationStatus.PENDING,
            priority=params.priority,
            device_tokens=valid_tokens,
            topic=params.topic,
            data=sanitized_data,
            image_url=params.image_url,
            template_id=params.template_id,
            template_data=params.template_data,
            scheduled_at=scheduled_at,
        ).to_bson()
        
        # Insert into database
        result = NotificationRepository.collection().insert_one(notification_bson)
        
        # Retrieve the created notification
        created_notification_bson = NotificationRepository.collection().find_one({"_id": result.inserted_id})
        
        return NotificationUtil.convert_notification_bson_to_notification(created_notification_bson)

    @staticmethod
    def update_notification_status(
        notification_id: str, 
        status: NotificationStatus, 
        error_message: Optional[str] = None
    ) -> Notification:
        """Update notification status"""
        try:
            object_id = ObjectId(notification_id)
        except Exception:
            raise NotificationNotFoundError(notification_id)
        
        update_data = {
            "status": status.value,
            "updated_at": datetime.now()
        }
        
        # Set timestamp based on status
        if status == NotificationStatus.SENT:
            update_data["sent_at"] = datetime.now()
        elif status == NotificationStatus.DELIVERED:
            update_data["delivered_at"] = datetime.now()
        elif status == NotificationStatus.CLICKED:
            update_data["clicked_at"] = datetime.now()
        
        if error_message:
            update_data["error_message"] = error_message
        
        updated_notification = NotificationRepository.collection().find_one_and_update(
            {"_id": object_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        
        if updated_notification is None:
            raise NotificationNotFoundError(notification_id)
        
        return NotificationUtil.convert_notification_bson_to_notification(updated_notification)

    @staticmethod
    def mark_notification_as_sent(notification_id: str) -> Notification:
        """Mark notification as sent"""
        return NotificationWriter.update_notification_status(notification_id, NotificationStatus.SENT)

    @staticmethod
    def mark_notification_as_failed(notification_id: str, error_message: str) -> Notification:
        """Mark notification as failed"""
        return NotificationWriter.update_notification_status(
            notification_id, NotificationStatus.FAILED, error_message
        )

    @staticmethod
    def mark_notification_as_delivered(notification_id: str) -> Notification:
        """Mark notification as delivered"""
        return NotificationWriter.update_notification_status(notification_id, NotificationStatus.DELIVERED)

    @staticmethod
    def mark_notification_as_clicked(notification_id: str) -> Notification:
        """Mark notification as clicked"""
        return NotificationWriter.update_notification_status(notification_id, NotificationStatus.CLICKED)

    @staticmethod
    def create_notification_template(
        name: str,
        title_template: str,
        body_template: str,
        default_data: Optional[Dict] = None
    ) -> NotificationTemplate:
        """Create a new notification template"""
        # Validate template data
        NotificationUtil.validate_notification_data(title_template, body_template)
        
        template_bson = NotificationTemplateModel(
            id=None,
            name=name,
            title_template=title_template,
            body_template=body_template,
            default_data=default_data
        ).to_bson()
        
        result = NotificationTemplateRepository.collection().insert_one(template_bson)
        created_template_bson = NotificationTemplateRepository.collection().find_one({"_id": result.inserted_id})
        
        return NotificationUtil.convert_template_bson_to_template(created_template_bson)

    @staticmethod
    def update_notification_template(
        template_id: str,
        name: Optional[str] = None,
        title_template: Optional[str] = None,
        body_template: Optional[str] = None,
        default_data: Optional[Dict] = None
    ) -> NotificationTemplate:
        """Update notification template"""
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise NotificationTemplateNotFoundError(template_id)
        
        update_data = {"updated_at": datetime.now()}
        
        if name is not None:
            update_data["name"] = name
        if title_template is not None:
            update_data["title_template"] = title_template
        if body_template is not None:
            update_data["body_template"] = body_template
        if default_data is not None:
            update_data["default_data"] = default_data
        
        updated_template = NotificationTemplateRepository.collection().find_one_and_update(
            {"_id": object_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        
        if updated_template is None:
            raise NotificationTemplateNotFoundError(template_id)
        
        return NotificationUtil.convert_template_bson_to_template(updated_template)

    @staticmethod
    def delete_notification_template(template_id: str) -> bool:
        """Delete notification template"""
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise NotificationTemplateNotFoundError(template_id)
        
        result = NotificationTemplateRepository.collection().delete_one({"_id": object_id})
        return result.deleted_count > 0

    @staticmethod
    def register_device_token(account_id: str, token: str, platform: str) -> DeviceToken:
        """Register or update device token for an account"""
        # Use upsert to either update existing or insert new
        DeviceTokenRepository.collection().update_one(
            {"token": token},  # Find by token
            {
                "$set": {
                    "account_id": account_id,
                    "platform": platform,
                    "is_active": True,
                    "updated_at": datetime.now()
                },
                "$setOnInsert": {
                    "created_at": datetime.now()
                }
            },
            upsert=True  # Create if doesn't exist, update if exists
        )
        
        return DeviceToken(token=token, platform=platform)

    @staticmethod
    def deactivate_device_token(token: str) -> bool:
        """Deactivate a device token"""
        result = DeviceTokenRepository.collection().update_many(
            {"token": token},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    @staticmethod
    def deactivate_device_tokens_for_account(account_id: str, platform: Optional[str] = None) -> int:
        """Deactivate all device tokens for an account"""
        query = {"account_id": account_id, "is_active": True}
        if platform:
            query["platform"] = platform
        
        result = DeviceTokenRepository.collection().update_many(
            query,
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        return result.modified_count

    @staticmethod
    def cleanup_old_notifications(days_old: int = 90) -> int:
        """Clean up old notifications"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        result = NotificationRepository.collection().delete_many({
            "created_at": {"$lt": cutoff_date},
            "status": {"$in": ["SENT", "DELIVERED", "CLICKED", "FAILED"]}
        })
        return result.deleted_count