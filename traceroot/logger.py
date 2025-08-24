import inspect
import logging
import os
import sys
import time
from typing import Any

import boto3
import watchtower
from opentelemetry.trace import get_current_span

from traceroot.config import TraceRootConfig
from traceroot.credentials import CredentialManager


class TraceIdFilter(logging.Filter):
    """Filter to add trace and span IDs to log records"""

    def __init__(self, config: TraceRootConfig):
        super().__init__()
        self.config = config

    def filter(self, record: logging.LogRecord) -> bool:
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
            # Extract path relative to repository root
            filename = frame_info.filename

            # Handle the case where the filename is in the site-packages folder
            # which is installed by the user.
            if "site-packages/" in filename:
                filename = filename.split("site-packages/", 1)[1]
                filename = self.config.github_repo_name + "/" + filename

            path_parts = filename.split(os.sep)
            filename = self._get_relative_path(path_parts)
            function_name = frame_info.function
            line_number = frame_info.lineno

            # NOTE (xinwei): This is a hack to skip tracing and logging module
            # frames, which are not relevant to the actual code that we want to
            # trace

            # Skip logging module frames
            # TODO: Improve this to avoid skipping user's scripts
            if (('traceroot' in filename and 'logger.py' in filename)
                    or ('traceroot' in filename and 'tracer.py' in filename)
                    or ('traceroot' in filename and 'logging/' in filename) or
                ('Lib' in filename and 'logging/' in filename)  # Windows
                    or filename.startswith('__')
                    or filename.endswith('/__init__.py')):
                continue
            relevant_frames.append(f"{filename}:{function_name}:{line_number}")

        return " -> ".join(
            reversed(relevant_frames)) if relevant_frames else "unknown"

    def _get_relative_path(self, path_parts: list) -> str:
        """Extract path relative to repository root"""
        # First try to find the repo name in the path
        if self.config.github_repo_name:
            try:
                repo_index = path_parts.index(self.config.github_repo_name)
                # Take everything after the repo name
                relative_parts = path_parts[repo_index + 1:]
                if relative_parts:
                    return os.sep.join(relative_parts)
            except ValueError:
                pass  # Repo name not found in path

        # Fallback: look for common project structure indicators
        for i, part in enumerate(path_parts):
            if part in ['src', 'lib', 'app', 'examples', 'tests']:
                relative_parts = path_parts[i:]
                if relative_parts:
                    return os.sep.join(relative_parts)

        # Final fallback: use last 2-3 parts for context
        if len(path_parts) >= 3:
            return os.sep.join(path_parts[-3:])
        elif len(path_parts) >= 2:
            return os.sep.join(path_parts[-2:])
        else:
            return os.path.basename(
                path_parts[-1]) if path_parts else "unknown"


class SpanEventHandler(logging.Handler):
    """Handler that adds log messages as events to the
    current OpenTelemetry span
    """

    def emit(self, record: logging.LogRecord):
        """Add log record as an event to the current span"""
        try:
            span = get_current_span()
            if span and span.is_recording():
                # Create attributes from the log record
                attributes = {
                    "log.level": record.levelname,
                    "log.logger": record.name,
                    "log.message": record.getMessage(),
                    "log.module": record.module,
                    "log.function": record.funcName,
                    "log.lineno": record.lineno,
                }

                # Add trace correlation attributes if available
                if hasattr(record, 'trace_id'):
                    attributes["log.trace_id"] = record.trace_id
                if hasattr(record, 'span_id'):
                    attributes["log.span_id"] = record.span_id
                if hasattr(record, 'stack_trace'):
                    attributes["log.stack_trace"] = record.stack_trace

                # Add service metadata if available
                if hasattr(record, 'service_name'):
                    attributes["log.service_name"] = record.service_name
                if hasattr(record, 'environment'):
                    attributes["log.environment"] = record.environment

                # Add exception information if present
                if record.exc_info:
                    attributes["log.exception"] = self.formatException(
                        record.exc_info)

                # Add the log as an event to the span
                span.add_event(
                    name=f"log.{record.levelname.lower()}",
                    attributes=attributes,
                    timestamp=int(record.created *
                                  1_000_000_000)  # Convert to nanoseconds
                )
        except Exception:
            # Don't let event logging errors interfere with the application
            pass


class TraceRootLogger:
    """Enhanced logger with trace correlation and AWS integration"""

    def __init__(self,
                 config: TraceRootConfig,
                 credential_manager: CredentialManager | None = None,
                 name: str | None = None):
        self.config = config
        # Use provided credential manager or create a new one
        self.credential_manager = credential_manager or CredentialManager(
            config)

        # TODO: investigate whether we need to add traceroot
        # prefix to the logger name
        self.logger = logging.getLogger(name or config.service_name)
        self.logger.setLevel(logging.DEBUG)

        # Configure logging to use UTC time
        logging.Formatter.converter = time.gmtime

        # Formatter and trace filter are only used for cloudwatch logging

        # Create formatter with trace correlation
        self.formatter = logging.Formatter(
            '%(asctime)s;%(levelname)s;%(service_name)s;'
            '%(github_commit_hash)s;%(github_owner)s;%(github_repo_name)s;'
            '%(environment)s;'
            '%(trace_id)s;%(span_id)s;%(stack_trace)s;%(message)s')

        # Create trace filter
        self.trace_filter = TraceIdFilter(config)

        # Setup handlers
        if self.config.enable_log_console_export:
            self._setup_console_handler()
        if (not self.config.local_mode
                and self.config.enable_span_cloud_export):
            # We still need to fetch the credentials to get the otlp endpoint
            # if the enable_log_cloud_export is False,
            # so we can still send logs to the traceroot endpoint
            self._setup_cloudwatch_handler()
        else:
            self._setup_otlp_logging_handler()

    def _setup_console_handler(self):
        r"""Setup console logging handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(console_handler)

    # Credential management is now handled by the shared CredentialManager

    def _create_cloudwatch_handler(
        self,
        credentials: dict[str, Any] | None = None
    ) -> watchtower.CloudWatchLogHandler | None:
        """Create a new CloudWatch handler with the provided credentials.

        Args:
            credentials: AWS credentials dict. If None, will fetch credentials.

        Returns:
            CloudWatch handler instance or None if creation failed
        """
        try:
            # Use provided credentials or fetch them
            if credentials is None:
                credentials = self.credential_manager.get_credentials()

            if not credentials:
                session = boto3.Session(region_name=self.config.aws_region)
                log_group = self.config._name
            else:
                log_group = credentials['hash']
                session = boto3.Session(
                    aws_access_key_id=credentials['aws_access_key_id'],
                    aws_secret_access_key=credentials['aws_secret_access_key'],
                    aws_session_token=credentials['aws_session_token'],
                    region_name=credentials['region'])

            # Only create CloudWatch handler if log cloud export is enabled
            if not self.config.enable_log_cloud_export:
                return None

            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=log_group,
                stream_name=self.config._sub_name,
                boto3_client=session.client('logs'),
                # Disable queues to prevent background thread issues
                send_interval=0.05,
                max_batch_size=1,
                max_batch_count=1,
                create_log_group=True,
                use_queues=False)
            cloudwatch_handler.setFormatter(self.formatter)
            cloudwatch_handler.addFilter(self.trace_filter)

            return cloudwatch_handler
        except Exception:
            # Silently handle handler creation errors
            return None

    def _setup_cloudwatch_handler(self):
        r"""Setup CloudWatch logging handler"""
        global _cloudwatch_handler
        try:
            # Fetch AWS credentials from the endpoint
            credentials = self.credential_manager.get_credentials()
            # Note: config is automatically updated by credential manager

            # Create and add the CloudWatch handler
            cloudwatch_handler = self._create_cloudwatch_handler(credentials)
            if cloudwatch_handler:
                self.logger.addHandler(cloudwatch_handler)
                # Store reference for proper shutdown
                _cloudwatch_handler = cloudwatch_handler
        except Exception:
            # Silently handle credential fetch errors
            pass

    def refresh_credentials(self) -> bool:
        """Manually refresh AWS credentials, update otlp endpoint
        and recreate CloudWatch handler if needed

        Returns:
            True if refresh was successful, False otherwise
        """
        global _cloudwatch_handler

        if self.config.local_mode or not self.config.enable_span_cloud_export:
            # No credentials needed in local mode or
            # when span cloud export is disabled
            return False

        try:
            # Force refresh credentials
            credentials = self.credential_manager.get_credentials(
                force_refresh=True)
            if not credentials:
                return False

            # Only recreate CloudWatch handler if log cloud export is enabled
            if self.config.enable_log_cloud_export:
                # Create new CloudWatch handler first (before removing old one)
                new_cloudwatch_handler = self._create_cloudwatch_handler(
                    credentials)

                # Remove existing CloudWatch handler if present
                if _cloudwatch_handler:
                    try:
                        _cloudwatch_handler.flush()
                        _cloudwatch_handler.close()
                        self.logger.removeHandler(_cloudwatch_handler)
                    except Exception:
                        # Don't use self.logger here to avoid recursion
                        pass

                # Add the new CloudWatch handler if creation was successful
                if new_cloudwatch_handler:
                    self.logger.addHandler(new_cloudwatch_handler)
                    # Store reference for proper shutdown
                    _cloudwatch_handler = new_cloudwatch_handler

            return True

        except Exception:
            # Silently handle credential refresh errors
            return False

    def _setup_otlp_logging_handler(self):
        """Setup OpenTelemetry logging handler for local mode
        that adds logs as span events to the current span.
        """
        try:
            # Create a custom handler that adds log messages
            # as events to the current span
            span_event_handler = SpanEventHandler()
            span_event_handler.setLevel(logging.DEBUG)
            span_event_handler.addFilter(self.trace_filter)

            self.logger.addHandler(span_event_handler)

        except Exception as e:
            self.logger.error(f"Failed to setup OpenTelemetry logging: {e}")

    def _check_and_refresh_credentials(self) -> None:
        """Check if credentials need refreshing and refresh if necessary"""
        if self.config.local_mode:
            return

        if not self.config.enable_span_cloud_export:
            return

        # Check if credentials changed (this also refreshes them automatically)
        try:
            credentials_changed = \
                self.credential_manager.check_and_refresh_if_needed()

            # If credentials changed and we have CloudWatch logging enabled,
            # refresh the CloudWatch handler
            if credentials_changed and self.config.enable_log_cloud_export:
                self.refresh_credentials()
        except Exception:
            # Silently handle credential refresh errors
            pass

    def _increment_span_log_count(self, attribute_name: str):
        """Increment the log count attribute for the current span"""
        try:
            span = get_current_span()
            if span and span.is_recording():
                # Get current count (default to 0 if not set)
                current_count = span.attributes.get(attribute_name, 0)
                # Increment and set the new value
                span.set_attribute(attribute_name, current_count + 1)
        except Exception:
            # Don't let span attribute errors interfere with logging
            pass

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self._check_and_refresh_credentials()
        self.logger.debug(message, *args, **kwargs)
        self._increment_span_log_count("num_debug_logs")

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self._check_and_refresh_credentials()
        self.logger.info(message, *args, **kwargs)
        self._increment_span_log_count("num_info_logs")

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self._check_and_refresh_credentials()
        self.logger.warning(message, *args, **kwargs)
        self._increment_span_log_count("num_warning_logs")

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self._check_and_refresh_credentials()
        self.logger.error(message, *args, **kwargs)
        self._increment_span_log_count("num_error_logs")

    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self._check_and_refresh_credentials()
        self.logger.critical(message, *args, **kwargs)
        self._increment_span_log_count("num_critical_logs")


# Global logger instance
_global_logger: TraceRootLogger | None = None
_cloudwatch_handler: watchtower.CloudWatchLogHandler | None = None


def initialize_logger(
        config: TraceRootConfig,
        credential_manager: CredentialManager | None = None
) -> TraceRootLogger:
    """Initialize the global logger instance"""
    global _global_logger
    _global_logger = TraceRootLogger(config, credential_manager)
    return _global_logger


def shutdown_logger() -> None:
    """
    Shutdown logger and flush any pending log messages.

    This should be called when your application is shutting down
    to ensure all logs are properly sent and avoid watchtower warnings.
    """
    import time
    global _global_logger, _cloudwatch_handler

    if _cloudwatch_handler is not None:
        try:
            # Flush any pending messages multiple times to be aggressive
            _cloudwatch_handler.flush()
            time.sleep(0.2)  # Give time for flush to complete
            _cloudwatch_handler.flush()
            time.sleep(0.1)  # Additional time
            # Close the handler to stop background threads
            _cloudwatch_handler.close()
        except Exception:
            # Ignore errors during shutdown
            pass
        finally:
            _cloudwatch_handler = None

    if _global_logger is not None:
        # Remove all handlers from the logger
        for handler in _global_logger.logger.handlers[:]:
            try:
                if hasattr(handler, 'flush'):
                    handler.flush()
                handler.close()
                _global_logger.logger.removeHandler(handler)
            except Exception:
                # Ignore errors during shutdown
                pass
        _global_logger = None


def get_logger(name: str | None = None) -> TraceRootLogger:
    """Get the global logger instance or create a new one"""
    if _global_logger is None:
        raise RuntimeError(
            "Logger not initialized. Call traceroot.init() first.")

    if name is None:
        return _global_logger

    # Create a new logger with the same config and
    # credential manager but different name
    return TraceRootLogger(
        _global_logger.config,
        _global_logger.credential_manager,
        name,
    )
