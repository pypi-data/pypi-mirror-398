"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

HTTP client with retry mechanisms, connection pooling, and error handling.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from urllib.parse import urljoin

# Prevent httpx from importing rich (Python 3.8+ only, no legacy deps)
os.environ.setdefault("HTTPX_NO_RICH", "1")

import httpx

from ..config.logging_setup import get_logger
from ..monitoring.error_recovery import retry_with_backoff
from .errors import HttpError

logger = get_logger("xwsystem.http_client.client")


@dataclass
class RetryConfig:
    """Configuration for HTTP request retries."""
    
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retry_on_status: list[int] = field(default_factory=lambda: [500, 502, 503, 504, 429])
    retry_on_exceptions: list[type] = field(default_factory=lambda: [httpx.ConnectError, httpx.TimeoutException])


class HttpClient:
    """
    High-performance HTTP client with retry mechanisms, connection pooling,
    and comprehensive error handling.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        retry_config: Optional[RetryConfig] = None,
        default_headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum keepalive connections
            retry_config: Retry configuration
            default_headers: Default headers for all requests
        """
        # httpx is now required
            
        self.base_url = base_url
        self.retry_config = retry_config or RetryConfig()
        self.default_headers = default_headers or {}
        
        # Configure httpx client
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections
        )
        
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            limits=limits,
            headers=self.default_headers
        )
        
        self._async_client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=limits,
            headers=self.default_headers
        )

    def __enter__(self) -> 'HttpClient':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client and cleanup connections."""
        try:
            self._client.close()
            if hasattr(self._async_client, 'aclose'):
                # Handle async client cleanup
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self._async_client.aclose())
                    else:
                        loop.run_until_complete(self._async_client.aclose())
                except RuntimeError:
                    # No event loop available
                    pass
        except Exception as e:
            logger.warning(f"Error closing HTTP client: {e}")

    def _should_retry(self, response: Optional[httpx.Response], exception: Optional[Exception]) -> bool:
        """Determine if a request should be retried."""
        if exception:
            return any(isinstance(exception, exc_type) for exc_type in self.retry_config.retry_on_exceptions)
        
        if response:
            return response.status_code in self.retry_config.retry_on_status
            
        return False

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        
        # Combine headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        # Prepare request arguments
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': request_headers,
            'params': params,
            'files': files,
        }
        
        if json_data is not None:
            request_kwargs['json'] = json_data
        elif data is not None:
            request_kwargs['data'] = data

        @retry_with_backoff(
            max_retries=self.retry_config.max_retries,
            base_delay=self.retry_config.base_delay,
            max_delay=self.retry_config.max_delay,
            exponential_base=self.retry_config.exponential_base
        )
        def _request() -> httpx.Response:
            try:
                response = self._client.request(**request_kwargs)
                
                if self._should_retry(response, None):
                    raise HttpError(
                        f"HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return response
                
            except Exception as e:
                if self._should_retry(None, e):
                    raise HttpError(f"Request failed: {e}") from e
                raise

        return _request()

    def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make GET request."""
        return self._make_request('GET', url, headers=headers, params=params)

    def post(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make POST request."""
        return self._make_request(
            'POST', url, headers=headers, params=params,
            json_data=json_data, data=data, files=files
        )

    def put(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make PUT request."""
        return self._make_request(
            'PUT', url, headers=headers, params=params,
            json_data=json_data, data=data
        )

    def patch(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make PATCH request."""
        return self._make_request(
            'PATCH', url, headers=headers, params=params,
            json_data=json_data, data=data
        )

    def delete(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make DELETE request."""
        return self._make_request('DELETE', url, headers=headers, params=params)

    def head(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HEAD request."""
        return self._make_request('HEAD', url, headers=headers, params=params)

    def options(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make OPTIONS request."""
        return self._make_request('OPTIONS', url, headers=headers, params=params)

    # Convenience methods for JSON responses
    def get_json(self, url: str, **kwargs: Any) -> Any:
        """GET request returning JSON data."""
        response = self.get(url, **kwargs)
        try:
            return response.json()
        except Exception as e:
            raise HttpError(f"Failed to parse JSON response: {e}") from e

    def post_json(self, url: str, **kwargs: Any) -> Any:
        """POST request returning JSON data."""
        response = self.post(url, **kwargs)
        try:
            return response.json()
        except Exception as e:
            raise HttpError(f"Failed to parse JSON response: {e}") from e

    # Health check methods
    def health_check(self, endpoint: str = "/health") -> bool:
        """Perform health check on the service."""
        try:
            response = self.get(endpoint)
            return 200 <= response.status_code < 300
        except Exception:
            return False

    def ping(self, endpoint: str = "/ping") -> float:
        """Ping the service and return response time in seconds."""
        start_time = time.perf_counter()
        try:
            self.get(endpoint)
            return time.perf_counter() - start_time
        except Exception as e:
            raise HttpError(f"Ping failed: {e}") from e


# Async HTTP Client
class AsyncHttpClient:
    """
    High-performance async HTTP client with retry mechanisms, connection pooling,
    and comprehensive error handling for high-concurrency scenarios.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        retry_config: Optional[RetryConfig] = None,
        default_headers: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Initialize async HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum keepalive connections
            retry_config: Retry configuration
            default_headers: Default headers for all requests
        """
        # httpx is now required
            
        self.base_url = base_url
        self.retry_config = retry_config or RetryConfig()
        self.default_headers = default_headers or {}
        
        # Configure httpx async client
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections
        )
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=limits,
            headers=self.default_headers
        )

    async def __aenter__(self) -> 'AsyncHttpClient':
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the async HTTP client and cleanup connections."""
        try:
            await self._client.aclose()
        except Exception as e:
            logger.warning(f"Error closing async HTTP client: {e}")

    def _should_retry(self, response: Optional[httpx.Response], exception: Optional[Exception]) -> bool:
        """Determine if a request should be retried."""
        if exception:
            return any(isinstance(exception, exc_type) for exc_type in self.retry_config.retry_on_exceptions)
        
        if response:
            return response.status_code in self.retry_config.retry_on_status
            
        return False

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async HTTP request with retry logic."""
        
        # Combine headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)

        # Prepare request arguments
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': request_headers,
            'params': params,
            'files': files,
        }
        
        if json_data is not None:
            request_kwargs['json'] = json_data
        elif data is not None:
            request_kwargs['data'] = data

        @retry_with_backoff(
            max_retries=self.retry_config.max_retries,
            base_delay=self.retry_config.base_delay,
            max_delay=self.retry_config.max_delay,
            exponential_base=self.retry_config.exponential_base
        )
        async def _request() -> httpx.Response:
            try:
                response = await self._client.request(**request_kwargs)
                
                if self._should_retry(response, None):
                    raise HttpError(
                        f"HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return response
                
            except Exception as e:
                if self._should_retry(None, e):
                    raise HttpError(f"Request failed: {e}") from e
                raise

        return await _request()

    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async GET request."""
        return await self._make_request('GET', url, headers=headers, params=params)

    async def post(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async POST request."""
        return await self._make_request(
            'POST', url, headers=headers, params=params,
            json_data=json_data, data=data, files=files
        )

    async def put(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make async PUT request."""
        return await self._make_request(
            'PUT', url, headers=headers, params=params,
            json_data=json_data, data=data
        )

    async def patch(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Make async PATCH request."""
        return await self._make_request(
            'PATCH', url, headers=headers, params=params,
            json_data=json_data, data=data
        )

    async def delete(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async DELETE request."""
        return await self._make_request('DELETE', url, headers=headers, params=params)

    async def head(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async HEAD request."""
        return await self._make_request('HEAD', url, headers=headers, params=params)

    async def options(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async OPTIONS request."""
        return await self._make_request('OPTIONS', url, headers=headers, params=params)

    # Convenience methods for JSON responses
    async def get_json(self, url: str, **kwargs: Any) -> Any:
        """Async GET request returning JSON data."""
        response = await self.get(url, **kwargs)
        try:
            return response.json()
        except Exception as e:
            raise HttpError(f"Failed to parse JSON response: {e}") from e

    async def post_json(self, url: str, **kwargs: Any) -> Any:
        """Async POST request returning JSON data."""
        response = await self.post(url, **kwargs)
        try:
            return response.json()
        except Exception as e:
            raise HttpError(f"Failed to parse JSON response: {e}") from e

    # Health check methods
    async def health_check(self, endpoint: str = "/health") -> bool:
        """Perform async health check on the service."""
        try:
            response = await self.get(endpoint)
            return 200 <= response.status_code < 300
        except Exception:
            return False

    async def ping(self, endpoint: str = "/ping") -> float:
        """Async ping the service and return response time in seconds."""
        start_time = time.perf_counter()
        try:
            await self.get(endpoint)
            return time.perf_counter() - start_time
        except Exception as e:
            raise HttpError(f"Ping failed: {e}") from e


# Convenience functions
def get(url: str, **kwargs: Any) -> httpx.Response:
    """Quick GET request with default client."""
    with HttpClient() as client:
        return client.get(url, **kwargs)


def post(url: str, **kwargs: Any) -> httpx.Response:
    """Quick POST request with default client."""
    with HttpClient() as client:
        return client.post(url, **kwargs)


def get_json(url: str, **kwargs: Any) -> Any:
    """Quick GET request returning JSON."""
    with HttpClient() as client:
        return client.get_json(url, **kwargs)
