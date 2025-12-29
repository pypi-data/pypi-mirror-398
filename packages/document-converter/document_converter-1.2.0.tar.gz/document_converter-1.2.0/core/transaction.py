import os
import shutil
import logging
import uuid
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TransactionManager:
    """
    Manages file system transactions with rollback support.
    Tracks created and modified files, restoring previous state on error.
    """

    def __init__(self):
        self._created_files: List[str] = []
        self._backups: Dict[str, str] = {} # original_path -> backup_path
        self._temp_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / ".tmp_backups" / str(uuid.uuid4())
        self._active = False

    def __enter__(self):
        self._active = True
        self._ensure_temp_dir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.warning("Transaction failed, rolling back changes...")
            self.rollback()
        else:
            self.commit()
        
        self._cleanup_temp_dir()
        self._active = False

    def _ensure_temp_dir(self):
        if not self._temp_dir.exists():
            self._temp_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_temp_dir(self):
        if self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir {self._temp_dir}: {e}")

    def register_file(self, file_path: str):
        """
        Register a file path that is about to be created or modified.
        Must be called BEFORE the operation.
        """
        if not self._active:
            return

        file_path = str(Path(file_path).absolute())
        
        if os.path.exists(file_path):
            # If valid file exists, backup it if not already backed up
            if file_path not in self._backups:
                try:
                    backup_name = f"{uuid.uuid4()}_{os.path.basename(file_path)}"
                    backup_path = self._temp_dir / backup_name
                    shutil.copy2(file_path, backup_path)
                    self._backups[file_path] = str(backup_path)
                    logger.debug(f"Backed up {file_path} to {backup_path}")
                except Exception as e:
                    logger.error(f"Failed to backup file {file_path}: {e}")
                    raise
        else:
            # New file, track for deletion
            if file_path not in self._created_files:
                self._created_files.append(file_path)

    def rollback(self):
        """Revert all changes made during the transaction."""
        # 1. Delete created files
        for file_path in reversed(self._created_files):
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Rollback: Deleted new file {file_path}")
                except Exception as e:
                    logger.warning(f"Rollback: Failed to delete {file_path}: {e}")

        # 2. Restore backups
        for original_path, backup_path in self._backups.items():
            try:
                # Ensure parent dir exists (if it was deleted? Unlikely for file mod but possible)
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.copy2(backup_path, original_path)
                logger.info(f"Rollback: Restored {original_path}")
            except Exception as e:
                logger.error(f"Rollback: Failed to restore {original_path}: {e}")

    def commit(self):
        """Confirm changes (nothing to do essentially, backups will be wiped on cleanup)."""
        logger.debug("Transaction committed.")
