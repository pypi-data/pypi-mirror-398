#!/usr/bin/env python
"""Database initialization script for Polymarket Fetcher."""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text

from polymarket_fetcher.storage import DatabaseManager
from polymarket_fetcher.models.market import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database(db_path: str, drop_existing: bool = False) -> None:
    """Initialize the database.

    Args:
        db_path: Path to the database file.
        drop_existing: Whether to drop existing tables.
    """
    logger.info(f"Initializing database at: {db_path}")

    manager = DatabaseManager(db_path)

    if drop_existing:
        logger.warning("Dropping existing tables...")
        Base.metadata.drop_all(manager._sync_engine)

    logger.info("Creating tables...")
    Base.metadata.create_all(manager._sync_engine)

    # Create indexes
    logger.info("Creating indexes...")
    with manager._sync_engine.connect() as conn:
        # Markets indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_volume
            ON markets(volume_num DESC)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_markets_active_status
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

    logger.info("Database initialized successfully!")

    # Print summary
    with manager._sync_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM markets"))
        market_count = result.scalar()
        logger.info(f"Markets table: {market_count} records")

        result = conn.execute(text("SELECT COUNT(*) FROM market_history"))
        history_count = result.scalar()
        logger.info(f"Market history table: {history_count} records")

        result = conn.execute(text("SELECT COUNT(*) FROM event_logs"))
        event_count = result.scalar()
        logger.info(f"Event logs table: {event_count} records")


def drop_database(db_path: str) -> None:
    """Drop all tables in the database.

    Args:
        db_path: Path to the database file.
    """
    logger.info(f"Dropping database at: {db_path}")

    manager = DatabaseManager(db_path)
    Base.metadata.drop_all(manager._sync_engine)

    logger.info("Database dropped successfully!")


def vacuum_database(db_path: str) -> None:
    """Vacuum the database to reclaim space.

    Args:
        db_path: Path to the database file.
    """
    logger.info(f"Vacuuming database at: {db_path}")

    manager = DatabaseManager(db_path)
    manager.vacuum()

    logger.info("Database vacuumed successfully!")


def show_stats(db_path: str) -> None:
    """Show database statistics.

    Args:
        db_path: Path to the database file.
    """
    logger.info(f"Showing statistics for database at: {db_path}")

    manager = DatabaseManager(db_path)

    with manager._sync_engine.connect() as conn:
        # Markets stats
        result = conn.execute(text("SELECT COUNT(*) FROM markets"))
        total_markets = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM markets WHERE active = 1"))
        active_markets = result.scalar()

        result = conn.execute(text("SELECT SUM(volume_num) FROM markets"))
        total_volume = result.scalar() or 0

        result = conn.execute(text("SELECT SUM(liquidity_num) FROM markets"))
        total_liquidity = result.scalar() or 0

        result = conn.execute(text("SELECT MAX(updated_at) FROM markets"))
        last_updated = result.scalar()

        print("\n=== Database Statistics ===")
        print(f"Total markets: {total_markets}")
        print(f"Active markets: {active_markets}")
        print(f"Closed/Archived: {total_markets - active_markets}")
        print(f"Total volume: {total_volume:,.2f}")
        print(f"Total liquidity: {total_liquidity:,.2f}")
        print(f"Last updated: {last_updated}")

        # History stats
        result = conn.execute(text("SELECT COUNT(*) FROM market_history"))
        history_count = result.scalar()
        print(f"\nHistory snapshots: {history_count}")

        # Event logs stats
        result = conn.execute(text("SELECT COUNT(*) FROM event_logs"))
        event_count = result.scalar()
        print(f"Event logs: {event_count}")

        result = conn.execute(text("""
            SELECT event_type, COUNT(*) as count
            FROM event_logs
            GROUP BY event_type
        """))
        print("\nEvent types:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Database management for Polymarket Fetcher"
    )
    parser.add_argument(
        "--db-path",
        default="data/polymarket.db",
        help="Path to the database file",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Vacuum the database",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )

    args = parser.parse_args()

    if args.vacuum:
        vacuum_database(args.db_path)
    elif args.stats:
        show_stats(args.db_path)
    elif args.drop:
        response = input("Are you sure you want to drop all tables? [y/N]: ")
        if response.lower() == "y":
            drop_database(args.db_path)
        else:
            print("Cancelled.")
    else:
        init_database(args.db_path, drop_existing=args.drop)


if __name__ == "__main__":
    main()
