#exonware/xwsystem/http/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

HTTP module base classes - abstract classes for HTTP client functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, AsyncGenerator
from .contracts import HttpMethod, HttpStatus, ContentType, AuthType


class AHttpClientBase(ABC):
    """Abstract base class for HTTP client operations."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[Any] = None
        self._headers: dict[str, str] = {}
        self._cookies: dict[str, str] = {}
    
    @abstractmethod
    def get(self, url: str, **kwargs) -> Any:
        """Make GET request."""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make POST request."""
        pass
    
    @abstractmethod
    def put(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make PUT request."""
        pass
    
    @abstractmethod
    def delete(self, url: str, **kwargs) -> Any:
        """Make DELETE request."""
        pass
    
    @abstractmethod
    def patch(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make PATCH request."""
        pass
    
    @abstractmethod
    def head(self, url: str, **kwargs) -> Any:
        """Make HEAD request."""
        pass
    
    @abstractmethod
    def options(self, url: str, **kwargs) -> Any:
        """Make OPTIONS request."""
        pass
    
    @abstractmethod
    def request(self, method: HttpMethod, url: str, **kwargs) -> Any:
        """Make HTTP request."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close HTTP client session."""
        pass


class AAsyncHttpClientBase(ABC):
    """Abstract base class for async HTTP client operations."""
    
    @abstractmethod
    async def aget(self, url: str, **kwargs) -> Any:
        """Make async GET request."""
        pass
    
    @abstractmethod
    async def apost(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make async POST request."""
        pass
    
    @abstractmethod
    async def aput(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make async PUT request."""
        pass
    
    @abstractmethod
    async def adelete(self, url: str, **kwargs) -> Any:
        """Make async DELETE request."""
        pass
    
    @abstractmethod
    async def apatch(self, url: str, data: Optional[Any] = None, **kwargs) -> Any:
        """Make async PATCH request."""
        pass
    
    @abstractmethod
    async def ahead(self, url: str, **kwargs) -> Any:
        """Make async HEAD request."""
        pass
    
    @abstractmethod
    async def aoptions(self, url: str, **kwargs) -> Any:
        """Make async OPTIONS request."""
        pass
    
    @abstractmethod
    async def arequest(self, method: HttpMethod, url: str, **kwargs) -> Any:
        """Make async HTTP request."""
        pass
    
    @abstractmethod
    async def aclose(self) -> None:
        """Close async HTTP client session."""
        pass


class AHttpResponseBase(ABC):
    """Abstract base class for HTTP response."""
    
    def __init__(self, status_code: int, headers: dict[str, str], content: Any):
        """
        Initialize HTTP response.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            content: Response content
        """
        self.status_code = status_code
        self.headers = headers
        self.content = content
    
    @abstractmethod
    def json(self) -> dict[str, Any]:
        """Parse response as JSON."""
        pass
    
    @abstractmethod
    def text(self) -> str:
        """Get response as text."""
        pass
    
    @abstractmethod
    def bytes(self) -> bytes:
        """Get response as bytes."""
        pass
    
    @abstractmethod
    def is_success(self) -> bool:
        """Check if response is successful."""
        pass
    
    @abstractmethod
    def is_error(self) -> bool:
        """Check if response is error."""
        pass
    
    @abstractmethod
    def get_header(self, name: str) -> Optional[str]:
        """Get response header."""
        pass
    
    @abstractmethod
    def get_cookies(self) -> dict[str, str]:
        """Get response cookies."""
        pass


class AHttpSessionBase(ABC):
    """Abstract base class for HTTP session management."""
    
    @abstractmethod
    def set_auth(self, auth_type: AuthType, **kwargs) -> None:
        """Set authentication."""
        pass
    
    @abstractmethod
    def set_headers(self, headers: dict[str, str]) -> None:
        """Set default headers."""
        pass
    
    @abstractmethod
    def set_cookies(self, cookies: dict[str, str]) -> None:
        """Set cookies."""
        pass
    
    @abstractmethod
    def set_proxy(self, proxy_url: str) -> None:
        """Set proxy."""
        pass
    
    @abstractmethod
    def set_verify_ssl(self, verify: bool) -> None:
        """Set SSL verification."""
        pass
    
    @abstractmethod
    def set_timeout(self, timeout: int) -> None:
        """Set request timeout."""
        pass
    
    @abstractmethod
    def get_session_info(self) -> dict[str, Any]:
        """Get session information."""
        pass


class AHttpRetryBase(ABC):
    """Abstract base class for HTTP retry logic."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize retry logic.
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retry delays
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    @abstractmethod
    def should_retry(self, response: AHttpResponseBase, attempt: int) -> bool:
        """Check if request should be retried."""
        pass
    
    @abstractmethod
    def get_retry_delay(self, attempt: int) -> float:
        """Get retry delay for attempt."""
        pass
    
    @abstractmethod
    def get_retry_status_codes(self) -> list[int]:
        """Get status codes that should trigger retry."""
        pass
    
    @abstractmethod
    def set_retry_status_codes(self, status_codes: list[int]) -> None:
        """Set status codes that should trigger retry."""
        pass


class AHttpStreamBase(ABC):
    """Abstract base class for HTTP streaming."""
    
    @abstractmethod
    def stream_request(self, method: HttpMethod, url: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """Stream HTTP request."""
        pass
    
    @abstractmethod
    def stream_response(self, response: AHttpResponseBase) -> AsyncGenerator[bytes, None]:
        """Stream HTTP response."""
        pass
    
    @abstractmethod
    def upload_file(self, url: str, file_path: str, **kwargs) -> Any:
        """Upload file via HTTP."""
        pass
    
    @abstractmethod
    def download_file(self, url: str, file_path: str, **kwargs) -> None:
        """Download file via HTTP."""
        pass
