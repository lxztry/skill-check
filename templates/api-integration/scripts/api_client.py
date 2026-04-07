#!/usr/bin/env python3
"""
API Client - Example API integration script
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 0


class APIClient:
    """Example API client with retry logic"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get('API_KEY')
        self.base_url = base_url or os.environ.get('API_BASE_URL', 'https://api.example.com')
        self.timeout = int(os.environ.get('TIMEOUT', '30'))
        self.retry_count = int(os.environ.get('RETRY_COUNT', '3'))
        
        if not self.api_key:
            raise ValueError("API key required. Set API_KEY environment variable.")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request with retry logic"""
        import requests
        
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.api_key}'
        headers['Content-Type'] = 'application/json'
        
        for attempt in range(self.retry_count):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                if response.status_code >= 400:
                    return APIResponse(
                        success=False,
                        error=response.text,
                        status_code=response.status_code
                    )
                
                return APIResponse(
                    success=True,
                    data=response.json() if response.text else None,
                    status_code=response.status_code
                )
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == self.retry_count - 1:
                    return APIResponse(success=False, error="Request timeout")
            except Exception as e:
                return APIResponse(success=False, error=str(e))
        
        return APIResponse(success=False, error="Max retries exceeded")
    
    def get(self, endpoint: str, params: Dict = None) -> APIResponse:
        """GET request"""
        return self._request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict = None) -> APIResponse:
        """POST request"""
        return self._request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Dict = None) -> APIResponse:
        """PUT request"""
        return self._request('PUT', endpoint, json=data)
    
    def delete(self, endpoint: str) -> APIResponse:
        """DELETE request"""
        return self._request('DELETE', endpoint)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        endpoint = sys.argv[1]
        client = APIClient()
        result = client.get(endpoint)
        print(json.dumps(result.__dict__, indent=2))
    else:
        print("Usage: python api_client.py <endpoint>")
