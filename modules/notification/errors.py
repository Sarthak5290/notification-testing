from modules.application.errors import AppError
from modules.notification.types import NotificationErrorCode


class NotificationNotFoundError(AppError):
    def __init__(self, notification_id: str) -> None:
        super().__init__(
            code=NotificationErrorCode.NOTIFICATION_NOT_FOUND,
            http_status_code=404,
            message=f"Notification with id '{notification_id}' not found.",
        )


class InvalidDeviceTokenError(AppError):
    def __init__(self, token: str) -> None:
        super().__init__(
            code=NotificationErrorCode.INVALID_DEVICE_TOKEN,
            http_status_code=400,
            message=f"Invalid device token: '{token}'",
        )


class NotificationTemplateNotFoundError(AppError):
    def __init__(self, template_id: str) -> None:
        super().__init__(
            code=NotificationErrorCode.TEMPLATE_NOT_FOUND,
            http_status_code=404,
            message=f"Notification template with id '{template_id}' not found.",
        )


class FCMServiceError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code=NotificationErrorCode.FCM_SERVICE_ERROR,
            http_status_code=503,
            message=f"FCM service error: {message}",
        )


class NotificationValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code=NotificationErrorCode.VALIDATION_ERROR,
            http_status_code=400,
            message=message,
        )