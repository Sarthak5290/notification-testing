from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from modules.application.repository import ApplicationRepository
from modules.notification.internal.store.notification_model import (
    DeviceTokenModel,
    NotificationModel,
    NotificationTemplateModel,
)
from modules.logger.logger import Logger

NOTIFICATION_VALIDATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "account_id",
            "title",
            "body",
            "notification_type",
            "status",
            "priority",
            "device_tokens",
            "created_at",
            "updated_at",
        ],
        "properties": {
            "account_id": {"bsonType": "string"},
            "title": {"bsonType": "string"},
            "body": {"bsonType": "string"},
            "notification_type": {"bsonType": "string", "enum": ["PUSH", "EMAIL", "SMS", "IN_APP"]},
            "status": {"bsonType": "string", "enum": ["PENDING", "SENT", "FAILED", "DELIVERED", "CLICKED"]},
            "priority": {"bsonType": "string", "enum": ["LOW", "NORMAL", "HIGH"]},
            "device_tokens": {"bsonType": "array", "items": {"bsonType": "string"}},
            "topic": {"bsonType": ["string", "null"]},
            "data": {"bsonType": ["object", "null"]},
            "image_url": {"bsonType": ["string", "null"]},
            "template_id": {"bsonType": ["string", "null"]},
            "template_data": {"bsonType": ["object", "null"]},
            "scheduled_at": {"bsonType": ["date", "null"]},
            "sent_at": {"bsonType": ["date", "null"]},
            "delivered_at": {"bsonType": ["date", "null"]},
            "clicked_at": {"bsonType": ["date", "null"]},
            "error_message": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
        },
    }
}

NOTIFICATION_TEMPLATE_VALIDATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "title_template", "body_template", "created_at", "updated_at"],
        "properties": {
            "name": {"bsonType": "string"},
            "title_template": {"bsonType": "string"},
            "body_template": {"bsonType": "string"},
            "default_data": {"bsonType": ["object", "null"]},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
        },
    }
}

DEVICE_TOKEN_VALIDATION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["account_id", "token", "platform", "is_active", "created_at", "updated_at"],
        "properties": {
            "account_id": {"bsonType": "string"},
            "token": {"bsonType": "string"},
            "platform": {"bsonType": "string", "enum": ["ios", "android", "web"]},
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
        },
    }
}


class NotificationRepository(ApplicationRepository):
    collection_name = NotificationModel.get_collection_name()

    @classmethod
    def on_init_collection(cls, collection: Collection) -> bool:
        collection.create_index("account_id")
        collection.create_index("status")
        collection.create_index("notification_type")
        collection.create_index("created_at")
        collection.create_index("scheduled_at")

        add_validation_command = {
            "collMod": cls.collection_name,
            "validator": NOTIFICATION_VALIDATION_SCHEMA,
            "validationLevel": "strict",
        }

        try:
            collection.database.command(add_validation_command)
        except OperationFailure as e:
            if e.code == 26:  # NamespaceNotFound MongoDB error code
                collection.database.create_collection(cls.collection_name, validator=NOTIFICATION_VALIDATION_SCHEMA)
            else:
                Logger.error(message=f"OperationFailure occurred for collection notifications: {e.details}")
        return True


class NotificationTemplateRepository(ApplicationRepository):
    collection_name = NotificationTemplateModel.get_collection_name()

    @classmethod
    def on_init_collection(cls, collection: Collection) -> bool:
        collection.create_index("name", unique=True)

        add_validation_command = {
            "collMod": cls.collection_name,
            "validator": NOTIFICATION_TEMPLATE_VALIDATION_SCHEMA,
            "validationLevel": "strict",
        }

        try:
            collection.database.command(add_validation_command)
        except OperationFailure as e:
            if e.code == 26:  # NamespaceNotFound MongoDB error code
                collection.database.create_collection(
                    cls.collection_name, validator=NOTIFICATION_TEMPLATE_VALIDATION_SCHEMA
                )
            else:
                Logger.error(message=f"OperationFailure occurred for collection notification_templates: {e.details}")
        return True


class DeviceTokenRepository(ApplicationRepository):
    collection_name = DeviceTokenModel.get_collection_name()

    @classmethod
    def on_init_collection(cls, collection: Collection) -> bool:
        collection.create_index("account_id")
        collection.create_index("token", unique=True)
        collection.create_index("platform")
        collection.create_index("is_active")

        add_validation_command = {
            "collMod": cls.collection_name,
            "validator": DEVICE_TOKEN_VALIDATION_SCHEMA,
            "validationLevel": "strict",
        }

        try:
            collection.database.command(add_validation_command)
        except OperationFailure as e:
            if e.code == 26:  # NamespaceNotFound MongoDB error code
                collection.database.create_collection(cls.collection_name, validator=DEVICE_TOKEN_VALIDATION_SCHEMA)
            else:
                Logger.error(message=f"OperationFailure occurred for collection device_tokens: {e.details}")
        return True