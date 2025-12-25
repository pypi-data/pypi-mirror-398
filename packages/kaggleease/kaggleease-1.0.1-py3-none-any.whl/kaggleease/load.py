import os
import re
from typing import Tuple, List, Optional
import pandas as pd
from pathlib import Path
import logging
from .auth import setup_auth
from .cache import get_dataset_path
from .errors import (
    DataFormatError,
    DatasetNotFoundError,
    MultipleFilesError,
    UnsupportedFormatError,
)

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

def _get_dataset_files(dataset_handle: str, timeout: int = 30) -> Tuple[List, int]:
    """
    Performs a metadata pre-scan of the dataset.

    Args:
        dataset_handle (str): The Kaggle dataset handle.
        timeout (int): Timeout in seconds for the API call.

    Returns:
        tuple: A tuple containing (files, total_size) where files is a list of file objects
               and total_size is the sum of all file sizes in bytes.

    Raises:
        DatasetNotFoundError: If the dataset cannot be found or accessed.
        AuthError: If authentication fails.
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        # Add timeout configuration for the API call
        files = api.dataset_list_files(dataset_handle, timeout=timeout).files
        total_size = sum(f.size for f in files)
        return files, total_size
    except Exception as e:
        # Differentiate error types for better user guidance
        error_msg = str(e).lower()
        
        if "not found" in error_msg or "404" in error_msg:
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
            raise DatasetNotFoundError(
                f"Network timeout while accessing metadata for '{dataset_handle}'. "
                f"Please check your internet connection and try again."
            ) from e
        else:
            raise DatasetNotFoundError(f"Could not find or access dataset '{dataset_handle}'. Is the handle correct?") from e

def _resolve_file_path(files: List, dataset_handle: str, file_name: Optional[str] = None) -> str:
    """
    Implements the strict file resolution logic.

    Args:
        files (list): List of file objects from the dataset.
        dataset_handle (str): The Kaggle dataset handle.
        file_name (str, optional): Specific file name to load.

    Returns:
        str: The name of the file to load.

    Raises:
        DataFormatError: If the specified file is not found.
        UnsupportedFormatError: If no supported files are found.
        MultipleFilesError: If multiple supported files are found but none is specified.
    """
    file_names = [f.name for f in files]

    # Case 1: file explicitly provided
    if file_name:
        if file_name in file_names:
            return file_name
        else:
            raise DataFormatError(
                f"The file '{file_name}' was not found in the dataset.\n"
                f"Available files: {', '.join(file_names)}"
            )

    # Case 2: Auto-resolution
    supported_files = [f for f in file_names if f.lower().endswith(".csv") or f.lower().endswith(".parquet")]

    if not supported_files:
        raise UnsupportedFormatError(
            "No supported files found (CSV or Parquet).\n"
            f"Available files: {', '.join(file_names)}"
        )

    if len(supported_files) > 1:
        raise MultipleFilesError(
            "Multiple supported files found. Please specify which one to load.\n"
            f"Found: {', '.join(supported_files)}\n"
            f'Fix: load("{dataset_handle}", file="{supported_files[0]}")'
        )

    return supported_files[0]


def load(dataset_handle: str, file: Optional[str] = None, timeout: int = 300) -> pd.DataFrame:
    """
    The main function to load a Kaggle dataset into a pandas DataFrame.

    It handles authentication, metadata pre-scan, file resolution,
    caching, and data loading.

    Args:
        dataset_handle (str): The Kaggle dataset handle (e.g., "owner/dataset-name").
        file (str, optional): The specific file to load from the dataset.
        timeout (int): Timeout in seconds for API calls and downloads.

    Returns:
        pandas.DataFrame: The loaded dataset.
    """
    # Validate dataset handle format
    _validate_dataset_handle(dataset_handle)
    
    setup_auth()

    # Metadata Pre-scan
    files, total_size = _get_dataset_files(dataset_handle, timeout=timeout)
    if total_size > 5 * 1024**3:  # 5GB
        logger.warning(f"Dataset is large ({total_size / 1024**3:.2f} GB). Download may take a while.")

    # File Resolution
    target_file = _resolve_file_path(files, dataset_handle, file)

    # Caching and Download
    # We download the specific file, not the whole dataset bundle
    local_file_path = get_dataset_path(dataset_handle, target_file, timeout=timeout)

    # Loading into pandas
    logger.info(f"Loading '{target_file}' into a pandas DataFrame...")
    target_file_lower = target_file.lower()
    if target_file_lower.endswith(".csv"):
        return pd.read_csv(local_file_path)
    elif target_file_lower.endswith(".parquet"):
        return pd.read_parquet(local_file_path)
    else:
        # This case should be prevented by the resolution logic, but is here for safety
        raise DataFormatError(f"Unsupported file format for: {target_file}")
