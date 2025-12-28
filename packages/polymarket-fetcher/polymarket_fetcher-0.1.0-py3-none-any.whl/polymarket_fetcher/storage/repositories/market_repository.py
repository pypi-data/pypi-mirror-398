"""Market repository for database operations."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.market import Market, MarketHistory, MarketBase


class MarketRepository:
    """Repository for market database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: Async database session.
        """
        self.session = session

    async def get_by_id(self, market_id: str) -> Optional[Market]:
        """Get a market by ID.

        Args:
            market_id: Market ID.

        Returns:
            Market instance or None.
        """
        result = await self.session.execute(
            select(Market).where(Market.id == market_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Market]:
        """Get a market by slug.

        Args:
            slug: Market slug.

        Returns:
            Market instance or None.
        """
        result = await self.session.execute(
            select(Market).where(Market.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        active: Optional[bool] = None,
        min_volume: Optional[float] = None,
        min_liquidity: Optional[float] = None,
    ) -> List[Market]:
        """Get all markets with optional filtering.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            active: Filter by active status.
            min_volume: Minimum volume.
            min_liquidity: Minimum liquidity.

        Returns:
            List of Market instances.
        """
        query = select(Market)

        conditions = []
        if active is not None:
            conditions.append(Market.active == active)
        if min_volume is not None:
            conditions.append(Market.volume_num >= min_volume)
        if min_liquidity is not None:
            conditions.append(Market.liquidity_num >= min_liquidity)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(Market.volume_num)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_updated_since(self, since: datetime) -> List[Market]:
        """Get markets updated since a given time.

        Args:
            since: Datetime to check from.

        Returns:
            List of Market instances.
        """
        result = await self.session.execute(
            select(Market)
            .where(Market.updated_at >= since)
            .order_by(desc(Market.updated_at))
        )
        return list(result.scalars().all())

    async def get_new_markets(
        self,
        since: datetime,
        existing_ids: Optional[set] = None,
    ) -> List[Market]:
        """Get new markets (created since a given time).

        Args:
            since: Datetime to check from.
            existing_ids: Set of existing market IDs to exclude.

        Returns:
            List of new Market instances.
        """
        result = await self.session.execute(
            select(Market)
            .where(Market.created_at >= since)
            .order_by(desc(Market.created_at))
        )
        markets = list(result.scalars().all())

        if existing_ids:
            markets = [m for m in markets if m.id not in existing_ids]

        return markets

    async def upsert(self, market_data: Dict[str, Any]) -> Market:
        """Insert or update a market.

        Args:
            market_data: Market data dictionary.

        Returns:
            Updated Market instance.
        """
        market_id = market_data.get("id")
        if not market_id:
            raise ValueError("Market data must have an 'id' field")

        # Get valid column names from Market model
        valid_columns = {column.name for column in Market.__table__.columns}

        # Filter out invalid fields
        filtered_data = {k: v for k, v in market_data.items() if k in valid_columns}

        # Check if market exists
        result = await self.session.execute(
            select(Market).where(Market.id == market_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing market
            for key, value in filtered_data.items():
                if hasattr(existing, key) and key != "id":
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            # Create new market
            market = Market(**filtered_data)
            self.session.add(market)
            return market

    async def upsert_many(self, markets_data: List[Dict[str, Any]]) -> List[Market]:
        """Insert or update multiple markets.

        Args:
            markets_data: List of market data dictionaries.

        Returns:
            List of Market instances.
        """
        markets = []
        for market_data in markets_data:
            market = await self.upsert(market_data)
            markets.append(market)
        return markets

    async def save_history(
        self,
        market_id: str,
        snapshot_data: Dict[str, Any],
    ) -> MarketHistory:
        """Save a market history snapshot.

        Args:
            market_id: Market ID.
            snapshot_data: Snapshot data dictionary.

        Returns:
            MarketHistory instance.
        """
        history = MarketHistory(
            market_id=market_id,
            snapshot_at=datetime.utcnow(),
            raw_data=json.dumps(snapshot_data),
            volume_num=snapshot_data.get("volume_num"),
            liquidity_num=snapshot_data.get("liquidity_num"),
            last_trade_price=snapshot_data.get("last_trade_price"),
        )
        self.session.add(history)
        return history

    async def get_history(
        self,
        market_id: str,
        limit: int = 100,
    ) -> List[MarketHistory]:
        """Get market history.

        Args:
            market_id: Market ID.
            limit: Maximum number of results.

        Returns:
            List of MarketHistory instances.
        """
        result = await self.session.execute(
            select(MarketHistory)
            .where(MarketHistory.market_id == market_id)
            .order_by(desc(MarketHistory.snapshot_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, active: Optional[bool] = None) -> int:
        """Count markets.

        Args:
            active: Filter by active status.

        Returns:
            Number of markets.
        """
        query = select(Market)
        if active is not None:
            query = query.where(Market.active == active)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def delete(self, market_id: str) -> bool:
        """Delete a market.

        Args:
            market_id: Market ID.

        Returns:
            True if deleted, False if not found.
        """
        market = await self.get_by_id(market_id)
        if market:
            await self.session.delete(market)
            return True
        return False

    async def search(
        self,
        query: str,
        limit: int = 50,
    ) -> List[Market]:
        """Search markets by question or description.

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            List of matching Market instances.
        """
        search_pattern = f"%{query}%"
        result = await self.session.execute(
            select(Market)
            .where(
                (Market.question.ilike(search_pattern)) |
                (Market.description.ilike(search_pattern))
            )
            .order_by(desc(Market.volume_num))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_keywords(
        self,
        keywords: List[str],
        match_mode: str = "contains",
        limit: int = 100,
    ) -> List[Market]:
        """Get markets matching keywords.

        Args:
            keywords: List of keywords to match.
            match_mode: Match mode (contains, regex).
            limit: Maximum number of results.

        Returns:
            List of matching Market instances.
        """
        if match_mode == "regex":
            # Use regex matching
            conditions = []
            for keyword in keywords:
                conditions.append(Market.question.regexp_match(keyword))
            query = select(Market).where(and_(*conditions))
        else:
            # Default to contains (ilike)
            conditions = []
            for keyword in keywords:
                search_pattern = f"%{keyword}%"
                conditions.append(Market.question.ilike(search_pattern))
            query = select(Market).where(and_(*conditions))

        query = query.order_by(desc(Market.volume_num)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_top_by_volume(
        self,
        limit: int = 10,
        active: bool = True,
    ) -> List[Market]:
        """Get top markets by volume.

        Args:
            limit: Number of markets to return.
            active: Only active markets.

        Returns:
            List of Market instances.
        """
        conditions = [Market.volume_num.is_not(None)]
        if active:
            conditions.append(Market.active == True)

        result = await self.session.execute(
            select(Market)
            .where(and_(*conditions))
            .order_by(desc(Market.volume_num))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self) -> Dict[str, Any]:
        """Get market statistics.

        Returns:
            Dictionary with statistics.
        """
        total = await self.count()
        active = await self.count(active=True)

        result = await self.session.execute(
            select(
                Market.volume_num,
                Market.liquidity_num,
            ).where(Market.active == True)
        )
        rows = list(result.scalars().all())

        total_volume = sum(r.volume_num or 0 for r in rows)
        total_liquidity = sum(r.liquidity_num or 0 for r in rows)

        return {
            "total_markets": total,
            "active_markets": active,
            "closed_or_archived": total - active,
            "total_volume": total_volume,
            "total_liquidity": total_liquidity,
        }
