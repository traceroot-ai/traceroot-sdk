import time

from traceroot.config import TraceRootConfig
from traceroot.logger import get_logger
from traceroot.tracer import TraceOptions, initialize_tracing, trace

initialize_tracing(config=TraceRootConfig(
    service_name="example-service",
    aws_region="us-west-2",
    otlp_endpoint="http://localhost:4318/v1/traces",
    github_owner="traceroot-ai",
    github_repo_name="traceroot-sdk",
    github_commit_hash="main",
), )

logger = get_logger()


@trace(TraceOptions(span_name="logging-function-2"))
def logging_function_2():
    logger.info("This is an info message 2")
    logger.warning("This is a warning message 2")
    logger.error("This is an error message 2")


@trace(TraceOptions(span_name="logging-function"))
def logging_function():
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logging_function_2()


@trace(TraceOptions(span_name="main"))
def main():
    logger.debug("Main function started")
    time.sleep(1)
    logging_function()
    logger.debug("Main function completed")


if __name__ == "__main__":
    main()
