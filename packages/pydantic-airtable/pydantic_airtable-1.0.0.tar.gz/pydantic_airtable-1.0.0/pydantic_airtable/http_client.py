"""
Unified HTTP client for all Airtable operations
"""

import json
import time
from importlib.metadata import version, PackageNotFoundError
from typing import Any, Dict, Optional
import requests
from urllib.parse import quote

from .exceptions import APIError, RecordNotFoundError


def _get_user_agent() -> str:
    """Get the User-Agent string for API requests"""
    try:
        pkg_version = version("pydantic-airtable")
    except PackageNotFoundError:
        pkg_version = "dev"
    return f"pydantic-airtable/{pkg_version}"


class BaseHTTPClient:
    """
    Unified HTTP client for all Airtable API operations
    Eliminates code duplication across different managers
    """
    
    BASE_URL = "https://api.airtable.com/v0"
    META_API_URL = "https://api.airtable.com/v0/meta"
    
    def __init__(self, access_token: str):
        """
        Initialize HTTP client
        
        Args:
            access_token: Airtable Personal Access Token
        """
        if not access_token:
            raise ValueError("access_token is required")
            
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": _get_user_agent()
        })
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions
        
        Args:
            response: HTTP response from Airtable API
            
        Returns:
            Parsed JSON data
            
        Raises:
            APIError: For API errors
            RecordNotFoundError: For 404 record errors
        """
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            data = {"error": {"message": response.text}}
        
        if not response.ok:
            error_info = data.get("error", {})
            error_message = error_info.get("message", f"HTTP {response.status_code}")
            
            # Handle specific error cases
            if response.status_code == 404:
                if "record" in error_message.lower():
                    raise RecordNotFoundError(error_message)
            
            raise APIError(
                message=f"{error_message} (Status: {response.status_code})",
                status_code=response.status_code,
                response_data=data
            )
        
        return data
    
    def _rate_limit_retry(
        self, 
        func, 
        *args, 
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with exponential backoff retry for rate limits
        
        Args:
            func: HTTP function to call (e.g., session.get, session.post)
            *args: Arguments for the function
            max_retries: Maximum number of retries
            base_delay: Base delay between retries in seconds
            **kwargs: Keyword arguments for the function
            
        Returns:
            Parsed response data
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = func(*args, **kwargs)
                return self._handle_response(response)
                
            except APIError as e:
                last_exception = e
                
                # Retry on rate limit (status 429) or server errors (5xx)
                if e.status_code in (429, 502, 503, 504) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue
                
                # Re-raise if not retryable or max retries exceeded
                raise
                
            except (requests.RequestException, Exception) as e:
                last_exception = e
                
                # Retry on network errors
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                
                # Convert to APIError for consistency
                raise APIError(f"Request failed: {str(e)}")
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise APIError("Request failed after all retries")
    
    # Convenience methods for different HTTP operations
    def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """GET request with retry logic"""
        return self._rate_limit_retry(self.session.get, url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """POST request with retry logic"""
        return self._rate_limit_retry(self.session.post, url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> Dict[str, Any]:
        """PATCH request with retry logic"""
        return self._rate_limit_retry(self.session.patch, url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """PUT request with retry logic"""
        return self._rate_limit_retry(self.session.put, url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """DELETE request with retry logic"""
        return self._rate_limit_retry(self.session.delete, url, **kwargs)
    
    def build_url(self, *parts: str, base_url: Optional[str] = None) -> str:
        """
        Build URL from parts with proper encoding
        
        Args:
            *parts: URL parts to join
            base_url: Base URL (defaults to BASE_URL)
            
        Returns:
            Complete URL
        """
        base = base_url or self.BASE_URL
        encoded_parts = [quote(str(part), safe='') for part in parts if part]
        return f"{base}/{'/'.join(encoded_parts)}"
    
    def build_meta_url(self, *parts: str) -> str:
        """Build Meta API URL"""
        return self.build_url(*parts, base_url=self.META_API_URL)
