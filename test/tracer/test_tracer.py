import unittest
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            SimpleSpanProcessor)

from traceroot.tracer import _initialize_tracing


class TestTracer(unittest.TestCase):

    def setUp(self):
        """Reset global state before each test"""
        import traceroot.logger as logger_module
        import traceroot.tracer as tracer_module

        # Clean up any existing providers
        if tracer_module._tracer_provider:
            tracer_module._tracer_provider.shutdown()
        tracer_module._tracer_provider = None
        tracer_module._config = None

        # Clean up logger state thoroughly
        if logger_module._global_logger:
            # Remove all handlers from existing logger
            for handler in logger_module._global_logger.logger.handlers[:]:
                logger_module._global_logger.logger.removeHandler(handler)
                if hasattr(handler, 'close'):
                    handler.close()
        logger_module._global_logger = None
        logger_module._cloudwatch_handler = None

    def tearDown(self):
        """Clean up after each test"""
        import traceroot.logger as logger_module
        import traceroot.tracer as tracer_module

        if tracer_module._tracer_provider:
            tracer_module._tracer_provider.shutdown()
        tracer_module._tracer_provider = None
        tracer_module._config = None

        # Clean up logger state thoroughly
        if logger_module._global_logger:
            # Remove all handlers from existing logger
            for handler in logger_module._global_logger.logger.handlers[:]:
                logger_module._global_logger.logger.removeHandler(handler)
                if hasattr(handler, 'close'):
                    handler.close()
        logger_module._global_logger = None
        logger_module._cloudwatch_handler = None

    @patch('traceroot.logger.TraceRootLogger._fetch_aws_credentials')
    @patch('boto3.Session')
    def test_both_console_and_cloud_span_enabled(
        self,
        mock_boto_session,
        mock_fetch_credentials,
    ):
        """Test that both console and cloud span processors
        are added when both are enabled
        """
        # Mock AWS credentials
        mock_fetch_credentials.return_value = None
        mock_boto_session.return_value = MagicMock()

        provider = _initialize_tracing(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_console_export=True,
            enable_span_cloud_export=True,
            otlp_endpoint="http://test-endpoint:4318/v1/traces")

        # Verify that a TracerProvider was created
        self.assertIsInstance(provider, TracerProvider)

        # Verify that both processors were added
        self.assertEqual(len(provider._active_span_processor._span_processors),
                         2)

        # Check processor types
        processors = provider._active_span_processor._span_processors
        processor_types = [type(processor) for processor in processors]

        # Should have both SimpleSpanProcessor
        # (console) and BatchSpanProcessor (OTLP)
        self.assertIn(SimpleSpanProcessor, processor_types)
        self.assertIn(BatchSpanProcessor, processor_types)

    def test_both_console_and_cloud_span_disabled(self):
        """Test that no span processors are added when both are disabled"""
        provider = _initialize_tracing(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_console_export=False,
            enable_span_cloud_export=False,
            otlp_endpoint="http://test-endpoint:4318/v1/traces")

        # Verify that a TracerProvider was created
        self.assertIsInstance(provider, TracerProvider)

        # Verify that no processors were added
        self.assertEqual(len(provider._active_span_processor._span_processors),
                         0)

    def test_only_console_span_enabled(self):
        """Test that only console span processor is
        added when only console is enabled
        """
        provider = _initialize_tracing(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_console_export=True,
            enable_span_cloud_export=False,
            otlp_endpoint="http://test-endpoint:4318/v1/traces")

        # Verify that a TracerProvider was created
        self.assertIsInstance(provider, TracerProvider)

        # Verify that only one processor was added
        self.assertEqual(len(provider._active_span_processor._span_processors),
                         1)

        # Check processor type
        processors = provider._active_span_processor._span_processors
        processor_types = [type(processor) for processor in processors]

        # Should only have SimpleSpanProcessor (console)
        self.assertIn(SimpleSpanProcessor, processor_types)
        self.assertNotIn(BatchSpanProcessor, processor_types)

    @patch('traceroot.logger.TraceRootLogger._fetch_aws_credentials')
    @patch('boto3.Session')
    def test_only_cloud_span_enabled(self, mock_boto_session,
                                     mock_fetch_credentials):
        """Test that only cloud span processor is added
        when only cloud is enabled
        """
        # Mock AWS credentials
        mock_fetch_credentials.return_value = None
        mock_boto_session.return_value = MagicMock()

        provider = _initialize_tracing(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_console_export=False,
            enable_span_cloud_export=True,
            otlp_endpoint="http://test-endpoint:4318/v1/traces")

        # Verify that a TracerProvider was created
        self.assertIsInstance(provider, TracerProvider)

        # Verify that only one processor was added
        self.assertEqual(len(provider._active_span_processor._span_processors),
                         1)

        # Check processor type
        processors = provider._active_span_processor._span_processors
        processor_types = [type(processor) for processor in processors]

        # Should only have BatchSpanProcessor (OTLP/cloud)
        self.assertIn(BatchSpanProcessor, processor_types)
        self.assertNotIn(SimpleSpanProcessor, processor_types)


if __name__ == '__main__':
    unittest.main()
