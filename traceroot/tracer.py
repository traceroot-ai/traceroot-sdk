"""Core tracing initialization and management"""

import inspect
import json
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Optional, Sequence, Union

import opentelemetry
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import get_current_span

from traceroot.config import TraceRootConfig
from traceroot.logger import initialize_logger
import pandas as pd

# Global state
_tracer_provider: Optional[TracerProvider] = None
_config: Optional[TraceRootConfig] = None


@dataclass
class TraceOptions:
    """Options for configuring function tracing"""
    
    span_name: str = ""
    span_name_suffix: str = ""
    
    # Parameter tracking options
    trace_params: Union[bool, Sequence[str]] = False
    trace_return_value: bool = False
    
    # Attribute handling
    flatten_attributes: bool = True
    
    def get_span_name(self, fn: Callable) -> str:
        """Get the span name for a function"""
        if self.span_name:
            return self.span_name
        return f'{fn.__module__}.{fn.__qualname__}{self.span_name_suffix}'


def initialize_tracing(
    service_name: str,
    config: Optional[TraceRootConfig] = None,
) -> TracerProvider:
    """
    Initialize TraceRoot tracing and logging.
    
    This is the main entry point for setting up tracing and logging.
    Call this once at the start of your application.
    
    Args:
        service_name: Name of your service
        config: Optional TraceRootConfig. If not provided, will be created from environment variables.
        
    Returns:
        TracerProvider instance
        
    Example:
        # Simple initialization
        initialize_tracing("my-service")
        
        # With custom config
        config = TraceRootConfig(
            service_name="my-service",
            environment="production",
            aws_region="us-east-1"
        )
        initialize_tracing("my-service", config)
    """
    global _tracer_provider, _config
    
    # Check if already initialized
    if _tracer_provider is not None:
        return _tracer_provider
    
    # Use provided config or create from environment
    # if config is None:
    #     config = get_config_from_env(service_name)
    _config = config
    
    # TODO(xinwei): separate logger initialization from tracer initialization.
    # Initialize logger first
    initialize_logger(config)
    
    # Create resource with service information
    resource = Resource(attributes={
        SERVICE_NAME: config.service_name,
        "service.version": config.github_version,
        "service.environment": config.environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add span processors based on configuration
    if config.enable_console_export:
        console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)
    
    if config.enable_xray_traces:
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


def get_tracer_provider() -> Optional[TracerProvider]:
    """Get the current tracer provider"""
    return _tracer_provider


def get_config() -> Optional[TraceRootConfig]:
    """Get the current configuration"""
    return _config

@contextmanager
def _trace(function: Callable, options: TraceOptions, *args: Any, **kwargs: Dict[str, Any]):
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
        # Add parameter attributes if requested
        if options.trace_params:
            parameter_values = _params_to_dict(
                function,
                options.trace_params,
                *args,
                **kwargs,
            )
            _store_dict_in_span(parameter_values, span, options.flatten_attributes)
        
        yield span


def trace(options: TraceOptions = TraceOptions()) -> Callable:
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
                    _store_dict_in_span({"return": ret}, span, options.flatten_attributes)
                return ret

        @wraps(function)
        async def _trace_async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _trace(function, options, *args, **kwargs) as span:
                ret = await function(*args, **kwargs)
                if options.trace_return_value and span:
                    _store_dict_in_span({"return": ret}, span, options.flatten_attributes)
                return ret

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(function):
            return _trace_async_wrapper
        else:
            return _trace_sync_wrapper

    return _inner_trace


def write_attributes_to_current_span(attributes: Dict[str, Any]) -> None:
    """Write custom attributes to the current active span"""
    span = get_current_span()
    if span and span.is_recording():
        _store_dict_in_span(attributes, span, flatten=False)


# Utility functions for span management


def _serialize_dict(d: Dict[Any, Any]) -> Dict[Any, Any]:
    """Serializes a dictionary."""
    return json.loads(json.dumps(d, default=str))

def _params_to_dict(
    func: Callable,
    params_to_track: Union[bool, Sequence[str]],
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
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


def _store_dict_in_span(data: Dict[str, Any], span: Any, flatten: bool = True):
    # """Store dictionary data as span attributes"""
    # if not span or not span.is_recording():
    #     return
        
    # try:
    #     if flatten:
    #         data = _flatten_dict(data)
        
    #     # Convert None values to string and serialize
    #     serialized_data = {
    #         k: v if v is not None else 'None' 
    #         for k, v in data.items()
    #     }
    #     serialized_data = json.loads(json.dumps(serialized_data, default=str))
        
    #     span.set_attributes(serialized_data)
    # except Exception:
    #     # Don't break execution if attribute setting fails
    #     pass
    """
    Stores a dictionary in a span (as attributes), optionally flattening it.
    """
    if flatten:
        data = _flatten_dict(data)
    data = {k: v if v is not None else 'None' for k, v in data.items()}
    span.set_attributes(_serialize_dict(data))


def _flatten_dict(data: Dict[str, Any], sep: str = "_") -> Dict[str, Any]:
    # """Flatten nested dictionary with separator"""
    # def _flatten_recursive(obj, parent_key=''):
    #     items = []
    #     if isinstance(obj, dict):
    #         for k, v in obj.items():
    #             new_key = f"{parent_key}{sep}{k}" if parent_key else k
    #             items.extend(_flatten_recursive(v, new_key).items())
    #     else:
    #         return {parent_key: obj}
    #     return dict(items)
    
    # return _flatten_recursive(data) 
    """Flattens a dictionary, joining parent/child keys with `sep`."""
    flattened = pd.json_normalize(data, sep=sep).to_dict(orient="records")
    return flattened[0] if len(flattened) > 0 else {}