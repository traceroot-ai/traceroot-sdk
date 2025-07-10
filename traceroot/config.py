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

    # OpenTelemetry Configuration
    aws_region: str = "us-west-2"
    otlp_endpoint: str = "http://localhost:4318/v1/traces"

    # Environment
    environment: str = "development"

    # Tracing options
    enable_console_export: bool = True

    def __post_init__(self):
        self._cloudwatch_log_group = self.name
        self._cloudwatch_stream_name = (f"{self.service_name}-"
                                        f"{self.environment}")
