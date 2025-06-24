"""Enhanced logging with automatic trace correlation"""

import inspect
import logging
import os
import sys
import time
from typing import Optional

import boto3
import watchtower
from opentelemetry.trace import get_current_span

from traceroot.config import TraceRootConfig


class TraceIdFilter(logging.Filter):
    """Filter to add trace and span IDs to log records"""

    def __init__(self, config: TraceRootConfig):
        super().__init__()
        self.config = config

    def filter(self, record):
        """Add trace correlation data to log record"""
        span = get_current_span()
        ctx = span.get_span_context()

        if ctx and ctx.trace_id != 0:
            # Convert trace ID to AWS X-Ray format
            # (1-{8 hex chars}-{24 hex chars})
            trace_id_hex = format(ctx.trace_id, "032x")
            record.trace_id = f"1-{trace_id_hex[:8]}-{trace_id_hex[8:]}"
            record.span_id = format(ctx.span_id,
                                    "016x") if ctx.span_id != 0 else "no-span"
        else:
            record.trace_id = "no-trace"
            record.span_id = "no-span"

        # Add stack trace for debugging
        record.stack_trace = self._get_stack_trace()

        # Add service metadata
        record.service_name = self.config.service_name
        record.github_commit_hash = self.config.github_commit_hash
        record.github_owner = self.config.github_owner
        record.github_repo_name = self.config.github_repo_name
        record.environment = self.config.environment

        return True

    def _get_stack_trace(self) -> str:
        """Get a clean stack trace showing the call path"""
        stack = inspect.stack()
        relevant_frames = []

        for frame_info in stack[
                3:]:  # Skip current frame, filter frame, and logging frame
            # Include parent directory in filename for better context
            path_parts = frame_info.filename.split(os.sep)
            filename = (os.sep.join(path_parts[-2:]) if len(path_parts) >= 2
                        else os.path.basename(frame_info.filename))
            function_name = frame_info.function
            line_number = frame_info.lineno

            # NOTE (xinwei): This is a hack to skip tracing and logging module
            # frames, which are not relevant to the actual code that we want to
            # trace

            # Skip logging module frames
            # TODO: Improve this to avoid skipping user's scripts
            if (('logger.py' in filename) or ('tracer.py' in filename)
                    or ('logging/' in filename) or filename.startswith('__')
                    or filename.endswith('/__init__.py')):
                continue

            relevant_frames.append(f"{filename}:{function_name}:{line_number}")

        return " -> ".join(
            reversed(relevant_frames)) if relevant_frames else "unknown"


class TraceRootLogger:
    """Enhanced logger with trace correlation and AWS integration"""

    def __init__(self, config: TraceRootConfig, name: Optional[str] = None):
        self.config = config
        self.logger = logging.getLogger(name or config.service_name)
        self.logger.setLevel(logging.DEBUG)

        # Configure logging to use UTC time
        logging.Formatter.converter = time.gmtime

        # Create formatter with trace correlation
        self.formatter = logging.Formatter(
            '%(asctime)s;%(levelname)s;%(service_name)s;'
            '%(github_commit_hash)s;%(github_owner)s;%(github_repo_name)s;'
            '%(environment)s;'
            '%(trace_id)s;%(span_id)s;%(stack_trace)s;%(message)s')

        # Create trace filter
        self.trace_filter = TraceIdFilter(config)

        # Setup handlers
        if self.config.enable_console_export:
            self._setup_console_handler()
        self._setup_cloudwatch_handler()

    def _setup_console_handler(self):
        """Setup console logging handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        console_handler.addFilter(self.trace_filter)
        self.logger.addHandler(console_handler)

    def _setup_cloudwatch_handler(self):
        """Setup CloudWatch logging handler"""
        try:
            session = boto3.Session(region_name=self.config.aws_region)
            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=self.config._cloudwatch_log_group,
                stream_name=self.config._cloudwatch_stream_name,
                boto3_client=session.client('logs'))
            cloudwatch_handler.setFormatter(self.formatter)
            cloudwatch_handler.addFilter(self.trace_filter)
            self.logger.addHandler(cloudwatch_handler)
        except Exception as e:
            self.logger.warning(f"Failed to setup CloudWatch logging: {e}")

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)


# Global logger instance
_global_logger: Optional[TraceRootLogger] = None


def initialize_logger(config: TraceRootConfig) -> TraceRootLogger:
    """Initialize the global logger instance"""
    global _global_logger
    _global_logger = TraceRootLogger(config)
    return _global_logger


def get_logger(name: Optional[str] = None) -> TraceRootLogger:
    """Get the global logger instance or create a new one"""
    if _global_logger is None:
        raise RuntimeError(
            "Logger not initialized. Call initialize_tracing() first.")

    if name is None:
        return _global_logger

    # Create a new logger with the same config but different name
    return TraceRootLogger(_global_logger.config, name)
