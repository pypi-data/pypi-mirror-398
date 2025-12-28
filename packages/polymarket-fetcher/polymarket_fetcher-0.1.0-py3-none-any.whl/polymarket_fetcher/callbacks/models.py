"""Event models for callbacks."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for market changes."""

    MARKET_NEW = "market.new"
    MARKET_UPDATED = "market.updated"
    MARKET_CLOSED = "market.closed"
    MARKET_ARCHIVED = "market.archived"
    VOLUME_SPIKE = "volume.spike"
    PRICE_CHANGE = "price.change"
    KEYWORD_MATCH = "keyword.match"
    FETCH_ERROR = "fetch.error"
    FETCH_WARNING = "fetch.warning"
    SYNC_COMPLETE = "sync.complete"
    SYNC_STARTED = "sync.started"


class MarketChange(BaseModel):
    """Information about a market field change."""

    market_id: str
    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    change_percent: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_percent": self.change_percent,
        }


class MarketEvent(BaseModel):
    """Market event for callbacks."""

    event_type: EventType
    market_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    changes: Optional[List[MarketChange]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "market_id": self.market_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "changes": [c.to_dict() for c in self.changes] if self.changes else None,
            "metadata": self.metadata,
        }


class SyncEvent(BaseModel):
    """Sync operation event."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    markets_fetched: int = 0
    markets_matched: int = 0
    changes_detected: int = 0
    new_markets: int = 0
    updated_markets: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "markets_fetched": self.markets_fetched,
            "markets_matched": self.markets_matched,
            "changes_detected": self.changes_detected,
            "new_markets": self.new_markets,
            "updated_markets": self.updated_markets,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }
