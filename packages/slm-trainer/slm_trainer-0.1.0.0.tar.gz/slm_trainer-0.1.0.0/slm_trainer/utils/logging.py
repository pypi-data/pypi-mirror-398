"""
Logging utilities for training metrics and progress tracking.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = 'slm_trainer',
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger with console and optional file output.

    Args:
        name: Logger name
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional file path to write logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class MetricsTracker:
    """
    Simple metrics tracker for training.

    Tracks and computes running averages of metrics like loss, accuracy, etc.
    """

    def __init__(self):
        """Initialize metrics tracker."""
        self.metrics = {}
        self.counts = {}

    def update(self, **kwargs):
        """
        Update metrics with new values.

        Args:
            **kwargs: Metric name-value pairs

        Example:
            >>> tracker = MetricsTracker()
            >>> tracker.update(loss=0.5, accuracy=0.9)
        """
        for key, value in kwargs.items():
            if key not in self.metrics:
                self.metrics[key] = 0.0
                self.counts[key] = 0

            self.metrics[key] += value
            self.counts[key] += 1

    def get_average(self, metric_name: str) -> float:
        """
        Get the average value of a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Average value of the metric

        Raises:
            KeyError: If metric doesn't exist
        """
        if metric_name not in self.metrics:
            raise KeyError(f"Metric '{metric_name}' not found")

        return self.metrics[metric_name] / self.counts[metric_name]

    def get_all_averages(self) -> dict:
        """
        Get average values of all metrics.

        Returns:
            Dictionary of metric name -> average value
        """
        return {
            key: self.metrics[key] / self.counts[key]
            for key in self.metrics.keys()
        }

    def reset(self):
        """Reset all metrics."""
        self.metrics = {}
        self.counts = {}

    def reset_metric(self, metric_name: str):
        """
        Reset a specific metric.

        Args:
            metric_name: Name of the metric to reset
        """
        if metric_name in self.metrics:
            del self.metrics[metric_name]
            del self.counts[metric_name]

    def __repr__(self) -> str:
        """String representation of current metrics."""
        if not self.metrics:
            return "MetricsTracker(empty)"

        metrics_str = ", ".join([
            f"{key}={self.get_average(key):.4f}"
            for key in self.metrics.keys()
        ])
        return f"MetricsTracker({metrics_str})"
