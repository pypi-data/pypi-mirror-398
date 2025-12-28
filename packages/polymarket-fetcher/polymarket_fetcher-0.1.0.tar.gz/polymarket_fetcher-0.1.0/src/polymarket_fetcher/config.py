"""Configuration management for Polymarket Fetcher."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field


class ProxyConfig(BaseModel):
    """Proxy configuration."""

    type: str = ""  # http, https, socks4, socks5, empty to disable
    url: str = ""
    username: str = ""
    password: str = ""

    @property
    def is_enabled(self) -> bool:
        """Check if proxy is enabled."""
        return bool(self.type and self.url)

    def get_proxy_url(self) -> Optional[str]:
        """Get the proxy URL for httpx.

        Returns:
            Proxy URL string or None.
        """
        if not self.is_enabled:
            return None

        # Build auth part if credentials provided
        auth_part = ""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"

        # Construct proxy URL
        if self.type in ("socks4", "socks5"):
            return f"{self.type}://{auth_part}{self.url}"
        else:
            return f"{self.type}://{auth_part}{self.url}" if self.type else self.url


class APIConfig(BaseModel):
    """API configuration."""

    base_url: str = "https://gamma-api.polymarket.com"
    timeout: int = 30
    rate_limit: Dict[str, Any] = Field(default_factory=dict)
    retry: Dict[str, Any] = Field(default_factory=dict)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)


class DatabaseConfig(BaseModel):
    """Database configuration."""

    path: str = "data/polymarket.db"
    pool_size: int = 5
    auto_flush: bool = True


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    enabled: bool = True
    market_fetch_interval: int = 60
    history_snapshot_interval: int = 300
    timezone: str = "UTC"


class CallbacksConfig(BaseModel):
    """Callbacks configuration."""

    enabled: bool = True
    async_dispatch: bool = True
    handlers: List[Dict[str, Any]] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = ""


class FiltersConfig(BaseModel):
    """Default filter settings."""

    min_volume: float = 1000
    min_liquidity: float = 500
    only_active: bool = True


class TopicFilterConfig(BaseModel):
    """Topic filter configuration for filtering by category or tags."""

    enabled: bool = False
    category: str = ""
    tags: List[str] = Field(default_factory=list)
    related_tags: bool = False
    exclude_tag_id: Optional[str] = None
    limit: int = 100


class FetcherConfig(BaseModel):
    """Main configuration class for the fetcher."""

    api: APIConfig = Field(default_factory=APIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    callbacks: CallbacksConfig = Field(default_factory=CallbacksConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    topic_filters: TopicFilterConfig = Field(default_factory=TopicFilterConfig)


class KeywordGroup(BaseModel):
    """Keyword group configuration."""

    name: str
    patterns: List[str]
    match_mode: str = "contains"  # contains, regex, fuzzy
    enabled: bool = True
    priority: int = 0


class ExcludeRule(BaseModel):
    """Exclusion rule configuration."""

    pattern: str
    reason: str = ""


class KeywordsConfig(BaseModel):
    """Keywords configuration."""

    keywords: List[KeywordGroup] = Field(default_factory=list)
    excludes: List[ExcludeRule] = Field(default_factory=list)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)


def load_yaml_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Parsed configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(
    settings_path: Union[str, Path],
    keywords_path: Optional[Union[str, Path]] = None,
) -> tuple[FetcherConfig, KeywordsConfig]:
    """Load configuration from YAML files.

    Args:
        settings_path: Path to settings.yaml.
        keywords_path: Optional path to keywords.yaml.

    Returns:
        Tuple of (FetcherConfig, KeywordsConfig).
    """
    # Load settings
    settings_data = load_yaml_config(settings_path)
    config = FetcherConfig(**settings_data)

    # Load keywords if provided
    keywords_config = KeywordsConfig()
    if keywords_path:
        keywords_data = load_yaml_config(keywords_path)
        if "keywords" in keywords_data:
            keywords_data["keywords"] = [
                KeywordGroup(**kg) for kg in keywords_data["keywords"]
            ]
        if "excludes" in keywords_data:
            keywords_data["excludes"] = [
                ExcludeRule(**ex) for ex in keywords_data["excludes"]
            ]
        keywords_config = KeywordsConfig(**keywords_data)

    return config, keywords_config


@dataclass
class RuntimeConfig:
    """Runtime configuration that combines all configs."""

    fetcher_config: FetcherConfig
    keywords_config: KeywordsConfig
    base_path: Path = field(default_factory=Path)

    @property
    def db_path(self) -> Path:
        """Get absolute database path."""
        db_path = Path(self.fetcher_config.database.path)
        if not db_path.is_absolute():
            return self.base_path / db_path
        return db_path

    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for an endpoint.

        Args:
            endpoint: API endpoint (e.g., "markets", "events").

        Returns:
            Full URL.
        """
        base = self.fetcher_config.api.base_url.rstrip("/")
        return f"{base}/{endpoint.lstrip('/')}"
