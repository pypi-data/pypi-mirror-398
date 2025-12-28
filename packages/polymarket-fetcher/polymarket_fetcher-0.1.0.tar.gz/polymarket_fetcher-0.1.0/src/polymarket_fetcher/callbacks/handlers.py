"""Callback handlers for event processing."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text

from .models import EventType, MarketEvent, SyncEvent
from .dispatcher import EventBus
from ..storage import DatabaseManager, MarketRepository

logger = logging.getLogger(__name__)


class BaseCallbackHandler(ABC):
    """Base class for callback handlers."""

    @abstractmethod
    async def handle(self, event: MarketEvent) -> None:
        """Handle an event.

        Args:
            event: Event to handle.
        """
        pass

    @abstractmethod
    def get_event_types(self) -> set[EventType]:
        """Get the event types this handler handles.

        Returns:
            Set of event types.
        """
        pass


class ConsoleHandler(BaseCallbackHandler):
    """Handler that prints events to the console."""

    def __init__(self, verbose: bool = False):
        """Initialize the console handler.

        Args:
            verbose: Whether to print detailed output.
        """
        self.verbose = verbose

    async def handle(self, event: MarketEvent) -> None:
        """Handle event by printing to console.

        Args:
            event: Event to handle.
        """
        if self.verbose:
            print(f"\n[Event] {event.event_type.value}")
            print(f"  Market: {event.market_id}")
            print(f"  Data: {json.dumps(event.data, indent=2)}")
        else:
            print(f"[{event.event_type.value}] Market: {event.market_id}")

    def get_event_types(self) -> set[EventType]:
        """Get all event types."""
        return set(EventType)


class DatabaseHandler(BaseCallbackHandler):
    """Handler that logs events to the database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the database handler.

        Args:
            db_manager: Database manager.
        """
        self.db_manager = db_manager

    async def handle(self, event: MarketEvent) -> None:
        """Handle event by logging to database.

        Args:
            event: Event to handle.
        """
        try:
            async with self.db_manager.session() as session:
                await session.execute(
                    text("""
                        INSERT INTO event_logs (event_type, market_id, payload)
                        VALUES (:event_type, :market_id, :payload)
                    """),
                    {
                        "event_type": event.event_type.value,
                        "market_id": event.market_id,
                        "payload": json.dumps(event.to_dict()),
                    },
                )
        except Exception as e:
            logger.error(f"Failed to log event to database: {e}")

    def get_event_types(self) -> set[EventType]:
        """Get all event types."""
        return set(EventType)


class WebhookHandler(BaseCallbackHandler):
    """Handler that sends events via HTTP webhooks."""

    def __init__(
        self,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
    ):
        """Initialize the webhook handler.

        Args:
            webhook_url: Webhook URL to call.
            headers: Additional headers.
            timeout: Request timeout.
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def handle(self, event: MarketEvent) -> None:
        """Handle event by sending webhook.

        Args:
            event: Event to handle.
        """
        try:
            payload = event.to_dict()
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            logger.debug(f"Webhook sent successfully for {event.event_type.value}")
        except httpx.HTTPError as e:
            logger.error(f"Webhook failed: {e}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    def get_event_types(self) -> set[EventType]:
        """Get all event types."""
        return set(EventType)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class VolumeSpikeHandler(BaseCallbackHandler):
    """Handler that detects and reports volume spikes."""

    def __init__(
        self,
        spike_threshold: float = 2.0,  # 200% increase
        min_volume: float = 1000,
    ):
        """Initialize the volume spike handler.

        Args:
            spike_threshold: Multiplier threshold for spike detection.
            min_volume: Minimum volume to consider.
        """
        self.spike_threshold = spike_threshold
        self.min_volume = min_volume
        self._last_volume: Dict[str, float] = {}

    async def handle(self, event: MarketEvent) -> None:
        """Handle event by checking for volume spikes.

        Args:
            event: Event to handle.
        """
        if event.event_type != EventType.MARKET_UPDATED:
            return

        data = event.data or {}
        changes = data.get("changes", [])
        market_id = event.market_id

        # Check if volume changed
        volume_change = None
        for change in changes:
            if change.get("field") == "volume_num":
                volume_change = change
                break

        if not volume_change:
            return

        old_volume = volume_change.get("old_value", 0) or 0
        new_volume = volume_change.get("new_value", 0) or 0

        # Skip if volume is too low
        if new_volume < self.min_volume:
            return

        # Calculate change percentage
        if old_volume > 0:
            change_percent = (new_volume - old_volume) / old_volume
        else:
            change_percent = 1.0 if new_volume > 0 else 0

        # Check for spike
        if change_percent >= self.spike_threshold:
            logger.info(
                f"Volume spike detected: {market_id} "
                f"({old_volume:.0f} -> {new_volume:.0f}, {change_percent*100:.1f}%)"
            )

    def get_event_types(self) -> set[EventType]:
        """Get event types this handler handles."""
        return {EventType.MARKET_UPDATED}


class NotificationHandler(BaseCallbackHandler):
    """Handler that sends notifications via various channels."""

    def __init__(self, channels: List[str] = None):
        """Initialize the notification handler.

        Args:
            channels: List of notification channels to use.
        """
        self.channels = channels or ["console"]
        self._pending_notifications: List[Dict[str, Any]] = []

    async def handle(self, event: MarketEvent) -> None:
        """Handle event by sending notifications.

        Args:
            event: Event to handle.
        """
        notification = {
            "type": event.event_type.value,
            "market_id": event.market_id,
            "message": self._format_message(event),
            "data": event.data,
        }

        for channel in self.channels:
            try:
                if channel == "console":
                    print(f"[Notification] {notification['message']}")
                elif channel == "log":
                    logger.info(notification["message"])
                # Add more channels as needed
            except Exception as e:
                logger.error(f"Notification error ({channel}): {e}")

    def _format_message(self, event: MarketEvent) -> str:
        """Format event as a notification message.

        Args:
            event: Event to format.

        Returns:
            Formatted message.
        """
        if event.event_type == EventType.KEYWORD_MATCH:
            question = event.data.get("question", "")
            matched = event.data.get("match_result", {}).get("matched_keywords", [])
            return f"Keyword match: {question[:50]}... (matched: {matched})"
        elif event.event_type == EventType.VOLUME_SPIKE:
            return f"Volume spike detected for market {event.market_id}"
        elif event.event_type == EventType.SYNC_COMPLETE:
            return f"Sync complete: {event.data.get('markets_fetched', 0)} markets fetched"
        else:
            return f"Event: {event.event_type.value} for market {event.market_id}"

    def get_event_types(self) -> set[EventType]:
        """Get event types this handler handles."""
        return {
            EventType.KEYWORD_MATCH,
            EventType.VOLUME_SPIKE,
            EventType.SYNC_COMPLETE,
            EventType.MARKET_NEW,
        }


def create_handler(
    handler_type: str,
    config: Dict[str, Any],
    db_manager: Optional[DatabaseManager] = None,
) -> BaseCallbackHandler:
    """Create a handler by type.

    Args:
        handler_type: Handler type (console, database, webhook, etc.).
        config: Handler configuration.
        db_manager: Database manager (if needed).

    Returns:
        Handler instance.
    """
    handlers = {
        "console": lambda: ConsoleHandler(verbose=config.get("verbose", False)),
        "database": lambda: DatabaseHandler(db_manager),
        "webhook": lambda: WebhookHandler(
            webhook_url=config["url"],
            headers=config.get("headers"),
            timeout=config.get("timeout", 10.0),
        ),
        "volume_spike": lambda: VolumeSpikeHandler(
            spike_threshold=config.get("spike_threshold", 2.0),
            min_volume=config.get("min_volume", 1000),
        ),
        "notification": lambda: NotificationHandler(
            channels=config.get("channels", ["console"]),
        ),
    }

    factory = handlers.get(handler_type)
    if not factory:
        raise ValueError(f"Unknown handler type: {handler_type}")

    return factory()


class HandlerManager:
    """Manages multiple callback handlers."""

    def __init__(self, event_bus: EventBus):
        """Initialize the handler manager.

        Args:
            event_bus: Event bus to attach handlers to.
        """
        self.event_bus = event_bus
        self._handlers: List[BaseCallbackHandler] = []

    def add_handler(self, handler: BaseCallbackHandler) -> None:
        """Add a handler to the manager.

        Args:
            handler: Handler to add.
        """
        self._handlers.append(handler)
        for event_type in handler.get_event_types():
            self.event_bus.subscribe(event_type, handler.handle)

    def add_handlers_from_config(
        self,
        configs: List[Dict[str, Any]],
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        """Add handlers from configuration.

        Args:
            configs: List of handler configurations.
            db_manager: Database manager.
        """
        for config in configs:
            if not config.get("enabled", True):
                continue

            handler_type = config.get("type")
            if handler_type:
                try:
                    handler = create_handler(handler_type, config, db_manager)
                    self.add_handler(handler)
                except Exception as e:
                    logger.error(f"Failed to create handler {handler_type}: {e}")

    def get_handlers(self) -> List[BaseCallbackHandler]:
        """Get all registered handlers.

        Returns:
            List of handlers.
        """
        return self._handlers
