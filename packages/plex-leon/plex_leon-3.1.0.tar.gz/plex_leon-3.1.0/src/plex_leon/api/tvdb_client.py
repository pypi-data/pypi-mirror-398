"""TVDB API client for fetching TV show metadata.

This module provides a client for interacting with The TVDB API v4.
It handles authentication and fetching season/episode information for TV shows.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None


class TVDBClient:
    """Client for The TVDB API v4.
    
    Requires a TVDB API key set in the environment variable TVDB_API_KEY.
    """
    
    BASE_URL = "https://api4.thetvdb.com/v4/"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the TVDB client.
        
        Parameters
        ----------
        api_key : str, optional
            TVDB API key. If not provided, will look for TVDB_API_KEY
            environment variable.
        """
        if requests is None:
            raise ImportError(
                "requests library is required for TVDB API. "
                "Install it with: pip install requests"
            )
        
        self.api_key = api_key or os.environ.get("TVDB_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TVDB API key is required. Set TVDB_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def _get_token(self) -> str:
        """Get or refresh the authentication token.
        
        Returns
        -------
        str
            Valid authentication token.
        """
        # Check if we have a valid token
        if self._token and time.time() < self._token_expires_at:
            return self._token
        
        # Request a new token
        url = urljoin(self.BASE_URL, "login")
        response = requests.post(
            url,
            json={"apikey": self.api_key},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        self._token = data["data"]["token"]
        # Token typically expires in 1 month, but we'll refresh after 29 days
        self._token_expires_at = time.time() + (29 * 24 * 60 * 60)
        
        return self._token
    
    def _request(self, endpoint: str) -> dict:
        """Make an authenticated request to the TVDB API.
        
        Parameters
        ----------
        endpoint : str
            API endpoint (without base URL).
        
        Returns
        -------
        dict
            JSON response data.
        """
        token = self._get_token()
        url = urljoin(self.BASE_URL, endpoint)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def get_series_episodes(self, tvdb_id: int) -> Dict[int, int]:
        """Get episode counts per season for a TV series.
        
        Parameters
        ----------
        tvdb_id : int
            The TVDB series ID.
        
        Returns
        -------
        Dict[int, int]
            Mapping of season number to episode count. Season 0 (specials)
            is excluded.
        """
        # Get all episodes for the series
        # TVDB API v4 uses extended endpoint for full episode data
        endpoint = f"series/{tvdb_id}/episodes/default"
        
        season_counts: Dict[int, int] = {}
        page = 0
        
        while True:
            try:
                # Add page parameter if not the first page
                page_endpoint = endpoint if page == 0 else f"{endpoint}?page={page}"
                data = self._request(page_endpoint)
                
                episodes = data.get("data", {}).get("episodes", [])
                if not episodes:
                    break
                
                # Count episodes per season
                for episode in episodes:
                    season_num = episode.get("seasonNumber")
                    # Skip specials (season 0) and invalid data
                    if season_num is None or season_num == 0:
                        continue
                    
                    season_counts[season_num] = season_counts.get(season_num, 0) + 1
                
                # Check if there are more pages
                links = data.get("links", {})
                if not links.get("next"):
                    break
                
                page += 1
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # Series not found or no episodes
                    break
                raise
        
        return season_counts
    
    def get_series_info(self, tvdb_id: int) -> Optional[Dict]:
        """Get basic information about a TV series.
        
        Parameters
        ----------
        tvdb_id : int
            The TVDB series ID.
        
        Returns
        -------
        dict or None
            Series information including name, year, etc., or None if not found.
        """
        try:
            endpoint = f"series/{tvdb_id}"
            data = self._request(endpoint)
            return data.get("data")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
