"""Custom SQLAlchemy types for Polymarket Fetcher."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, TypeDecorator, Text, text
from sqlalchemy.engine import Engine


class JSONType(TypeDecorator):
    """SQLAlchemy type for storing JSON data as text.

    Serializes to JSON string for storage and deserializes back to Python objects.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """Convert Python object to JSON string for storage.

        Args:
            value: Python object to serialize.
            dialect: SQLAlchemy dialect.

        Returns:
            JSON string or None.
        """
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: str | None, dialect: Any) -> Any:
        """Convert JSON string back to Python object.

        Args:
            value: JSON string from storage.
            dialect: SQLAlchemy dialect.

        Returns:
            Python object or None.
        """
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class DateTimeType(DateTime):
    """Extended DateTime type with timezone support.

    Stores datetime values and handles timezone-aware datetimes.
    """

    def __init__(self, default_tz: str = "UTC", **kwargs):
        """Initialize the DateTime type.

        Args:
            default_tz: Default timezone for naive datetimes.
            **kwargs: Additional arguments for DateTime.
        """
        super().__init__(**kwargs)
        self.default_tz = default_tz

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        """Process datetime values from the database.

        Args:
            value: Datetime value from storage.
            dialect: SQLAlchemy dialect.

        Returns:
            Datetime with timezone info.
        """
        if value is None:
            return None
        return value


def create_indexes(engine: Engine) -> None:
    """Create all custom indexes for the database.

    Args:
        engine: SQLAlchemy engine.
    """
    with engine.connect() as conn:
        # Market indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_volume
            ON markets(volume_num DESC)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_active
            ON markets(active, closed, archived)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_updated_at
            ON markets(updated_at)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_slug
            ON markets(slug)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_question
            ON markets(question)
        """))

        # Market history indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_history_market_time
            ON market_history(market_id, snapshot_at)
        """))

        # Event log indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_event_logs_type_time
            ON event_logs(event_type, created_at)
        """))

        conn.commit()
