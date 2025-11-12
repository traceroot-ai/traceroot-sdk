"""
Integration tests for logger with real OpenTelemetry spans

These tests verify that the logger correctly extracts parent_span_id and
span_name from actual OpenTelemetry span objects (not mocked).
"""
import io
import logging
import unittest

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (ConsoleSpanExporter,
                                            SimpleSpanProcessor)

from traceroot.config import TraceRootConfig
from traceroot.logger import TraceIdFilter


class TestLoggerWithRealSpans(unittest.TestCase):
    """Integration tests using real OpenTelemetry spans"""

    def setUp(self):
        """Set up a real OpenTelemetry tracer"""
        # Create a real tracer provider
        self.provider = TracerProvider()

        # Use a console exporter for debugging if needed
        # (output won't interfere with test output)
        span_processor = SimpleSpanProcessor(
            ConsoleSpanExporter(out=io.StringIO()))
        self.provider.add_span_processor(span_processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self.provider)

        # Get a tracer
        self.tracer = trace.get_tracer(__name__)

        # Create config and filter
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      environment="test")
        self.filter = TraceIdFilter(self.config)

    def tearDown(self):
        """Clean up tracer provider"""
        if self.provider:
            self.provider.shutdown()

    def test_root_span_integration(self):
        """Test logger with a real root span"""
        with self.tracer.start_as_current_span("root_operation") as span:
            # Create a log record
            record = logging.LogRecord(name="test",
                                       level=logging.INFO,
                                       pathname="test.py",
                                       lineno=1,
                                       msg="Root span log",
                                       args=(),
                                       exc_info=None)

            # Apply filter
            result = self.filter.filter(record)

            # Verify filter succeeded
            self.assertTrue(result)

            # Verify trace_id is set
            self.assertNotEqual(record.trace_id, "no-trace")
            self.assertTrue(record.trace_id.startswith("1-"))

            # Verify span_id is set
            self.assertNotEqual(record.span_id, "no-span")
            self.assertEqual(len(record.span_id), 16)  # 16 hex chars

            # Verify parent_span_id is "no-parent" for root span
            self.assertEqual(record.parent_span_id, "no-parent")

            # Verify span_name is correct
            self.assertEqual(record.span_name, "root_operation")

            # Verify span_id matches the actual span
            actual_span_id = format(span.get_span_context().span_id, "016x")
            self.assertEqual(record.span_id, actual_span_id)

    def test_nested_span_integration(self):
        """Test logger with real nested spans (parent -> child)"""
        with self.tracer.start_as_current_span(
                "parent_operation") as parent_span:
            parent_span_id = format(parent_span.get_span_context().span_id,
                                    "016x")

            with self.tracer.start_as_current_span(
                    "child_operation") as child_span:
                # Create a log record inside child span
                record = logging.LogRecord(name="test",
                                           level=logging.INFO,
                                           pathname="test.py",
                                           lineno=1,
                                           msg="Child span log",
                                           args=(),
                                           exc_info=None)

                # Apply filter
                result = self.filter.filter(record)
                self.assertTrue(result)

                # Verify trace_id is set
                self.assertNotEqual(record.trace_id, "no-trace")

                # Verify child span_id
                child_span_id = format(child_span.get_span_context().span_id,
                                       "016x")
                self.assertEqual(record.span_id, child_span_id)

                # Verify parent_span_id matches parent's span_id
                self.assertEqual(record.parent_span_id, parent_span_id)

                # Verify span_name
                self.assertEqual(record.span_name, "child_operation")

                # Verify parent and child span IDs are different
                self.assertNotEqual(record.span_id, record.parent_span_id)

    def test_deeply_nested_spans_integration(self):
        """Test logger with deeply nested spans (3 levels deep)"""
        with self.tracer.start_as_current_span("grandparent"):
            with self.tracer.start_as_current_span("parent") as parent:
                parent_span_id = format(parent.get_span_context().span_id,
                                        "016x")

                with self.tracer.start_as_current_span("child"):
                    record = logging.LogRecord(name="test",
                                               level=logging.INFO,
                                               pathname="test.py",
                                               lineno=1,
                                               msg="Deep child log",
                                               args=(),
                                               exc_info=None)

                    result = self.filter.filter(record)
                    self.assertTrue(result)

                    # Should have immediate parent's span_id, not grandparent
                    self.assertEqual(record.parent_span_id, parent_span_id)
                    self.assertEqual(record.span_name, "child")

    def test_multiple_sibling_spans_integration(self):
        """Test logger with multiple sibling spans"""
        with self.tracer.start_as_current_span("parent") as parent:
            parent_span_id = format(parent.get_span_context().span_id, "016x")

            # First child
            with self.tracer.start_as_current_span("child1"):
                record1 = logging.LogRecord(name="test",
                                            level=logging.INFO,
                                            pathname="test.py",
                                            lineno=1,
                                            msg="Child 1 log",
                                            args=(),
                                            exc_info=None)
                self.filter.filter(record1)

                self.assertEqual(record1.parent_span_id, parent_span_id)
                self.assertEqual(record1.span_name, "child1")

            # Second child (sibling of first)
            with self.tracer.start_as_current_span("child2"):
                record2 = logging.LogRecord(name="test",
                                            level=logging.INFO,
                                            pathname="test.py",
                                            lineno=1,
                                            msg="Child 2 log",
                                            args=(),
                                            exc_info=None)
                self.filter.filter(record2)

                # Same parent
                self.assertEqual(record2.parent_span_id, parent_span_id)
                self.assertEqual(record2.span_name, "child2")

                # Different span IDs
                self.assertNotEqual(record1.span_id, record2.span_id)

    def test_trace_id_consistency_across_nested_spans(self):
        """Test that trace_id remains consistent across nested spans"""
        with self.tracer.start_as_current_span("parent"):
            record_parent = logging.LogRecord(name="test",
                                              level=logging.INFO,
                                              pathname="test.py",
                                              lineno=1,
                                              msg="Parent log",
                                              args=(),
                                              exc_info=None)
            self.filter.filter(record_parent)

            with self.tracer.start_as_current_span("child"):
                record_child = logging.LogRecord(name="test",
                                                 level=logging.INFO,
                                                 pathname="test.py",
                                                 lineno=1,
                                                 msg="Child log",
                                                 args=(),
                                                 exc_info=None)
                self.filter.filter(record_child)

                # Trace IDs should be identical
                self.assertEqual(record_parent.trace_id, record_child.trace_id)

                # Span IDs should be different
                self.assertNotEqual(record_parent.span_id,
                                    record_child.span_id)

    def test_service_metadata_with_real_spans(self):
        """Test that service metadata is correctly set with real spans"""
        with self.tracer.start_as_current_span("test_op"):
            record = logging.LogRecord(name="test",
                                       level=logging.INFO,
                                       pathname="test.py",
                                       lineno=1,
                                       msg="Test log",
                                       args=(),
                                       exc_info=None)
            self.filter.filter(record)

            # Verify service metadata
            self.assertEqual(record.service_name, "test-service")
            self.assertEqual(record.github_owner, "test-owner")
            self.assertEqual(record.github_repo_name, "test-repo")
            self.assertEqual(record.github_commit_hash, "test-hash")
            self.assertEqual(record.environment, "test")

            # Verify stack trace is set
            self.assertIsNotNone(record.stack_trace)
            self.assertNotEqual(record.stack_trace, "unknown")


class TestFormatterWithRealSpans(unittest.TestCase):
    """Integration tests for log formatter with real spans"""

    def setUp(self):
        """Set up tracer and formatter"""
        self.provider = TracerProvider()
        span_processor = SimpleSpanProcessor(
            ConsoleSpanExporter(out=io.StringIO()))
        self.provider.add_span_processor(span_processor)
        trace.set_tracer_provider(self.provider)
        self.tracer = trace.get_tracer(__name__)

        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      environment="test")
        self.filter = TraceIdFilter(self.config)

        # Create formatter matching the one in TraceRootLogger
        self.formatter = logging.Formatter(
            '%(asctime)s;%(levelname)s;%(service_name)s;'
            '%(github_commit_hash)s;%(github_owner)s;%(github_repo_name)s;'
            '%(environment)s;'
            '%(trace_id)s;%(span_id)s;%(stack_trace)s;%(message)s;'
            '%(parent_span_id)s;%(span_name)s')

    def tearDown(self):
        """Clean up"""
        if self.provider:
            self.provider.shutdown()

    def test_formatted_output_structure_with_real_spans(self):
        """Test formatted log output structure with real spans"""
        with self.tracer.start_as_current_span("parent"):
            with self.tracer.start_as_current_span("child"):
                record = logging.LogRecord(name="test",
                                           level=logging.INFO,
                                           pathname="test.py",
                                           lineno=1,
                                           msg="Test message",
                                           args=(),
                                           exc_info=None)

                # Apply filter to populate trace fields
                self.filter.filter(record)

                # Format the record
                formatted = self.formatter.format(record)

                # Split by semicolon
                parts = formatted.split(';')

                # Should have 13 parts (12 semicolons = 13 parts)
                # 0: asctime, 1: levelname, 2: service_name
                # 3: github_commit_hash, 4: github_owner
                # 5: github_repo_name, 6: environment
                # 7: trace_id, 8: span_id, 9: stack_trace
                # 10: message, 11: parent_span_id, 12: span_name
                self.assertEqual(len(parts), 13)

                self.assertEqual(parts[1], "INFO")
                self.assertEqual(parts[2], "test-service")
                self.assertEqual(parts[6], "test")
                self.assertTrue(parts[7].startswith("1-"))  # trace_id

                # Verify parent_span_id is NOT "no-parent" (child span)
                parent_span_id_part = parts[-2]
                self.assertNotEqual(parent_span_id_part, "no-parent")
                self.assertEqual(len(parent_span_id_part), 16)  # hex span_id

                # Verify span_name is correct
                span_name_part = parts[-1]
                self.assertEqual(span_name_part, "child")

    def test_formatted_output_with_root_span(self):
        """Test formatted output with root span (no parent)"""
        with self.tracer.start_as_current_span("root"):
            record = logging.LogRecord(name="test",
                                       level=logging.INFO,
                                       pathname="test.py",
                                       lineno=1,
                                       msg="Root message",
                                       args=(),
                                       exc_info=None)

            self.filter.filter(record)
            formatted = self.formatter.format(record)
            parts = formatted.split(';')

            # Verify parent_span_id is "no-parent"
            self.assertEqual(parts[-2], "no-parent")

            # Verify span_name
            self.assertEqual(parts[-1], "root")

    def test_backwards_compatibility_parsing(self):
        """Test that new fields at end allow backwards compatible parsing"""
        with self.tracer.start_as_current_span("test"):
            record = logging.LogRecord(name="test",
                                       level=logging.INFO,
                                       pathname="test.py",
                                       lineno=1,
                                       msg="Test message",
                                       args=(),
                                       exc_info=None)

            self.filter.filter(record)
            formatted = self.formatter.format(record)
            parts = formatted.split(';')

            # Old parser would read first 11 fields
            # New parser can read from the end:
            # message = parts[-3]
            # parent_span_id = parts[-2]
            # span_name = parts[-1]

            message = parts[-3]
            parent_span_id = parts[-2]
            span_name = parts[-1]

            self.assertEqual(message, "Test message")
            self.assertEqual(span_name, "test")
            # parent_span_id should be either a hex string or "no-parent"
            self.assertTrue(parent_span_id == "no-parent"
                            or len(parent_span_id) == 16)


class TestLoggerWithoutSpan(unittest.TestCase):
    """Test logger behavior when no span is active"""

    def setUp(self):
        """Set up config and filter"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      environment="test")
        self.filter = TraceIdFilter(self.config)

    def test_no_active_span(self):
        """Test logger when no span is active"""
        # Don't create any span context
        record = logging.LogRecord(name="test",
                                   level=logging.INFO,
                                   pathname="test.py",
                                   lineno=1,
                                   msg="No span log",
                                   args=(),
                                   exc_info=None)

        result = self.filter.filter(record)
        self.assertTrue(result)

        # Should have safe defaults
        self.assertEqual(record.trace_id, "no-trace")
        self.assertEqual(record.span_id, "no-span")
        self.assertEqual(record.parent_span_id, "no-parent")
        self.assertEqual(record.span_name, "unknown")


if __name__ == '__main__':
    unittest.main()
