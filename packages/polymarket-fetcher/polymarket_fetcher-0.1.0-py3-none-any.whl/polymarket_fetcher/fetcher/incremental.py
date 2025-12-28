"""Incremental update logic for market data."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dateutil import parser as date_parser

from ..config import FetcherConfig, FiltersConfig
from ..matcher import KeywordMatcher
from ..storage import DatabaseManager, MarketRepository

logger = logging.getLogger(__name__)


@dataclass
class ChangeInfo:
    """Information about a market change."""

    market_id: str
    is_new: bool = False
    changed_fields: List[str] = None
    volume_change: float = 0.0
    liquidity_change: float = 0.0
    price_change: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.changed_fields is None:
            self.changed_fields = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "is_new": self.is_new,
            "changed_fields": self.changed_fields,
            "volume_change": self.volume_change,
            "liquidity_change": self.liquidity_change,
            "price_change": self.price_change,
            "timestamp": self.timestamp.isoformat(),
        }


class IncrementalUpdater:
    """Handles incremental updates of market data.

    Detects changes in market data and only updates what's necessary.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Optional[FetcherConfig] = None,
    ):
        """Initialize the incremental updater.

        Args:
            db_manager: Database manager.
            config: Fetcher configuration.
        """
        self.db_manager = db_manager
        self.config = config or FetcherConfig()
        self.filters = self.config.filters

        # Track last update times
        self._last_update: Optional[datetime] = None
        self._known_market_ids: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize by loading existing market IDs."""
        async with self.db_manager.session() as session:
            repo = MarketRepository(session)
            markets = await repo.get_all(limit=10000)
            self._known_market_ids = {m.id for m in markets}
        logger.info(f"Initialized with {len(self._known_market_ids)} known markets")

    def get_since(self) -> Optional[datetime]:
        """Get the last update timestamp.

        Returns:
            Last update timestamp or None.
        """
        return self._last_update

    def set_since(self, timestamp: datetime) -> None:
        """Set the last update timestamp.

        Args:
            timestamp: Timestamp to set.
        """
        self._last_update = timestamp

    async def detect_changes(
        self,
        markets_data: List[Dict[str, Any]],
    ) -> tuple[List[ChangeInfo], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Detect changes in market data.

        Args:
            markets_data: List of market data from API.

        Returns:
            Tuple of (changes, new_markets, updated_markets).
        """
        changes: List[ChangeInfo] = []
        new_markets: List[Dict[str, Any]] = []
        updated_markets: List[Dict[str, Any]] = []

        for market_data in markets_data:
            market_id = market_data.get("id")
            if not market_id:
                continue

            if market_id not in self._known_market_ids:
                # New market
                change = ChangeInfo(market_id=market_id, is_new=True)
                changes.append(change)
                new_markets.append(market_data)
                self._known_market_ids.add(market_id)
            else:
                # Check for updates - we'll do a detailed check in update
                updated_markets.append(market_data)

        return changes, new_markets, updated_markets

    async def update(
        self,
        markets_data: List[Dict[str, Any]],
        save_history: bool = True,
        matcher: Optional[KeywordMatcher] = None,
    ) -> List[ChangeInfo]:
        """Perform incremental update.

        Args:
            markets_data: List of market data from API.
            save_history: Whether to save history snapshots.
            matcher: Optional keyword matcher.

        Returns:
            List of detected changes.
        """
        changes: List[ChangeInfo] = []
        now = datetime.utcnow()

        # Normalize field names from camelCase to snake_case
        markets_data = self._normalize_market_data(markets_data)

        # Detect new/updated markets
        _, new_markets, updated_markets = await self.detect_changes(markets_data)

        # Process new markets
        async with self.db_manager.session() as session:
            repo = MarketRepository(session)

            for market_data in new_markets:
                try:
                    await repo.upsert(market_data)
                    change = ChangeInfo(
                        market_id=market_data["id"],
                        is_new=True,
                        changed_fields=["new_market"],
                    )
                    changes.append(change)
                    logger.debug(f"New market: {market_data.get('question', market_data.get('id'))}")
                except Exception as e:
                    logger.error(f"Failed to insert new market: {e}")

            # Process updated markets - detect changes
            for market_data in updated_markets:
                market_id = market_data.get("id")
                if not market_id:
                    continue

                try:
                    # Get existing market
                    existing = await repo.get_by_id(market_id)
                    if not existing:
                        continue

                    # Detect field changes
                    changed_fields = self._detect_field_changes(existing, market_data)

                    if changed_fields:
                        # Update market
                        await repo.upsert(market_data)

                        # Calculate metric changes
                        old_volume = existing.volume_num or 0
                        new_volume = market_data.get("volume_num") or 0
                        old_liquidity = existing.liquidity_num or 0
                        new_liquidity = market_data.get("liquidity_num") or 0
                        old_price = existing.last_trade_price or 0
                        new_price = market_data.get("last_trade_price") or 0

                        change = ChangeInfo(
                            market_id=market_id,
                            is_new=False,
                            changed_fields=changed_fields,
                            volume_change=new_volume - old_volume,
                            liquidity_change=new_liquidity - old_liquidity,
                            price_change=new_price - old_price,
                        )
                        changes.append(change)

                        # Save history snapshot
                        if save_history:
                            await repo.save_history(market_id, market_data)

                        logger.debug(f"Updated market: {market_data.get('question', market_id)}, changes: {changed_fields}")
                except Exception as e:
                    logger.error(f"Failed to update market {market_id}: {e}")

        self._last_update = now
        return changes

    def _detect_field_changes(
        self,
        existing: Any,
        new_data: Dict[str, Any],
    ) -> List[str]:
        """Detect which fields have changed.

        Args:
            existing: Existing market ORM object.
            new_data: New market data.

        Returns:
            List of changed field names.
        """
        changed = []
        key_fields = [
            "volume_num",
            "volume_24hr",
            "liquidity_num",
            "last_trade_price",
            "best_bid",
            "best_ask",
            "active",
            "closed",
            "archived",
            "question",
            "description",
        ]

        for field in key_fields:
            if field not in new_data:
                continue

            old_value = getattr(existing, field, None)
            new_value = new_data.get(field)

            # Handle None comparisons
            if old_value is None and new_value is None:
                continue
            if old_value is None or new_value is None:
                changed.append(field)
            elif old_value != new_value:
                changed.append(field)

        return changed

    def apply_filters(
        self,
        markets_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Apply filters to market data.

        Args:
            markets_data: List of market data.

        Returns:
            Filtered market data.
        """
        filtered = []

        for market in markets_data:
            # Skip if not active and we only want active
            if self.filters.only_active:
                if not market.get("active", True):
                    continue

            # Check volume
            volume = market.get("volume_num", 0) or 0
            if volume < self.filters.min_volume:
                continue

            # Check liquidity
            liquidity = market.get("liquidity_num", 0) or 0
            if liquidity < self.filters.min_liquidity:
                continue

            filtered.append(market)

        return filtered

    def _normalize_market_data(self, markets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize market data by converting camelCase to snake_case and parsing dates.

        Args:
            markets_data: List of market data dictionaries.

        Returns:
            Normalized market data list.
        """
        # Mapping from API field names to database field names
        field_mapping = {
            "conditionId": "condition_id",
            "marketMakerAddress": "market_maker_address",
            "resolutionSource": "resolution_source",
            "startDate": "start_date",
            "endDate": "end_date",
            "startDateIso": "start_date_iso",
            "endDateIso": "end_date_iso",
            "createdAt": "created_at",
            "updatedAt": "updated_at",
            "closedTime": "closed_time",
            "twitterCardImage": "twitter_card_image",
            "clobTokenIds": "clob_token_ids",
            "volumeNum": "volume_num",
            "volume24hr": "volume_24hr",
            "volume1wk": "volume_1wk",
            "volume1mo": "volume_1mo",
            "volume1yr": "volume_1yr",
            "volume24hrAmm": "volume_24hr_amm",
            "volume24hrClob": "volume_24hr_clob",
            "volume1wkAmm": "volume_1wk_amm",
            "volume1moAmm": "volume_1mo_amm",
            "volume1yrAmm": "volume_1yr_amm",
            "volume1wkClob": "volume_1wk_clob",
            "volume1moClob": "volume_1mo_clob",
            "volume1yrClob": "volume_1yr_clob",
            "liquidityNum": "liquidity_num",
            "liquidityAmm": "liquidity_amm",
            "liquidityClob": "liquidity_clob",
            "lastTradePrice": "last_trade_price",
            "bestBid": "best_bid",
            "bestAsk": "best_ask",
            "acceptingOrders": "accepting_orders",
            "mailchimpTag": "mailchimp_tag",
            "fpmmLive": "fpmm_live",
            "hasReviewedDates": "has_reviewed_dates",
            "readyForCron": "ready_for_cron",
            "umaEndDate": "uma_end_date",
            "umaEndDateIso": "uma_end_date_iso",
            "umaResolutionStatus": "uma_resolution_status",
            "umaBond": "uma_bond",
            "umaReward": "uma_reward",
            "sportsMarketType": "sports_market_type",
            "gameStartTime": "game_start_time",
            "oneDayPriceChange": "one_day_price_change",
            "oneHourPriceChange": "one_hour_price_change",
            "oneWeekPriceChange": "one_week_price_change",
            "oneMonthPriceChange": "one_month_price_change",
            "oneYearPriceChange": "one_year_price_change",
            "customLiveness": "custom_liveness",
            "orderMinSize": "order_min_size",
            "orderPriceMinTickSize": "order_price_min_tick_size",
        }

        # Fields that should be parsed as datetime
        datetime_fields = {
            "start_date", "end_date", "start_date_iso", "end_date_iso",
            "created_at", "updated_at", "closed_time",
            "uma_end_date", "uma_end_date_iso", "game_start_time",
            "indexed_at",
        }

        normalized = []
        for market in markets_data:
            normalized_market = {}
            for key, value in market.items():
                # Use mapped name or convert camelCase to snake_case
                new_key = field_mapping.get(key)
                if new_key is None:
                    # Convert camelCase to snake_case
                    import re
                    new_key = re.sub('([A-Z]+)', r'_\1', key).lower().lstrip('_')

                # Parse datetime strings
                if new_key in datetime_fields and value and isinstance(value, str):
                    try:
                        normalized_market[new_key] = date_parser.isoparse(value)
                    except (ValueError, TypeError):
                        # If parsing fails, skip this field
                        pass
                else:
                    normalized_market[new_key] = value
            normalized.append(normalized_market)

        return normalized

    def get_stats(self) -> Dict[str, Any]:
        """Get update statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "known_markets": len(self._known_market_ids),
            "last_update": self._last_update.isoformat() if self._last_update else None,
        }
