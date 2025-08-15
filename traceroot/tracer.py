import inspect
import json
import logging
import time
import weakref
from collections.abc import AsyncGenerator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Sequence, Set

import opentelemetry
import pandas as pd
from opentelemetry import trace
from opentelemetry import trace as otel_trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter,
                                            SimpleSpanProcessor)
from opentelemetry.trace import Status, StatusCode, get_current_span
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

from traceroot.config import TraceRootConfig
from traceroot.logger import initialize_logger, shutdown_logger
from traceroot.utils.config import find_traceroot_config

# Global state
_tracer_provider: TracerProvider | None = None
_config: TraceRootConfig | None = None

# Global registry for tracking deferred spans
_deferred_spans: Set[weakref.ref] = set()


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
    """
    global _tracer_provider, _config

    # Check if already initialized
    if _tracer_provider is not None:
        return _tracer_provider

    # Load configuration from YAML file first
    yaml_config = find_traceroot_config()

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
            "telemetry.sdk.language": "python",
        })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processors based on configuration
    if config.enable_span_console_export:
        console_processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)

    exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint)
    batch_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(batch_processor)

    # Set as global tracer provider
    otel_trace.set_tracer_provider(provider)
    _tracer_provider = provider

    # Configure propagators to enable distributed tracing
    # This is crucial for FastAPI to properly extract trace context from
    # HTTP headers
    # and create child spans instead of new root spans
    propagator = CompositePropagator([
        TraceContextTextMapPropagator(
        ),  # Handles traceparent/tracestate headers (W3C Trace Context)
        W3CBaggagePropagator(),  # Handles baggage header (W3C Baggage)
    ])
    set_global_textmap(propagator)

    return provider


def _force_close_deferred_spans(max_age_seconds: int = 300) -> int:
    """
    Force close deferred spans that have been open too long.

    Args:
        max_age_seconds: Maximum age in seconds before force closing (default: 5 minutes)

    Returns:
        Number of spans that were force closed
    """
    current_time = time.time()
    closed_count = 0

    global _deferred_spans
    to_remove = []

    for span_ref in _deferred_spans.copy():
        span_context = span_ref()
        if span_context is None:
            # Span was garbage collected
            to_remove.append(span_ref)
        elif not span_context._closed:
            age = current_time - span_context._created_at
            if age > max_age_seconds:
                try:
                    # Mark as force closed and close the span
                    if span_context.span and span_context.span.is_recording():
                        span_context.span.set_attribute("force_closed", True)
                        span_context.span.set_attribute(
                            "close_reason", "timeout")
                        span_context.span.set_attribute(
                            "age_seconds", int(age))

                    span_context.close_span()
                    closed_count += 1
                    print(
                        f"Force closed deferred span after {age:.1f} seconds")
                except Exception as e:
                    print(f"Error force closing span: {e}")

                to_remove.append(span_ref)

    # Clean up references
    for ref in to_remove:
        _deferred_spans.discard(ref)

    return closed_count


def shutdown_tracing() -> None:
    """
    Shutdown tracing and flush any pending spans.

    This should be called when your application is shutting down
    to ensure all traces are properly exported.
    """
    global _tracer_provider

    if _tracer_provider is not None:
        # First: Force close any open deferred spans
        closed_count = _force_close_deferred_spans(
            max_age_seconds=0)  # Close all deferred spans
        if closed_count > 0:
            print(
                f"Force closed {closed_count} deferred spans during shutdown")

        # Then: Force flush any pending spans before shutdown
        print("Force flushing spans")
        _tracer_provider.force_flush(timeout_millis=5000)  # 5 second timeout
        _tracer_provider.shutdown()
        _tracer_provider = None


def shutdown() -> None:
    """
    Shutdown both tracing and logging systems.

    This should be called when your application is shutting down
    to ensure all traces and logs are properly exported and to avoid
    warnings about messages sent after logging system shutdown.
    """
    shutdown_logger()
    shutdown_tracing()


def is_initialized() -> bool:
    """Check if tracing has been initialized"""
    return _tracer_provider is not None


def get_tracer_provider() -> TracerProvider | None:
    """Get the current tracer provider"""
    return _tracer_provider


def get_config() -> TraceRootConfig | None:
    """Get the current configuration"""
    return _config


class _DeferredSpanContext:
    """Context manager that can defer span closing for async generators."""

    def __init__(self, span: Any, span_context: Any):
        self.span = span
        self.span_context = span_context
        self._closed = False
        self._created_at = time.time()

        # Register this span context for cleanup tracking
        global _deferred_spans
        _deferred_spans.add(weakref.ref(self, self._cleanup_callback))

    @staticmethod
    def _cleanup_callback(ref):
        """Called when span context is garbage collected."""
        global _deferred_spans
        _deferred_spans.discard(ref)

    def __enter__(self):
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't auto-close - wait for manual close_span call
        pass

    def close_span(self, exc_type=None, exc_val=None, exc_tb=None):
        """Manually close the span with optional exception info."""
        if not self._closed and self.span_context:
            try:
                # Ensure the span is properly ended before the context exits
                if self.span and self.span.is_recording():
                    if exc_type:
                        self.span.record_exception(exc_val)
                        self.span.set_status(
                            Status(StatusCode.ERROR, str(exc_val)))
                    else:
                        self.span.set_status(Status(StatusCode.OK))

                # Close the span context
                self.span_context.__exit__(exc_type, exc_val, exc_tb)
                self._closed = True
                print("Deferred span closed successfully")
            except ValueError as ve:
                # Handle context detachment errors specifically (common with asyncio cancellation)
                if "was created in a different Context" in str(ve):
                    print(
                        f"Warning: Context detachment failed (harmless with cancelled tasks): {ve}"
                    )
                    # Still mark as closed and try to end the span directly
                    try:
                        if self.span and self.span.is_recording():
                            self.span.end()
                    except Exception:
                        pass
                    self._closed = True
                else:
                    print(f"Error closing deferred span: {ve}")
                    self._closed = True
            except Exception as e:
                print(f"Error closing deferred span: {e}")
                # Try to end the span directly as fallback
                try:
                    if self.span and self.span.is_recording():
                        self.span.end()
                except Exception:
                    pass
                self._closed = True


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
        print(f"Creating span with name: {_span_name}")

        # Create and start new span
        _span = tracer.start_as_current_span(_span_name)
        print(f"Created span: {_span}")
    except Exception:
        # If span creation fails, yield None and continue without tracing
        print(f"Failed to create span: {_span_name}")
        yield None
        return

    with _span as span:
        # Set AWS X-Ray annotations as individual attributes
        # Avoid setting hash in local mode
        if not _config.local_mode:
            span.set_attribute("hash", _config._name)
        span.set_attribute("service_name", _config.service_name)
        span.set_attribute("service_environment", _config.environment)
        span.set_attribute("telemetry_sdk_language", "python")

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
        def _trace_async_gen_wrapper(*args: Any,
                                     **kwargs: Any) -> AsyncGenerator:
            """Wrapper for async generator functions."""
            # Create the generator by calling the function
            async_gen = function(*args, **kwargs)

            print(f"Async generator: {async_gen}")

            # Start tracing manually to have more control
            if not is_initialized():
                return async_gen

            try:
                # Get tracer instance
                tracer = opentelemetry.trace.get_tracer(__name__)
                _span_name = options.get_span_name(function)
                print(f"Creating span with name: {_span_name}")

                # Create and start new span
                span_context = tracer.start_as_current_span(_span_name)
                span = span_context.__enter__()
                print(f"Created span: {span}")

                # Set attributes
                if not _config.local_mode:
                    span.set_attribute("hash", _config._name)
                span.set_attribute("service_name", _config.service_name)
                span.set_attribute("service_environment", _config.environment)
                span.set_attribute("telemetry_sdk_language", "python")
                span.set_attribute("async_generator.enabled", True)

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

                # Create a deferred context to manage span lifecycle
                deferred_context = _DeferredSpanContext(span, span_context)

                # Return the traced generator
                return _trace_async_generator(async_gen, deferred_context,
                                              options)

            except Exception:
                print(f"Failed to create span: {_span_name}")
                return async_gen

        @wraps(function)
        async def _trace_async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start tracing manually to have more control
            if not is_initialized():
                ret = await function(*args, **kwargs)
                return ret

            try:
                # Get tracer instance
                tracer = opentelemetry.trace.get_tracer(__name__)
                _span_name = options.get_span_name(function)
                print(f"Creating span with name: {_span_name}")

                # Create and start new span
                span_context = tracer.start_as_current_span(_span_name)
                print(f"Created span context: {span_context}")
                span = span_context.__enter__()

                # Set attributes
                if not _config.local_mode:
                    span.set_attribute("hash", _config._name)
                span.set_attribute("service_name", _config.service_name)
                span.set_attribute("service_environment", _config.environment)
                span.set_attribute("telemetry_sdk_language", "python")

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

            except Exception:
                print(f"Failed to create span: {_span_name}")
                ret = await function(*args, **kwargs)
                return ret

            try:
                # Execute the function
                ret = await function(*args, **kwargs)

                # Check if the return value contains an async generator
                async_gen = _extract_async_generator(ret)

                # Also check if the function itself is an async generator function
                if async_gen is None and inspect.isasyncgenfunction(function):
                    async_gen = ret

                if async_gen is not None:
                    # For async generators, we need to keep the span alive
                    # Create a deferred context to manage span lifecycle
                    deferred_context = _DeferredSpanContext(span, span_context)
                    print(f"Created deferred context: {deferred_context}")

                    # Replace the generator with our traced version
                    traced_gen = _trace_async_generator(
                        async_gen, deferred_context, options)
                    print(f"Created traced generator: {traced_gen}")

                    # If it's a StreamingResponse, replace its body_iterator
                    if hasattr(ret, 'body_iterator'):
                        ret.body_iterator = traced_gen
                        print("Replaced body_iterator with traced generator")
                    elif hasattr(ret, 'content'):
                        ret.content = traced_gen
                        print("Replaced content with traced generator")
                    else:
                        # Direct async generator return
                        ret = traced_gen
                        print(f"Direct async generator return: {ret}")

                    # Mark as streaming - DON'T close the span here
                    if span:
                        span.set_attribute("streaming.enabled", True)

                    # CRITICAL: Don't auto-close the span context for streaming responses
                    # The _DeferredSpanContext will handle proper cleanup
                    print("Deferring span close for streaming response")
                    return ret
                else:
                    # Normal async function - close span normally
                    if options.trace_return_value and span:
                        _store_dict_in_span({"return": ret}, span,
                                            options.flatten_attributes)

                    # Close the span using context manager
                    span_context.__exit__(None, None, None)
                    return ret

            except Exception as e:
                # Close span on exception
                span_context.__exit__(type(e), e, e.__traceback__)
                raise

        # Return appropriate wrapper based on function type
        if inspect.isasyncgenfunction(function):
            return _trace_async_gen_wrapper
        elif inspect.iscoroutinefunction(function):
            return _trace_async_wrapper
        else:
            return _trace_sync_wrapper

    return _inner_trace


def write_attributes_to_current_span(attributes: dict[str, Any]) -> None:
    """Write custom attributes to the current active span"""
    span = get_current_span()
    if span and span.is_recording():
        _store_dict_in_span(attributes, span, flatten=False)


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


def _extract_async_generator(obj: Any) -> AsyncGenerator | None:
    """Extract async generator from various wrapper objects like StreamingResponse."""
    if inspect.isasyncgen(obj):
        return obj

    # Check for FastAPI StreamingResponse or similar
    if hasattr(obj, 'body_iterator') and inspect.isasyncgen(obj.body_iterator):
        return obj.body_iterator

    # Check for other common streaming response patterns
    if hasattr(obj, 'content') and inspect.isasyncgen(obj.content):
        return obj.content

    return None


@contextmanager
def _suppress_context_detachment_errors():
    """Context manager that suppresses OpenTelemetry context detachment errors during asyncio cancellation."""
    # Temporarily suppress the specific OpenTelemetry context logger
    otel_context_logger = logging.getLogger('opentelemetry.context')
    original_level = otel_context_logger.level
    original_disabled = otel_context_logger.disabled

    try:
        # Suppress context detachment error logs
        otel_context_logger.setLevel(logging.CRITICAL)
        otel_context_logger.disabled = True
        yield
    finally:
        # Restore original logging settings
        otel_context_logger.level = original_level
        otel_context_logger.disabled = original_disabled


async def _trace_async_generator(generator: AsyncGenerator,
                                 deferred_context: _DeferredSpanContext,
                                 options: TraceOptions) -> AsyncGenerator:
    """Wrap an async generator to keep the span alive during iteration."""
    exc_info = None

    # Use context manager to suppress context detachment errors during cancellation
    with _suppress_context_detachment_errors():
        try:
            async for item in generator:
                yield item
        except Exception as e:
            exc_info = (type(e), e, e.__traceback__)
            raise
        finally:
            # Close the span when this generator is exhausted or closed
            try:
                if deferred_context.span and deferred_context.span.is_recording(
                ):
                    deferred_context.span.set_attribute(
                        "generator.completed", True)

                # Close span with exception info if any
                if exc_info:
                    deferred_context.close_span(*exc_info)
                else:
                    deferred_context.close_span()
            except Exception as cleanup_error:
                # Log context detachment errors but don't re-raise
                # This commonly happens with asyncio.CancelledError when tasks are cancelled
                print(
                    f"Warning: Error during span cleanup (this is usually harmless): {cleanup_error}"
                )
                # Still try to close the span without context management
                try:
                    if deferred_context.span and deferred_context.span.is_recording(
                    ):
                        if exc_info:
                            deferred_context.span.set_status(
                                Status(StatusCode.ERROR, str(exc_info[1])))
                        else:
                            deferred_context.span.set_status(
                                Status(StatusCode.OK))
                        deferred_context.span.end()
                except Exception:
                    pass  # Ignore any further errors
