import sys
import logging
from typing import Optional
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class ProgressBar:
    """Simple progress bar for file downloads."""
    
    def __init__(self, total_size: int, desc: str = "Download"):
        self.total_size = total_size
        self.desc = desc
        self.downloaded = 0
        self._progress_shown = False
    
    def update(self, chunk_size: int):
        """Update progress with newly downloaded chunk size."""
        self.downloaded += chunk_size
        if self.total_size > 0:
            percent = min(100, int(100 * self.downloaded / self.total_size))
            bar_length = 30
            filled_length = int(bar_length * self.downloaded // self.total_size)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            # Clear previous progress
            if self._progress_shown:
                sys.stdout.write('\r')
            else:
                self._progress_shown = True
                
            # Print progress bar
            sys.stdout.write(f'{self.desc}: |{bar}| {percent}% ({self._format_bytes(self.downloaded)}/{self._format_bytes(self.total_size)})')
            sys.stdout.flush()
    
    def complete(self):
        """Mark download as complete."""
        if self._progress_shown:
            sys.stdout.write('\n')
            sys.stdout.flush()
    
    @staticmethod
    def _format_bytes(bytes_size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"


def show_progress(downloaded: int, total: int, desc: str = "Download"):
    """Show progress for a download operation."""
    if total > 0:
        progress = ProgressBar(total, desc)
        progress.update(downloaded)
        return progress
    return None

def check_memory_safety(file_size_bytes: int):
    """
    Check if the file size is safe to load into memory based on available RAM.
    Warns the user if the file size exceeds 50% of available memory.
    """
    if psutil:
        try:
            available_ram = psutil.virtual_memory().available
            # Conservative estimate: Pandas can take 5x-10x the CSV file size in RAM, 
            # but we'll use 50% of available RAM as a threshold for a strong warning.
            if file_size_bytes > available_ram * 0.5:
                file_size_str = ProgressBar._format_bytes(file_size_bytes)
                ram_str = ProgressBar._format_bytes(available_ram)
                logger.warning(
                    f"POTENTIAL MEMORY RISK: File size ({file_size_str}) is more than 50% "
                    f"of available RAM ({ram_str}).\n"
                    "Loading this dataset might crash your kernel.\n"
                    "TIP: Try passing 'chunksize' to load it in chunks, or specify a subset of columns."
                )
        except Exception as e:
            logger.debug(f"Failed to check memory safety: {e}")
    else:
        # Fallback if psutil is missing (though we added it to dependencies)
        if file_size_bytes > 1*1024**3: # 1GB
             logger.warning("Large file detected (>1GB). Ensure you have enough RAM to load it.")