from typing import List, Type

from temporalio import activity, workflow

from modules.application.types import BaseWorker, RegisteredWorker
from modules.application.workers.health_check_worker import HealthCheckWorker

# Try to import notification workers, but don't fail if missing
try:
    from modules.notification.workers.notification_worker import (
        NotificationCleanupWorker,
        NotificationSchedulerWorker,
    )
    NOTIFICATION_WORKERS = [NotificationSchedulerWorker, NotificationCleanupWorker]
except ImportError:
    NOTIFICATION_WORKERS = []


class TemporalConfig:
    WORKERS: List[Type[BaseWorker]] = [HealthCheckWorker] + NOTIFICATION_WORKERS

    REGISTERED_WORKERS: List[RegisteredWorker] = []

    @staticmethod
    def _register_worker(cls: Type[BaseWorker]) -> None:
        # Wrap the execute() method so Temporal recognizes it as an activity
        wrapped_execute = activity.defn(fn=cls.execute, name=f"{cls.__name__}_execute")  # type: ignore
        setattr(cls, "execute", wrapped_execute)

        # Wrap the run() method so Temporal recognizes it as the application entry point
        wrapped_run = workflow.run(cls.run)
        setattr(cls, "run", wrapped_run)

        # Decorate the class itself as a workflow definition
        cls = workflow.defn(cls)

        TemporalConfig.REGISTERED_WORKERS.append(RegisteredWorker(cls=cls, priority=cls.priority))

    @staticmethod
    def mount_workers() -> None:
        for worker in TemporalConfig.WORKERS:
            TemporalConfig._register_worker(worker)

    @staticmethod
    def get_all_registered_workers() -> List[RegisteredWorker]:
        return TemporalConfig.REGISTERED_WORKERS