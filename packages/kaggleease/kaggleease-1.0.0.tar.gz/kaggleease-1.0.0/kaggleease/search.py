from typing import List, Dict, Optional
from .auth import setup_auth
import re
import logging
from .errors import DatasetNotFoundError

logger = logging.getLogger(__name__)

def _validate_dataset_handle(dataset_handle: str) -> None:
    """
    Validate that a dataset handle follows the expected format.
    
    Args:
        dataset_handle (str): The dataset handle to validate.
    
    Raises:
        DatasetNotFoundError: If the handle format is invalid.
    """
    if not dataset_handle or not isinstance(dataset_handle, str):
        raise DatasetNotFoundError("Dataset handle must be a non-empty string.")
    
    # Check for the expected format: owner/dataset-name
    if '/' not in dataset_handle:
        raise DatasetNotFoundError(
            f"Invalid dataset handle format: '{dataset_handle}'. "
            "Expected format: 'owner/dataset-name' (e.g., 'kaggle/titanic')"
        )
    
    parts = dataset_handle.split('/')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise DatasetNotFoundError(
            f"Invalid dataset handle format: '{dataset_handle}'. "
            "Expected format: 'owner/dataset-name' with both owner and dataset name."
        )
    
    # Validate characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', dataset_handle):
        raise DatasetNotFoundError(
            f"Invalid characters in dataset handle: '{dataset_handle}'. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )

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
        timeout (int): Timeout in seconds for the API call.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              information about a dataset. Returns an empty list
              if the search fails.
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        setup_auth()
        api = KaggleApi()
        api.authenticate()

        # Add timeout configuration for the API call
        results = api.dataset_list(search=query, sort_by='votes', page_size=top, timeout=timeout)

        # Additional safety check for None or invalid return values
        if not results or results is None:
            logger.warning(f"No datasets found for query: '{query}'")
            return []

        formatted_results = []
        for dataset in results:
            formatted_results.append({
                "handle": dataset.ref,
                "title": dataset.title,
                "size": _format_size(dataset.totalBytes),
                "votes": dataset.votes,
            })
        return formatted_results

    except Exception as e:
        # Differentiate error types for better user guidance
        error_msg = str(e).lower()
        
        if "timeout" in error_msg or "timed out" in error_msg:
            logger.error(f"Network timeout while searching for '{query}'. Please check your internet connection and try again.")
        else:
            logger.error(f"An error occurred during the search operation: {e}")
        return []
