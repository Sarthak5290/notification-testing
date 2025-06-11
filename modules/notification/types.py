from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class DeviceToken:
    token: str
    platform: str  # 'ios' | 'android' | 'web'


@dataclass(frozen=True)
class NotificationData:
    title: str
    body: str
    image_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SendNotificationParams:
    recipient_tokens: List[str]
    notification: NotificationData
    topic: Optional[str] = None


@dataclass(frozen=True)
class SendTopicNotificationParams:
    topic: str
    notification: NotificationData


@dataclass(frozen=True)
class SubscribeToTopicParams:
    tokens: List[str]
    topic: str


@dataclass(frozen=True)
class UnsubscribeFromTopicParams:
    tokens: List[str]
    topic: str


@dataclass(frozen=True)
class NotificationTemplate:
    id: str
    name: str
    title_template: str
    body_template: str
    default_data: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SendTemplatedNotificationParams:
    recipient_tokens: List[str]
    template_id: str
    template_data: Dict[str, Any]
    topic: Optional[str] = None


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"
    CLICKED = "CLICKED"


class NotificationType(StrEnum):
    PUSH = "PUSH"
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"


class NotificationPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


@dataclass(frozen=True)
class Notification:
    id: str
    account_id: str
    title: str
    body: str
    notification_type: NotificationType
    status: NotificationStatus
    priority: NotificationPriority
    device_tokens: List[str]
    topic: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    clicked_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class CreateNotificationParams:
    account_id: str
    title: str
    body: str
    notification_type: NotificationType
    device_tokens: List[str]
    priority: NotificationPriority = NotificationPriority.NORMAL
    topic: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[str] = None


@dataclass(frozen=True)
class NotificationSearchParams:
    account_id: Optional[str] = None
    status: Optional[NotificationStatus] = None
    notification_type: Optional[NotificationType] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class NotificationErrorCode:
    NOTIFICATION_NOT_FOUND = "NOTIFICATION_ERR_01"
    INVALID_DEVICE_TOKEN = "NOTIFICATION_ERR_02"
    TEMPLATE_NOT_FOUND = "NOTIFICATION_ERR_03"
    FCM_SERVICE_ERROR = "NOTIFICATION_ERR_04"
    VALIDATION_ERROR = "NOTIFICATION_ERR_05"


@dataclass(frozen=True)
class ValidationFailure:
    field: str
    message: str


@dataclass(frozen=True)
class FCMResponse:
    success_count: int
    failure_count: int
    failed_tokens: List[str]
    message_id: Optional[str] = None