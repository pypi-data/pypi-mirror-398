"""Extensions module for extending fetcher functionality."""

from .base import (
    BaseExtension,
    DataSourceExtension,
    ProcessorExtension,
    NotificationExtension,
    ExtensionManager,
)

__all__ = [
    "BaseExtension",
    "DataSourceExtension",
    "ProcessorExtension",
    "NotificationExtension",
    "ExtensionManager",
]
