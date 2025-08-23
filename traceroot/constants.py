"""Constants and configuration mappings for TraceRoot"""

DEFAULT_VERIFICATION_ENDPOINT = "https://api.test.traceroot.ai/v1/verify/credentials"  # noqa: E501

# Environment variable to config field mapping
# Pattern: TRACEROOT_[CAPITALIZED_CONFIG_FIELD_NAME] -> config_field_name
ENV_VAR_MAPPING = {
    "TRACEROOT_SERVICE_NAME": "service_name",
    "TRACEROOT_GITHUB_OWNER": "github_owner",
    "TRACEROOT_GITHUB_REPO_NAME": "github_repo_name",
    "TRACEROOT_GITHUB_COMMIT_HASH": "github_commit_hash",
    "TRACEROOT_TOKEN": "token",
    "TRACEROOT_NAME": "name",
    "TRACEROOT_AWS_REGION": "aws_region",
    "TRACEROOT_OTLP_ENDPOINT": "otlp_endpoint",
    "TRACEROOT_ENVIRONMENT": "environment",
    "TRACEROOT_ENABLE_SPAN_CONSOLE_EXPORT": "enable_span_console_export",
    "TRACEROOT_ENABLE_LOG_CONSOLE_EXPORT": "enable_log_console_export",
    "TRACEROOT_ENABLE_SPAN_CLOUD_EXPORT": "enable_span_cloud_export",
    "TRACEROOT_ENABLE_LOG_CLOUD_EXPORT": "enable_log_cloud_export",
    "TRACEROOT_LOCAL_MODE": "local_mode",
    "TRACEROOT_VERIFICATION_ENDPOINT": "verification_endpoint",
}
