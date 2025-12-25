class KaggleEaseError(Exception):
    """Base exception for all kaggleease errors."""
    pass

class AuthError(KaggleEaseError):
    """Raised when Kaggle API authentication fails."""
    pass

class MultipleFilesError(KaggleEaseError):
    """Raised when a dataset contains multiple ambiguous files."""
    pass

class UnsupportedFormatError(KaggleEaseError):
    """Raised when a dataset contains no supported file formats."""
    pass

class DataFormatError(KaggleEaseError):
    """Generic error for data format issues."""
    pass

class DatasetNotFoundError(KaggleEaseError):
    """Raised when a dataset cannot be found on Kaggle."""
    pass
