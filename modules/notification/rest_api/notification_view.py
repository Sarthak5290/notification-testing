from dataclasses import asdict
from typing import Dict, List

from flask import jsonify, request
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from modules.authentication.rest_api.access_auth_middleware import access_auth_middleware
from modules.notification.notification_service import NotificationService
from modules.notification.types import (
    CreateNotificationParams,
    NotificationData,
    NotificationPriority,
    NotificationSearchParams,
    NotificationStatus,
    NotificationType,
    SendNotificationParams,
    SendTopicNotificationParams,
    SubscribeToTopicParams,
    UnsubscribeFromTopicParams,
)


class NotificationView(MethodView):
    @access_auth_middleware
    def post(self) -> ResponseReturnValue:
        """Create and send notification"""
        request_data = request.get_json()
        account_id = getattr(request, 'account_id')
        
        # Extract notification parameters
        title = request_data.get('title')
        body = request_data.get('body')
        device_tokens = request_data.get('device_tokens', [])
        notification_type = NotificationType(request_data.get('notification_type', 'PUSH'))
        priority = NotificationPriority(request_data.get('priority', 'NORMAL'))
        topic = request_data.get('topic')
        data = request_data.get('data')
        image_url = request_data.get('image_url')
        template_id = request_data.get('template_id')
        template_data = request_data.get('template_data')
        scheduled_at = request_data.get('scheduled_at')
        
        # Create notification
        create_params = CreateNotificationParams(
            account_id=account_id,
            title=title,
            body=body,
            notification_type=notification_type,
            device_tokens=device_tokens,
            priority=priority,
            topic=topic,
            data=data,
            image_url=image_url,
            template_id=template_id,
            template_data=template_data,
            scheduled_at=scheduled_at
        )
        
        notification = NotificationService.create_notification(create_params)
        
        # If not scheduled, send immediately
        if not scheduled_at:
            try:
                if topic:
                    # Send to topic
                    notification_data = NotificationData(
                        title=title,
                        body=body,
                        image_url=image_url,
                        data=data
                    )
                    send_params = SendTopicNotificationParams(
                        topic=topic,
                        notification=notification_data
                    )
                    NotificationService.send_topic_notification(send_params)
                else:
                    # Send to devices
                    notification_data = NotificationData(
                        title=title,
                        body=body,
                        image_url=image_url,
                        data=data
                    )
                    send_params = SendNotificationParams(
                        recipient_tokens=device_tokens,
                        notification=notification_data
                    )
                    NotificationService.send_notification(send_params)
                
                # Update status to sent
                notification = NotificationService.mark_notification_as_delivered(notification.id)
                
            except Exception as e:
                # Keep the notification but mark as failed
                notification = NotificationService.mark_notification_as_failed(notification.id, str(e))
        
        notification_dict = asdict(notification)
        return jsonify(notification_dict), 201

    @access_auth_middleware
    def get(self) -> ResponseReturnValue:
        """Get notifications for the authenticated user"""
        account_id = getattr(request, 'account_id')
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')
        notification_type = request.args.get('notification_type')
        
        # Create search parameters
        search_params = NotificationSearchParams(
            account_id=account_id,
            status=NotificationStatus(status) if status else None,
            notification_type=NotificationType(notification_type) if notification_type else None,
            limit=limit,
            offset=offset
        )
        
        notifications = NotificationService.get_notifications(search_params)
        notifications_dict = [asdict(notification) for notification in notifications]
        
        return jsonify({
            'notifications': notifications_dict,
            'count': len(notifications_dict),
            'limit': limit,
            'offset': offset
        }), 200


class NotificationDetailView(MethodView):
    @access_auth_middleware
    def get(self, notification_id: str) -> ResponseReturnValue:
        """Get specific notification"""
        notification = NotificationService.get_notification_by_id(notification_id)
        notification_dict = asdict(notification)
        return jsonify(notification_dict), 200

    @access_auth_middleware
    def patch(self, notification_id: str) -> ResponseReturnValue:
        """Update notification status (delivered/clicked)"""
        request_data = request.get_json()
        action = request_data.get('action')
        
        if action == 'delivered':
            notification = NotificationService.mark_notification_as_delivered(notification_id)
        elif action == 'clicked':
            notification = NotificationService.mark_notification_as_clicked(notification_id)
        else:
            return jsonify({'error': 'Invalid action. Use "delivered" or "clicked"'}), 400
        
        notification_dict = asdict(notification)
        return jsonify(notification_dict), 200


class DeviceTokenView(MethodView):
    @access_auth_middleware
    def post(self) -> ResponseReturnValue:
        """Register device token"""
        request_data = request.get_json()
        account_id = getattr(request, 'account_id')
        
        token = request_data.get('token')
        platform = request_data.get('platform')
        
        device_token = NotificationService.register_device_token(account_id, token, platform)
        device_token_dict = asdict(device_token)
        
        return jsonify(device_token_dict), 201

    @access_auth_middleware
    def get(self) -> ResponseReturnValue:
        """Get device tokens for account"""
        account_id = getattr(request, 'account_id')
        platform = request.args.get('platform')
        
        device_tokens = NotificationService.get_device_tokens_for_account(account_id, platform)
        device_tokens_dict = [asdict(token) for token in device_tokens]
        
        return jsonify({'device_tokens': device_tokens_dict}), 200

    @access_auth_middleware
    def delete(self) -> ResponseReturnValue:
        """Deactivate device token"""
        request_data = request.get_json()
        token = request_data.get('token')
        
        success = NotificationService.deactivate_device_token(token)
        
        if success:
            return jsonify({'message': 'Device token deactivated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to deactivate device token'}), 400


class TopicView(MethodView):
    @access_auth_middleware
    def post(self) -> ResponseReturnValue:
        """Subscribe to topic"""
        request_data = request.get_json()
        account_id = getattr(request, 'account_id')
        
        topic = request_data.get('topic')
        tokens = request_data.get('tokens', [])
        
        # If no tokens provided, get all tokens for the account
        if not tokens:
            device_tokens = NotificationService.get_device_tokens_for_account(account_id)
            tokens = [dt.token for dt in device_tokens]
        
        subscribe_params = SubscribeToTopicParams(tokens=tokens, topic=topic)
        response = NotificationService.subscribe_to_topic(subscribe_params)
        
        response_dict = asdict(response)
        return jsonify(response_dict), 200

    @access_auth_middleware
    def delete(self) -> ResponseReturnValue:
        """Unsubscribe from topic"""
        request_data = request.get_json()
        account_id = getattr(request, 'account_id')
        
        topic = request_data.get('topic')
        tokens = request_data.get('tokens', [])
        
        # If no tokens provided, get all tokens for the account
        if not tokens:
            device_tokens = NotificationService.get_device_tokens_for_account(account_id)
            tokens = [dt.token for dt in device_tokens]
        
        unsubscribe_params = UnsubscribeFromTopicParams(tokens=tokens, topic=topic)
        response = NotificationService.unsubscribe_from_topic(unsubscribe_params)
        
        response_dict = asdict(response)
        return jsonify(response_dict), 200


class NotificationTemplateView(MethodView):
    def post(self) -> ResponseReturnValue:
        """Create notification template"""
        request_data = request.get_json()
        
        name = request_data.get('name')
        title_template = request_data.get('title_template')
        body_template = request_data.get('body_template')
        default_data = request_data.get('default_data')
        
        template = NotificationService.create_notification_template(
            name, title_template, body_template, default_data
        )
        template_dict = asdict(template)
        
        return jsonify(template_dict), 201

    def get(self) -> ResponseReturnValue:
        """Get all notification templates"""
        templates = NotificationService.get_all_notification_templates()
        templates_dict = [asdict(template) for template in templates]
        
        return jsonify({'templates': templates_dict}), 200


class NotificationTemplateDetailView(MethodView):
    def get(self, template_id: str) -> ResponseReturnValue:
        """Get specific notification template"""
        template = NotificationService.get_notification_template_by_id(template_id)
        template_dict = asdict(template)
        
        return jsonify(template_dict), 200

    def put(self, template_id: str) -> ResponseReturnValue:
        """Update notification template"""
        request_data = request.get_json()
        
        name = request_data.get('name')
        title_template = request_data.get('title_template')
        body_template = request_data.get('body_template')
        default_data = request_data.get('default_data')
        
        template = NotificationService.update_notification_template(
            template_id, name, title_template, body_template, default_data
        )
        template_dict = asdict(template)
        
        return jsonify(template_dict), 200

    def delete(self, template_id: str) -> ResponseReturnValue:
        """Delete notification template"""
        success = NotificationService.delete_notification_template(template_id)
        
        if success:
            return jsonify({'message': 'Template deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete template'}), 400


class NotificationStatsView(MethodView):
    @access_auth_middleware
    def get(self) -> ResponseReturnValue:
        """Get notification statistics for account"""
        account_id = getattr(request, 'account_id')
        
        total_count = NotificationService.get_notification_count_for_account(account_id)
        unread_count = NotificationService.get_unread_notification_count_for_account(account_id)
        
        stats = {
            'total_notifications': total_count,
            'unread_notifications': unread_count,
            'read_notifications': total_count - unread_count
        }
        
        return jsonify(stats), 200