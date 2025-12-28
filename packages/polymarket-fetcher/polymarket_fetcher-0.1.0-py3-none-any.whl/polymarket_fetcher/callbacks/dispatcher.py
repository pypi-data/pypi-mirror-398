"""Event dispatcher for callbacks."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from .models import EventType, MarketEvent, SyncEvent

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Event subscription."""

    event_type: EventType
    handler: Callable[..., Awaitable[None]]
    priority: int = 0
    filters: Optional[Dict[str, Any]] = None


class EventBus:
    """Event bus for publishing and subscribing to events.

    Implements a publish-subscribe pattern with support for
    async handlers, priorities, and filtering.
    """

    def __init__(self, async_dispatch: bool = True):
        """Initialize the event bus.

        Args:
            async_dispatch: Whether to dispatch events asynchronously.
        """
        self._subscriptions: Dict[EventType, List[Subscription]] = {}
        self._middleware: List[Callable] = []
        self._async_dispatch = async_dispatch
        self._stats: Dict[str, int] = {}

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[..., Awaitable[None]],
        priority: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Subscription:
        """Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to.
            handler: Async handler function.
            priority: Handler priority (higher = called first).
            filters: Optional filters for the event.

        Returns:
            Subscription instance.
        """
        subscription = Subscription(
            event_type=event_type,
            handler=handler,
            priority=priority,
            filters=filters,
        )

        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        self._subscriptions[event_type].append(subscription)

        # Sort by priority (descending)
        self._subscriptions[event_type].sort(
            key=lambda s: s.priority, reverse=True
        )

        logger.debug(f"Subscribed to {event_type.value} with priority {priority}")
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from an event.

        Args:
            subscription: Subscription to remove.
        """
        if subscription.event_type in self._subscriptions:
            try:
                self._subscriptions[subscription.event_type].remove(subscription)
                logger.debug(f"Unsubscribed from {subscription.event_type.value}")
            except ValueError:
                pass

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the event bus.

        Args:
            middleware: Middleware function.
        """
        self._middleware.append(middleware)

    async def publish(
        self,
        event: MarketEvent,
    ) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish.
        """
        event_type = event.event_type
        subscriptions = self._subscriptions.get(event_type, [])

        if not subscriptions:
            return

        # Run middleware
        for middleware in self._middleware:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    await middleware(event)
                else:
                    middleware(event)
            except Exception as e:
                logger.error(f"Middleware error: {e}")

        # Dispatch to handlers
        if self._async_dispatch:
            await self._dispatch_async(event, subscriptions)
        else:
            await self._dispatch_sync(event, subscriptions)

        # Update stats
        self._stats[event_type.value] = self._stats.get(event_type.value, 0) + 1

    async def _dispatch_async(
        self,
        event: MarketEvent,
        subscriptions: List[Subscription],
    ) -> None:
        """Dispatch event asynchronously to all handlers.

        Args:
            event: Event to dispatch.
            subscriptions: List of subscriptions.
        """
        tasks = []
        for subscription in subscriptions:
            if self._matches_filters(event, subscription.filters):
                task = asyncio.create_task(subscription.handler(event))
                tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _dispatch_sync(
        self,
        event: MarketEvent,
        subscriptions: List[Subscription],
    ) -> None:
        """Dispatch event synchronously to all handlers.

        Args:
            event: Event to dispatch.
            subscriptions: List of subscriptions.
        """
        for subscription in subscriptions:
            if self._matches_filters(event, subscription.filters):
                try:
                    await subscription.handler(event)
                except Exception as e:
                    logger.error(f"Handler error: {e}")

    def _matches_filters(
        self,
        event: MarketEvent,
        filters: Optional[Dict[str, Any]],
    ) -> bool:
        """Check if event matches filters.

        Args:
            event: Event to check.
            filters: Filter conditions.

        Returns:
            True if event matches filters.
        """
        if not filters:
            return True

        for key, expected in filters.items():
            actual = getattr(event, key, None)
            if actual != expected:
                return False

        return True

    async def publish_sync_complete(self, sync_event: SyncEvent) -> None:
        """Publish a sync complete event.

        Args:
            sync_event: Sync event data.
        """
        event = MarketEvent(
            event_type=EventType.SYNC_COMPLETE,
            market_id="",
            data=sync_event.to_dict(),
        )
        await self.publish(event)

    async def publish_keyword_match(
        self,
        market_id: str,
        question: str,
        match_result: Dict[str, Any],
    ) -> None:
        """Publish a keyword match event.

        Args:
            market_id: Market ID.
            question: Market question.
            match_result: Match result data.
        """
        event = MarketEvent(
            event_type=EventType.KEYWORD_MATCH,
            market_id=market_id,
            data={
                "question": question,
                "match_result": match_result,
            },
        )
        await self.publish(event)

    async def publish_market_new(self, market_data: Dict[str, Any]) -> None:
        """Publish a new market event.

        Args:
            market_data: Market data.
        """
        event = MarketEvent(
            event_type=EventType.MARKET_NEW,
            market_id=market_data.get("id", ""),
            data=market_data,
        )
        await self.publish(event)

    async def publish_market_updated(
        self,
        market_id: str,
        changes: List[Dict[str, Any]],
    ) -> None:
        """Publish a market updated event.

        Args:
            market_id: Market ID.
            changes: List of changes.
        """
        event = MarketEvent(
            event_type=EventType.MARKET_UPDATED,
            market_id=market_id,
            data={"changes": changes},
        )
        await self.publish(event)

    async def publish_fetch_error(self, error: str) -> None:
        """Publish a fetch error event.

        Args:
            error: Error message.
        """
        event = MarketEvent(
            event_type=EventType.FETCH_ERROR,
            market_id="",
            data={"error": error},
        )
        await self.publish(event)

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Dictionary with statistics.
        """
        total = sum(self._stats.values())
        return {
            "total_events": total,
            "by_type": dict(self._stats),
            "subscription_count": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
        }


class EventDispatcher(EventBus):
    """Convenience wrapper for EventBus.

    Provides helper methods for common dispatching scenarios.
    """

    def __init__(self, async_dispatch: bool = True):
        """Initialize the event dispatcher.

        Args:
            async_dispatch: Whether to dispatch asynchronously.
        """
        super().__init__(async_dispatch)
        self._handlers: List[Callable] = []

    def add_handler(self, handler: Callable) -> None:
        """Add a general event handler.

        Args:
            handler: Handler function.
        """
        self._handlers.append(handler)

    async def dispatch(self, event: MarketEvent) -> None:
        """Dispatch an event.

        Args:
            event: Event to dispatch.
        """
        await self.publish(event)

        # Also call general handlers
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error: {e}")
