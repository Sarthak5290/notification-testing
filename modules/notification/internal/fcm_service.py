import json
from typing import Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, messaging

from modules.config.config_service import ConfigService
from modules.logger.logger import Logger
from modules.notification.errors import FCMServiceError, NotificationValidationError
from modules.notification.types import (
    FCMResponse,
    NotificationData,
    SendNotificationParams,
    SendTopicNotificationParams,
    SubscribeToTopicParams,
    UnsubscribeFromTopicParams,
)


class FCMService:
    _app: Optional[firebase_admin.App] = None

    @staticmethod
    def _initialize_app() -> firebase_admin.App:
        """Initialize Firebase Admin SDK"""
        if FCMService._app is None:
            try:
                # Get the service account key from config
                service_account_key = ConfigService[str].get_value(key="fcm.service_account_key_path")
                
                # Initialize the Firebase Admin SDK
                cred = credentials.Certificate(service_account_key)
                FCMService._app = firebase_admin.initialize_app(cred)
                
                Logger.info(message="Firebase Admin SDK initialized successfully")
            except Exception as e:
                Logger.error(message=f"Failed to initialize Firebase Admin SDK: {str(e)}")
                raise FCMServiceError(f"Failed to initialize Firebase: {str(e)}")
        
        return FCMService._app

    @staticmethod
    def _validate_tokens(tokens: List[str]) -> None:
        """Validate device tokens"""
        if not tokens:
            raise NotificationValidationError("Device tokens list cannot be empty")
        
        for token in tokens:
            if not token or not isinstance(token, str):
                raise NotificationValidationError(f"Invalid device token: {token}")

    @staticmethod
    def _create_message(notification_data: NotificationData, token: str) -> messaging.Message:
        """Create FCM message object"""
        notification = messaging.Notification(
            title=notification_data.title,
            body=notification_data.body,
            image=notification_data.image_url
        )
        
        android_config = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                title=notification_data.title,
                body=notification_data.body,
                image=notification_data.image_url,
                sound="default",
                channel_id="default"
            )
        )
        
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(
                        title=notification_data.title,
                        body=notification_data.body
                    ),
                    sound="default",
                    badge=1
                )
            )
        )
        
        webpush_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=notification_data.title,
                body=notification_data.body,
                image=notification_data.image_url,
                icon="/icon-192x192.png"
            )
        )
        
        return messaging.Message(
            notification=notification,
            token=token,
            data=notification_data.data or {},
            android=android_config,
            apns=apns_config,
            webpush=webpush_config
        )

    @staticmethod
    def send_notification(params: SendNotificationParams) -> FCMResponse:
        """Send push notification to multiple devices"""
        try:
            FCMService._initialize_app()
            FCMService._validate_tokens(params.recipient_tokens)
            
            # Create messages for each token
            messages = []
            for token in params.recipient_tokens:
                message = FCMService._create_message(params.notification, token)
                messages.append(message)
            
            # Send multicast message
            response = messaging.send_all(messages)
            
            failed_tokens = []
            for i, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(params.recipient_tokens[i])
                    Logger.warn(
                        message=f"Failed to send notification to token {params.recipient_tokens[i]}: {resp.exception}"
                    )
            
            Logger.info(
                message=f"Notification sent. Success: {response.success_count}, Failed: {response.failure_count}"
            )
            
            return FCMResponse(
                success_count=response.success_count,
                failure_count=response.failure_count,
                failed_tokens=failed_tokens
            )
            
        except Exception as e:
            Logger.error(message=f"FCM send notification error: {str(e)}")
            raise FCMServiceError(str(e))

    @staticmethod
    def send_topic_notification(params: SendTopicNotificationParams) -> FCMResponse:
        """Send notification to a topic"""
        try:
            FCMService._initialize_app()
            
            if not params.topic:
                raise NotificationValidationError("Topic cannot be empty")
            
            notification = messaging.Notification(
                title=params.notification.title,
                body=params.notification.body,
                image=params.notification.image_url
            )
            
            message = messaging.Message(
                notification=notification,
                topic=params.topic,
                data=params.notification.data or {}
            )
            
            response = messaging.send(message)
            
            Logger.info(message=f"Topic notification sent successfully. Message ID: {response}")
            
            return FCMResponse(
                success_count=1,
                failure_count=0,
                failed_tokens=[],
                message_id=response
            )
            
        except Exception as e:
            Logger.error(message=f"FCM send topic notification error: {str(e)}")
            raise FCMServiceError(str(e))

    @staticmethod
    def subscribe_to_topic(params: SubscribeToTopicParams) -> FCMResponse:
        """Subscribe tokens to a topic"""
        try:
            FCMService._initialize_app()
            FCMService._validate_tokens(params.tokens)
            
            if not params.topic:
                raise NotificationValidationError("Topic cannot be empty")
            
            response = messaging.subscribe_to_topic(params.tokens, params.topic)
            
            Logger.info(
                message=f"Subscribed tokens to topic '{params.topic}'. Success: {response.success_count}, Failed: {response.failure_count}"
            )
            
            failed_tokens = []
            for i, error in enumerate(response.errors):
                if error:
                    failed_tokens.append(params.tokens[i])
                    Logger.warn(message=f"Failed to subscribe token {params.tokens[i]}: {error}")
            
            return FCMResponse(
                success_count=response.success_count,
                failure_count=response.failure_count,
                failed_tokens=failed_tokens
            )
            
        except Exception as e:
            Logger.error(message=f"FCM subscribe to topic error: {str(e)}")
            raise FCMServiceError(str(e))

    @staticmethod
    def unsubscribe_from_topic(params: UnsubscribeFromTopicParams) -> FCMResponse:
        """Unsubscribe tokens from a topic"""
        try:
            FCMService._initialize_app()
            FCMService._validate_tokens(params.tokens)
            
            if not params.topic:
                raise NotificationValidationError("Topic cannot be empty")
            
            response = messaging.unsubscribe_from_topic(params.tokens, params.topic)
            
            Logger.info(
                message=f"Unsubscribed tokens from topic '{params.topic}'. Success: {response.success_count}, Failed: {response.failure_count}"
            )
            
            failed_tokens = []
            for i, error in enumerate(response.errors):
                if error:
                    failed_tokens.append(params.tokens[i])
                    Logger.warn(message=f"Failed to unsubscribe token {params.tokens[i]}: {error}")
            
            return FCMResponse(
                success_count=response.success_count,
                failure_count=response.failure_count,
                failed_tokens=failed_tokens
            )
            
        except Exception as e:
            Logger.error(message=f"FCM unsubscribe from topic error: {str(e)}")
            raise FCMServiceError(str(e))

    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate a single device token"""
        try:
            FCMService._initialize_app()
            
            # Try to send a dry run message to validate the token
            message = messaging.Message(
                data={"test": "validation"},
                token=token
            )
            
            messaging.send(message, dry_run=True)
            return True
            
        except Exception as e:
            Logger.warn(message=f"Token validation failed for {token}: {str(e)}")
            return False