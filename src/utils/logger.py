"""
Pipeline System Logger

Handles logging to pipeline-specific system.log files.
Each pipeline has its own log file in .pipeline_system/logs/system.log
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from threading import Lock

import config

# Thread lock for safe file operations
_log_lock = Lock()
_loggers = {}  # Cache of loggers per pipeline_id


class PipelineLogger:
    """
    Logger for a specific pipeline.

    Writes logs to .pipeline_system/logs/system.log
    """

    def __init__(self, pipeline_id: str):
        """
        Initialize logger for a pipeline.

        Args:
            pipeline_id: The pipeline UUID
        """
        self.pipeline_id = pipeline_id
        self.base_path = Path(config.BASE_PIPELINES_PATH) / pipeline_id
        self.logs_dir = self.base_path / config.PIPELINE_SYSTEM_DIR / config.PIPELINE_LOGS_DIR
        self.log_file = self.logs_dir / config.SYSTEM_LOG_FILENAME

        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(f"pipeline.{pipeline_id}")
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create file handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def info(self, message: str) -> None:
        """Log an info message."""
        self._log("info", message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._log("warning", message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self._log("error", message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._log("debug", message)

    def _log(self, level: str, message: str) -> None:
        """Internal log method with thread safety."""
        with _log_lock:
            log_method = getattr(self.logger, level, None)
            if log_method:
                log_method(message)

    def log_event(self, event_type: str, description: str, metadata: dict = None) -> None:
        """
        Log a structured event.

        Args:
            event_type: Type of event (e.g., 'pipeline_created', 'checkpoint_started')
            description: Human-readable description
            metadata: Optional additional data
        """
        metadata_str = f" | {metadata}" if metadata else ""
        self.info(f"[{event_type}] {description}{metadata_str}")


def get_logger(pipeline_id: str) -> PipelineLogger:
    """
    Get or create a logger for a pipeline.

    Args:
        pipeline_id: The pipeline UUID

    Returns:
        PipelineLogger instance for the pipeline
    """
    if pipeline_id not in _loggers:
        _loggers[pipeline_id] = PipelineLogger(pipeline_id)
    return _loggers[pipeline_id]


def log_pipeline_event(pipeline_id: str, event_type: str, description: str, metadata: dict = None) -> None:
    """
    Convenience function to log a pipeline event.

    Args:
        pipeline_id: The pipeline UUID
        event_type: Type of event
        description: Human-readable description
        metadata: Optional additional data
    """
    logger = get_logger(pipeline_id)
    logger.log_event(event_type, description, metadata)
