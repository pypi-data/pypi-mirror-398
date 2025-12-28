"""API endpoint definitions for Polymarket Gamma API."""

from dataclasses import dataclass
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"


@dataclass
class Endpoint:
    """API endpoint definition."""

    path: str
    method: HTTPMethod = HTTPMethod.GET
    description: str = ""


class Endpoints:
    """Collection of all API endpoints."""

    # Markets endpoints
    LIST_MARKETS = Endpoint(
        path="markets",
        method=HTTPMethod.GET,
        description="List all markets with filtering options",
    )
    GET_MARKET = Endpoint(
        path="markets/{market_id}",
        method=HTTPMethod.GET,
        description="Get a specific market by ID",
    )
    GET_MARKET_BY_SLUG = Endpoint(
        path="markets/slug/{slug}",
        method=HTTPMethod.GET,
        description="Get a market by slug",
    )
    GET_MARKET_TAGS = Endpoint(
        path="markets/{market_id}/tags",
        method=HTTPMethod.GET,
        description="Get tags for a specific market",
    )

    # Events endpoints
    LIST_EVENTS = Endpoint(
        path="events",
        method=HTTPMethod.GET,
        description="List all events with filtering options",
    )
    GET_EVENT = Endpoint(
        path="events/{event_id}",
        method=HTTPMethod.GET,
        description="Get a specific event by ID",
    )

    # Other endpoints
    GET_TAGS = Endpoint(
        path="tags",
        method=HTTPMethod.GET,
        description="List all tags",
    )
    GET_SERIES = Endpoint(
        path="series",
        method=HTTPMethod.GET,
        description="List all series",
    )
    GET_COMMENTS = Endpoint(
        path="comments",
        method=HTTPMethod.GET,
        description="List comments",
    )
    SEARCH = Endpoint(
        path="search",
        method=HTTPMethod.GET,
        description="Search markets and events",
    )

    @classmethod
    def get_url(cls, endpoint: "Endpoint", **kwargs) -> str:
        """Format endpoint URL with path parameters.

        Args:
            endpoint: Endpoint definition.
            **kwargs: Path parameters to substitute.

        Returns:
            Formatted URL path.
        """
        return endpoint.path.format(**kwargs)

    @classmethod
    def list_all(cls) -> list[Endpoint]:
        """List all available endpoints.

        Returns:
            List of all endpoints.
        """
        return [
            cls.LIST_MARKETS,
            cls.GET_MARKET,
            cls.GET_MARKET_BY_SLUG,
            cls.GET_MARKET_TAGS,
            cls.LIST_EVENTS,
            cls.GET_EVENT,
            cls.GET_TAGS,
            cls.GET_SERIES,
            cls.GET_COMMENTS,
            cls.SEARCH,
        ]
