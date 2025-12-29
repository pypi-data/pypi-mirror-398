"""
Main WHOOP SDK client for making API calls.
"""

import requests
from typing import Dict, Any, Optional, List
from .auth import AuthManager


class Whoop:
    """
    Main WHOOP SDK client for accessing WHOOP developer API data.
    """
    
    BASE_URL = "https://api.prod.whoop.com/developer/v2"
    
    def __init__(self):
        """Initialize the WHOOP client with authentication."""
        self.auth = AuthManager()
    
    def login(self) -> bool:
        """
        Perform OAuth login to authenticate with WHOOP.
        
        Returns:
            bool: True if login was successful
            
        Note:
            This only needs to be called once. Tokens are saved automatically.
        """
        return self.auth.login()
    
    def reset_config(self) -> None:
        """
        Reset/clear all stored configuration and tokens.
        
        Use this if you need to re-authenticate with different credentials.
        """
        self.auth.reset_config()
    
    def reset_auth(self) -> bool:
        """
        Clear tokens only (keeps credentials) and trigger OAuth flow.
        
        Use this to re-authenticate without re-entering client credentials.
        
        Returns:
            bool: True if login was successful
        """
        return self.auth.reset_auth()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the WHOOP API.
        
        Args:
            endpoint: API endpoint (e.g., '/user/profile/basic')
            params: Query parameters
            
        Returns:
            Dict containing the API response
            
        Raises:
            RuntimeError: If authentication fails
            requests.HTTPError: If API request fails
        """
        # Get access token (auto-refreshes if needed)
        access_token = self.auth.ensure_access_token()
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Make the request
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()

    def _make_paginated_request(
        self,
        endpoint: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: Optional[int] = None,
        max_pages: Optional[int] = 3,
    ) -> Dict[str, Any]:
        """
        Make a paginated request that follows next_token and aggregates records.

        Args:
            endpoint: API endpoint path starting with '/'
            start: Optional ISO8601 start timestamp (with Z)
            end: Optional ISO8601 end timestamp (with Z)
            limit: Page size per request (API default if not provided)
            max_pages: Max number of pages to fetch (default 3). None = no page cap.

        Returns:
            Dict with a single key 'records' containing aggregated list
        """
        aggregated: List[Dict[str, Any]] = []
        next_token: Optional[str] = None
        pages: int = 0

        while True:
            if max_pages is not None and pages >= max_pages:
                break
            params: Dict[str, Any] = {}
            
            # Only include start/end/limit on the FIRST request (when there's no next_token)
            # The next_token encodes all pagination state (filters + page size) for subsequent requests
            if not next_token:
                if start:
                    params["start"] = start
                if end:
                    params["end"] = end
                if limit is not None:
                    params["limit"] = limit
            else:
                # For subsequent requests, only use nextToken (API expects camelCase)
                # The nextToken already contains all the necessary state
                params["nextToken"] = next_token

            resp = self._make_request(endpoint, params=params)
            page_records = resp.get("records", []) or []

            aggregated.extend(page_records)

            next_token = resp.get("next_token")
            pages += 1
            if not next_token:
                break

        return {"records": aggregated}
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get the user's basic profile information.
        
        Returns:
            Dict containing user profile data (user_id, email, first_name, last_name, etc.)
        """
        return self._make_request("/user/profile/basic")
    
    def get_recovery(self, start: Optional[str] = None, end: Optional[str] = None, limit: Optional[int] = None, max_pages: Optional[int] = 3) -> Dict[str, Any]:
        """
        Get recovery data for the user.
        
        Args:
            start: Optional ISO start date (e.g., '2024-01-01T00:00:00.000Z')
            end: Optional ISO end date (e.g., '2024-01-31T23:59:59.999Z')
            limit: Page size (WHOOP defaults to 10, max 25)
            max_pages: Max pages to fetch (default 3). None = no page cap.
            
        Returns:
            Dict containing recovery records
        """
        return self._make_paginated_request(
            "/recovery", start=start, end=end, limit=limit, max_pages=max_pages
        )
    
    def get_sleep(self, start: Optional[str] = None, end: Optional[str] = None, limit: Optional[int] = None, max_pages: Optional[int] = 3) -> Dict[str, Any]:
        """
        Get sleep data for the user.
        
        Args:
            start: Optional ISO start date (e.g., '2024-01-01T00:00:00.000Z')
            end: Optional ISO end date (e.g., '2024-01-31T23:59:59.999Z')
            limit: Page size (WHOOP defaults to 10, max 25)
            max_pages: Max pages to fetch (default 3). None = no page cap.
            
        Returns:
            Dict containing sleep records
        """
        return self._make_paginated_request(
            "/activity/sleep", start=start, end=end, limit=limit, max_pages=max_pages
        )
    
    def get_sleep_by_id(self, sleep_id: str) -> Dict[str, Any]:
        """
        Get a single sleep by its ID.
        
        Args:
            sleep_id: The WHOOP sleep ID
            
        Returns:
            Dict containing the sleep record
        """
        return self._make_request(f"/activity/sleep/{sleep_id}")
    
    def get_workouts(self, start: Optional[str] = None, end: Optional[str] = None, limit: Optional[int] = None, max_pages: Optional[int] = 3) -> Dict[str, Any]:
        """
        Get workout data for the user.
        
        Args:
            start: Optional ISO start date (e.g., '2024-01-01T00:00:00.000Z')
            end: Optional ISO end date (e.g., '2024-01-31T23:59:59.999Z')
            limit: Page size (WHOOP defaults to 10, max 25)
            max_pages: Max pages to fetch (default 3). None = no page cap.
            
        Returns:
            Dict containing workout records
        """
        return self._make_paginated_request(
            "/activity/workout", start=start, end=end, limit=limit, max_pages=max_pages
        )

    def get_workout_by_id(self, workout_id: str) -> Dict[str, Any]:
        """
        Get a single workout by its ID.
        
        Args:
            workout_id: The WHOOP workout ID
            
        Returns:
            Dict containing the workout record
        """
        return self._make_request(f"/activity/workout/{workout_id}")

    def get_cycles(self, start: Optional[str] = None, end: Optional[str] = None, limit: Optional[int] = None, max_pages: Optional[int] = 3,) -> Dict[str, Any]:
        """
        Get cycle data for the user.

        Args:
            start: Optional ISO start date (e.g., '2024-01-01T00:00:00.000Z')
            end: Optional ISO end date (e.g., '2024-01-31T23:59:59.999Z')
            limit: Page size per request (WHOOP defaults to 10, max 25)
            max_pages: Max pages to fetch (default 3). None = no page cap.

        Returns:
            Dict containing cycle records
        """
        return self._make_paginated_request(
            "/cycle", start=start, end=end, limit=limit, max_pages=max_pages
        )

    def get_cycle_by_id(self, cycle_id: str) -> Dict[str, Any]:
        """
        Get a single cycle by its ID.
        
        Args:
            cycle_id: The WHOOP cycle ID
            
        Returns:
            Dict containing the cycle record
        """
        return self._make_request(f"/cycle/{cycle_id}")

    def get_sleep_by_cycle_id(self, cycle_id: str) -> Dict[str, Any]:
        """
        Get sleep for a given cycle ID.
        
        Args:
            cycle_id: The WHOOP cycle ID
            
        Returns:
            Dict containing the sleep record for the cycle
        """
        return self._make_request(f"/cycle/{cycle_id}/sleep")

    def get_recovery_by_cycle_id(self, cycle_id: str) -> Dict[str, Any]:
        """
        Get recovery for a given cycle ID.
        
        Args:
            cycle_id: The WHOOP cycle ID
            
        Returns:
            Dict containing the recovery record for the cycle
        """
        return self._make_request(f"/cycle/{cycle_id}/recovery")

    def get_body_measurements(
        self,
    ) -> Dict[str, Any]:
        """
        Get body measurements for the user.

        Args:
            None

        Returns:
            Dict containing body measurement data
            (height_meter, weight_kilogram, max_heart_rate)
        """
        return self._make_request(
            "/user/measurement/body"
        )
    
