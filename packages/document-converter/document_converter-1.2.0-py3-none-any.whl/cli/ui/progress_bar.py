from typing import Optional, List
from tqdm import tqdm

class ProgressBar:
    """
    A wrapper around tqdm for displaying progress bars in the CLI.
    """

    def __init__(self, total: int, desc: str = "Processing", unit: str = "it", leave: bool = True, position: int = 0):
        """
        Initialize the progress bar.
        
        Args:
            total: Total number of items.
            desc: Description of the task.
            unit: Unit of measurement (e.g., 'file', 'MB').
            leave: Whether to leave the bar after completion.
            position: Position of the bar (for multi-bar support).
        """
        self.pbar = tqdm(total=total, desc=desc, unit=unit, leave=leave, position=position)

    def update(self, n: int = 1):
        """Update progress by n."""
        self.pbar.update(n)

    def set_description(self, desc: str):
        """Update the description."""
        self.pbar.set_description(desc)

    def close(self):
        """Close the progress bar."""
        self.pbar.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class MultiProgressBar:
    """
    Manages multiple progress bars.
    """
    def __init__(self):
        self.bars: List[ProgressBar] = []

    def create_bar(self, total: int, desc: str = "Task", unit: str = "it") -> ProgressBar:
        """
        Create a new progress bar at the next available position.
        """
        position = len(self.bars)
        bar = ProgressBar(total=total, desc=desc, unit=unit, position=position)
        self.bars.append(bar)
        return bar

    def close_all(self):
        """Close all managed bars."""
        for bar in self.bars:
            bar.close()
