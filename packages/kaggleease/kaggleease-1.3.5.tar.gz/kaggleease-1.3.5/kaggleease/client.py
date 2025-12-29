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
        """
        try:
            self._ensure_auth()
            url = f"{self.BASE_URL}/datasets/list"
            params = {
                "search": query,
                "sortBy": "relevance",  # Use relevance for better fuzzy matches
                "pageSize": top,
                "page": 1
            }
            response = requests.get(url, auth=self.auth, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Search failed with status {response.status_code}: {response.text}")
                return []
            
            results = response.json()
            formatted = []
            for d in results:
                handle = d.get("ref") or d.get("handle")
                if not handle:
                    # Some responses use ownerRef/slug instead of ref
                    owner = d.get("ownerRef")
                    slug = d.get("slug")
                    if owner and slug:
                        handle = f"{owner}/{slug}"
                
                if handle:
                    formatted.append({
                        "handle": handle,
                        "title": d.get("title", handle),
                        "size": int(d.get("totalBytes", 0) or 0),
                        "votes": int(d.get("voteCount", 0) or d.get("votes", 0) or 0)
                    })
            return formatted
        except Exception as e:
            logger.debug(f"Kaggle REST search error: {e}")
            return []

    def list_files(self, dataset_handle: str) -> List[Dict]:
        """
        List files in a dataset with self-healing logic for 404 errors.
        """
        self._ensure_auth()
        
        if '/' not in dataset_handle:
             raise DatasetNotFoundError(f"Invalid dataset handle: '{dataset_handle}'. Expected 'owner/slug'.")
        
        # Normalize: ensure no leading/trailing slashes or spaces
        handle = dataset_handle.strip().strip('/')
        owner, slug = handle.split('/', 1)
        
        # Try primary endpoint
        url = f"{self.BASE_URL}/datasets/list/files/{owner}/{slug}"
        logger.debug(f"Trying primary list_files URL: {url}")
        
        response = requests.get(url, auth=self.auth, timeout=30)
        
        # Fallback: Maybe the handle itself works better?
        if response.status_code == 404:
            url_alt = f"{self.BASE_URL}/datasets/list/files/{handle}"
            logger.debug(f"Primary failed, trying alt URL: {url_alt}")
            response = requests.get(url_alt, auth=self.auth, timeout=30)
            
        if response.status_code == 404:
             # Intelligence: Verify if the dataset even exists via 'view'
             view_url = f"{self.BASE_URL}/datasets/view/{owner}/{slug}"
             view_res = requests.get(view_url, auth=self.auth, timeout=10)
             
             if view_res.status_code == 404:
                 raise DatasetNotFoundError(
                     f"Dataset '{handle}' not found on Kaggle.",
                     fix_suggestion=f"Check the handle spelling. Verified via view endpoint: 404."
                 )
             elif view_res.status_code == 403:
                 raise AuthError(
                     f"Access denied for '{handle}'.",
                     fix_suggestion="This dataset might be private or require you to accept rules on the Kaggle website."
                 )
             else:
                 raise DatasetNotFoundError(
                     f"Dataset '{handle}' exists but files cannot be listed (Status {response.status_code}).",
                     fix_suggestion="The dataset might be empty or in a competition-only format not supported by this API."
                 )

        elif response.status_code == 403:
            raise AuthError(f"Access denied for '{handle}'. Check your credentials or dataset permissions.")
        elif response.status_code != 200:
            raise Exception(f"Failed to list files (Status {response.status_code}): {response.text}")
            
        data = response.json()
        files = data if isinstance(data, list) else data.get("files", [])
        return [{"name": f.get("name"), "size": f.get("totalBytes", 0)} for f in files]
