import queue
import time
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass(order=True)
class Task:
    """
    Represents a task in the priority queue.
    Lower priority number means higher priority.
    Timestamp is used to ensure FIFO order for tasks with the same priority.
    """
    priority: int
    timestamp: float = field(compare=True)
    data: Any = field(compare=False)

    def __init__(self, priority: int, data: Any):
        self.priority = priority
        self.timestamp = time.time()
        self.data = data

class TaskQueue:
    """
    A thread-safe task queue with priority support.
    """
    def __init__(self):
        self._queue = queue.PriorityQueue()

    def enqueue(self, task_data: Any, priority: int = 10):
        """
        Add a task to the queue.
        
        Args:
            task_data: The data associated with the task (e.g., function, args).
            priority: Priority of the task (lower is higher priority). Default is 10.
        """
        task = Task(priority, task_data)
        self._queue.put(task)

    def dequeue(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """
        Remove and return the highest priority task from the queue.
        
        Args:
            block: Whether to block if the queue is empty.
            timeout: Time to wait if blocking.
            
        Returns:
            The data of the dequeued task.
            
        Raises:
            queue.Empty: If the queue is empty.
        """
        task = self._queue.get(block=block, timeout=timeout)
        return task.data

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

    def size(self) -> int:
        """Return the number of tasks in the queue."""
        return self._queue.qsize()
