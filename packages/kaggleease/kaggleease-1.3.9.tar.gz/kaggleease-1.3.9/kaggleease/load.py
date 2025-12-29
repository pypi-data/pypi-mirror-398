import os
import re
from typing import Tuple, List, Optional, Union
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
def _get_dataset_files(dataset_handle, timeout=300):
    """
    Finds files for a dataset handle, handles implicit resolution and competitions.
    Returns: (standard_files, total_size, resource_type, resolved_handle)
    """
    try:
        from .client import KaggleClient
        client = KaggleClient()
        files = client.list_files(dataset_handle)
        
        # files is a list of dicts like [{"name": "...", "size": ..., "type": "..."}]
        resource_type = files[0].get("type", "dataset") if files else "dataset"
        
        from collections import namedtuple
        KaggleFile = namedtuple('KaggleFile', ['name', 'size', 'type'])
        standard_files = [KaggleFile(f['name'], f['size'], f.get('type', 'dataset')) for f in files]
        
        total_size = sum(f.size for f in standard_files)
        return standard_files, total_size, resource_type, dataset_handle

    except Exception as e:
        error_msg = str(e).lower()
        # Implicit resolution (e.g. 'titanic' -> search or competition)
        if '/' not in dataset_handle and ("not found" in error_msg or "404" in error_msg):
             from .search import search
             results = search(dataset_handle, top=1)
             if results:
                 resolved = results[0]['handle']
                 logger.info(f"Implicitly resolved '{dataset_handle}' to '{resolved}'")
                 return _get_dataset_files(resolved, timeout=timeout)
        
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
            
            raise error_class(final_msg, fix_suggestion=fix) from e
        raise e

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
            from .errors import DataFormatError
            raise DataFormatError(
                f"The file '{file_name}' was not found in the dataset.\n"
                f"Available files: {', '.join(file_names)}"
            )

    # Case 2: Auto-resolution
    supported_exts = (".csv", ".parquet", ".json", ".xlsx", ".xls", ".sqlite", ".db")
    supported_files = [f for f in file_names if f.lower().endswith(supported_exts)]

    if not supported_files:
        from .errors import UnsupportedFormatError
        raise UnsupportedFormatError(
            "No supported tabular files found (CSV, Parquet, JSON, Excel, or SQLite).\n"
            f"Available files: {', '.join(file_names)}"
        )

    if len(supported_files) > 1:
        from .errors import MultipleFilesError
        raise MultipleFilesError(
            "Multiple supported files found. Please specify which one to load.\n"
            f"Found: {', '.join(supported_files[:10])}{'...' if len(supported_files) > 10 else ''}\n"
            f'Fix: load("{dataset_handle}", file="{supported_files[0]}")'
        )

    return supported_files[0]


def load(dataset_handle: str, file: Optional[str] = None, timeout: int = 300, **kwargs) -> Union[pd.DataFrame, str]:
    """
    The main function to load a Kaggle dataset into a pandas DataFrame or return the path.
    """
    setup_auth()
    
    # 1. Resolve files, resource type, and resolved handle
    files, total_size, res_type, resolved_handle = _get_dataset_files(dataset_handle, timeout=timeout)
    
    # Check memory safety
    from .progress import check_memory_safety
    check_memory_safety(total_size)

    # 2. Resolve specific file path if possible
    is_obscured = any("__AUTO_RESOLVE_" in f.name for f in files)
    
    selected_file = file
    if not is_obscured:
        try:
             # This filters for CSV/Parquet/JSON/Excel/SQLite
             selected_file = _resolve_file_path(files, dataset_handle, file)
        except Exception:
             # If resolution fails but it's a competition or obscured, we swap to late-res
             if res_type == "competition":
                 is_obscured = True 
             else:
                 # If no tabular files found in metadata, we might want to just download and return path
                 is_obscured = True

    # 3. Download via KaggleHub
    import kagglehub
    try:
        if res_type == "competition":
            comp_slug = resolved_handle.split('/')[-1]
            path = kagglehub.competition_download(comp_slug)
        else:
            path = kagglehub.dataset_download(resolved_handle)
            
        # 4. Late Resolution / Fallback SCAN
        # Supported extensions for auto-loading
        tabular_exts = ('.csv', '.parquet', '.json', '.xlsx', '.xls', '.sqlite', '.db')
        
        if is_obscured or not selected_file:
            available_files = []
            for root, _, fs in os.walk(path):
                for f in fs:
                    if f.lower().endswith(tabular_exts):
                        available_files.append(os.path.join(root, f))
            
            if not available_files:
                 logger.info(f"ℹ️ No tabular data found in '{dataset_handle}'. Returning directory path.")
                 return path
                 
            # If multiple, prefer the one matching 'file' if provided
            if file:
                matches = [f for f in available_files if file.lower() in f.lower()]
                full_selected_path = matches[0] if matches else available_files[0]
            else:
                full_selected_path = available_files[0]
        else:
            # Standard path construction
            if os.path.isabs(selected_file):
                full_selected_path = selected_file
            else:
                full_selected_path = os.path.join(path, selected_file)

        # 5. Load into Pandas based on extension
        f_lower = full_selected_path.lower()
        logger.info(f"Loading {os.path.basename(full_selected_path)}...")
        
        if f_lower.endswith('.csv'):
            return pd.read_csv(full_selected_path, **kwargs)
        elif f_lower.endswith('.parquet'):
            return pd.read_parquet(full_selected_path, **kwargs)
        elif f_lower.endswith('.json'):
            return pd.read_json(full_selected_path, **kwargs)
        elif f_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(full_selected_path, **kwargs)
        elif f_lower.endswith(('.sqlite', '.db')):
            import sqlite3
            conn = sqlite3.connect(full_selected_path)
            # Try to get the first table name
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()
            if table_name:
                df = pd.read_sql_query(f"SELECT * FROM {table_name[0]}", conn, **kwargs)
                conn.close()
                return df
            conn.close()
            return full_selected_path # Return path if no tables found
        else:
            logger.warning(f"Unsupported format for auto-loading: {f_lower}. Returning path.")
            return full_selected_path

    except Exception as e:
        from .errors import DatasetNotFoundError, AuthError
        if isinstance(e, (DatasetNotFoundError, AuthError, KaggleEaseError)):
            raise e
        logger.error(f"Load failed: {e}. Returning path as fallback.")
        # Final fallback: return the path instead of crashing
        try:
            return path
        except:
            raise KaggleEaseError(f"An error occurred while loading: {e}")
