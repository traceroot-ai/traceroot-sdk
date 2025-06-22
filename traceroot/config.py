"""Configuration management for TraceRoot"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TraceRootConfig:
    """Configuration for TraceRoot tracing and logging"""
    
    # Service identification
    service_name: str
    github_version: str = "latest"
    environment: str = "development"
    
    # AWS Configuration
    aws_region: str = "us-west-2"
    cloudwatch_log_group: Optional[str] = None
    cloudwatch_stream_name: Optional[str] = None
    
    # OpenTelemetry Configuration  
    otlp_endpoint: str = "http://localhost:4318/v1/traces"
    
    # Tracing options
    enable_console_export: bool = False
    enable_cloudwatch_logs: bool = True
    enable_xray_traces: bool = True
    
    def __post_init__(self):
        # Set default CloudWatch log group if not provided
        if self.cloudwatch_log_group is None:
            self.cloudwatch_log_group = f"traceroot-{self.service_name}"
            
        # Set default stream name if not provided  
        if self.cloudwatch_stream_name is None:
            self.cloudwatch_stream_name = f"{self.service_name}-{self.environment}"


# def get_config_from_env(service_name: str) -> TraceRootConfig:
#     """Create configuration from environment variables"""
#     return TraceRootConfig(
#         service_name=service_name,
#         github_version=os.getenv("TRACEROOT_GITHUB_VERSION", "latest"),
#         environment=os.getenv("TRACEROOT_ENVIRONMENT", "development"),
#         aws_region=os.getenv("AWS_REGION", "us-west-2"),
#         cloudwatch_log_group=os.getenv("TRACEROOT_LOG_GROUP"),
#         cloudwatch_stream_name=os.getenv("TRACEROOT_STREAM_NAME"),
#         otlp_endpoint=os.getenv("TRACEROOT_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"),
#         enable_console_export=os.getenv("TRACEROOT_CONSOLE_EXPORT", "false").lower() == "true",
#         enable_cloudwatch_logs=os.getenv("TRACEROOT_CLOUDWATCH_LOGS", "true").lower() == "true",
#         enable_xray_traces=os.getenv("TRACEROOT_XRAY_TRACES", "true").lower() == "true",
#     ) 