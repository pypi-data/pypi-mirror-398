from typing import List, Dict, Optional
from .auth import setup_auth
import re
import logging
from .errors import DatasetNotFoundError

logger = logging.getLogger(__name__)


def _format_size(bytes_size: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_size (int): Size in bytes.
    
    Returns:
        str: Human-readable size string (e.g., "1.5 GB", "250 MB").
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 ** 2:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 ** 3:
        return f"{bytes_size / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_size / (1024 ** 3):.2f} GB"

def search(query: str, top: int = 5, timeout: int = 30) -> List[Dict[str, str|int]]:
    """
    Searches for datasets on Kaggle.

    Args:
        query (str): The search query.
        top (int): The maximum number of results to return.
        timeout (int): Timeout in seconds for the API call (ignored).

    Returns:
        list: A list of dictionaries, where each dictionary contains
              information about a dataset. Returns an empty list
              if the search fails.
    """
    try:
        from .client import KaggleClient
        client = KaggleClient()
        results = client.search_datasets(query, top=top)

        # Additional safety check for None or invalid return values
        if not results:
            logger.warning(f"No datasets found for query: '{query}'")
            return []

        formatted_results = []
        for dataset in results:
            formatted_results.append({
                "handle": dataset["handle"],
                "title": dataset["title"],
                "size": _format_size(dataset["size"]),
                "votes": dataset["votes"],
            })
        return formatted_results

    except Exception as e:
        # Differentiate error types for better user guidance
        error_msg = str(e).lower()
        
        if "timeout" in error_msg or "timed out" in error_msg:
            logger.error(f"Network timeout while searching for '{query}'. Please check your internet connection and try again.")
        else:
            logger.error(f"An error occurred during the search operation: {e}")
        
        # Return empty list instead of crashing, per "No stacktraces" for supporting features
        return []
