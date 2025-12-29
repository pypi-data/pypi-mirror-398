from typing import Optional

class KaggleEaseError(Exception):
    """Base exception for all kaggleease errors."""
    def __init__(self, message: str, fix_suggestion: Optional[str] = None, docs_link: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.fix_suggestion = fix_suggestion
        self.docs_link = docs_link

class AuthError(KaggleEaseError):
    """Raised when Kaggle API authentication fails."""
    def __init__(self, message: str, fix_suggestion: Optional[str] = "Make sure your kaggle.json is in ~/.kaggle/ and has 600 permissions."):
        super().__init__(message, fix_suggestion=fix_suggestion, docs_link="https://github.com/Kaggle/kaggle-api#creds")

class MultipleFilesError(KaggleEaseError):
    """Raised when a dataset contains multiple ambiguous files."""
    def __init__(self, message: str, fix_suggestion: Optional[str] = "Specify a specific file using the 'file' parameter."):
        super().__init__(message, fix_suggestion=fix_suggestion)

class UnsupportedFormatError(KaggleEaseError):
    """Raised when a dataset contains no supported file formats."""
    def __init__(self, message: str, fix_suggestion: Optional[str] = "KaggleEase support CSV and Parquet files. Check your dataset contents."):
        super().__init__(message, fix_suggestion=fix_suggestion)

class DataFormatError(KaggleEaseError):
    """Generic error for data format issues."""
    pass

class DatasetNotFoundError(KaggleEaseError):
    """Raised when a dataset cannot be found on Kaggle."""
    def __init__(self, message: str, fix_suggestion: Optional[str] = "Check the spelling of your dataset handle or use search() to find it."):
        super().__init__(message, fix_suggestion=fix_suggestion)
