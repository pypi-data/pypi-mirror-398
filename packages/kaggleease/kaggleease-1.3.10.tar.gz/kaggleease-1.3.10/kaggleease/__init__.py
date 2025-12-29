"""
KaggleEase: The fastest, notebook-first way to load Kaggle datasets.
"""
__version__ = "1.3.10"

from .load import load
from .search import search
from .magics import register_magics
from .progress import ProgressBar, show_progress

# Auto-register the magics when imported in an IPython environment
register_magics()

def load_ipython_extension(ipython):
    """
    Standard function to load the extension in IPython/Jupyter.
    Allows using `%load_ext kaggleease`.
    """
    from .magics import KaggleMagics
    ipython.register_magics(KaggleMagics)
