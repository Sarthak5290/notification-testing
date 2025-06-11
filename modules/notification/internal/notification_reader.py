from typing import List, Optional

from bson.objectid import ObjectId
from pymongo import DESCENDING

from modules.notification.errors import NotificationNotFoundError, NotificationTemplateNotFoundError
from modules.notification.internal.notification_util import NotificationUtil
from modules.notification.internal.store.notification_repository import (
    DeviceTokenRepository,
    NotificationRepository,
    NotificationTemplateRepository,
)
from modules.notification.types import (
    DeviceToken,
    Notification,
    NotificationSearchParams,
    NotificationTemplate,
)


class NotificationReader:
    @staticmethod
    def get_notification_by_id(notification_id: str) -> Notification:
        """Get notification by ID"""
        try:
            object_id = ObjectId(notification_id)
        except Exception:
            raise NotificationNotFoundError(notification_id)
        
        notification_bson = NotificationRepository.collection().find_one({"_id": object_id})
        
        if notification_bson is None:
            raise NotificationNotFoundError(notification_id)
        
        return NotificationUtil.convert_notification_bson_to_notification(notification_bson)

    @staticmethod
    def get_notifications(params: NotificationSearchParams) -> List[Notification]:
        """Get notifications with filtering and pagination"""
        query = {}
        
        if params.account_id:
            query["account_id"] = params.account_id
        
        if params.status:
            query["status"] = params.status.value
        
        if params.notification_type:
            query["notification_type"] = params.notification_type.value
        
        cursor = (
            NotificationRepository.collection()
            .find(query)
            .sort("created_at", DESCENDING)
            .skip(params.offset)
            .limit(params.limit)
        )
        
        notifications = []
        for notification_bson in cursor:
            notification = NotificationUtil.convert_notification_bson_to_notification(notification_bson)
            notifications.append(notification)
        
        return notifications

    @staticmethod
    def get_notifications_by_account_id(account_id: str, limit: int = 50, offset: int = 0) -> List[Notification]:
        """Get notifications for a specific account"""
        params = NotificationSearchParams(account_id=account_id, limit=limit, offset=offset)
        return NotificationReader.get_notifications(params)

    @staticmethod
    def get_pending_notifications() -> List[Notification]:
        """Get all pending notifications"""
        cursor = NotificationRepository.collection().find({"status": "PENDING"}).sort("created_at", 1)
        
        notifications = []
        for notification_bson in cursor:
            notification = NotificationUtil.convert_notification_bson_to_notification(notification_bson)
            notifications.append(notification)
        
        return notifications

    @staticmethod
    def get_scheduled_notifications() -> List[Notification]:
        """Get all scheduled notifications that are ready to be sent"""
        from datetime import datetime
        
        current_time = datetime.now()
        cursor = (
            NotificationRepository.collection()
            .find({
                "status": "PENDING",
                "scheduled_at": {"$lte": current_time}
            })
            .sort("scheduled_at", 1)
        )
        
        notifications = []
        for notification_bson in cursor:
            notification = NotificationUtil.convert_notification_bson_to_notification(notification_bson)
            notifications.append(notification)
        
        return notifications

    @staticmethod
    def get_template_by_id(template_id: str) -> NotificationTemplate:
        """Get notification template by ID"""
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise NotificationTemplateNotFoundError(template_id)
        
        template_bson = NotificationTemplateRepository.collection().find_one({"_id": object_id})
        
        if template_bson is None:
            raise NotificationTemplateNotFoundError(template_id)
        
        return NotificationUtil.convert_template_bson_to_template(template_bson)

    @staticmethod
    def get_template_by_name(name: str) -> NotificationTemplate:
        """Get notification template by name"""
        template_bson = NotificationTemplateRepository.collection().find_one({"name": name})
        
        if template_bson is None:
            raise NotificationTemplateNotFoundError(name)
        
        return NotificationUtil.convert_template_bson_to_template(template_bson)

    @staticmethod
    def get_all_templates() -> List[NotificationTemplate]:
        """Get all notification templates"""
        cursor = NotificationTemplateRepository.collection().find().sort("name", 1)
        
        templates = []
        for template_bson in cursor:
            template = NotificationUtil.convert_template_bson_to_template(template_bson)
            templates.append(template)
        
        return templates

    @staticmethod
    def get_device_tokens_by_account_id(account_id: str, platform: Optional[str] = None) -> List[DeviceToken]:
        """Get device tokens for an account"""
        query = {"account_id": account_id, "is_active": True}
        
        if platform:
            query["platform"] = platform
        
        cursor = DeviceTokenRepository.collection().find(query).sort("created_at", DESCENDING)
        
        device_tokens = []
        for token_bson in cursor:
            device_token = DeviceToken(
                token=token_bson["token"],
                platform=token_bson["platform"]
            )
            device_tokens.append(device_token)
        
        return device_tokens

    @staticmethod
    def get_active_device_tokens_by_account_id(account_id: str) -> List[str]:
        """Get active device token strings for an account"""
        cursor = DeviceTokenRepository.collection().find(
            {"account_id": account_id, "is_active": True}
        )
        
        return [token_doc["token"] for token_doc in cursor]

    @staticmethod
    def check_device_token_exists(token: str) -> bool:
        """Check if device token exists in database"""
        result = DeviceTokenRepository.collection().find_one({"token": token})
        return result is not None

    @staticmethod
    def get_notification_count_by_account_id(account_id: str) -> int:
        """Get total notification count for an account"""
        return NotificationRepository.collection().count_documents({"account_id": account_id})

    @staticmethod
    def get_unread_notification_count_by_account_id(account_id: str) -> int:
        """Get unread notification count for an account"""
        return NotificationRepository.collection().count_documents({
            "account_id": account_id,
            "status": {"$in": ["PENDING", "SENT", "DELIVERED"]}
        })