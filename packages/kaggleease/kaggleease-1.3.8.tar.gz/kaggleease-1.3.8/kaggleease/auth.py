import os
import sys
from pathlib import Path
import threading
import logging
from typing import Optional
from .errors import AuthError, KaggleEaseError
import json

# Set up logging
logger = logging.getLogger(__name__)

# Thread-safe authentication cache
_auth_cache = {}
_auth_lock = threading.Lock()

def setup_auth() -> None:
    """
    Sets up authentication for the Kaggle API with thread safety.

    Handles two cases:
    1. Running in a Google Colab environment: Prompts for kaggle.json upload.
    2. Running in a local environment: Checks for ~/.kaggle/kaggle.json.

    Ensures the kaggle.json file has permissions set to 600.
    """
    # Thread-safe check to avoid redundant auth operations
    with _auth_lock:
        thread_id = threading.get_ident()
        if thread_id in _auth_cache:
            logger.debug(f"Using cached auth for thread {thread_id}")
            return
        
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_json_path = kaggle_dir / "kaggle.json"

        # Case 1: In Google Colab and kaggle.json does not exist.
        if "google.colab" in sys.modules and not kaggle_json_path.exists():
            try:
                from google.colab import files
                logger.info("Kaggle API key not found. Please upload your kaggle.json file.")
                uploaded = files.upload()

                if "kaggle.json" not in uploaded:
                    raise AuthError("The uploaded file was not named 'kaggle.json'. Please try again.")

                # Ensure the .kaggle directory exists
                kaggle_dir.mkdir(parents=True, exist_ok=True)

                # Write the uploaded file to the target path
                with open(kaggle_json_path, "wb") as f:
                    f.write(uploaded["kaggle.json"])

                logger.info("Kaggle API key loaded. You're ready to load datasets!")

            except ImportError:
                raise AuthError("Failed to import google.colab.files. This function is designed to work in a Google Colab environment.")
            except Exception as e:
                raise AuthError(f"An error occurred during the Colab file upload process: {e}")

        # Case 2: Local environment check
        if not kaggle_json_path.exists():
            logger.error(f"Kaggle API credentials not found. Please place your kaggle.json file at {kaggle_json_path}")
            raise AuthError(f"Kaggle API credentials not found. Please place your kaggle.json file at {kaggle_json_path}")

        # Set permissions for the kaggle.json file
        try:
            os.chmod(kaggle_json_path, 0o600)
            logger.debug(f"Set secure permissions for {kaggle_json_path}")
        except Exception as e:
            # On Windows, chmod may not work as expected, but we'll still warn
            # On Unix-like systems, we should enforce this for security
            import platform
            if platform.system() != 'Windows':
                logger.error(f"Could not set secure permissions (600) for {kaggle_json_path}. Error: {e}")
                raise AuthError(f"Could not set secure permissions (600) for {kaggle_json_path}. "
                               f"Kaggle API requires strict permissions for security. Error: {e}") from e
            else:
                logger.warning(f"Could not set permissions for {kaggle_json_path}. Error: {e}")
                logger.info("On Windows, file permissions are handled differently but your credentials should still be secure.")
        
        # Mark authentication as completed for this thread
        _auth_cache[thread_id] = True

def get_kaggle_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Retrieves Kaggle credentials from environment variables or kaggle.json.
    
    Returns:
        tuple: (username, key) or (None, None) if not found.
    """
    # 1. Check environment variables
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if username and key:
        return username, key
        
    # 2. Check kaggle.json
    kaggle_json_path = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json_path.exists():
        try:
            with open(kaggle_json_path, "r") as f:
                data = json.load(f)
                return data.get("username"), data.get("key")
        except Exception as e:
            logger.warning(f"Failed to read credentials from {kaggle_json_path}: {e}")
            
    return None, None

