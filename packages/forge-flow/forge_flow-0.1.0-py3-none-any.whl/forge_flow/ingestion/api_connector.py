"""API connector with enterprise-grade resilience.

Provides HTTP client with retry logic, rate limiting, and pagination support.
"""

import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urljoin

import requests
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from forge_flow.exceptions import IngestionError
from forge_flow.ingestion.base import DataSource

logger = structlog.get_logger(__name__)


class APIConnector(DataSource):
    """HTTP API connector with resilience patterns.

    Features:
    - Exponential backoff with jitter
    - Rate limit handling (429 responses)
    - Automatic retries on transient failures
    - Pagination support (cursor and offset-based)
    - Request/response logging

    Example:
        >>> connector = APIConnector(
        ...     base_url="https://api.example.com",
        ...     headers={"Authorization": "Bearer token"}
        ... )
        >>> data = connector.get("/users", params={"limit": 100})
        >>> df = pd.DataFrame(data)
    """

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
    ) -> None:
        """Initialize API connector.

        Args:
            base_url: Base URL for the API.
            headers: Optional HTTP headers (e.g., authentication).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            rate_limit_delay: Delay in seconds when rate limited.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch(self) -> Any:
        """Not implemented for APIConnector.

        Use specific HTTP methods (get, post, etc.) instead.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError(
            "APIConnector requires explicit HTTP method. Use get(), post(), etc."
        )

    @retry(
        retry=retry_if_exception_type(
            (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Perform GET request with automatic retries.

        Args:
            endpoint: API endpoint (relative to base_url).
            params: Optional query parameters.
            **kwargs: Additional arguments passed to requests.get.

        Returns:
            Response JSON data.

        Raises:
            IngestionError: If request fails after retries.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            logger.info("api_get_request", url=url, params=params)

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                **kwargs,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", self.rate_limit_delay))
                logger.warning("rate_limited", url=url, retry_after=retry_after)
                time.sleep(retry_after)
                return self.get(endpoint, params, **kwargs)

            response.raise_for_status()

            logger.info(
                "api_get_success",
                url=url,
                status_code=response.status_code,
            )

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(
                "api_get_http_error",
                url=url,
                status_code=e.response.status_code if e.response else None,
                error=str(e),
            )
            raise IngestionError(f"HTTP error for {url}: {e}") from e

        except requests.exceptions.RequestException as e:
            logger.error("api_get_request_error", url=url, error=str(e))
            raise IngestionError(f"Request failed for {url}: {e}") from e

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Perform POST request.

        Args:
            endpoint: API endpoint (relative to base_url).
            data: Optional form data.
            json: Optional JSON payload.
            **kwargs: Additional arguments passed to requests.post.

        Returns:
            Response JSON data.

        Raises:
            IngestionError: If request fails.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            logger.info("api_post_request", url=url)

            response = self.session.post(
                url,
                data=data,
                json=json,
                timeout=self.timeout,
                **kwargs,
            )

            response.raise_for_status()

            logger.info(
                "api_post_success",
                url=url,
                status_code=response.status_code,
            )

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("api_post_error", url=url, error=str(e))
            raise IngestionError(f"POST request failed for {url}: {e}") from e

    def paginate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        page_size: int = 100,
        max_pages: int | None = None,
        next_page_fn: Callable[[Any], str | None] | None = None,
    ) -> list[Any]:
        """Fetch paginated data from API.

        Args:
            endpoint: API endpoint.
            params: Optional query parameters.
            page_size: Number of items per page.
            max_pages: Maximum number of pages to fetch (None = unlimited).
            next_page_fn: Optional function to extract next page URL/cursor from response.
                         If None, uses offset-based pagination.

        Returns:
            List of all items from all pages.

        Raises:
            IngestionError: If pagination fails.
        """
        all_items: list[Any] = []
        page = 0
        params = params or {}

        logger.info(
            "pagination_started",
            endpoint=endpoint,
            page_size=page_size,
            max_pages=max_pages,
        )

        while True:
            if max_pages and page >= max_pages:
                break

            # Offset-based pagination by default
            if next_page_fn is None:
                params["limit"] = page_size
                params["offset"] = page * page_size

            response = self.get(endpoint, params=params)

            # Extract items (assumes response is dict with 'data' or 'results' key)
            items = response.get("data") or response.get("results") or response

            if not items:
                break

            all_items.extend(items)
            page += 1

            logger.info("pagination_page_fetched", page=page, items_count=len(items))

            # Check for next page
            if next_page_fn:
                next_url = next_page_fn(response)
                if not next_url:
                    break
                endpoint = next_url
                params = {}
            else:
                # Stop if we got fewer items than page_size
                if len(items) < page_size:
                    break

        logger.info("pagination_complete", total_pages=page, total_items=len(all_items))

        return all_items

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        logger.info("api_session_closed")

    def __enter__(self) -> "APIConnector":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
