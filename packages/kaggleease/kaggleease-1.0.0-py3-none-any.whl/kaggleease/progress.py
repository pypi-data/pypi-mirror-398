"""Progress indication utilities for large file downloads."""
import sys
from typing import Optional


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