from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from modules.application.base_model import BaseModel
from modules.notification.types import NotificationPriority, NotificationStatus, NotificationType


@dataclass
class NotificationModel(BaseModel):
    account_id: str
    title: str
    body: str
    notification_type: NotificationType
    status: NotificationStatus
    priority: NotificationPriority
    device_tokens: List[str]
    id: Optional[ObjectId | str] = None
    topic: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    @classmethod
    def from_bson(cls, bson_data: dict) -> "NotificationModel":
        return cls(
            id=bson_data.get("_id"),
            account_id=bson_data.get("account_id", ""),
            title=bson_data.get("title", ""),
            body=bson_data.get("body", ""),
            notification_type=NotificationType(bson_data.get("notification_type", NotificationType.PUSH)),
            status=NotificationStatus(bson_data.get("status", NotificationStatus.PENDING)),
            priority=NotificationPriority(bson_data.get("priority", NotificationPriority.NORMAL)),
            device_tokens=bson_data.get("device_tokens", []),
            topic=bson_data.get("topic"),
            data=bson_data.get("data"),
            image_url=bson_data.get("image_url"),
            template_id=bson_data.get("template_id"),
            template_data=bson_data.get("template_data"),
            scheduled_at=bson_data.get("scheduled_at"),
            sent_at=bson_data.get("sent_at"),
            delivered_at=bson_data.get("delivered_at"),
            clicked_at=bson_data.get("clicked_at"),
            error_message=bson_data.get("error_message"),
            created_at=bson_data.get("created_at"),
            updated_at=bson_data.get("updated_at"),
        )

    @staticmethod
    def get_collection_name() -> str:
        return "notifications"


@dataclass
class NotificationTemplateModel(BaseModel):
    name: str
    title_template: str
    body_template: str
    id: Optional[ObjectId | str] = None
    default_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    @classmethod
    def from_bson(cls, bson_data: dict) -> "NotificationTemplateModel":
        return cls(
            id=bson_data.get("_id"),
            name=bson_data.get("name", ""),
            title_template=bson_data.get("title_template", ""),
            body_template=bson_data.get("body_template", ""),
            default_data=bson_data.get("default_data"),
            created_at=bson_data.get("created_at"),
            updated_at=bson_data.get("updated_at"),
        )

    @staticmethod
    def get_collection_name() -> str:
        return "notification_templates"


@dataclass
class DeviceTokenModel(BaseModel):
    account_id: str
    token: str
    platform: str
    is_active: bool = True
    id: Optional[ObjectId | str] = None
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    @classmethod
    def from_bson(cls, bson_data: dict) -> "DeviceTokenModel":
        return cls(
            id=bson_data.get("_id"),
            account_id=bson_data.get("account_id", ""),
            token=bson_data.get("token", ""),
            platform=bson_data.get("platform", ""),
            is_active=bson_data.get("is_active", True),
            created_at=bson_data.get("created_at"),
            updated_at=bson_data.get("updated_at"),
        )

    @staticmethod
    def get_collection_name() -> str:
        return "device_tokens"