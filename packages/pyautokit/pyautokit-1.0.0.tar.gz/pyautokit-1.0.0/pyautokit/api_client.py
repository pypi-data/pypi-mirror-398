"""Generic API client with retry logic and rate limiting."""

import argparse
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import requests
from .logger import setup_logger
from .config import Config
from .utils import save_json

logger = setup_logger("APIClient", level=Config.LOG_LEVEL)


class APIClient:
    """Generic API client with retry and rate limiting."""

    def __init__(
        self,
        base_url: str = Config.API_BASE_URL,
        api_key: Optional[str] = Config.API_KEY,
        timeout: int = Config.API_TIMEOUT,
        retries: int = Config.API_RETRIES,
        retry_delay: int = Config.API_RETRY_DELAY
    ):
        """Initialize API client.
        
        Args:
            base_url: Base API URL
            api_key: API authentication key
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        return urljoin(self.base_url, endpoint.lstrip("/"))

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """Make request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object or None on failure
        """
        last_exception = None
        
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exception = e
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.retries + 1}): {e}"
                )
                
                if attempt < self.retries:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"All retry attempts failed: {last_exception}")
        return None

    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional request parameters
            
        Returns:
            JSON response or None
        """
        url = self._build_url(endpoint)
        response = self._request_with_retry("GET", url, params=params, **kwargs)
        
        if response:
            try:
                return response.json()
            except ValueError:
                logger.error("Invalid JSON response")
                return {"text": response.text}
        return None

    def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make POST request.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            **kwargs: Additional request parameters
            
        Returns:
            JSON response or None
        """
        url = self._build_url(endpoint)
        response = self._request_with_retry(
            "POST",
            url,
            data=data,
            json=json,
            **kwargs
        )
        
        if response:
            try:
                return response.json()
            except ValueError:
                return {"status": "success", "text": response.text}
        return None

    def put(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make PUT request.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data
            **kwargs: Additional request parameters
            
        Returns:
            JSON response or None
        """
        url = self._build_url(endpoint)
        response = self._request_with_retry(
            "PUT",
            url,
            data=data,
            json=json,
            **kwargs
        )
        
        if response:
            try:
                return response.json()
            except ValueError:
                return {"status": "success"}
        return None

    def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> bool:
        """Make DELETE request.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            True if successful
        """
        url = self._build_url(endpoint)
        response = self._request_with_retry("DELETE", url, **kwargs)
        return response is not None


def main() -> None:
    """CLI for API client."""
    parser = argparse.ArgumentParser(description="Generic API client")
    parser.add_argument("endpoint", help="API endpoint")
    parser.add_argument(
        "--method",
        choices=["GET", "POST", "PUT", "DELETE"],
        default="GET"
    )
    parser.add_argument("--base-url", help="Base API URL")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--param", action="append", help="Query param (key=value)")
    parser.add_argument("--data", help="JSON data for POST/PUT")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    base_url = args.base_url or Config.API_BASE_URL
    api_key = args.api_key or Config.API_KEY
    
    client = APIClient(base_url=base_url, api_key=api_key)
    
    params = {}
    if args.param:
        for param in args.param:
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
    
    if args.method == "GET":
        result = client.get(args.endpoint, params=params)
    elif args.method == "POST":
        import json
        data = json.loads(args.data) if args.data else {}
        result = client.post(args.endpoint, json=data)
    elif args.method == "PUT":
        import json
        data = json.loads(args.data) if args.data else {}
        result = client.put(args.endpoint, json=data)
    else:
        result = client.delete(args.endpoint)
    
    if result:
        if args.output:
            save_json(result, Config.DATA_DIR / args.output)
            logger.info(f"Saved to {args.output}")
        else:
            import json
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()