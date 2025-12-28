"""Base HTTP client for Dremio API."""

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dremio_cli.utils.exceptions import ApiError, AuthenticationError


class BaseClient:
    """Base HTTP client for Dremio API."""

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize base client.
        
        Args:
            base_url: Base URL for API
            token: Authentication token
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        
        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication.
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response.
        
        Args:
            response: HTTP response
            
        Returns:
            Parsed JSON response
            
        Raises:
            AuthenticationError: If authentication fails
            ApiError: If API request fails
        """
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed. Check your credentials.")
        
        if response.status_code == 403:
            raise ApiError("Access forbidden. Check your permissions.", status_code=403)
        
        if response.status_code == 404:
            raise ApiError("Resource not found.", status_code=404)
        
        if not response.ok:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if "errorMessage" in error_data:
                    error_msg = error_data["errorMessage"]
                    if "moreInfo" in error_data:
                        error_msg += f": {error_data['moreInfo']}"
            except Exception:
                error_msg += f": {response.text}"
            
            raise ApiError(error_msg, status_code=response.status_code, response_body=response.text)
        
        # Return empty dict for 204 No Content
        if response.status_code == 204:
            return {}
        
        try:
            return response.json()
        except Exception:
            return response.text

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        url = self._build_url(endpoint)
        response = self.session.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Make POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data
        """
        url = self._build_url(endpoint)
        response = self.session.post(
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Make PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data
        """
        url = self._build_url(endpoint)
        response = self.session.put(
            url,
            headers=self._get_headers(),
            json=data,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def delete(self, endpoint: str) -> Any:
        """Make DELETE request.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response data
        """
        url = self._build_url(endpoint)
        response = self.session.delete(
            url,
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)
