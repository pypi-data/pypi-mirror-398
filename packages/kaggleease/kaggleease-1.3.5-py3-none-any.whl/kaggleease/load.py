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
    KaggleEaseError,
)
from .progress import check_memory_safety

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
    
    # If the handle is a single slug, we'll try to resolve it in the load() function
    if '/' not in dataset_handle:
        if not re.match(r'^[a-zA-Z0-9_-]+$', dataset_handle):
            raise DatasetNotFoundError(
                f"Invalid dataset slug: '{dataset_handle}'. "
                "Only alphanumeric characters, hyphens, and underscores are allowed."
            )
        return
    
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
        from .client import KaggleClient
        client = KaggleClient()
        files = client.list_files(dataset_handle)
        
        # files is a list of dicts like [{"name": "...", "size": ...}]
        # Map back to simple objects for existing logic or simplify
        from collections import namedtuple
        KaggleFile = namedtuple('KaggleFile', ['name', 'size'])
        standard_files = [KaggleFile(f['name'], f['size']) for f in files]
        
        total_size = sum(f.size for f in standard_files)
        return standard_files, total_size
    except Exception as e:
        # Differentiate error types for better user guidance
        error_msg = str(e).lower()
        
        if "not found" in error_msg or "404" in error_msg or "inaccessible" in error_msg:
            # Intelligence: Try to find what they meant
            fix = "Check the spelling of your dataset handle or use search() to find it."
            
            if '/' in dataset_handle:
                from .search import search
                owner, slug = dataset_handle.split('/')
                potential = search(slug, top=3)
                if potential:
                    # Filter out the handle itself if it's already failing
                    names = [p['handle'] for p in potential if p['handle'].lower() != dataset_handle.lower()]
                    if names:
                        fix = f"Did you mean one of these? {', '.join(names)}"
                    else:
                        fix = "This dataset might be private or require you to accept rules on the Kaggle website."
            
            error_class = DatasetNotFoundError
            final_msg = f"Dataset '{dataset_handle}' not found or inaccessible."
            
            if "403" in error_msg or "access denied" in error_msg:
                from .errors import AuthError
                error_class = AuthError
                final_msg = f"Access denied for dataset '{dataset_handle}'."
                fix = "This dataset might be private or require you to accept rules on the Kaggle website."
            
            raise error_class(
                final_msg,
                fix_suggestion=fix
            ) from e
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            from .errors import AuthError
            raise AuthError(
                f"Authentication failed while accessing '{dataset_handle}'.",
                fix_suggestion="If this is Colab, upload kaggle.json. Locally, check ~/.kaggle/kaggle.json permissions."
            ) from e
        else:
            raise DatasetNotFoundError(
                f"Could not find or access dataset '{dataset_handle}'.",
                fix_suggestion="Check the spelling or try searching for it using kaggleease.search()"
            ) from e

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


def load(dataset_handle: str, file: Optional[str] = None, timeout: int = 300, **kwargs) -> pd.DataFrame:
    """
    The main function to load a Kaggle dataset into a pandas DataFrame.

    It handles authentication, metadata pre-scan, file resolution,
    caching, and data loading.

    Args:
        dataset_handle (str): The Kaggle dataset handle (e.g., "owner/dataset-name" or "titanic").
        file (str, optional): The specific file to load from the dataset.
        timeout (int): Timeout in seconds for API calls and downloads.
        **kwargs: Additional arguments passed to pd.read_csv or pd.read_parquet.

    Returns:
        pandas.DataFrame: The loaded dataset.
    """
    try:
        # Validate dataset handle format
        _validate_dataset_handle(dataset_handle)
        
        # Implicit resolution for single slugs
        if '/' not in dataset_handle:
            from .search import search
            results = search(dataset_handle, top=1)
            if not results:
                raise DatasetNotFoundError(f"Could not find any dataset matching slug '{dataset_handle}'")
            best_match = results[0]
            original_handle = dataset_handle
            dataset_handle = best_match['handle']
            logger.info(f"Resolved slug '{original_handle}' to '{dataset_handle}' ('{best_match['title']}' with {best_match['votes']} votes)")
        
        setup_auth()

        # Metadata Pre-scan
        files, total_size = _get_dataset_files(dataset_handle, timeout=timeout)
        if total_size > 5 * 1024**3:  # 5GB
            logger.warning(f"Dataset is large ({total_size / 1024**3:.2f} GB). Download may take a while.")
        
        # Memory-safety check
        if 'chunksize' not in kwargs:
            check_memory_safety(total_size)

        # File Resolution
        target_file = _resolve_file_path(files, dataset_handle, file)

        # Caching and Download
        local_file_path = get_dataset_path(dataset_handle, target_file, timeout=timeout)

        # Loading into pandas
        logger.info(f"Loading '{target_file}' into a pandas DataFrame...")
        target_file_lower = target_file.lower()
        if target_file_lower.endswith(".csv"):
            return pd.read_csv(local_file_path, **kwargs)
        elif target_file_lower.endswith(".parquet"):
            return pd.read_parquet(local_file_path, **kwargs)
        else:
            raise DataFormatError(f"Unsupported file format for: {target_file}")
            
    except KaggleEaseError:
        # Re-raise our own errors
        raise
    except Exception as e:
        # Shield raw stacktraces, translate to KaggleEaseError
        error_msg = str(e)
        logger.error(f"Unexpected error: {error_msg}")
        raise KaggleEaseError(
            f"Failed to load dataset: {error_msg}\n"
            "This might be a data format issue or network failure. "
            "Try specifying the file explicitly or check your connection."
        ) from None
