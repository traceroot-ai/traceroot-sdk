"""Configuration management for TraceRoot"""

from dataclasses import dataclass


@dataclass
class TraceRootConfig:
    r"""Configuration for TraceRoot tracing and logging"""
    # Identification
    name: str
    service_name: str
    aws_region: str

    # OpenTelemetry Configuration
    otlp_endpoint: str

    # GitHub Identification
    github_owner: str
    github_repo_name: str
    github_commit_hash: str

    # OpenTelemetry Configuration
    otlp_endpoint: str

    # Environment
    environment: str = "development"

    # Tracing options
    enable_console_export: bool = True

    def __post_init__(self):
        self._cloudwatch_log_group = self.name
        self._cloudwatch_stream_name = (f"{self.service_name}-"
                                        f"{self.environment}")
