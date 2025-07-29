"""
Complex end-to-end test for TraceRoot

This test file contains a sophisticated test scenario that exercises:
1. Multiple stages of nested async functions
2. Sequential execution with dependencies between stages
3. Mixed sync/async calls within each stage
4. Error handling across async boundaries
5. Custom attribute propagation
6. Complex data transformations with tracing
7. State management between stages
"""

import asyncio
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.testclient import TestClient

import traceroot
from traceroot.integrations.fastapi import connect_fastapi
from traceroot.logger import get_logger
from traceroot.tracer import (TraceOptions, trace,
                              write_attributes_to_current_span)

# Initialize tracing
traceroot.init(
    name="traceroot-ai-experiment",
    service_name="complex-test-service",
    github_owner="test-owner",
    github_repo_name="test-repo",
    github_commit_hash="v0.1.0",
    environment="test",
    aws_region="us-west-2",
    otlp_endpoint="http://localhost:4318/v1/traces",
    enable_span_console_export=True,
    enable_log_console_export=True,
)

logger = get_logger()


# Stage 1: Initial data processing with nested async operations
@trace(TraceOptions(trace_params=True, trace_return_value=True))
async def process_nested_data(data: List[int],
                              depth: int = 0) -> Dict[str, Any]:
    """Process data with nested async calls"""
    logger.info(f"Processing nested data at depth {depth}")

    write_attributes_to_current_span({
        "depth": depth,
        "data_size": len(data),
        "stage": "initial_processing"
    })

    await asyncio.sleep(0.1)  # Simulate some work

    if depth >= 2:
        return {
            "depth": depth,
            "result": sum(data),
            "total": sum(data)  # Add total here for consistency
        }

    mid = len(data) // 2
    left_data = data[:mid]
    right_data = data[mid:]

    # Process left branch first
    left_result = await process_nested_data(left_data, depth + 1)
    # Then process right branch
    right_result = await process_nested_data(right_data, depth + 1)

    total = left_result["total"] + right_result["total"]

    combined = {
        "depth": depth,
        "left": left_result,
        "right": right_result,
        "result": total,  # Add result here for consistency
        "total": total
    }

    write_attributes_to_current_span({"combined_total": combined["total"]})

    return combined


# Stage 2: Parallel validation operations
@trace(TraceOptions(trace_params=True))
async def validate_data_chunk(chunk: Dict[str, Any]) -> bool:
    """Validate a chunk of processed data"""
    logger.info(f"Validating chunk at depth {chunk['depth']}")
    await asyncio.sleep(0.2)  # Simulate validation work
    return chunk["total"] > 0


@trace(TraceOptions(trace_params=True))
async def run_validation_stage(processed_data: Dict[str, Any]) -> List[bool]:
    """Run validation checks on processed data"""
    logger.info("Starting validation stage")

    # Create two parallel validation tasks
    validation_tasks = [
        validate_data_chunk(processed_data["left"]),
        validate_data_chunk(processed_data["right"])
    ]

    # Run validations in parallel
    results = await asyncio.gather(*validation_tasks)

    write_attributes_to_current_span({
        "validation_results": results,
        "stage": "validation"
    })

    return results


# Stage 3: Sequential transformation chain
@trace(TraceOptions(trace_params=True))
async def transform_stage_1(data: Dict[str, Any]) -> Dict[str, Any]:
    """First transformation stage"""
    logger.info("Running transform stage 1")
    await asyncio.sleep(0.15)
    result = {"stage": "transform_1", "value": data["total"] * 2}
    write_attributes_to_current_span({"transform": "stage_1"})
    return result


@trace(TraceOptions(trace_params=True))
async def transform_stage_2(data: Dict[str, Any]) -> Dict[str, Any]:
    """Second transformation stage"""
    logger.info("Running transform stage 2")
    await asyncio.sleep(0.15)
    result = {"stage": "transform_2", "value": data["value"] + 100}
    write_attributes_to_current_span({"transform": "stage_2"})
    return result


@trace(TraceOptions(trace_params=True))
async def transform_stage_3(data: Dict[str, Any]) -> Dict[str, Any]:
    """Third transformation stage"""
    logger.info("Running transform stage 3")
    await asyncio.sleep(0.15)
    if data["value"] > 1000:
        raise ValueError("Value too large in transform stage 3")
    result = {"stage": "transform_3", "value": data["value"] * 1.5}
    write_attributes_to_current_span({"transform": "stage_3"})
    return result


# Main complex operation
@trace(TraceOptions(trace_params=True, trace_return_value=True))
async def complex_sequential_operation(
        initial_data: List[int]) -> Dict[str, Any]:
    """Execute multiple stages of nested async operations sequentially"""
    logger.info("Starting complex sequential operation")
    try:
        # Stage 1: Process nested data
        logger.info("Starting Stage 1: Nested Processing")
        stage1_result = await process_nested_data(initial_data)
        write_attributes_to_current_span({
            "stage1_complete": True,
            "stage1_total": stage1_result["total"]
        })

        # Stage 2: Run validations
        logger.info("Starting Stage 2: Validation")
        validation_results = await run_validation_stage(stage1_result)
        if not all(validation_results):
            raise ValueError("Validation failed")
        write_attributes_to_current_span({
            "stage2_complete": True,
            "all_validations_passed": True
        })

        # Stage 3: Sequential transformations
        logger.info("Starting Stage 3: Transformations")
        transform1_result = await transform_stage_1(stage1_result)
        transform2_result = await transform_stage_2(transform1_result)
        final_result = await transform_stage_3(transform2_result)

        write_attributes_to_current_span({
            "stage3_complete": True,
            "final_value": final_result["value"]
        })

        return {
            "initial_processing": stage1_result,
            "validation_results": validation_results,
            "final_transformation": final_result,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in complex sequential operation: {str(e)}")
        write_attributes_to_current_span({
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise


# FastAPI app for testing
app = FastAPI()
connect_fastapi(app)


@app.post("/process")
async def process_endpoint(data: List[int]):
    """Complex endpoint that exercises all tracing features"""
    logger.info("Processing request")
    try:
        result = await complex_sequential_operation(data)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"status": "error", "message": str(e)}


# Main test function
async def run_complex_test():
    """Execute the complex test scenario"""
    logger.info("Starting complex test scenario")

    # Generate test data
    test_data = list(range(1, 17))  # 16 numbers

    try:
        result = await complex_sequential_operation(test_data)
        logger.info(f"Test completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise


def test_complex_scenario():
    """Main test function that runs the complex scenario"""
    # NOTE (xinwei): This is to compare against the FastAPI endpoint tracing
    # to verify that the tracing works because of the `connect_fastapi`
    # function.

    # Run the async test (tracing will not be triggered here)
    result = asyncio.run(run_complex_test())

    # Verify results
    assert result is not None
    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert "initial_processing" in result
    assert "validation_results" in result
    assert "final_transformation" in result
    assert all(result["validation_results"])  # All validations should pass
    assert result["final_transformation"]["value"] > 0

    # Test the FastAPI endpoint (tracing will be triggered here)
    client = TestClient(app)
    response = client.post("/process", json=list(range(1, 17)))
    assert response.status_code == 200
    assert response.json()["status"] == "success"


if __name__ == "__main__":
    test_complex_scenario()
