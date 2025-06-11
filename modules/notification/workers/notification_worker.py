from typing import Any

from modules.application.types import BaseWorker
from modules.logger.logger import Logger


class NotificationSchedulerWorker(BaseWorker):
    """Worker to process scheduled notifications"""
    
    max_execution_time_in_seconds = 300  # 5 minutes
    max_retries = 2

    @staticmethod
    async def execute(*args: Any) -> None:
        try:
            # Import here to avoid circular imports
            from modules.notification.notification_service import NotificationService
            
            Logger.info(message="Starting scheduled notification processing")
            
            # Process scheduled notifications that are ready to be sent
            processed_notifications = NotificationService.process_scheduled_notifications()
            
            Logger.info(
                message=f"Processed {len(processed_notifications)} scheduled notifications"
            )
            
        except Exception as e:
            Logger.error(message=f"Error processing scheduled notifications: {str(e)}")
            raise

    async def run(self, *args: Any) -> None:
        await super().run(*args)


class NotificationCleanupWorker(BaseWorker):
    """Worker to clean up old notifications"""
    
    max_execution_time_in_seconds = 600  # 10 minutes
    max_retries = 1

    @staticmethod
    async def execute(*args: Any) -> None:
        try:
            # Import here to avoid circular imports
            from modules.notification.notification_service import NotificationService
            
            Logger.info(message="Starting notification cleanup")
            
            # Clean up notifications older than 90 days
            deleted_count = NotificationService.cleanup_old_notifications(days_old=90)
            
            Logger.info(message=f"Cleaned up {deleted_count} old notifications")
            
        except Exception as e:
            Logger.error(message=f"Error during notification cleanup: {str(e)}")
            raise

    async def run(self, *args: Any) -> None:
        await super().run(*args)