#!/usr/bin/env python3
"""
Unit tests to verify that traceroot properly handles async generators
and streaming responses without prematurely closing spans.
"""

import asyncio
import pytest
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

import traceroot
from fastapi.responses import StreamingResponse


class TestStreamingTrace:
    """Test suite for streaming trace functionality."""

    @pytest.fixture(autouse=True)
    def setup_traceroot(self):
        """Initialize traceroot for each test."""
        traceroot.init(
            service_name="streaming-test",
            environment="test",
            local_mode=True,
            enable_span_console_export=False  # Disable console output for tests
        )

    async def mock_async_generator(self, data: str) -> AsyncGenerator[str, None]:
        """Mock async generator that simulates streaming data processing."""
        for i in range(3):
            yield f"data: Processing step {i} for {data}\n\n"
            await asyncio.sleep(0.01)  # Small delay to simulate work

    @traceroot.trace()
    async def streaming_endpoint(self, data: str) -> StreamingResponse:
        """Test endpoint that returns a StreamingResponse with async generator."""
        return StreamingResponse(
            self.mock_async_generator(data), 
            media_type="text/event-stream"
        )

    @traceroot.trace()
    async def direct_generator_endpoint(self, data: str) -> AsyncGenerator[str, None]:
        """Test endpoint that directly returns an async generator."""
        async for item in self.mock_async_generator(data):
            yield item

    @pytest.mark.asyncio
    async def test_streaming_response_span_lifecycle(self):
        """Test that spans stay alive during StreamingResponse consumption."""
        with patch('traceroot.tracer.print') as mock_print:
            # Call the streaming endpoint
            response = await self.streaming_endpoint("test-data")
            
            # Verify we got a StreamingResponse
            assert isinstance(response, StreamingResponse)
            
            # Consume the streaming response
            items = []
            async for chunk in response.body_iterator:
                chunk_str = chunk if isinstance(chunk, str) else chunk.decode()
                items.append(chunk_str)
            
            # Verify we got all expected chunks
            assert len(items) == 3
            assert all("Processing step" in item for item in items)
            assert all("test-data" in item for item in items)
            
            # Verify span creation was logged (check actual span name from output)
            span_creation_calls = [call for call in mock_print.call_args_list if "Creating span with name:" in str(call)]
            assert len(span_creation_calls) > 0, f"No span creation found in calls: {mock_print.call_args_list}"

    @pytest.mark.asyncio
    async def test_direct_async_generator_span_lifecycle(self):
        """Test that spans stay alive during direct async generator consumption."""
        with patch('traceroot.tracer.print') as mock_print:
            # Call the direct generator endpoint (don't await - it returns a generator directly)
            generator = self.direct_generator_endpoint("test-data")
            
            # Verify we got an async generator
            assert hasattr(generator, '__aiter__')
            
            # Consume the generator
            items = []
            async for chunk in generator:
                items.append(chunk)
            
            # Verify we got all expected chunks
            assert len(items) == 3
            assert all("Processing step" in item for item in items)
            assert all("test-data" in item for item in items)
            
            # Verify span creation was logged (check actual span name from output)
            span_creation_calls = [call for call in mock_print.call_args_list if "Creating span with name:" in str(call)]
            assert len(span_creation_calls) > 0, f"No span creation found in calls: {mock_print.call_args_list}"

    @pytest.mark.asyncio
    async def test_span_attributes_for_streaming(self):
        """Test that streaming spans get proper attributes set."""
        from opentelemetry.trace import get_current_span
        
        # Mock the span to capture attributes
        with patch('opentelemetry.trace.get_tracer') as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_span_context = MagicMock()
            mock_span = MagicMock()
            
            mock_get_tracer.return_value = mock_tracer
            mock_tracer.start_as_current_span.return_value = mock_span_context
            mock_span_context.__enter__.return_value = mock_span
            mock_span.is_recording.return_value = True
            
            # Call the streaming endpoint
            response = await self.streaming_endpoint("test-data")
            
            # Consume the response
            items = []
            async for chunk in response.body_iterator:
                items.append(chunk)
            
            # Verify streaming attribute was set
            mock_span.set_attribute.assert_any_call("streaming.enabled", True)
            
            # Verify generator completion attribute was set
            mock_span.set_attribute.assert_any_call("generator.completed", True)

    @pytest.mark.asyncio
    async def test_normal_async_function_still_works(self):
        """Test that normal async functions (non-streaming) still work correctly."""
        
        @traceroot.trace()
        async def normal_async_function(data: str) -> str:
            return f"processed: {data}"
        
        with patch('traceroot.tracer.print') as mock_print:
            result = await normal_async_function("test-data")
            
            # Verify normal function behavior
            assert result == "processed: test-data"
            
            # Verify span was created (check actual span name from output)
            span_creation_calls = [call for call in mock_print.call_args_list if "Creating span with name:" in str(call)]
            assert len(span_creation_calls) > 0, f"No span creation found in calls: {mock_print.call_args_list}"

    def test_extract_async_generator_detection(self):
        """Test the async generator detection helper function."""
        from traceroot.tracer import _extract_async_generator
        
        # Test direct async generator
        async def test_gen():
            yield "test"
        
        gen = test_gen()
        assert _extract_async_generator(gen) == gen
        gen.aclose()  # Clean up
        
        # Test StreamingResponse with async generator
        gen2 = test_gen()
        response = StreamingResponse(gen2, media_type="text/plain")
        assert _extract_async_generator(response) == gen2
        gen2.aclose()  # Clean up
        
        # Test non-generator object
        assert _extract_async_generator("not a generator") is None
        assert _extract_async_generator(123) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
