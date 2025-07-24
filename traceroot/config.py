"""Configuration management for TraceRoot"""

from dataclasses import dataclass


@dataclass
class TraceRootConfig:
    r"""Configuration for TraceRoot tracing and logging"""
    # Identification
    service_name: str

    # GitHub Identification
    github_owner: str
    github_repo_name: str
    github_commit_hash: str

    # Token for TraceRoot API
    token: str | None = None

    # User identification
    name: str | None = None

    # AWS Configuration
    aws_region: str = "us-west-2"

    # OpenTelemetry Configuration
    otlp_endpoint: str = "http://localhost:4318/v1/traces"

    # Environment
    environment: str = "development"

    # Tracing options
    enable_span_console_export: bool = False
    enable_log_console_export: bool = False

    # Local mode
    local_mode: bool = False

    def __post_init__(self):
        self._name = self.name
        self._sub_name = (f"{self.service_name}-"
                          f"{self.environment}")
