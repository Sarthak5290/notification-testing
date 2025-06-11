from flask import Blueprint

from modules.notification.rest_api.notification_view import (
    DeviceTokenView,
    NotificationDetailView,
    NotificationStatsView,
    NotificationTemplateDetailView,
    NotificationTemplateView,
    NotificationView,
    TopicView,
)


class NotificationRouter:
    @staticmethod
    def create_route(*, blueprint: Blueprint) -> Blueprint:
        # Notification routes
        blueprint.add_url_rule(
            "/notifications", 
            view_func=NotificationView.as_view("notification_view"),
            methods=["GET", "POST"]
        )
        
        blueprint.add_url_rule(
            "/notifications/<notification_id>", 
            view_func=NotificationDetailView.as_view("notification_detail_view"),
            methods=["GET", "PATCH"]
        )
        
        # Device token routes
        blueprint.add_url_rule(
            "/device-tokens", 
            view_func=DeviceTokenView.as_view("device_token_view"),
            methods=["GET", "POST", "DELETE"]
        )
        
        # Topic subscription routes
        blueprint.add_url_rule(
            "/topics/subscribe", 
            view_func=TopicView.as_view("topic_subscribe_view"),
            methods=["POST"]
        )
        
        blueprint.add_url_rule(
            "/topics/unsubscribe", 
            view_func=TopicView.as_view("topic_unsubscribe_view"),
            methods=["DELETE"]
        )
        
        # Template routes
        blueprint.add_url_rule(
            "/templates", 
            view_func=NotificationTemplateView.as_view("notification_template_view"),
            methods=["GET", "POST"]
        )
        
        blueprint.add_url_rule(
            "/templates/<template_id>", 
            view_func=NotificationTemplateDetailView.as_view("notification_template_detail_view"),
            methods=["GET", "PUT", "DELETE"]
        )
        
        # Statistics routes
        blueprint.add_url_rule(
            "/stats", 
            view_func=NotificationStatsView.as_view("notification_stats_view"),
            methods=["GET"]
        )
        
        return blueprint