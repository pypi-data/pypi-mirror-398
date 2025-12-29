"""
KaggleEase: The fastest, notebook-first way to load Kaggle datasets.
"""

from .load import load
from .search import search
from .magics import register_magics
from .progress import ProgressBar, show_progress

# Auto-register the magics when imported in an IPython environment
register_magics()
