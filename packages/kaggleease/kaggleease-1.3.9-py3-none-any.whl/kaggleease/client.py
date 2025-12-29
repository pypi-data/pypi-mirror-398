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
        List files in a dataset or competition. Detects resource type.
        """
        self._ensure_auth()
        handle = dataset_handle.strip().strip('/')
        
        # 1. Try Dataset API
        if '/' in handle:
            owner, slug = handle.split('/', 1)
            url = f"{self.BASE_URL}/datasets/list/files/{owner}/{slug}"
            response = requests.get(url, auth=self.auth, timeout=30)
            if response.status_code == 200:
                data = response.json()
                files = data if isinstance(data, list) else data.get("files", [])
                return [{"name": f.get("name"), "size": f.get("totalBytes", 0), "type": "dataset"} for f in files]

        # 2. Try Competition API
        # Many handles like 'titanic' are competitions
        slug = handle.split('/')[-1]
        comp_url = f"{self.BASE_URL}/competitions/storage/list/files/{slug}"
        comp_response = requests.get(comp_url, auth=self.auth, timeout=30)
        
        if comp_response.status_code == 200:
            data = comp_response.json()
            # Competitions often return a different structure
            files = data if isinstance(data, list) else data.get("files", [])
            return [{"name": f.get("name"), "size": f.get("totalBytes", 0), "type": "competition"} for f in files]

        # 3. Final Stand: Search verification for metadata ONLY
        # If we can't find files but search finds the handle, we signal "Unknown Files"
        search_results = self.search_datasets(handle, top=1)
        for r in search_results:
            if r['handle'].lower() == handle.lower():
                # Signal to load.py: "Dataset exists, but files are obscured. Download everything."
                return [{"name": f"__AUTO_RESOLVE_{handle}__", "size": r['size'], "type": "dataset"}]

        # 4. Actual 404
        raise DatasetNotFoundError(
            f"Dataset or Competition '{handle}' not found or inaccessible.",
            fix_suggestion="Check the spelling or try searching for it using kaggleease.search()"
        )
