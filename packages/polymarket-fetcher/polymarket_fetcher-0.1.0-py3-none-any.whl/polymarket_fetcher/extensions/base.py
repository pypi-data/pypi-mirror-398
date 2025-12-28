"""Base classes for extensions."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ExtensionType(str, Enum):
    """Types of extensions."""

    DATA_SOURCE = "data_source"
    PROCESSOR = "processor"
    NOTIFICATION = "notification"


@dataclass
class ExtensionMetadata:
    """Metadata for an extension."""

    name: str
    version: str
    description: str
    author: str
    extension_type: ExtensionType
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BaseExtension(ABC):
    """Base class for all extensions.

    Extensions provide a way to extend the functionality of the fetcher
    without modifying core code.
    """

    metadata: ExtensionMetadata

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the extension.

        Args:
            config: Extension configuration.
        """
        self.config = config or {}
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        """Check if the extension is enabled."""
        return self._enabled

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the extension name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Get the extension version."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the extension description."""
        pass

    @property
    @abstractmethod
    def extension_type(self) -> ExtensionType:
        """Get the extension type."""
        pass

    def enable(self) -> None:
        """Enable the extension."""
        self._enabled = True
        logger.info(f"Extension {self.name} enabled")

    def disable(self) -> None:
        """Disable the extension."""
        self._enabled = False
        logger.info(f"Extension {self.name} disabled")

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the extension.

        Args:
            config: Configuration dictionary.
        """
        self.config.update(config)
        logger.info(f"Extension {self.name} configured")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the extension.

        Called when the fetcher starts.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the extension.

        Called when the fetcher stops.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get extension information.

        Returns:
            Dictionary with extension info.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "type": self.extension_type.value,
            "enabled": self._enabled,
        }


class DataSourceExtension(BaseExtension):
    """Base class for data source extensions.

    Data source extensions allow adding new data sources
    beyond the built-in Polymarket API.
    """

    @property
    @abstractmethod
    def extension_type(self) -> ExtensionType:
        """Return the extension type."""
        return ExtensionType.DATA_SOURCE

    @abstractmethod
    async def fetch_markets(
        self,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Fetch markets from this data source.

        Args:
            **kwargs: Additional arguments.

        Returns:
            List of market data dictionaries.
        """
        pass

    @abstractmethod
    async def fetch_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific market.

        Args:
            market_id: Market ID.

        Returns:
            Market data or None.
        """
        pass

    @abstractmethod
    def supports_market_id(self, market_id: str) -> bool:
        """Check if this data source handles a market ID.

        Args:
            market_id: Market ID to check.

        Returns:
            True if this data source handles the ID.
        """
        pass


class ProcessorExtension(BaseExtension):
    """Base class for processor extensions.

    Processor extensions allow processing market data
    in various ways (analysis, transformation, etc.).
    """

    @property
    @abstractmethod
    def extension_type(self) -> ExtensionType:
        """Return the extension type."""
        return ExtensionType.PROCESSOR

    @abstractmethod
    async def process_market(
        self,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process a single market.

        Args:
            market_data: Market data to process.

        Returns:
            Processed market data.
        """
        pass

    @abstractmethod
    async def process_markets(
        self,
        markets_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Process multiple markets.

        Args:
            markets_data: Markets data to process.

        Returns:
            Processed markets data.
        """
        pass


class NotificationExtension(BaseExtension):
    """Base class for notification extensions.

    Notification extensions allow sending notifications
    through various channels (email, Slack, etc.).
    """

    @property
    @abstractmethod
    def extension_type(self) -> ExtensionType:
        """Return the extension type."""
        return ExtensionType.NOTIFICATION

    @abstractmethod
    async def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info",
        **kwargs,
    ) -> bool:
        """Send a notification.

        Args:
            title: Notification title.
            message: Notification message.
            level: Notification level (info, warning, error).
            **kwargs: Additional arguments.

        Returns:
            True if sent successfully.
        """
        pass


class ExtensionManager:
    """Manager for extensions."""

    def __init__(self):
        """Initialize the extension manager."""
        self._extensions: List[BaseExtension] = []
        self._extensions_by_name: Dict[str, BaseExtension] = {}

    def register(self, extension: BaseExtension) -> None:
        """Register an extension.

        Args:
            extension: Extension to register.
        """
        if extension.name in self._extensions_by_name:
            raise ValueError(f"Extension {extension.name} already registered")

        self._extensions.append(extension)
        self._extensions_by_name[extension.name] = extension
        logger.info(f"Registered extension: {extension.name} ({extension.version})")

    def unregister(self, name: str) -> Optional[BaseExtension]:
        """Unregister an extension.

        Args:
            name: Extension name.

        Returns:
            Unregistered extension or None.
        """
        extension = self._extensions_by_name.pop(name, None)
        if extension:
            self._extensions.remove(extension)
            logger.info(f"Unregistered extension: {name}")
        return extension

    def get(self, name: str) -> Optional[BaseExtension]:
        """Get an extension by name.

        Args:
            name: Extension name.

        Returns:
            Extension or None.
        """
        return self._extensions_by_name.get(name)

    def get_by_type(self, extension_type: ExtensionType) -> List[BaseExtension]:
        """Get extensions by type.

        Args:
            extension_type: Extension type.

        Returns:
            List of matching extensions.
        """
        return [e for e in self._extensions if e.extension_type == extension_type]

    async def initialize_all(self) -> None:
        """Initialize all registered extensions."""
        for extension in self._extensions:
            if extension.is_enabled:
                try:
                    await extension.initialize()
                except Exception as e:
                    logger.error(f"Failed to initialize extension {extension.name}: {e}")

    async def shutdown_all(self) -> None:
        """Shutdown all registered extensions."""
        for extension in self._extensions:
            try:
                await extension.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown extension {extension.name}: {e}")

    def get_all_info(self) -> List[Dict[str, Any]]:
        """Get info for all extensions.

        Returns:
            List of extension info dictionaries.
        """
        return [e.get_info() for e in self._extensions]

    def list_names(self) -> List[str]:
        """List all registered extension names.

        Returns:
            List of extension names.
        """
        return list(self._extensions_by_name.keys())
