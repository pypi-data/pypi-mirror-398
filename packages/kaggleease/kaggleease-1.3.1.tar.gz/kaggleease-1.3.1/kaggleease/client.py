import requests
import logging
from typing import List, Dict, Optional
from .auth import get_kaggle_credentials, setup_auth
from .errors import AuthError, DatasetNotFoundError

logger = logging.getLogger(__name__)

class KaggleClient:
    """
    A minimal internal client to interact with the Kaggle REST API directly.
    Replaces the heavy 'kaggle' package for metadata and search.
    """
    BASE_URL = "https://www.kaggle.com/api/v1"

    def __init__(self):
        self.auth = None

    def _ensure_auth(self):
        """Ensure credentials are loaded and set for Basic Auth."""
        if not self.auth:
            setup_auth()
            username, key = get_kaggle_credentials()
            if not username or not key:
                raise AuthError(
                    "Kaggle credentials not found. "
                    "Please place kaggle.json in ~/.kaggle/ or set KAGGLE_USERNAME and KAGGLE_KEY."
                )
            self.auth = (username, key)

    def search_datasets(self, query: str, top: int = 5) -> List[Dict]:
        """
        Search for datasets using the Kaggle REST API.
        
        Args:
            query (str): Search term.
            top (int): Number of results.
            
        Returns:
            List[Dict]: List of datasets with handle, title, size, and votes.
        """
        try:
            self._ensure_auth()
            url = f"{self.BASE_URL}/datasets/list"
            params = {
                "search": query,
                "sortBy": "votes",
                "pageSize": top
            }
            response = requests.get(url, auth=self.auth, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Search failed with status {response.status_code}: {response.text}")
                return []
            
            results = response.json()
            formatted = []
            for d in results:
                formatted.append({
                    "handle": d.get("ref"),
                    "title": d.get("title"),
                    "size": d.get("totalBytes", 0),
                    "votes": d.get("votes", 0)
                })
            return formatted
        except Exception as e:
            logger.debug(f"Kaggle REST search error: {e}")
            return []

    def list_files(self, dataset_handle: str) -> List[Dict]:
        """
        List files in a dataset.
        
        Args:
            dataset_handle (str): owner/slug
            
        Returns:
            List[Dict]: List of file info (name, size).
        """
        self._ensure_auth()
        url = f"{self.BASE_URL}/datasets/list/files/{dataset_handle}"
        
        response = requests.get(url, auth=self.auth, timeout=30)
        
        if response.status_code == 404:
            raise DatasetNotFoundError(f"Dataset '{dataset_handle}' not found.")
        elif response.status_code == 403:
            raise AuthError(f"Access denied for dataset '{dataset_handle}'. Check your permissions.")
        elif response.status_code != 200:
            raise Exception(f"Failed to list files (Status {response.status_code}): {response.text}")
            
        # The list/files response contains a list of File objects with 'name' and 'totalBytes'
        data = response.json()
        files = data if isinstance(data, list) else data.get("files", [])
        
        # Standardize for load.py
        return [{"name": f.get("name"), "size": f.get("totalBytes", 0)} for f in files]
