import os
import logging
from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from concurrent.futures import as_completed
from converter.engine import ConversionEngine
from core.worker_pool import WorkerPool

logger = logging.getLogger(__name__)

@dataclass
class ConversionTask:
    input_path: str
    output_path: str
    options: Dict

@dataclass
class BatchProcessingReport:
    total: int = 0
    success: int = 0
    failed: int = 0
    failures: List[Tuple[str, str]] = field(default_factory=list) # (filename, reason)

class BatchProcessor:
    """
    Processor for handling batch document conversions in parallel.
    Scans directories and manages a queue of conversion tasks.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        self.queue: List[ConversionTask] = []
        self.engine = ConversionEngine()
        self.pool = WorkerPool(max_workers=max_workers)

    def scan_directory(self, input_dir: str, output_dir: str, 
                       recursive: bool = False, 
                       from_format: Optional[str] = None, 
                       to_format: str = "pdf",
                       **task_options) -> int:
        """
        Scan a directory for files to convert and add them to the queue.
        """
        if not os.path.exists(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return 0
            
        added_count = 0
        
        if recursive:
            for root, _, files in os.walk(input_dir):
                for file in files:
                    if self._should_process(file, from_format):
                        self._add_file_task(root, file, input_dir, output_dir, to_format, **task_options)
                        added_count += 1
        else:
            files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
            for file in files:
                if self._should_process(file, from_format):
                    self._add_file_task(input_dir, file, input_dir, output_dir, to_format, **task_options)
                    added_count += 1
                    
        return added_count

    def _should_process(self, filename: str, from_format: Optional[str]) -> bool:
        if from_format:
            return filename.lower().endswith(f".{from_format.lower().lstrip('.')}")
        return True 

    def _add_file_task(self, root: str, filename: str, base_input_dir: str, base_output_dir: str, to_format: str, **task_options):
        input_path = os.path.join(root, filename)
        rel_path = os.path.relpath(root, base_input_dir)
        target_dir = os.path.join(base_output_dir, rel_path)
        
        name_no_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(target_dir, f"{name_no_ext}.{to_format}")
        
        task = ConversionTask(
            input_path=input_path,
            output_path=output_path,
            options=task_options
        )
        self.queue.append(task)

    def add_task(self, input_path: str, output_path: str, **options):
        """Manually add a single task."""
        self.queue.append(ConversionTask(input_path, output_path, options))

    def _process_single_task(self, task: ConversionTask) -> Tuple[ConversionTask, bool, Optional[str]]:
        """
        Helper to run a single task in a worker.
        Returns: (task, success, error_message)
        """
        try:
            # Ensure output dir exists (thread-safe enough with exist_ok)
            output_dir = os.path.dirname(task.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            success = self.engine.convert(task.input_path, task.output_path, **task.options)
            return task, success, None if success else "Conversion failed"
        except Exception as e:
            return task, False, str(e)

    def process_queue(self, progress_callback: Optional[Callable[[], None]] = None) -> BatchProcessingReport:
        """
        Process all tasks in the queue in parallel.
        Returns a BatchProcessingReport with detailed results.
        """
        report = BatchProcessingReport(total=len(self.queue))
        logger.info(f"Processing {report.total} tasks with {self.pool.max_workers} workers...")
        
        futures = []
        for task in self.queue:
            # Submit task to pool
            f = self.pool.submit(self._process_single_task, task)
            futures.append(f)
            
        # Process results as they complete
        for future in as_completed(futures):
            try:
                task, success, error_msg = future.result()
                if success:
                    report.success += 1
                else:
                    report.failed += 1
                    report.failures.append((task.input_path, error_msg or "Unknown error"))
                    logger.error(f"Failed to convert {task.input_path}: {error_msg}")
            except Exception as e:
                # This catches errors in the wrapper or submission itself
                logger.error(f"Task execution failed completely: {e}")
                report.failed += 1
                report.failures.append(("Unknown Task", str(e)))
                
            if progress_callback:
                progress_callback()
                
        # Clear queue after processing
        self.queue = []
                
        return report

    def clear_queue(self):
        self.queue = []
