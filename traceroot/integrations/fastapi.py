"""FastAPI integration for automatic request tracing"""

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Span

from traceroot.tracer import get_config, get_tracer_provider


def connect_fastapi(app: FastAPI) -> None:
    """
    Setup automatic tracing for FastAPI application with distributed tracing
    support.

    This adds middleware to automatically trace all HTTP requests,
    correlate them with logs, and properly handle incoming trace context
    from other services in a microservice architecture.

    Args:
        app: FastAPI application instance

    Example:
        import traceroot
        from fastapi import FastAPI
        from traceroot import connect_fastapi

        app = FastAPI()
        traceroot.init()
        connect_fastapi(app)
    """
    provider = get_tracer_provider()
    config = get_config()

    if provider is None:
        raise RuntimeError(
            "Tracing not initialized. Call traceroot.init() first.")

    if config is None:
        raise RuntimeError("Configuration not available.")

    def server_request_hook(span: Span, scope: dict):
        """Hook called when server receives a request"""
        if span and span.is_recording():
            # Add service metadata to the span
            span.set_attribute("service.name", config.service_name)
            span.set_attribute("service.github_owner", config.github_owner)
            span.set_attribute("service.github_repo_name",
                               config.github_repo_name)
            span.set_attribute("service.version", config.github_commit_hash)
            span.set_attribute("service.environment", config.environment)
            span.set_attribute("telemetry.sdk.language", "python")

            # Add request path
            path = scope.get('path', '')
            if path:
                span.set_attribute("http.path", path)

            method = scope.get('method', '')
            if method:
                span.set_attribute("http.method", method)

    def client_request_hook(span: Span, scope: dict, message: dict = None):
        """Hook called when making outbound requests"""
        if span and span.is_recording():
            span.set_attribute("service.name", config.service_name)
            span.set_attribute("telemetry.sdk.language", "python")

            # TODO (xinwei): This is might be the same as the information in
            # server_request_hook. Let's check and deprecate it as necessary.
            path = scope.get('path', '')
            method = scope.get('method', '')
            if path:
                span.set_attribute("http.path", path)
            if method:
                span.set_attribute("http.method", method)

            if message:
                status_code = message.get('status', '')
                if status_code:
                    span.set_attribute("http.status_code", status_code)

                headers = message.get('headers', [])
                assert isinstance(headers, list)
                for key, value in headers:
                    span.set_attribute(f"http.header.{key}", value)

    def client_response_hook(span: Span, scope: dict, message: dict):
        """Hook called when receiving responses from outbound requests.
        NOTE: We are not using scope here because it's the same as the
        one used in client_request_hook.
        """
        if span and span.is_recording():
            span.set_attribute("service.name", config.service_name)
            span.set_attribute("telemetry.sdk.language", "python")
            body = message.get('body', '')
            if body:
                # Only log first 1000 chars of body to avoid huge spans
                body_str = str(body)[:1000]
                span.set_attribute("http.response.body_preview", body_str)

    # Instrument the FastAPI app
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        server_request_hook=server_request_hook,
        client_request_hook=client_request_hook,
        client_response_hook=client_response_hook,
    )
