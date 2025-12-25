from typing import Dict, List, Optional

import requests


class BaseAPIClient:
    """Base class containing common API functionality"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token

    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers with authorization and content type"""
        return {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}

    def _get_headers_without_content_type(self) -> Dict[str, str]:
        """Get headers without content type (for file uploads)"""
        return {"Authorization": f"Token {self.token}"}

    def _get_paginated_data(
        self, url: str, params: dict = {}, max_results: Optional[int] = None
    ) -> List[dict]:
        """Get all paginated data from an endpoint"""
        next_url = url
        data = []
        total_fetched = 0
        use_https = url.startswith("https://")
        is_first_call = True

        while next_url:
            # Ensure HTTPS consistency if base URL uses HTTPS
            if use_https and next_url.startswith("http://"):
                next_url = next_url.replace("http://", "https://")
            if is_first_call:
                response = requests.get(next_url, headers=self._get_headers(), params=params)
                is_first_call = False
            else:
                response = requests.get(next_url, headers=self._get_headers())
            response.raise_for_status()
            response_data = response.json()
            results = response_data["results"]
            if max_results is not None:
                remaining = max_results - len(data)
                results = results[:remaining]
            data.extend(results)
            total_fetched += len(results)
            if max_results is not None and total_fetched >= max_results:
                break
            next_url = response_data.get("next")

        return data
