import re
from datetime import datetime
from string import Template
from typing import Any, Dict, List

from modules.notification.errors import NotificationTemplateNotFoundError, NotificationValidationError
from modules.notification.internal.store.notification_model import NotificationModel, NotificationTemplateModel
from modules.notification.types import Notification, NotificationTemplate


class NotificationUtil:
    @staticmethod
    def convert_notification_bson_to_notification(notification_bson: dict[str, Any]) -> Notification:
        """Convert BSON data to Notification object"""
        validated_notification_data = NotificationModel.from_bson(notification_bson)
        return Notification(
            id=str(validated_notification_data.id),
            account_id=validated_notification_data.account_id,
            title=validated_notification_data.title,
            body=validated_notification_data.body,
            notification_type=validated_notification_data.notification_type,
            status=validated_notification_data.status,
            priority=validated_notification_data.priority,
            device_tokens=validated_notification_data.device_tokens,
            topic=validated_notification_data.topic,
            data=validated_notification_data.data,
            image_url=validated_notification_data.image_url,
            template_id=validated_notification_data.template_id,
            template_data=validated_notification_data.template_data,
            scheduled_at=validated_notification_data.scheduled_at.isoformat() if validated_notification_data.scheduled_at else None,
            sent_at=validated_notification_data.sent_at.isoformat() if validated_notification_data.sent_at else None,
            delivered_at=validated_notification_data.delivered_at.isoformat() if validated_notification_data.delivered_at else None,
            clicked_at=validated_notification_data.clicked_at.isoformat() if validated_notification_data.clicked_at else None,
            error_message=validated_notification_data.error_message,
        )

    @staticmethod
    def convert_template_bson_to_template(template_bson: dict[str, Any]) -> NotificationTemplate:
        """Convert BSON data to NotificationTemplate object"""
        validated_template_data = NotificationTemplateModel.from_bson(template_bson)
        return NotificationTemplate(
            id=str(validated_template_data.id),
            name=validated_template_data.name,
            title_template=validated_template_data.title_template,
            body_template=validated_template_data.body_template,
            default_data=validated_template_data.default_data,
        )

    @staticmethod
    def render_template(template: str, data: Dict[str, Any]) -> str:
        """Render template with provided data using string interpolation"""
        try:
            template_obj = Template(template)
            return template_obj.safe_substitute(data)
        except Exception as e:
            raise NotificationValidationError(f"Template rendering failed: {str(e)}")

    @staticmethod
    def validate_device_tokens(tokens: List[str]) -> List[str]:
        """Validate and filter device tokens"""
        if not tokens:
            raise NotificationValidationError("Device tokens list cannot be empty")
        
        valid_tokens = []
        token_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
        for token in tokens:
            if not token or not isinstance(token, str):
                continue
            
            # Basic token format validation
            if len(token) < 10 or len(token) > 4096:
                continue
                
            # Allow alphanumeric, underscore, and hyphen characters
            if not token_pattern.match(token.replace(':', '').replace('.', '')):
                continue
                
            valid_tokens.append(token)
        
        if not valid_tokens:
            raise NotificationValidationError("No valid device tokens found")
        
        return valid_tokens

    @staticmethod
    def validate_notification_data(title: str, body: str) -> None:
        """Validate notification title and body"""
        if not title or not title.strip():
            raise NotificationValidationError("Notification title cannot be empty")
        
        if not body or not body.strip():
            raise NotificationValidationError("Notification body cannot be empty")
        
        if len(title) > 500:
            raise NotificationValidationError("Notification title too long (max 500 characters)")
        
        if len(body) > 4000:
            raise NotificationValidationError("Notification body too long (max 4000 characters)")

    @staticmethod
    def validate_topic_name(topic: str) -> None:
        """Validate FCM topic name"""
        if not topic or not topic.strip():
            raise NotificationValidationError("Topic name cannot be empty")
        
        # FCM topic name requirements
        topic_pattern = re.compile(r'^[a-zA-Z0-9-_.~%]+$')
        
        if not topic_pattern.match(topic):
            raise NotificationValidationError(
                "Invalid topic name. Must contain only alphanumeric characters, hyphens, underscores, dots, tildes, and percent signs"
            )
        
        if len(topic) > 900:
            raise NotificationValidationError("Topic name too long (max 900 characters)")

    @staticmethod
    def is_scheduled_notification(scheduled_at: str) -> bool:
        """Check if notification is scheduled for future"""
        if not scheduled_at:
            return False
        
        try:
            scheduled_time = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            return scheduled_time > datetime.now()
        except ValueError:
            return False

    @staticmethod
    def extract_template_variables(template: str) -> List[str]:
        """Extract variable names from template string"""
        # Get all identifiers used in the template
        pattern = re.compile(r'\$\{?([a-zA-Z_]\w*)\}?')
        matches = pattern.findall(template)
        return list(set(matches))

    @staticmethod
    def validate_template_data(template: str, data: Dict[str, Any]) -> None:
        """Validate that all required template variables are provided"""
        required_vars = NotificationUtil.extract_template_variables(template)
        missing_vars = [var for var in required_vars if var not in data]
        
        if missing_vars:
            raise NotificationValidationError(
                f"Missing template variables: {', '.join(missing_vars)}"
            )

    @staticmethod
    def sanitize_notification_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize notification data for security"""
        sanitized = {}
        
        for key, value in data.items():
            # Convert to string and limit length
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = str(value)[:1000]  # Limit to 1000 characters
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries (limited depth)
                sanitized[key] = NotificationUtil.sanitize_notification_data(value)
            elif isinstance(value, list):
                # Convert list items to strings
                sanitized[key] = [str(item)[:1000] for item in value[:10]]  # Limit to 10 items
        
        return sanitized

    @staticmethod
    def create_notification_tracking_data(notification_id: str, account_id: str) -> Dict[str, str]:
        """Create tracking data for analytics"""
        return {
            "notification_id": notification_id,
            "account_id": account_id,
            "timestamp": datetime.now().isoformat(),
            "source": "backend_notification_system"
        }