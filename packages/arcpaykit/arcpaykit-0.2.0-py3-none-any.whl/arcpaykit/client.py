"""HTTP client for ArcPayKit API requests."""

import json
from typing import Any, Dict, Optional
import requests


class ArcPayError(Exception):
    """Base exception for ArcPayKit errors."""
    pass


class ArcPayClient:
    """HTTP client for making requests to the ArcPayKit API."""
    
    def __init__(self, api_key: str, base_url: str = "https://pay.arcpaykit.com"):
        """
        Initialize the ArcPay client.
        
        Args:
            api_key: Your ArcPay API key
            base_url: Base URL for the API (defaults to production)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
    
    def request(
        self, 
        path: str, 
        method: str = "GET", 
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Make an HTTP request to the ArcPayKit API.
        
        Args:
            path: API endpoint path (e.g., "/api/payments/create")
            method: HTTP method (GET, POST, etc.)
            data: Request body data (will be JSON encoded)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            ArcPayError: If the request fails
        """
        url = f"{self.base_url}{path}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=kwargs.get("params"), **kwargs)
            elif method.upper() == "POST":
                response = self.session.post(
                    url, 
                    json=data, 
                    **{k: v for k, v in kwargs.items() if k != "params"}
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, 
                    json=data, 
                    **{k: v for k, v in kwargs.items() if k != "params"}
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(url, **kwargs)
            else:
                response = self.session.request(
                    method, 
                    url, 
                    json=data, 
                    **kwargs
                )
            
            # Handle errors
            if not response.ok:
                error_text = response.text
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", error_data.get("message", error_text))
                except (json.JSONDecodeError, ValueError):
                    error_message = error_text or f"HTTP {response.status_code}: {response.reason}"
                
                raise ArcPayError(f"HTTP {response.status_code}: {error_message}")
            
            # Return parsed JSON
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ArcPayError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise ArcPayError(f"Invalid JSON response: {str(e)}")

