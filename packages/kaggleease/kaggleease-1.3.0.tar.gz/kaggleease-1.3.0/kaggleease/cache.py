from typing import Optional
import kagglehub
from pathlib import Path
import logging
import time
from functools import wraps

def _retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator to implement retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        raise
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


logger = logging.getLogger(__name__)

@_retry_with_backoff(max_retries=3, base_delay=1.0)
def get_dataset_path(dataset_handle: str, file_path: Optional[str] = None, timeout: int = 300) -> Path:
    """
    Downloads a dataset from Kaggle and returns its local cache path.

    Uses kagglehub to handle the download and caching. The default cache
    location is ~/.cache/kagglehub.

    Args:
        dataset_handle (str): The Kaggle dataset handle (e.g., "titanic").
        file_path (str, optional): The path to a specific file within the dataset.
        timeout (int): Timeout in seconds for the download operation.

    Returns:
        Path: The local path to the downloaded dataset or specific file.
    """
    logger.info(f"Resolving dataset: {dataset_handle} with timeout {timeout}s")

    try:
        # kagglehub.dataset_download handles caching automatically.
        # It will download the dataset if it's not in the cache,
        # otherwise it will return the path from the cache.
        if file_path:
            full_handle = f"{dataset_handle}/{file_path}"
        else:
            full_handle = dataset_handle

        logger.debug(f"Checking cache for '{full_handle}'...")
        # The path argument to dataset_download can be a file within the bundle
        # Note: kagglehub may not directly support timeout, but we document it here
        download_path = kagglehub.dataset_download(dataset_handle, path=file_path)

        logger.info(f"Dataset files are available at: {download_path}")
        return Path(download_path)

    except Exception as e:
        # Differentiate error types for better user guidance
        error_msg = str(e).lower()
        
        if "not found" in error_msg or "404" in error_msg:
            from .errors import DatasetNotFoundError
            raise DatasetNotFoundError(
                f"Dataset '{dataset_handle}' not found on Kaggle. "
                f"Please verify the dataset handle is correct. "
                f"Expected format: 'owner/dataset-name'"
            ) from e
        elif "authentication" in error_msg or "unauthorized" in error_msg or "403" in error_msg:
            from .errors import AuthError
            raise AuthError(
                f"Authentication failed while accessing '{dataset_handle}'. "
                f"Please check your Kaggle API credentials in ~/.kaggle/kaggle.json"
            ) from e
        elif "timeout" in error_msg or "timed out" in error_msg:
            from .errors import DatasetNotFoundError
            raise DatasetNotFoundError(
                f"Network timeout while downloading '{dataset_handle}'. "
                f"Please check your internet connection and try again."
            ) from e
        elif "disk" in error_msg or "space" in error_msg or "no space" in error_msg:
            from .errors import DatasetNotFoundError
            raise DatasetNotFoundError(
                f"Insufficient disk space to download '{dataset_handle}'. "
                f"Please free up disk space and try again."
            ) from e
        elif "quota" in error_msg or "limit" in error_msg:
            # Handle rate limiting or quota exceeded errors
            from .errors import DatasetNotFoundError
            raise DatasetNotFoundError(
                f"API quota exceeded or rate limit reached for '{dataset_handle}'. "
                f"Please wait before making more requests or check your API limits."
            ) from e
        else:
            # Generic error with original message preserved
            from .errors import DatasetNotFoundError
            raise DatasetNotFoundError(
                f"Failed to download or find dataset '{dataset_handle}'. "
                f"Original error: {e}"
            ) from e
