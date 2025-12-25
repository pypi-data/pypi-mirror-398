"""
Worker Queue Metrics Service.

This service provides business logic for calculating worker queue metrics
including worker health, task statistics, and performance metrics.
"""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from control_plane_api.app.models.worker import WorkerQueue, WorkerHeartbeat
from control_plane_api.app.models.execution import Execution
from control_plane_api.app.schemas.worker_queue_observability_schemas import WorkerQueueMetricsResponse

logger = structlog.get_logger()


class WorkerQueueMetricsService:
    """Service for calculating worker queue metrics"""

    def __init__(self, db: Session):
        self.db = db

    async def get_queue_metrics(
        self,
        queue_id: str,
        organization_id: str
    ) -> WorkerQueueMetricsResponse:
        """
        Calculate comprehensive metrics for a worker queue.

        Args:
            queue_id: Worker queue UUID
            organization_id: Organization ID

        Returns:
            WorkerQueueMetricsResponse with calculated metrics

        Raises:
            ValueError: If queue not found or doesn't belong to organization
        """
        # Verify queue exists and belongs to organization
        queue = self.db.query(WorkerQueue).filter(
            WorkerQueue.id == queue_id,
            WorkerQueue.organization_id == organization_id
        ).first()

        if not queue:
            raise ValueError("Worker queue not found")

        now = datetime.utcnow()

        # Calculate worker status counts
        worker_stats = self._get_worker_status_counts(queue_id, now)

        # Calculate 24h task metrics
        task_metrics = self._get_task_metrics_24h(queue_id, now)

        # Get last activity timestamp
        last_activity = self._get_last_activity(queue_id)

        # Build response
        return WorkerQueueMetricsResponse(
            queue_id=queue_id,
            active_workers=worker_stats["active"],
            idle_workers=worker_stats["idle"],
            busy_workers=worker_stats["busy"],
            total_workers=worker_stats["total"],
            tasks_processed_24h=task_metrics["processed"],
            tasks_failed_24h=task_metrics["failed"],
            tasks_pending=task_metrics["pending"],
            avg_task_duration_ms=task_metrics["avg_duration_ms"],
            error_rate_percent=task_metrics["error_rate"],
            last_error_at=task_metrics["last_error_at"],
            task_queue_backlog=0,  # TODO: Implement Temporal queue metrics
            task_queue_pollers=0,  # TODO: Implement Temporal queue metrics
            last_activity_at=last_activity,
            updated_at=now
        )

    def _get_worker_status_counts(self, queue_id: str, now: datetime) -> Dict[str, int]:
        """
        Get worker status counts from WorkerHeartbeat table.

        Workers are considered stale if last_heartbeat > 90 seconds ago.
        """
        stale_threshold = now - timedelta(seconds=90)

        # Query recent heartbeats
        heartbeats = self.db.query(WorkerHeartbeat).filter(
            WorkerHeartbeat.worker_queue_id == queue_id,
            WorkerHeartbeat.last_heartbeat > stale_threshold
        ).all()

        active = sum(1 for hb in heartbeats if hb.status == "active")
        idle = sum(1 for hb in heartbeats if hb.status == "idle")
        busy = sum(1 for hb in heartbeats if hb.status == "busy")
        total = len(heartbeats)

        logger.info(
            "worker_status_calculated",
            queue_id=queue_id,
            active=active,
            idle=idle,
            busy=busy,
            total=total
        )

        return {
            "active": active,
            "idle": idle,
            "busy": busy,
            "total": total
        }

    def _get_task_metrics_24h(self, queue_id: str, now: datetime) -> Dict:
        """Calculate task metrics for the last 24 hours"""
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Get executions in last 24h
        executions_24h = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.created_at >= twenty_four_hours_ago
        ).all()

        # Count processed and failed tasks
        processed = sum(1 for e in executions_24h if e.status in ["completed", "failed"])
        failed = sum(1 for e in executions_24h if e.status == "failed")

        # Get pending tasks count
        pending = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "pending"
        ).count()

        # Calculate average duration for completed tasks
        completed_executions = [
            e for e in executions_24h
            if e.status == "completed" and e.started_at and e.completed_at
        ]

        if completed_executions:
            total_duration_ms = sum(
                (e.completed_at - e.started_at).total_seconds() * 1000
                for e in completed_executions
            )
            avg_duration_ms = total_duration_ms / len(completed_executions)
        else:
            avg_duration_ms = 0

        # Calculate error rate
        error_rate = (failed / processed * 100) if processed > 0 else 0

        # Get last error timestamp
        last_error = self.db.query(Execution).filter(
            Execution.worker_queue_id == queue_id,
            Execution.status == "failed"
        ).order_by(Execution.completed_at.desc()).first()

        last_error_at = last_error.completed_at if last_error else None

        logger.info(
            "task_metrics_calculated",
            queue_id=queue_id,
            processed=processed,
            failed=failed,
            pending=pending,
            avg_duration_ms=avg_duration_ms,
            error_rate=error_rate
        )

        return {
            "processed": processed,
            "failed": failed,
            "pending": pending,
            "avg_duration_ms": avg_duration_ms,
            "error_rate": error_rate,
            "last_error_at": last_error_at
        }

    def _get_last_activity(self, queue_id: str) -> Optional[datetime]:
        """Get timestamp of last worker activity"""
        last_activity = self.db.query(WorkerHeartbeat).filter(
            WorkerHeartbeat.worker_queue_id == queue_id
        ).order_by(WorkerHeartbeat.last_heartbeat.desc()).first()

        return last_activity.last_heartbeat if last_activity else None
