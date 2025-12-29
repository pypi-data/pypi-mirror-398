import time
from typing import Dict, Any, Optional

class ProgressTracker:
    """
    Tracks the progress of multiple long-running tasks.
    """

    def __init__(self):
        """
        Initialize the progress tracker.
        """
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def add_task(self, task_id: str, total: int, desc: str = ""):
        """
        Add a new task to track.
        """
        self.tasks[task_id] = {
            "total": total,
            "processed": 0,
            "start_time": time.time(),
            "last_update_time": time.time(),
            "desc": desc,
            "status": "Pending"
        }

    def update_progress(self, task_id: str, processed: int, status: Optional[str] = None):
        """
        Update the progress of a specific task.
        """
        if task_id in self.tasks:
            self.tasks[task_id]["processed"] = processed
            self.tasks[task_id]["last_update_time"] = time.time()
            if status:
                self.tasks[task_id]["status"] = status

    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress stats for a specific task.
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        processed = task["processed"]
        total = task["total"]
        
        percent = 0.0
        if total > 0:
            percent = min(100.0, (processed / total) * 100.0)
        elif total == 0:
            percent = 100.0

        return {
            "task_id": task_id,
            "processed": processed,
            "total": total,
            "percent": percent,
            "status": task["status"],
            "desc": task["desc"]
        }

