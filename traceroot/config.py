"""Configuration management for TraceRoot"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TraceRootConfig:
    """Configuration for TraceRoot tracing and logging"""

    # Service identification
    service_name: str
    aws_region: str

    # OpenTelemetry Configuration
    otlp_endpoint: str

    # version and environment
    environment: str = "development"

    # GitHub Identification
    owner: str = "octocat"
    repo_name: str = "Hello-World"
    commit_hash: str = "main"

    # log group and stream name Configuration
    cloudwatch_log_group: Optional[str] = None
    cloudwatch_stream_name: Optional[str] = None

    # OpenTelemetry Configuration
    otlp_endpoint: str

    # Tracing options
    enable_console_export: bool = True

    # enable_cloudwatch_logs: bool = True
    # enable_xray_traces: bool = True

    def __post_init__(self):
        # Set default CloudWatch log group if not provided
        if self.cloudwatch_log_group is None:
            self.cloudwatch_log_group = f"traceroot-{self.service_name}"

        # Set default stream name if not provided
        if self.cloudwatch_stream_name is None:
            self.cloudwatch_stream_name = (f"{self.service_name}-"
                                           f"{self.environment}")
