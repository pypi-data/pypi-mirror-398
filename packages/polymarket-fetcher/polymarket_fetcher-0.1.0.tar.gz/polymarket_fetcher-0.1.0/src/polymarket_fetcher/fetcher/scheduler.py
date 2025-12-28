"""Scheduler for market data fetching using APScheduler.

This module provides a lightweight, pure-Python scheduling solution
using APScheduler's AsyncIOScheduler. It supports cron, interval,
and date-based triggers with proper async support.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apscheduler.schedulers.async_ import AsyncIOScheduler
    from apscheduler.triggers.base import BaseTrigger


class FetchScheduler:
    """Scheduler for periodic market data fetching using APScheduler.

    This scheduler uses APScheduler's AsyncIOScheduler for async-compatible
    scheduling with cron, interval, and date-based triggers.

    Configuration is loaded from settings.yaml under the `scheduler` section.

    Example:
        >>> from polymarket_fetcher import load_config
        >>> config, _ = load_config("config/settings.yaml")
        >>> scheduler = FetchScheduler(config=config)
        >>> await scheduler.start()
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        timezone: Optional[str] = None,
        market_fetch_interval: Optional[int] = None,
        history_snapshot_interval: Optional[int] = None,
    ):
        """Initialize the scheduler.

        Args:
            config: Configuration object with scheduler settings.
            timezone: Override timezone for scheduling.
            market_fetch_interval: Override market fetch interval in seconds.
            history_snapshot_interval: Override history snapshot interval in seconds.
        """
        self.config = config
        self._running = False
        self._scheduler: Optional["AsyncIOScheduler"] = None
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}

        # Load settings from config or use overrides
        if config and hasattr(config, 'scheduler'):
            scheduler_config = config.scheduler
            self.timezone = timezone or getattr(scheduler_config, 'timezone', 'UTC')
            self.market_fetch_interval = market_fetch_interval or getattr(
                scheduler_config, 'market_fetch_interval', 60
            )
            self.history_snapshot_interval = history_snapshot_interval or getattr(
                scheduler_config, 'history_snapshot_interval', 300
            )
            self._enabled = getattr(scheduler_config, 'enabled', True)
        else:
            self.timezone = timezone or 'UTC'
            self.market_fetch_interval = market_fetch_interval or 60
            self.history_snapshot_interval = history_snapshot_interval or 300
            self._enabled = True

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

        Creates and starts an AsyncIOScheduler with configured timezone.
        """
        if self._running:
            logger.warning("FetchScheduler is already running")
            return

        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            raise ImportError(
                "apscheduler is required for scheduling. "
                "Install it with: pip install apscheduler"
            )

        # Create scheduler with timezone
        self._scheduler = AsyncIOScheduler(timezone=self.timezone)

        # Add default jobs if configured
        if self._enabled:
            # Note: Jobs are added via add_job() method
            pass

        self._scheduler.start()
        self._running = True

        logger.info(
            f"FetchScheduler started (timezone: {self.timezone}, "
            f"fetch_interval: {self.market_fetch_interval}s)"
        )

    async def stop(self, graceful: bool = True) -> None:
        """Stop the scheduler.

        Args:
            graceful: If True, wait for running jobs to complete.
        """
        if not self._running:
            return

        if self._scheduler:
            # Shutdown with optional wait for running jobs
            self._scheduler.shutdown(wait=graceful)
            self._scheduler = None

        self._running = False
        self._jobs.clear()
        self._handlers.clear()

        logger.info("FetchScheduler stopped")

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
                seconds = self.market_fetch_interval
            return IntervalTrigger(seconds=seconds, timezone=self.timezone)
        elif trigger == "cron":
            if cron is None:
                # Default to every minute
                cron = "* * * * *"
            return CronTrigger.from_crontab(cron, timezone=self.timezone)
        elif trigger == "date":
            return DateTrigger(timezone=self.timezone)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

    async def add_job(
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
            func: Async function to call.
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

        # Store job info for reference
        self._jobs[job_id] = {
            "func": func,
            "name": name or job_id,
            "trigger": trigger,
            "seconds": seconds,
            "cron": cron,
            "kwargs": kwargs,
        }
        self._handlers[job_id] = func

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

        if job_id in self._scheduler.get_jobs():
            self._scheduler.remove_job(job_id)

        self._jobs.pop(job_id, None)
        self._handlers.pop(job_id, None)

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
            if hasattr(trigger, 'interval'):
                cron_info = f"interval/{trigger.interval.total_seconds():.0f}s"
            elif hasattr(trigger, 'fields'):
                cron_info = str(trigger)
            else:
                cron_info = str(trigger)

            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": type(trigger).__name__,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })

        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job.

        Args:
            job_id: Job ID.

        Returns:
            Job information dictionary or None.
        """
        if not self._scheduler:
            return None

        job = self._scheduler.get_job(job_id)
        if not job:
            return None

        trigger = job.trigger
        return {
            "id": job.id,
            "name": job.name,
            "trigger": type(trigger).__name__,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }

    async def run_job_now(self, job_id: str) -> bool:
        """Trigger a job to run immediately.

        Args:
            job_id: Job ID.

        Returns:
            True if job was triggered.
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.run_job(job_id)
            logger.info(f"Job triggered immediately: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False

    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a job and return result.

        Args:
            job_id: Job ID to execute.

        Returns:
            Execution result dictionary.
        """
        start_time = datetime.now()
        func = self._handlers.get(job_id)

        if not func:
            return {
                "code": 500,
                "msg": f"Job not found: {job_id}",
                "data": None,
            }

        try:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()

            exec_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "jobId": job_id,
                    "execTime": int(exec_time),
                    "executeDate": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Job execution failed: {e}", exc_info=True)
            return {
                "code": 500,
                "msg": str(e),
                "data": None,
            }

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status.

        Returns:
            Status dictionary.
        """
        return {
            "running": self._running,
            "timezone": self.timezone,
            "jobs_count": len(self._jobs),
            "enabled": self._enabled,
            "fetch_interval": self.market_fetch_interval,
            "snapshot_interval": self.history_snapshot_interval,
        }
