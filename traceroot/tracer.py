"""Core tracing initialization and management"""

import inspect
import json
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Sequence

import opentelemetry
import pandas as pd
import yaml
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter,
                                            SimpleSpanProcessor)
from opentelemetry.trace import get_current_span

from traceroot.config import TraceRootConfig
from traceroot.logger import initialize_logger
from traceroot.utils.io import list_parent_folders, list_sub_folders

# Global state
_tracer_provider: TracerProvider | None = None
_config: TraceRootConfig | None = None


@dataclass
class TraceOptions:
    r"""Options for configuring function tracing"""
    span_name: str | None = None
    span_name_suffix: str | None = None

    # Parameter tracking options
    trace_params: bool | Sequence[str] = False
    trace_return_value: bool = False

    # Attribute handling
    flatten_attributes: bool = True

    def get_span_name(self, fn: Callable) -> str:
        r"""Get the span name for a function"""
        if self.span_name is not None:
            return self.span_name
        if self.span_name_suffix is not None:
            return f'{fn.__module__}.{fn.__qualname__}{self.span_name_suffix}'
        return f'{fn.__module__}.{fn.__qualname__}'


def _initialize_tracing(**kwargs: Any) -> TracerProvider:
    r"""Initialize TraceRoot tracing and logging.

    This is the main entry point for setting up tracing and logging.
    Call this once at the start of your application.

    Args:
        **kwargs: Configuration parameters for TraceRootConfig.
            If a .traceroot-config.yaml file exists, it will be loaded first,
            and any kwargs provided will override the file configuration.

    Returns:
        TracerProvider instance

    Example:
        # With custom config
        _initialize_tracing(
            service_name="my-service",
            environment="production",
            aws_region="us-west-2"
        )

        # Or using .traceroot-config.yaml file with optional overrides
        _initialize_tracing(environment="staging")  # Override only environment
    """
    global _tracer_provider, _config

    # Check if already initialized
    if _tracer_provider is not None:
        return _tracer_provider

    # Load configuration from YAML file first
    yaml_config = _find_traceroot_config()

    # Merge YAML config with kwargs (kwargs take precedence)
    if yaml_config:
        config_params = {**yaml_config, **kwargs}
    else:
        config_params = kwargs

    if len(config_params) == 0:
        return

    config = TraceRootConfig(**config_params)

    _config = config

    # TODO(xinwei): separate logger initialization from tracer initialization.
    # Initialize logger first
    initialize_logger(config)

    # Create resource with service information
    resource = Resource(
        attributes={
            SERVICE_NAME: config.service_name,
            "service.github_owner": config.github_owner,
            "service.github_repo_name": config.github_repo_name,
            "service.version": config.github_commit_hash,
            "service.environment": config.environment,
        })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processors based on configuration
    if config.enable_console_export:
        console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)

    # OTLP exporter for X-Ray (via OpenTelemetry Collector)
    otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
    batch_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(batch_processor)

    # Set as global tracer provider
    otel_trace.set_tracer_provider(provider)
    _tracer_provider = provider

    return provider


def shutdown_tracing() -> None:
    """
    Shutdown tracing and flush any pending spans.

    This should be called when your application is shutting down
    to ensure all traces are properly exported.
    """
    global _tracer_provider

    if _tracer_provider is not None:
        _tracer_provider.shutdown()
        _tracer_provider = None


def is_initialized() -> bool:
    """Check if tracing has been initialized"""
    return _tracer_provider is not None


def get_tracer_provider() -> TracerProvider | None:
    """Get the current tracer provider"""
    return _tracer_provider


def get_config() -> TraceRootConfig | None:
    """Get the current configuration"""
    return _config


@contextmanager
def _trace(function: Callable, options: TraceOptions, *args: Any,
           **kwargs: dict[str, Any]):
    """Internal context manager for tracing function execution"""
    # no-op if tracing is not initialized
    if not is_initialized():
        yield None
        return

    try:
        # Get tracer instance
        tracer = opentelemetry.trace.get_tracer(__name__)

        # Get span name from options
        _span_name = options.get_span_name(function)

        # Create and start new span

        _span = tracer.start_as_current_span(_span_name)
    except Exception:
        # If span creation fails, yield None and continue without tracing
        yield None
        return

    with _span as span:
        # Set AWS X-Ray annotations as individual attributes
        span.set_attribute("hash", _config._cloudwatch_log_group)
        span.set_attribute("service_name", _config.service_name)
        span.set_attribute("service_environment", _config.environment)
        # Add parameter attributes if requested
        if options.trace_params:
            parameter_values = _params_to_dict(
                function,
                options.trace_params,
                *args,
                **kwargs,
            )
            _store_dict_in_span(parameter_values, span,
                                options.flatten_attributes)

        yield span


def trace(options: TraceOptions = TraceOptions()) -> Callable[..., Any]:
    """
    Decorator for tracing function execution.

    Args:
        options: TraceOptions instance to configure tracing behavior

    Returns:
        Decorated function with tracing enabled

    Example:
        @trace()
        def my_function():
            pass

        @trace(TraceOptions(trace_params=True, trace_return_value=True))
        def detailed_function(x, y):
            return x + y
    """

    def _inner_trace(function: Callable) -> Callable:

        @wraps(function)
        def _trace_sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _trace(function, options, *args, **kwargs) as span:
                ret = function(*args, **kwargs)
                if options.trace_return_value and span:
                    _store_dict_in_span({"return": ret}, span,
                                        options.flatten_attributes)
                return ret

        @wraps(function)
        async def _trace_async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _trace(function, options, *args, **kwargs) as span:
                ret = await function(*args, **kwargs)
                if options.trace_return_value and span:
                    _store_dict_in_span({"return": ret}, span,
                                        options.flatten_attributes)
                return ret

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(function):
            return _trace_async_wrapper
        else:
            return _trace_sync_wrapper

    return _inner_trace


def write_attributes_to_current_span(attributes: dict[str, Any]) -> None:
    """Write custom attributes to the current active span"""
    span = get_current_span()
    if span and span.is_recording():
        _store_dict_in_span(attributes, span, flatten=False)


# Utility functions for span management


def _serialize_dict(d: dict[Any, Any]) -> dict[Any, Any]:
    """Serializes a dictionary."""
    return json.loads(json.dumps(d, default=str))


def _params_to_dict(
    func: Callable,
    params_to_track: bool | Sequence[str],
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convert function parameters to dictionary for tracing"""
    try:
        bound_arguments = inspect.signature(func).bind(*args, **kwargs)
        bound_arguments.apply_defaults()

        def _should_track_key(key: str) -> bool:
            if key == 'self':
                return False
            if isinstance(params_to_track, bool):
                return params_to_track
            return key in params_to_track

        return {
            f'params.{key}': value
            for key, value in bound_arguments.arguments.items()
            if _should_track_key(key)
        }
    except Exception:
        return {}


def _store_dict_in_span(data: dict[str, Any], span: Any, flatten: bool = True):
    """
    Stores a dictionary in a span (as attributes), optionally flattening it.
    """
    if flatten:
        data = _flatten_dict(data)
    data = {k: v if v is not None else 'None' for k, v in data.items()}
    span.set_attributes(_serialize_dict(data))


def _flatten_dict(data: dict[str, Any], sep: str = "_") -> dict[str, Any]:
    """Flattens a dictionary, joining parent/child keys with `sep`."""
    flattened = pd.json_normalize(data, sep=sep).to_dict(orient="records")
    return flattened[0] if len(flattened) > 0 else {}


def _find_traceroot_config() -> dict[str, Any] | None:
    """Find and load the .traceroot-config.yaml file.

    Searches the current directory for the configuration file.

    Returns:
        Dictionary containing the configuration, or None if no file found.
    """
    config_filename = ".traceroot-config.yaml"

    # Check current working directory
    current_path = Path.cwd()
    config_path = current_path / config_filename

    if config_path.exists():
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file {config_path}: {e}")

    # Check subfolders for config file up to 4 levels
    sub_folders = list_sub_folders(4, config_filename, current_path)
    for config_path in sub_folders:
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file "
                             f"{config_path}: {e}")

    # Check parent folders for config file up to 4 levels
    parent_folders = list_parent_folders(4, config_filename, current_path)
    for config_path in parent_folders:
        try:
            with open(config_path) as file:
                config_data = yaml.safe_load(file)
                return config_data if config_data else {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Error reading config file "
                             f"{config_path}: {e}")
    return None
