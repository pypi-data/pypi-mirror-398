"""Market data fetcher for Polymarket."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..api import GammaAPIClient, create_api_client, ProxyConfig
from ..config import FetcherConfig, KeywordsConfig, load_config, RuntimeConfig
from ..matcher import KeywordMatcher, MatchResult
from ..storage import AsyncDatabaseManager, MarketRepository
from .incremental import ChangeInfo, IncrementalUpdater
from .scheduler import FetchScheduler

logger = logging.getLogger(__name__)


class MarketFetcher:
    """Main market data fetcher for Polymarket.

    Combines API fetching, database storage, keyword matching,
    and event callbacks into a unified interface.
    """

    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        keywords_path: Optional[str] = None,
        base_path: Optional[Path] = None,
        api_client: Optional[GammaAPIClient] = None,
        db_manager: Optional[AsyncDatabaseManager] = None,
    ):
        """Initialize the market fetcher.

        Args:
            config_path: Path to settings.yaml.
            keywords_path: Path to keywords.yaml.
            base_path: Base path for relative paths.
            api_client: Optional pre-configured API client.
            db_manager: Optional pre-configured database manager.
        """
        self.base_path = base_path or Path.cwd()

        # Load configurations
        settings_path = self.base_path / config_path
        self.fetcher_config, self.keywords_config = load_config(
            settings_path,
            keywords_path and (self.base_path / keywords_path),
        )

        # Create runtime config
        self.runtime_config = RuntimeConfig(
            fetcher_config=self.fetcher_config,
            keywords_config=self.keywords_config,
            base_path=self.base_path,
        )

        # Initialize components
        self._api_client = api_client
        self._db_manager = db_manager
        self._matcher: Optional[KeywordMatcher] = None
        self._updater: Optional[IncrementalUpdater] = None
        self._scheduler: Optional[FetchScheduler] = None

        # State
        self._running = False
        self._last_fetch: Optional[datetime] = None
        self._total_fetched = 0
        self._total_matches = 0

        # Event callbacks
        self._event_handlers: Dict[str, List[callable]] = {}

    @property
    def api_client(self) -> GammaAPIClient:
        """Get or create the API client."""
        if self._api_client is None:
            # Create proxy config from settings
            proxy_config = None
            api_proxy = self.fetcher_config.api.proxy
            if api_proxy.is_enabled:
                proxy_config = ProxyConfig(
                    proxy_type=api_proxy.type,
                    proxy_url=api_proxy.url,
                    proxy_username=api_proxy.username,
                    proxy_password=api_proxy.password,
                )

            self._api_client = GammaAPIClient(
                base_url=self.fetcher_config.api.base_url,
                timeout=float(self.fetcher_config.api.timeout),
                proxy_config=proxy_config,
            )
        return self._api_client

    @property
    def db_manager(self) -> AsyncDatabaseManager:
        """Get or create the database manager."""
        if self._db_manager is None:
            self._db_manager = AsyncDatabaseManager(
                db_path=str(self.runtime_config.db_path),
                pool_size=self.fetcher_config.database.pool_size,
            )
        return self._db_manager

    @property
    def matcher(self) -> KeywordMatcher:
        """Get the keyword matcher."""
        if self._matcher is None:
            self._matcher = KeywordMatcher(self.keywords_config)
        return self._matcher

    @property
    def updater(self) -> IncrementalUpdater:
        """Get the incremental updater."""
        if self._updater is None:
            self._updater = IncrementalUpdater(
                self.db_manager,
                self.fetcher_config,
            )
        return self._updater

    @property
    def scheduler(self) -> FetchScheduler:
        """Get the scheduler."""
        if self._scheduler is None:
            self._scheduler = FetchScheduler(
                self.fetcher_config,
                timezone=self.fetcher_config.scheduler.timezone,
            )
        return self._scheduler

    async def connect(self) -> None:
        """Connect to API and database."""
        await self.api_client.connect()
        self.db_manager.create_tables()
        await self.updater.initialize()
        logger.info("MarketFetcher connected")

    async def disconnect(self) -> None:
        """Disconnect from API and database."""
        if self._api_client:
            await self._api_client.disconnect()
        if self._scheduler and self._scheduler.is_running:
            self._scheduler.stop()
        if self._db_manager:
            await self._db_manager.close()
        logger.info("MarketFetcher disconnected")

    async def fetch_all_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: Optional[bool] = True,
        closed: Optional[bool] = False,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        exclude_tag_id: Optional[str] = None,
        related_tags: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch all markets from the API with optional filtering.

        Args:
            limit: Maximum number of markets to fetch.
            offset: Number of markets to skip.
            active: Filter by active status.
            closed: Filter by closed status (default: False to exclude closed markets).
            category: Filter by category name (fuzzy match, case-insensitive).
            tags: Filter by tag ID(s).
            exclude_tag_id: Exclude markets with this tag ID.
            related_tags: Include markets with related tags.

        Returns:
            List of market data dictionaries.
        """
        try:
            response = await self.api_client.list_markets(
                limit=limit,
                offset=offset,
                active=active,
                closed=closed,
                category=category,
                tag_id=tags[0] if tags else None,
                exclude_tag_id=exclude_tag_id,
                related_tags=related_tags,
            )
            markets = response.get("markets", [])
            filter_type = category or (f"tags:{','.join(tags)}" if tags else "all")
            logger.info(f"Fetched {len(markets)} markets (offset={offset}, filter={filter_type})")
            return markets
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            return []

    async def fetch_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific market by ID.

        Args:
            market_id: Market ID.

        Returns:
            Market data dictionary or None.
        """
        try:
            return await self.api_client.get_market(market_id)
        except Exception as e:
            logger.error(f"Failed to fetch market {market_id}: {e}")
            return None

    async def sync_once(
        self,
        limit: int = 100,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Perform a single sync operation.

        Args:
            limit: Maximum markets to fetch per request.
            save_history: Whether to save history snapshots.

        Returns:
            Sync result statistics.
        """
        start_time = datetime.utcnow()
        all_changes: List[ChangeInfo] = []
        matched_markets: List[Dict[str, Any]] = []

        try:
            # Check if topic filtering is enabled
            topic_config = self.fetcher_config.topic_filters
            if topic_config.enabled:
                # Use topic-based filtering
                logger.info(f"Using topic filter: category={topic_config.category}, tags={topic_config.tags}")

                result = await self.sync_by_topic(
                    category=topic_config.category or None,
                    tags=topic_config.tags or None,
                    limit=topic_config.limit,
                    save_history=save_history,
                )

                # Add topic filter info to result
                result["topic_filter"] = {
                    "category": topic_config.category,
                    "tags": topic_config.tags,
                    "enabled": True,
                }

                self._last_fetch = start_time
                return result
            else:
                # Fetch all active markets without topic filtering
                markets_data = await self.fetch_all_markets(limit=limit, active=True)

                if not markets_data:
                    logger.warning("No markets fetched")
                    return {
                        "success": False,
                        "error": "No markets fetched",
                        "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    }

                # Apply filters
                filtered_markets = self.updater.apply_filters(markets_data)

                # Match keywords
                for market in filtered_markets:
                    match_result = self.matcher.match_market_data(market)
                    if match_result.matched:
                        market["_match_result"] = match_result.to_dict()
                        matched_markets.append(market)
                        self._total_matches += 1

                # Perform incremental update
                changes = await self.updater.update(filtered_markets, save_history=save_history)
                all_changes.extend(changes)

                # Calculate stats
                new_count = sum(1 for c in changes if c.is_new)
                updated_count = len(changes) - new_count

                result = {
                    "success": True,
                    "markets_fetched": len(markets_data),
                    "markets_filtered": len(filtered_markets),
                    "markets_matched": len(matched_markets),
                    "changes_detected": len(changes),
                    "new_markets": new_count,
                    "updated_markets": updated_count,
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "timestamp": start_time.isoformat(),
                    "topic_filter": {"enabled": False},
                }

                self._last_fetch = start_time
                self._total_fetched += len(markets_data)

                # Emit sync complete event
                await self._emit_event("sync.complete", result)

                # Emit keyword match events
                for market in matched_markets:
                    await self._emit_event(
                        "keyword.match",
                        {
                            "market_id": market["id"],
                            "question": market.get("question"),
                            "match_result": market.get("_match_result"),
                        },
                    )

                logger.info(f"Sync completed: {result}")
                return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            await self._emit_event("sync.error", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }

    def start(self, background: bool = True) -> None:
        """Start the periodic sync scheduler.

        Args:
            background: Whether to run in background.
        """
        if self._running:
            logger.warning("Fetcher is already running")
            return

        interval = self.fetcher_config.scheduler.market_fetch_interval

        # Add sync job
        self.scheduler.add_job(
            self._sync_job,
            seconds=interval,
            id="market_sync",
            name="Market Data Sync",
        )

        if background:
            self.scheduler.start()
        else:
            # Run in current event loop
            self._running = True

        self._running = True
        logger.info(f"MarketFetcher started (interval={interval}s)")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.is_running:
            self.scheduler.stop()
        self._running = False
        logger.info("MarketFetcher stopped")

    async def _sync_job(self) -> None:
        """Internal sync job for the scheduler."""
        await self.sync_once()

    def on_event(self, event_type: str, handler: callable) -> None:
        """Register an event handler.

        Args:
            event_type: Event type (e.g., "sync.complete", "keyword.match").
            handler: Handler function.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all handlers.

        Args:
            event_type: Event type.
            data: Event data.
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "running": self._running,
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
            "total_fetched": self._total_fetched,
            "total_matches": self._total_matches,
            "known_markets": self.updater.get_stats(),
            "scheduler_jobs": self.scheduler.get_jobs() if self._scheduler else [],
        }

    async def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get a market from the database.

        Args:
            market_id: Market ID.

        Returns:
            Market data or None.
        """
        async with self.db_manager.session() as session:
            repo = MarketRepository(session)
            market = await repo.get_by_id(market_id)
            if market:
                return self._market_to_dict(market)
            return None

    async def search_markets(
        self,
        query: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search markets by keyword.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching markets.
        """
        async with self.db_manager.session() as session:
            repo = MarketRepository(session)
            markets = await repo.search(query, limit=limit)
            return [self._market_to_dict(m) for m in markets]

    async def get_top_markets(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top markets by volume.

        Args:
            limit: Number of markets.

        Returns:
            List of top markets.
        """
        async with self.db_manager.session() as session:
            repo = MarketRepository(session)
            markets = await repo.get_top_by_volume(limit=limit)
            return [self._market_to_dict(m) for m in markets]

    async def fetch_markets_by_category(
        self,
        category: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch markets by category name.

        Args:
            category: Category name (e.g., "Crypto", "Politics", "Sports").
                     Uses fuzzy matching, case-insensitive.
            limit: Maximum number of markets to fetch.

        Returns:
            List of market data dictionaries.
        """
        markets = await self.fetch_all_markets(
            category=category,
            active=True,
            limit=limit,
        )
        logger.info(f"Fetched {len(markets)} markets for category '{category}'")
        return markets

    async def fetch_markets_by_tags(
        self,
        tags: List[str],
        related_tags: bool = False,
        exclude_tag_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch markets by tag ID(s).

        Args:
            tags: List of tag ID(s).
            related_tags: Include markets with related tags.
            exclude_tag_id: Exclude markets with this tag ID.
            limit: Maximum number of markets to fetch.

        Returns:
            List of market data dictionaries.
        """
        markets = await self.fetch_all_markets(
            tags=tags,
            active=True,
            related_tags=related_tags,
            exclude_tag_id=exclude_tag_id,
            limit=limit,
        )
        logger.info(f"Fetched {len(markets)} markets for tags {tags}")
        return markets

    async def get_available_tags(self) -> List[Dict[str, Any]]:
        """Get all available tags from the API.

        Returns:
            List of tag dictionaries with id, label, slug, etc.
        """
        try:
            response = await self.api_client.list_tags()
            tags = response.get("tags", [])
            logger.info(f"Fetched {len(tags)} available tags")
            return tags
        except Exception as e:
            logger.error(f"Failed to fetch tags: {e}")
            return []

    async def get_sports_tags(self) -> Dict[str, Any]:
        """Get sports-related tag metadata.

        Returns detailed metadata for sports including tag IDs,
        images, resolution sources, and series information.

        Returns:
            Dictionary with sports metadata.
        """
        try:
            return await self.api_client.list_sports()
        except Exception as e:
            logger.error(f"Failed to fetch sports metadata: {e}")
            return {}

    async def sync_by_topic(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Sync markets by topic (category or tags).

        Args:
            category: Category name for filtering.
            tags: Tag ID(s) for filtering.
            limit: Maximum markets to fetch.
            save_history: Whether to save history snapshots.

        Returns:
            Sync result statistics.
        """
        if not category and not tags:
            raise ValueError("Must specify either 'category' or 'tags'")

        start_time = datetime.utcnow()

        # Fetch markets by topic
        if category:
            markets_data = await self.fetch_markets_by_category(category, limit)
        else:
            markets_data = await self.fetch_markets_by_tags(tags, limit=limit)

        if not markets_data:
            logger.warning("No markets fetched for topic")
            return {
                "success": False,
                "error": "No markets fetched",
                "topic": category or f"tags:{','.join(tags)}",
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
            }

        # Apply filters
        filtered_markets = self.updater.apply_filters(markets_data)

        # Match keywords
        matched_markets: List[Dict[str, Any]] = []
        for market in filtered_markets:
            match_result = self.matcher.match_market_data(market)
            if match_result.matched:
                market["_match_result"] = match_result.to_dict()
                matched_markets.append(market)

        # Perform incremental update
        changes = await self.updater.update(filtered_markets, save_history=save_history)

        # Calculate stats
        new_count = sum(1 for c in changes if c.is_new)
        updated_count = len(changes) - new_count

        result = {
            "success": True,
            "topic": category or f"tags:{','.join(tags)}",
            "markets_fetched": len(markets_data),
            "markets_filtered": len(filtered_markets),
            "markets_matched": len(matched_markets),
            "changes_detected": len(changes),
            "new_markets": new_count,
            "updated_markets": updated_count,
            "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
            "timestamp": start_time.isoformat(),
        }

        self._last_fetch = start_time
        self._total_fetched += len(markets_data)
        self._total_matches += len(matched_markets)

        # Emit sync complete event
        await self._emit_event("sync.complete", result)

        logger.info(f"Topic sync completed: {result}")
        return result

    def _market_to_dict(self, market) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary.

        Args:
            market: SQLAlchemy market model.

        Returns:
            Dictionary representation.
        """
        result = {}
        for column in market.__table__.columns:
            value = getattr(market, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    async def __aenter__(self) -> "MarketFetcher":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
