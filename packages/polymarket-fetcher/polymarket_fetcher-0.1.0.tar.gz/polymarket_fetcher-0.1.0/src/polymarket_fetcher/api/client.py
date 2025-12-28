"""Gamma API client for Polymarket."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .endpoints import Endpoints, Endpoint
from .rate_limiter import RateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


class ProxyConfig:
    """Proxy configuration for the API client."""

    def __init__(
        self,
        proxy_type: str = "",
        proxy_url: str = "",
        proxy_username: str = "",
        proxy_password: str = "",
    ):
        """Initialize proxy configuration.

        Args:
            proxy_type: Proxy type (http, https, socks4, socks5).
            proxy_url: Proxy URL (e.g., 127.0.0.1:7890).
            proxy_username: Optional proxy username.
            proxy_password: Optional proxy password.
        """
        self.proxy_type = proxy_type
        self.proxy_url = proxy_url
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

    @property
    def is_enabled(self) -> bool:
        """Check if proxy is enabled."""
        return bool(self.proxy_type and self.proxy_url)

    def get_httpx_proxy(self) -> Optional[Union[str, httpx.Proxy]]:
        """Get the proxy configuration for httpx.

        Returns:
            Proxy URL string or httpx.Proxy object.
        """
        if not self.is_enabled:
            return None

        # Build auth part if credentials provided
        auth = None
        if self.proxy_username and self.proxy_password:
            auth = httpx.BasicAuth(self.proxy_username, self.proxy_password)

        # Build proxy URL
        # Handle URLs that already have protocol prefix
        proxy_url = self.proxy_url

        # If URL already has a protocol, use it as-is
        if not any(proxy_url.startswith(p) for p in ("http://", "https://", "socks4://", "socks5://")):
            # Add protocol prefix based on type
            if self.proxy_type in ("socks4", "socks5"):
                proxy_url = f"{self.proxy_type}://{proxy_url}"
            elif self.proxy_type in ("http", "https"):
                proxy_url = f"{self.proxy_type}://{proxy_url}"

        # Return httpx.Proxy for better compatibility
        return httpx.Proxy(
            url=proxy_url,
            auth=auth,
        )


class GammaAPIError(Exception):
    """Exception raised for Gamma API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[httpx.Response] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GammaAPIClient:
    """Async client for the Polymarket Gamma API.

    Provides methods for interacting with the Gamma API including
    rate limiting, retry logic, proxy support, and connection management.
    """

    def __init__(
        self,
        base_url: str = "https://gamma-api.polymarket.com",
        timeout: float = 30.0,
        rate_limit_config: Optional[RateLimitConfig] = None,
        max_retries: int = 3,
        raise_on_error: bool = True,
        proxy_config: Optional[ProxyConfig] = None,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL for the API.
            timeout: Request timeout in seconds.
            rate_limit_config: Rate limit configuration.
            max_retries: Maximum number of retry attempts.
            raise_on_error: Whether to raise exceptions on API errors.
            proxy_config: Proxy configuration.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.raise_on_error = raise_on_error
        self.proxy_config = proxy_config

        # Rate limiter
        self._rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

        # Retry strategy
        self._retry_strategy = AsyncRetrying(
            retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=0.5, max=10),
        )

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._client is not None and self._client.is_closed is False

    def _get_client_kwargs(self) -> Dict[str, Any]:
        """Get keyword arguments for httpx.AsyncClient.

        Returns:
            Dictionary of client arguments.
        """
        kwargs = {
            "timeout": self.timeout,
        }

        # Add proxy if configured
        if self.proxy_config and self.proxy_config.is_enabled:
            proxy = self.proxy_config.get_httpx_proxy()
            if proxy:
                kwargs["proxy"] = proxy
                logger.info(f"Using proxy: {self.proxy_config.proxy_type}://{self.proxy_config.proxy_url}")

        return kwargs

    async def connect(self) -> None:
        """Connect to the API."""
        if self._client is None:
            kwargs = self._get_client_kwargs()
            self._client = httpx.AsyncClient(**kwargs)

    async def disconnect(self) -> None:
        """Disconnect from the API."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator["GammaAPIClient", None]:
        """Context manager for connection lifecycle.

        Yields:
            The connected client.
        """
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    def _get_url(self, endpoint: str) -> str:
        """Get the full URL for an endpoint.

        Args:
            endpoint: API endpoint path.

        Returns:
            Full URL.
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    async def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retries.

        Args:
            method: HTTP method.
            url: Full URL.
            params: Query parameters.
            data: Request body data.
            headers: Request headers.

        Returns:
            HTTP response.

        Raises:
            GammaAPIError: If the request fails and raise_on_error is True.
        """
        # Apply rate limiting
        host = httpx.URL(url).host
        await self._rate_limiter.wait(host)

        # Make request with retry
        async for attempt in self._retry_strategy:
            with attempt:
                if self._client is None:
                    raise RuntimeError("Client not connected. Call connect() first.")

                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                )

                # Check for errors
                if self.raise_on_error:
                    response.raise_for_status()

                return response

        raise GammaAPIError("Max retries exceeded")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as a dictionary.
        """
        url = self._get_url(endpoint)
        response = await self._request("GET", url, params=params)
        return response.json()

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint path.
            data: Request body data.
            params: Query parameters.

        Returns:
            JSON response as a dictionary.
        """
        url = self._get_url(endpoint)
        response = await self._request("POST", url, params=params, data=data)
        return response.json()

    # Convenience methods for common endpoints

    async def list_markets(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        active: Optional[bool] = None,
        closed: Optional[bool] = None,
        archived: Optional[bool] = None,
        slug: Optional[str] = None,
        tag_id: Optional[Union[str, List[str]]] = None,
        category: Optional[str] = None,
        exclude_tag_id: Optional[str] = None,
        related_tags: bool = False,
        liquidity_num_min: Optional[float] = None,
        liquidity_num_max: Optional[float] = None,
        volume_num_min: Optional[float] = None,
        volume_num_max: Optional[float] = None,
        start_date_min: Optional[str] = None,
        start_date_max: Optional[str] = None,
        end_date_min: Optional[str] = None,
        end_date_max: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List markets with optional filtering.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            active: Filter by active status.
            closed: Filter by closed status.
            archived: Filter by archived status.
            slug: Filter by slug.
            tag_id: Filter by tag ID(s). Can be a single string or list of strings.
            category: Filter by category name (fuzzy match, case-insensitive).
            exclude_tag_id: Exclude markets with this tag ID.
            related_tags: Include markets with related tags.
            liquidity_num_min: Minimum liquidity.
            liquidity_num_max: Maximum liquidity.
            volume_num_min: Minimum volume.
            volume_num_max: Maximum volume.
            start_date_min: Minimum start date (ISO format).
            start_date_max: Maximum start date (ISO format).
            end_date_min: Minimum end date (ISO format).
            end_date_max: Maximum end date (ISO format).
            **kwargs: Additional parameters.

        Returns:
            API response with markets list (wrapped in dict for compatibility).
        """
        params: Dict[str, Any] = {}

        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if active is not None:
            params["active"] = active
        if closed is not None:
            params["closed"] = closed
        if archived is not None:
            params["archived"] = archived
        if slug is not None:
            params["slug"] = slug
        if tag_id is not None:
            params["tag_id"] = tag_id
        if category is not None:
            params["category"] = category
        if exclude_tag_id is not None:
            params["exclude_tag_id"] = exclude_tag_id
        if related_tags:
            params["related_tags"] = "true"
        if liquidity_num_min is not None:
            params["liquidity_num_min"] = liquidity_num_min
        if liquidity_num_max is not None:
            params["liquidity_num_max"] = liquidity_num_max
        if volume_num_min is not None:
            params["volume_num_min"] = volume_num_min
        if volume_num_max is not None:
            params["volume_num_max"] = volume_num_max
        if start_date_min is not None:
            params["start_date_min"] = start_date_min
        if start_date_max is not None:
            params["start_date_max"] = start_date_max
        if end_date_min is not None:
            params["end_date_min"] = end_date_min
        if end_date_max is not None:
            params["end_date_max"] = end_date_max

        params.update(kwargs)

        # API returns a list directly, wrap it for compatibility
        markets = await self.get("markets", params=params)
        if isinstance(markets, list):
            return {"markets": markets}
        return markets

    async def get_market(self, market_id: str) -> Dict[str, Any]:
        """Get a specific market by ID.

        Args:
            market_id: The market ID.

        Returns:
            Market details.
        """
        return await self.get(f"markets/{market_id}")

    async def get_market_by_slug(self, slug: str) -> Dict[str, Any]:
        """Get a market by slug.

        Args:
            slug: Market slug.

        Returns:
            Market details.
        """
        return await self.get(f"markets/slug/{slug}")

    async def list_events(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        active: Optional[bool] = None,
        tag: Optional[str] = None,
        tag_id: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List events with optional filtering.

        Args:
            limit: Maximum number of results.
            offset: Number of results to skip.
            active: Filter by active status.
            tag: Filter by tag label.
            tag_id: Filter by tag ID(s). Can be a single string or list of strings.
            **kwargs: Additional parameters.

        Returns:
            API response with events list.
        """
        params: Dict[str, Any] = {}

        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if active is not None:
            params["active"] = active
        if tag is not None:
            params["tag"] = tag
        if tag_id is not None:
            params["tag_id"] = tag_id

        params.update(kwargs)

        return await self.get("events", params=params)

    async def list_tags(
        self,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
    ) -> Dict[str, Any]:
        """List all available tags.

        Args:
            limit: Maximum number of results (default 100).
            offset: Number of results to skip (default 0).

        Returns:
            API response with tags list (wrapped in dict for compatibility).
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        # API returns a list directly, wrap it for compatibility
        tags = await self.get("tags", params=params)
        if isinstance(tags, list):
            return {"tags": tags}
        return tags

    async def list_sports(self) -> Dict[str, Any]:
        """Get sports-related tag metadata.

        Returns detailed metadata for sports including tag IDs,
        images, resolution sources, and series information.

        Returns:
            API response with sports metadata.
        """
        return await self.get("sports")

    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get a specific event by ID.

        Args:
            event_id: The event ID.

        Returns:
            Event details.
        """
        return await self.get(f"events/{event_id}")


async def create_api_client(
    base_url: str = "https://gamma-api.polymarket.com",
    timeout: float = 30.0,
    rate_limit: float = 5.0,
    max_retries: int = 3,
    proxy_config: Optional[ProxyConfig] = None,
) -> GammaAPIClient:
    """Create and connect an API client.

    Args:
        base_url: Base URL for the API.
        timeout: Request timeout in seconds.
        rate_limit: Requests per second limit.
        max_retries: Maximum retry attempts.
        proxy_config: Proxy configuration.

    Returns:
        Connected API client.
    """
    client = GammaAPIClient(
        base_url=base_url,
        timeout=timeout,
        rate_limit_config=RateLimitConfig(requests_per_second=rate_limit),
        max_retries=max_retries,
        proxy_config=proxy_config,
    )
    await client.connect()
    return client
