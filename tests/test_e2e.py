"""
Example usage of the TraceRoot package

This example shows how to:
1. Initialize tracing and logging
2. Use the @trace decorator with various options
3. Set up FastAPI integration
4. Query logs and traces
"""

import asyncio
import time

from fastapi import FastAPI
from query.client import TraceRootClient

from integrations.fastapi import connect_fastapi
from traceroot.config import TraceRootConfig
from traceroot.logger import get_logger
# Import TraceRoot - only public API
from traceroot.tracer import (TraceOptions, initialize_tracing, trace,
                              write_attributes_to_current_span)

# Initialize tracing (call this once at startup)
initialize_tracing(config=TraceRootConfig(
    service_name="example-service",
    owner="octocat",
    repo_name="Hello-World",
    commit_hash="v0.1.0",
    environment="development",
    aws_region="us-west-2",
    otlp_endpoint="http://localhost:4318/v1/traces",
))

# Get logger instance
logger = get_logger()


# Example 1: Simple function tracing
@trace()
def simple_function():
    """A simple function with basic tracing"""
    logger.info("This is a simple function")
    time.sleep(0.1)
    return "Hello from simple function"


# Example 2: Function with parameter and return value tracing
@trace(TraceOptions(trace_params=True, trace_return_value=True))
def detailed_function(x: int, y: int, name: str = "default"):
    """Function with detailed tracing of parameters and return value"""
    logger.info(f"Processing {name} with values {x} and {y}")
    result = x + y
    logger.debug(f"Calculated result: {result}")
    return result


# Example 3: Async function tracing
@trace(TraceOptions(span_name="custom-async-operation"))
async def async_function(delay: float):
    """Async function with custom span name"""
    logger.info(f"Starting async operation with delay {delay}")
    await asyncio.sleep(delay)
    logger.info("Async operation completed")
    return f"Completed after {delay} seconds"


# Example 4: Function with custom attributes using
# write_attributes_to_current_span
@trace(TraceOptions(trace_params=True,
                    span_name="custom-attributes-operation"))
def function_with_custom_attributes(value: int):
    """Example showing how to add custom attributes to the current span"""
    logger.info(f"Processing value: {value}")

    result = value * 2

    # Add custom attributes to the current span
    write_attributes_to_current_span({
        "operation_type": "multiplication",
        "input_value": value,
        "output_value": result,
        "custom_metadata": "example_data"
    })

    logger.info(f"Custom attributes operation result: {result}")
    return result


# Example 5: Complex operation with nested traced functions
@trace(TraceOptions(span_name="complex-operation"))
def complex_operation_example():
    """Example showing nested spans through function calls"""
    logger.info("Starting complex operation")

    # Add operation metadata
    write_attributes_to_current_span({"operation_id": "complex-001"})

    data = "start"

    # Each step is a separate traced function
    data = step_one(data)
    data = step_two(data)
    data = step_three(data)

    logger.info(f"Complex operation result: {data}")
    return data


@trace(
    TraceOptions(span_name="step-1",
                 trace_params=True,
                 trace_return_value=True))
def step_one(data: str) -> str:
    """First step of complex operation"""
    write_attributes_to_current_span({"step_number": 1})
    return data + " -> step1"


@trace(
    TraceOptions(span_name="step-2",
                 trace_params=True,
                 trace_return_value=True))
def step_two(data: str) -> str:
    """Second step of complex operation"""
    write_attributes_to_current_span({"step_number": 2})
    return data + " -> step2"


@trace(
    TraceOptions(span_name="step-3",
                 trace_params=True,
                 trace_return_value=True))
def step_three(data: str) -> str:
    """Third step of complex operation"""
    write_attributes_to_current_span({"step_number": 3})
    return data + " -> step3"


# Example 6: Function with selective parameter tracing
@trace(
    TraceOptions(trace_params=["important_param", "config"],
                 trace_return_value=True))
def selective_param_tracing(important_param: str, secret_param: str,
                            config: dict, debug_info: str):
    """Example showing how to trace only specific parameters"""
    logger.info("Processing with selective parameter tracing")

    # Only important_param and config will be traced,
    # not secret_param or debug_info
    result = (f"Processed {important_param} with config keys: "
              f"{list(config.keys())}")

    write_attributes_to_current_span({
        "processing_mode": "selective",
        "config_size": len(config)
    })

    return result


# Example 7: Error handling in traced functions
@trace(TraceOptions(trace_params=True, span_name="error-prone-operation"))
def error_prone_function(should_fail: bool = False):
    """Example showing how errors are handled in traced functions"""
    logger.info(f"Running error-prone function, should_fail={should_fail}")

    write_attributes_to_current_span({"test_mode": should_fail})

    if should_fail:
        logger.error("Simulating an error")
        raise ValueError("Simulated error for testing")

    logger.info("Function completed successfully")
    return "Success!"


# Example 8: FastAPI integration
app = FastAPI(title="TraceRoot Example API")

# Setup automatic FastAPI tracing
connect_fastapi(app)


@app.get("/")
async def root():
    """Root endpoint that calls traced functions"""
    logger.info("Root endpoint called")

    # Call traced functions
    simple_result = simple_function()
    detailed_result = detailed_function(10, 20, "api-call")
    async_result = await async_function(0.2)
    custom_attrs_result = function_with_custom_attributes(42)
    complex_result = complex_operation_example()
    selective_result = selective_param_tracing(
        important_param="api-data",
        secret_param="secret123",
        config={
            "env": "production",
            "debug": False
        },
        debug_info="internal-debug-data")

    return {
        "message": "TraceRoot example API",
        "simple_result": simple_result,
        "detailed_result": detailed_result,
        "async_result": async_result,
        "custom_attrs_result": custom_attrs_result,
        "complex_result": complex_result,
        "selective_result": selective_result,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.debug("Health check called")
    return {"status": "healthy"}


@app.get("/error-test")
async def error_test():
    """Endpoint to test error handling in traced functions"""
    try:
        # This will succeed
        success_result = error_prone_function(should_fail=False)

        # This will fail and show error tracing
        error_prone_function(should_fail=True)

        return {"result": success_result}
    except ValueError as e:
        logger.error(f"Caught expected error: {e}")
        return {"error": str(e), "message": "Error was properly traced"}


# Example 9: Querying logs and traces
def query_example():
    """Example of how to query logs and traces"""
    client = TraceRootClient(aws_region="us-west-2")

    # Query recent logs for the service
    recent_logs = client.query_logs_by_service(
        service_name="example-service",
        log_group_name="traceroot-example-service",
        minutes=60)
    print(f"Found {len(recent_logs)} recent log entries")

    # Query logs by trace ID (you would get this from a trace)
    # trace_id = "1-4bd3ef22-1264608c127ced6a0c99f898"  # Example trace ID
    # trace_logs = client.query_logs_by_trace_id(trace_id)
    # print(f"Found {len(trace_logs)} logs for trace {trace_id}")

    # Get recent traces
    recent_traces = client.get_recent_traces(minutes=60,
                                             service_name="example-service")
    print(f"Found {len(recent_traces)} recent traces")


if __name__ == "__main__":
    # Run some example functions
    print("Running TraceRoot examples...")

    # Test traced functions
    simple_function()
    detailed_function(5, 10, "test-run")

    # Test async function
    asyncio.run(async_function(0.1))

    # Test custom attributes
    function_with_custom_attributes(21)

    # Test selective parameter tracing
    selective_param_tracing(important_param="test-data",
                            secret_param="secret456",
                            config={
                                "mode": "test",
                                "verbose": True
                            },
                            debug_info="test-debug-info")

    # Test complex operation
    complex_operation_example()

    # Test error handling
    try:
        error_prone_function(should_fail=False)
        print("✅ Success case handled correctly")
    except Exception as e:
        print(f"❌ Unexpected error in success case: {e}")

    try:
        error_prone_function(should_fail=True)
        print("❌ Error case should have failed")
    except ValueError:
        print("✅ Error case handled correctly")

    # Example query (uncomment if you have AWS credentials configured)
    # query_example()

    print("Examples completed!")

    # To run the FastAPI server, use:
    # uvicorn example_usage:app --reload
