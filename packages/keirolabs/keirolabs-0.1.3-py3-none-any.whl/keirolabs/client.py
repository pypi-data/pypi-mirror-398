"""
KeiroLabs Python SDK - Enhanced Main Client with All Endpoints
"""
import requests
from typing import Optional, Dict, Any, List
from .exceptions import (
    KeiroAPIError,
    KeiroAuthError,
    KeiroRateLimitError,
    KeiroValidationError,
    KeiroConnectionError,
)


class Keiro:
    """
    Main KeiroLabs API Client
    
    Args:
        api_key: Your KeiroLabs API key
        base_url: Base URL for the API (default: production server)
        timeout: Request timeout in seconds (default: 30)
    
    Example:
        >>> from keiro import Keiro
        >>> client = Keiro(api_key="your-api-key")
        >>> result = client.search("What is machine learning?")
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://keiro-production.up.railway.app/api",
        timeout: int = 30
    ):
        if not api_key:
            raise KeiroValidationError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'keirolabs-python-sdk/0.1.0'
        })
    
    # ==================== API Key Validation ====================
    
    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate the API key and get key information
        
        Returns:
            dict: API key validation status and details
            
        Example:
            >>> validation = client.validate_api_key()
            >>> print(validation['valid'])
            >>> print(validation['plans'])
        """
        try:
            # Try a simple health check with the API key
            health = self.health_check()
            
            # If health check passes, key is valid
            # Try to get more info about the key
            return {
                "valid": True,
                "message": "API key is valid",
                "server_status": health.get('status'),
                "environment": health.get('environment')
            }
        except KeiroAuthError:
            return {
                "valid": False,
                "message": "Invalid API key",
                "error": "Authentication failed"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation failed: {str(e)}",
                "error": str(e)
            }
    
    # ==================== Search APIs ====================
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform basic search (costs 1 credit)
        
        Args:
            query: Search query string
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Search results with data and creditsRemaining
        
        Example:
            >>> result = client.search("Python programming")
            >>> print(result['data'])
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/search", payload)
    
    def search_pro(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform advanced search with Pro features
        
        Args:
            query: Search query string
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Advanced search results
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/search-pro", payload)
    
    # ==================== Answer API ====================
    
    def answer(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generate detailed answer (costs 5 credits)
        
        Args:
            query: Question to answer
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Answer with data and creditsRemaining
        
        Example:
            >>> answer = client.answer("Explain quantum computing")
            >>> print(answer['data'])
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/answer", payload)
    
    # ==================== Research APIs ====================
    
    def research(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform research on a topic
        
        Args:
            query: Research topic
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Research results
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/research", payload)
    
    def research_pro(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform advanced research with Pro features
        
        Args:
            query: Research topic
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Advanced research results
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/research-pro", payload)
    
    # ==================== Web Crawler API ====================
    
    def web_crawler(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Crawl a website
        
        Args:
            url: URL to crawl
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Crawled data
        """
        if not url:
            raise KeiroValidationError("URL is required")
        
        payload = {"url": url, **kwargs}
        return self._make_request("/web-crawler", payload)
    
    # ==================== Search Engine API ====================
    
    def search_engine(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Use the search engine functionality
        
        Args:
            query: Search query
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            dict: Search engine results
        """
        if not query:
            raise KeiroValidationError("Query is required")
        
        payload = {"query": query, **kwargs}
        return self._make_request("/search-engine", payload)
    
    # ==================== Health Check ====================
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status
        
        Returns:
            dict: Health status information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            raise KeiroConnectionError(f"Health check failed: {str(e)}")
    
    # ==================== Internal Methods ====================
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to make API requests
        
        Args:
            endpoint: API endpoint (e.g., "/search")
            data: Request payload
        
        Returns:
            dict: API response
        
        Raises:
            KeiroAuthError: Invalid API key
            KeiroRateLimitError: Out of credits
            KeiroAPIError: Other API errors
            KeiroConnectionError: Connection failures
        """
        # Add API key to request
        data["apiKey"] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=self.timeout
            )
            
            # Handle specific status codes
            if response.status_code == 400:
                error_msg = response.json().get('error', 'Bad request')
                raise KeiroValidationError(f"Validation error: {error_msg}")
            
            elif response.status_code == 401:
                raise KeiroAuthError("Invalid API key")
            
            elif response.status_code == 402:
                raise KeiroRateLimitError("Out of credits")
            
            elif response.status_code == 403:
                error_msg = response.json().get('error', 'Forbidden')
                raise KeiroAuthError(f"Access denied: {error_msg}")
            
            elif response.status_code >= 500:
                raise KeiroAPIError(f"Server error: {response.status_code}")
            
            elif not response.ok:
                raise KeiroAPIError(
                    f"API request failed: {response.status_code} - {response.text}"
                )
            
            return response.json()
        
        except requests.exceptions.Timeout:
            raise KeiroConnectionError(f"Request timeout after {self.timeout}s")
        
        except requests.exceptions.ConnectionError:
            raise KeiroConnectionError(f"Failed to connect to {url}")
        
        except requests.exceptions.RequestException as e:
            raise KeiroConnectionError(f"Request failed: {str(e)}")
    
    def set_base_url(self, base_url: str) -> None:
        """
        Update the base URL (useful for switching between dev/prod)
        
        Args:
            base_url: New base URL
        
        Example:
            >>> client.set_base_url("https://keiro-production.up.railway.app/api")
        """
        self.base_url = base_url.rstrip('/')
    
    def close(self) -> None:
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()