"""Polymarket Fetcher - A通用 Polymarket 赌盘数据获取模块.

Features:
- 定时抓取 Polymarket 赌盘数据
- 基于关键词/话题的灵活匹配
- SQLite 持久化存储
- 事件回调机制支持
- 可扩展的数据源和处理器
"""

__version__ = "0.1.0"

from .config import FetcherConfig, load_config
from .fetcher import MarketFetcher

__all__ = [
    "__version__",
    "FetcherConfig",
    "load_config",
    "MarketFetcher",
]
