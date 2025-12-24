"""
Structured logging integration with Google Cloud Logging.

Provides structured logging with automatic integration to Cloud Logging.
"""

import logging
from typing import Any


class StructuredLogger:
    """
    Structured logger with Cloud Logging integration.

    Provides methods for structured logging with automatic Cloud Logging integration.
    Falls back to standard logging if Cloud Logging is unavailable.
    """

    def __init__(self, project_id: str, service_name: str = "gemini-sre"):
        """
        Initialize structured logger.

        Args:
            project_id: GCP project ID
            service_name: Service name for log entries
        """
        self.project_id = project_id
        self.service_name = service_name

        # Setup console logger
        self._console_logger = logging.getLogger(__name__)
        self._console_logger.setLevel(logging.INFO)

        if not self._console_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            self._console_logger.addHandler(handler)

        # Try to setup Cloud Logging
        self._cloud_logger = None
        self._initialize_cloud_logging()

    def _initialize_cloud_logging(self):
        """Initialize Cloud Logging client."""
        try:
            from google.cloud import logging as cloud_logging

            logging_client = cloud_logging.Client(project=self.project_id)
            logging_client.setup_logging()
            self._cloud_logger = logging_client.logger(self.service_name)

        except Exception as e:
            self._console_logger.warning(f"Cloud Logging setup failed: {e}")
            self._cloud_logger = None

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._console_logger.info(message)
        if self._cloud_logger:
            self._log_struct("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._console_logger.warning(message)
        if self._cloud_logger:
            self._log_struct("WARNING", message, kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._console_logger.error(message)
        if self._cloud_logger:
            self._log_struct("ERROR", message, kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._console_logger.debug(message)
        if self._cloud_logger:
            self._log_struct("DEBUG", message, kwargs)

    def _log_struct(self, severity: str, message: str, extra: dict[str, Any]):
        """Write structured log entry to Cloud Logging."""
        if not self._cloud_logger:
            return

        try:
            log_entry = {
                "severity": severity,
                "message": message,
                "service": self.service_name,
                **extra,
            }
            self._cloud_logger.log_struct(log_entry)
        except Exception as e:
            self._console_logger.error(f"Failed to write Cloud Logging entry: {e}")
