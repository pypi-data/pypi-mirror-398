"""Scheduler for Telegram bot using APScheduler.

This module provides a lightweight, pure-Python scheduling solution
using APScheduler's AsyncIOScheduler. It supports cron, interval,
and date-based triggers with proper async support.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apscheduler.schedulers.async_ import AsyncIOScheduler
    from apscheduler.triggers.base import BaseTrigger


def load_scheduler_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load scheduler configuration from settings.yaml.

    Args:
        config_path: Path to settings.yaml. If None, looks in default locations.

    Returns:
        Dictionary with scheduler configuration.
    """
    if config_path is None:
        possible_paths = [
            Path.cwd() / "config" / "settings.yaml",
            Path.cwd() / "settings.yaml",
            Path(__file__).parent.parent.parent / "config" / "settings.yaml",
        ]
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break

    if config_path is None or not Path(config_path).exists():
        logger.warning(f"Config file not found, using defaults")
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data.get("scheduler", {})


class APScheduler:
    """Simple async scheduler using APScheduler.

    This class wraps APScheduler's AsyncIOScheduler to provide
    scheduling capabilities with configuration loaded from settings.yaml.

    Example:
        >>> from polymarket_telegram.scheduler import APScheduler
        >>> scheduler = APScheduler()
        >>> scheduler.add_job(my_task, "interval", seconds=60)
        >>> await scheduler.start()
    """

    def __init__(
        self,
        timezone: str = "UTC",
        config_path: Optional[str] = None,
    ):
        """Initialize the scheduler.

        Args:
            timezone: Timezone for scheduling.
            config_path: Path to settings.yaml for config loading.
        """
        self.timezone = timezone
        self.config_path = config_path
        self._running = False
        self._scheduler: Optional["AsyncIOScheduler"] = None
        self._tasks: Dict[str, Dict[str, Any]] = {}

        # Load config from settings.yaml
        scheduler_config = load_scheduler_config(config_path)
        self._enabled = scheduler_config.get("enabled", True)

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    @property
    def is_enabled(self) -> bool:
        """Check if scheduling is enabled in config."""
        return self._enabled

    async def start(self) -> None:
        """Start the scheduler.

        Creates and starts an AsyncIOScheduler.
        """
        if self._running:
            logger.warning("APScheduler is already running")
            return

        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
        except ImportError:
            raise ImportError(
                "apscheduler is required for scheduling. "
                "Install it with: pip install apscheduler"
            )

        self._scheduler = AsyncIOScheduler(timezone=self.timezone)
        self._scheduler.start()
        self._running = True

        logger.info(f"APScheduler started (timezone: {self.timezone})")

    async def stop(self, graceful: bool = True) -> None:
        """Stop the scheduler.

        Args:
            graceful: If True, wait for running jobs to complete.
        """
        if not self._running:
            return

        if self._scheduler:
            self._scheduler.shutdown(wait=graceful)
            self._scheduler = None

        self._running = False
        self._tasks.clear()

        logger.info("APScheduler stopped")

    def _parse_trigger(
        self,
        trigger: str,
        seconds: Optional[int] = None,
        cron: Optional[str] = None,
    ) -> "BaseTrigger":
        """Parse trigger configuration into APScheduler trigger.

        Args:
            trigger: Trigger type ("cron", "interval", or "date").
            seconds: Interval in seconds (for interval trigger).
            cron: Cron expression (for cron trigger).

        Returns:
            Configured APScheduler trigger.
        """
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger

        if trigger == "interval":
            if seconds is None:
                seconds = 60  # Default to 60 seconds
            return IntervalTrigger(seconds=seconds, timezone=self.timezone)
        elif trigger == "cron":
            if cron is None:
                cron = "* * * * *"  # Default to every minute
            return CronTrigger.from_crontab(cron, timezone=self.timezone)
        elif trigger == "date":
            return DateTrigger(timezone=self.timezone)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

    def add_job(
        self,
        func: Callable,
        trigger: str = "interval",
        seconds: Optional[int] = None,
        cron: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        replace_existing: bool = True,
        **kwargs,
    ) -> str:
        """Add a job to the scheduler.

        Args:
            func: Async function to execute.
            trigger: Trigger type ("cron", "interval", or "date").
            seconds: Interval in seconds (for interval trigger).
            cron: Cron expression (for cron trigger).
            id: Job ID.
            name: Job name.
            replace_existing: Replace existing job with same ID.
            **kwargs: Additional arguments for the function.

        Returns:
            Job ID.
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler is not running. Call start() first.")

        job_id = id or f"job_{datetime.now().timestamp()}"

        # Store task info
        self._tasks[job_id] = {
            "func": func,
            "name": name or job_id,
            "trigger": trigger,
            "seconds": seconds,
            "cron": cron,
            "kwargs": kwargs,
        }

        # Create the trigger
        trigger_obj = self._parse_trigger(trigger, seconds, cron)

        # Wrap async function for APScheduler
        async def async_wrapper() -> None:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()

        # Add job to scheduler
        self._scheduler.add_job(
            async_wrapper,
            trigger=trigger_obj,
            id=job_id,
            name=name,
            replace_existing=replace_existing,
            **kwargs,
        )

        logger.info(f"Job added: {job_id} ({name or 'unnamed'}) - trigger: {trigger}")

        return job_id

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler.

        Args:
            job_id: Job ID to remove.
        """
        if not self._scheduler:
            return

        if job_id in self._tasks:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
            del self._tasks[job_id]
            logger.info(f"Job removed: {job_id}")

    def get_jobs(self) -> list:
        """Get all scheduled jobs.

        Returns:
            List of job information dictionaries.
        """
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            trigger = job.trigger
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": type(trigger).__name__,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })

        return jobs

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status.

        Returns:
            Status dictionary.
        """
        return {
            "running": self._running,
            "timezone": self.timezone,
            "tasks_count": len(self._tasks),
            "enabled": self._enabled,
        }


class SimpleScheduler:
    """Simple async scheduler as fallback when APScheduler is not available.

    This provides basic cron-based scheduling without external dependencies.
    """

    def __init__(self, timezone: str = "UTC"):
        """Initialize the simple scheduler.

        Args:
            timezone: Timezone for scheduling.
        """
        self.timezone = timezone
        self._running = False
        self._tasks: Dict[str, Dict[str, Any]] = {}

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        self._running = True
        logger.info(f"SimpleScheduler started (timezone: {self.timezone})")

        # Start all cron tasks
        for job_id, task_info in self._tasks.items():
            asyncio.create_task(self._cron_loop(job_id, task_info))

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        logger.info("SimpleScheduler stopped")

    async def _cron_loop(self, job_id: str, task_info: Dict) -> None:
        """Run cron loop for a task."""
        func = task_info["func"]
        cron_expr = task_info["cron"]
        parts = cron_expr.split()

        if len(parts) != 5:
            logger.error(f"Invalid cron expression: {cron_expr}")
            return

        minute, hour, day, month, weekday = parts

        while self._running:
            now = datetime.now()
            should_run = (
                (minute == '*' or now.minute == int(minute)) and
                (hour == '*' or now.hour == int(hour))
            )

            if should_run:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()
                except Exception as e:
                    logger.error(f"Cron job failed: {e}")

            await asyncio.sleep(60)

    def add_job(
        self,
        func: Callable,
        cron_expr: str,
        job_id: str,
        **kwargs,
    ) -> None:
        """Add a cron job.

        Args:
            func: Async function to execute.
            cron_expr: Cron expression (e.g., "0 8 * * *").
            job_id: Job identifier.
            **kwargs: Additional arguments for the function.
        """
        self._tasks[job_id] = {
            "func": func,
            "cron": cron_expr,
            "kwargs": kwargs,
        }
        logger.info(f"Cron job added: {job_id} ({cron_expr})")

    def remove_job(self, job_id: str) -> None:
        """Remove a cron job."""
        if job_id in self._tasks:
            del self._tasks[job_id]
            logger.info(f"Cron job removed: {job_id}")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status.

        Returns:
            Status dictionary.
        """
        return {
            "running": self._running,
            "timezone": self.timezone,
            "tasks_count": len(self._tasks),
        }
