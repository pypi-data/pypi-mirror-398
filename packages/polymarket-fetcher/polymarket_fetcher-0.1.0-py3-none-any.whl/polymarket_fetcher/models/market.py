"""Market data models for Polymarket Fetcher."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from .sqlalchemy_types import JSONType


class MarketStatus(str, Enum):
    """Market status enum."""

    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Market(Base):
    """SQLAlchemy model for Polymarket markets."""

    __tablename__ = "markets"

    # Primary identifiers
    id = Column(String(64), primary_key=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Basic info
    question = Column(Text)
    description = Column(Text)

    # Volume and liquidity (core metrics)
    volume_num = Column(Float, default=0.0)
    volume_24hr = Column(Float, default=0.0)
    volume_1wk = Column(Float, default=0.0)
    volume_1mo = Column(Float, default=0.0)
    volume_1yr = Column(Float, default=0.0)
    volume_24hr_amm = Column(Float, default=0.0)
    volume_24hr_clob = Column(Float, default=0.0)

    liquidity_num = Column(Float, default=0.0)
    liquidity_amm = Column(Float, default=0.0)
    liquidity_clob = Column(Float, default=0.0)

    # Price information
    last_trade_price = Column(Float)
    best_bid = Column(Float)
    best_ask = Column(Float)

    # Status fields
    active = Column(Boolean, default=True, index=True)
    closed = Column(Boolean, default=False, index=True)
    archived = Column(Boolean, default=False, index=True)
    accepting_orders = Column(Boolean, default=True)

    # Time fields
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    start_date_iso = Column(DateTime)
    end_date_iso = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, index=True)
    closed_time = Column(DateTime)

    # JSON fields for complex data
    outcomes = Column(JSONType)
    outcome_prices = Column(JSONType)
    categories = Column(JSONType)
    tags = Column(JSONType)
    events = Column(JSONType)
    collections = Column(JSONType)
    clob_token_ids = Column(JSONType)

    # Creator info
    creator = Column(String(64))
    fee = Column(Float)

    # Media
    image = Column(String(512))
    icon = Column(String(512))
    twitter_card_image = Column(String(512))

    # Additional fields
    condition_id = Column(String(64))
    market_maker_address = Column(String(128))
    resolution_source = Column(String(512))
    resolved_by = Column(String(128))
    category = Column(String(128))

    # UMA related
    uma_end_date = Column(DateTime)
    uma_end_date_iso = Column(DateTime)
    uma_resolution_status = Column(String(64))
    uma_bond = Column(String(64))
    uma_reward = Column(String(64))

    # Sports related
    team_a_id = Column(String(64))
    team_b_id = Column(String(64))
    game_id = Column(String(64))
    game_start_time = Column(DateTime)
    sports_market_type = Column(String(64))
    line = Column(Float)

    # Price changes
    one_day_price_change = Column(Float)
    one_hour_price_change = Column(Float)
    one_week_price_change = Column(Float)
    one_month_price_change = Column(Float)
    one_year_price_change = Column(Float)

    # Misc
    score = Column(Float)
    spread = Column(Float)
    custom_liveness = Column(Integer)
    order_min_size = Column(Float)
    order_price_min_tick_size = Column(Float)

    # Timestamps
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    history = relationship(
        "MarketHistory",
        back_populates="market",
        lazy="dynamic",
    )

    # Indexes
    __table_args__ = (
        Index("idx_markets_volume", "volume_num"),
        Index("idx_markets_active_status", "active", "closed", "archived"),
        Index("idx_markets_question", "question"),
    )


class MarketHistory(Base):
    """SQLAlchemy model for market history snapshots."""

    __tablename__ = "market_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market_id = Column(
        String(64),
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
    )
    snapshot_at = Column(DateTime, nullable=False)

    # Snapshot metrics
    volume_num = Column(Float)
    volume_24hr = Column(Float)
    liquidity_num = Column(Float)
    last_trade_price = Column(Float)
    best_bid = Column(Float)
    best_ask = Column(Float)

    # Complete snapshot data
    raw_data = Column(Text, nullable=False)

    # Relationships
    market = relationship("Market", back_populates="history")

    # Constraints
    __table_args__ = (
        UniqueConstraint("market_id", "snapshot_at", name="uq_market_snapshot"),
        Index("idx_history_market_time", "market_id", "snapshot_at"),
    )


class KeywordConfig(Base):
    """SQLAlchemy model for keyword configurations."""

    __tablename__ = "keyword_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    keywords = Column(JSONType, nullable=False)  # List of patterns
    match_mode = Column(String(16), default="contains")
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class EventLog(Base):
    """SQLAlchemy model for event logs."""

    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    market_id = Column(String(64), index=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_event_logs_type_time", "event_type", "created_at"),
    )


# ============================================================================
# Pydantic Models for API/Serialization
# ============================================================================


class MarketBase(BaseModel):
    """Base Pydantic model for market data."""

    id: str
    slug: str
    question: Optional[str] = None
    description: Optional[str] = None

    # Volume
    volume_num: Optional[float] = None
    volume_24hr: Optional[float] = None
    volume_1wk: Optional[float] = None
    volume_1mo: Optional[float] = None
    volume_1yr: Optional[float] = None

    # Liquidity
    liquidity_num: Optional[float] = None
    liquidity_amm: Optional[float] = None
    liquidity_clob: Optional[float] = None

    # Price
    last_trade_price: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None

    # Status
    active: Optional[bool] = None
    closed: Optional[bool] = None
    archived: Optional[bool] = None
    accepting_orders: Optional[bool] = None

    # Time
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_date_iso: Optional[str] = None
    end_date_iso: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_time: Optional[str] = None

    # JSON fields
    outcomes: Optional[Any] = None
    outcome_prices: Optional[Any] = None
    categories: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    events: Optional[List[Dict[str, Any]]] = None
    clob_token_ids: Optional[List[str]] = None

    # Media
    image: Optional[str] = None
    icon: Optional[str] = None

    # Additional
    resolution_source: Optional[str] = None
    category: Optional[str] = None
    creator: Optional[str] = None

    class Config:
        populate_by_name = True


class MarketCreate(MarketBase):
    """Pydantic model for creating a market."""

    pass


class MarketUpdate(BaseModel):
    """Pydantic model for updating a market."""

    question: Optional[str] = None
    description: Optional[str] = None
    volume_num: Optional[float] = None
    volume_24hr: Optional[float] = None
    liquidity_num: Optional[float] = None
    last_trade_price: Optional[float] = None
    active: Optional[bool] = None
    closed: Optional[bool] = None
    archived: Optional[bool] = None
    updated_at: Optional[str] = None

    class Config:
        populate_by_name = True


class MarketSchema(MarketBase):
    """Complete Pydantic model for market data."""

    # Include all fields from base
    condition_id: Optional[str] = None
    market_maker_address: Optional[str] = None
    resolved_by: Optional[str] = None
    fee: Optional[float] = None

    # Price changes
    one_day_price_change: Optional[float] = None
    one_hour_price_change: Optional[float] = None
    one_week_price_change: Optional[float] = None
    one_month_price_change: Optional[float] = None
    one_year_price_change: Optional[float] = None

    # Sports
    team_a_id: Optional[str] = None
    team_b_id: Optional[str] = None
    game_id: Optional[str] = None
    game_start_time: Optional[str] = None
    sports_market_type: Optional[str] = None
    line: Optional[float] = None

    # UMA
    uma_end_date: Optional[str] = None
    uma_end_date_iso: Optional[str] = None
    uma_resolution_status: Optional[str] = None
    uma_bond: Optional[str] = None
    uma_reward: Optional[str] = None

    # Misc
    score: Optional[float] = None
    spread: Optional[float] = None
    custom_liveness: Optional[int] = None
    order_min_size: Optional[float] = None
    order_price_min_tick_size: Optional[float] = None

    class Config:
        populate_by_name = True


class MarketHistorySnapshot(BaseModel):
    """Pydantic model for market history snapshot."""

    market_id: str
    snapshot_at: datetime
    volume_num: Optional[float] = None
    volume_24hr: Optional[float] = None
    liquidity_num: Optional[float] = None
    last_trade_price: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None
    raw_data: Dict[str, Any]


class KeywordGroup(BaseModel):
    """Pydantic model for keyword group."""

    name: str
    patterns: List[str]
    match_mode: str = "contains"
    enabled: bool = True
    priority: int = 0


class ExcludeRule(BaseModel):
    """Pydantic model for exclude rule."""

    pattern: str
    reason: str = ""
