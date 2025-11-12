"""
Unit tests for TraceIdFilter with parent_span_id and span_name fields
"""
import logging
import unittest
from unittest.mock import MagicMock, patch

from traceroot.config import TraceRootConfig
from traceroot.logger import TraceIdFilter


class TestTraceIdFilterFields(unittest.TestCase):
    """Test the parent_span_id and span_name fields in TraceIdFilter"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      environment="test")
        self.filter = TraceIdFilter(self.config)
        self.record = logging.LogRecord(name="test",
                                        level=logging.INFO,
                                        pathname="test.py",
                                        lineno=1,
                                        msg="test message",
                                        args=(),
                                        exc_info=None)

    def test_nested_span_with_parent(self):
        """Test that parent_span_id is extracted from a nested span"""
        # Mock parent span context
        mock_parent_context = MagicMock()
        mock_parent_context.span_id = 0x1234567890ABCDEF

        # Mock current span with parent
        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xFEDCBA0987654321
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = mock_parent_context
        mock_span.name = "child_operation"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        # Verify filter returns True
        self.assertTrue(result)

        # Verify trace_id and span_id
        self.assertEqual(self.record.trace_id,
                         "1-12345678-901234567890123456789012")
        self.assertEqual(self.record.span_id, "fedcba0987654321")

        # Verify parent_span_id and span_name
        self.assertEqual(self.record.parent_span_id, "1234567890abcdef")
        self.assertEqual(self.record.span_name, "child_operation")

    def test_root_span_no_parent(self):
        """Test that parent_span_id is 'no-parent' for root spans"""
        # Mock root span (no parent)
        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xABCDEF1234567890
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = None  # Root span has no parent
        mock_span.name = "root_operation"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        self.assertEqual(self.record.parent_span_id, "no-parent")
        self.assertEqual(self.record.span_name, "root_operation")

    def test_parent_with_zero_span_id(self):
        """Test that parent_span_id is 'no-parent' when parent span_id is 0"""
        # Mock parent with span_id = 0
        mock_parent_context = MagicMock()
        mock_parent_context.span_id = 0  # Invalid span ID

        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xABCDEF1234567890
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = mock_parent_context
        mock_span.name = "child_with_invalid_parent"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        self.assertEqual(self.record.parent_span_id, "no-parent")
        self.assertEqual(self.record.span_name, "child_with_invalid_parent")

    def test_parent_without_span_id_attribute(self):
        """Test handling when parent context doesn't have span_id attribute"""
        # Mock parent without span_id attribute
        mock_parent_context = MagicMock(spec=[])  # No attributes

        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xABCDEF1234567890
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = mock_parent_context
        mock_span.name = "operation_name"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        self.assertEqual(self.record.parent_span_id, "no-parent")

    def test_no_span_context(self):
        """Test that fields default to safe values when no span context"""
        # Mock span with no valid context
        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0  # Invalid trace ID
        mock_span.get_span_context.return_value = mock_span_context

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        self.assertEqual(self.record.trace_id, "no-trace")
        self.assertEqual(self.record.span_id, "no-span")
        self.assertEqual(self.record.parent_span_id, "no-parent")
        self.assertEqual(self.record.span_name, "unknown")

    def test_span_without_name_attribute(self):
        """Test handling when span doesn't have name attribute"""
        mock_span = MagicMock(spec=['get_span_context', 'parent'])
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xABCDEF1234567890
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = None
        # No 'name' attribute

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        self.assertEqual(self.record.span_name, "unknown")

    def test_deeply_nested_span(self):
        """Test a deeply nested span (grandparent -> parent -> child)"""
        # In practice, we only capture immediate parent
        mock_parent_context = MagicMock()
        mock_parent_context.span_id = 0x9999999999999999

        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0x8888888888888888
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = mock_parent_context
        mock_span.name = "deeply_nested_operation"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        # Should have immediate parent's span_id
        self.assertEqual(self.record.parent_span_id, "9999999999999999")
        self.assertEqual(self.record.span_name, "deeply_nested_operation")

    def test_service_metadata_still_set(self):
        """Test that service metadata fields are still populated correctly"""
        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0x12345678901234567890123456789012
        mock_span_context.span_id = 0xABCDEF1234567890
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = None
        mock_span.name = "test_op"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        # Verify service metadata is still set
        self.assertEqual(self.record.service_name, "test-service")
        self.assertEqual(self.record.github_owner, "test-owner")
        self.assertEqual(self.record.github_repo_name, "test-repo")
        self.assertEqual(self.record.github_commit_hash, "test-hash")
        self.assertEqual(self.record.environment, "test")
        # Verify stack trace is set
        self.assertIsNotNone(self.record.stack_trace)

    def test_hex_format_consistency(self):
        """Test that span IDs are formatted consistently as lowercase hex"""
        mock_parent_context = MagicMock()
        mock_parent_context.span_id = 0xABCDEF0123456789

        mock_span = MagicMock()
        mock_span_context = MagicMock()
        mock_span_context.trace_id = 0xABCDEF01234567890123456789012345
        mock_span_context.span_id = 0x1234567890ABCDEF
        mock_span.get_span_context.return_value = mock_span_context
        mock_span.parent = mock_parent_context
        mock_span.name = "format_test"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            result = self.filter.filter(self.record)

        self.assertTrue(result)
        # Verify lowercase hex format (16 chars for span_id)
        self.assertEqual(self.record.span_id, "1234567890abcdef")
        self.assertEqual(self.record.parent_span_id, "abcdef0123456789")
        # Both should be lowercase
        self.assertTrue(self.record.span_id.islower())
        self.assertTrue(self.record.parent_span_id.islower())


class TestLogFormatterFields(unittest.TestCase):
    """Test that the log formatter includes parent_span_id and span_name
    fields
    """

    def setUp(self):
        """Set up test fixtures"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      environment="test")

    def test_formatter_includes_fields(self):
        """Test that formatter includes parent_span_id and span_name"""
        from traceroot.credentials import CredentialManager
        from traceroot.logger import TraceRootLogger

        with patch.object(CredentialManager,
                          'get_credentials',
                          return_value=None):
            with patch.object(TraceRootLogger, '_setup_otlp_logging_handler'):
                logger = TraceRootLogger(self.config)

        # Get the formatter format string
        format_string = logger.formatter._fmt

        # Verify fields are in the format string
        self.assertIn('%(parent_span_id)s', format_string)
        self.assertIn('%(span_name)s', format_string)

        # Verify they come after message (at the end)
        message_index = format_string.index('%(message)s')
        parent_span_id_index = format_string.index('%(parent_span_id)s')
        span_name_index = format_string.index('%(span_name)s')

        self.assertGreater(parent_span_id_index, message_index,
                           "parent_span_id should come after message")
        self.assertGreater(span_name_index, message_index,
                           "span_name should come after message")

    def test_formatted_log_message_structure(self):
        """Test that a formatted log message has the correct structure"""
        from traceroot.credentials import CredentialManager
        from traceroot.logger import TraceRootLogger

        with patch.object(CredentialManager,
                          'get_credentials',
                          return_value=None):
            with patch.object(TraceRootLogger, '_setup_otlp_logging_handler'):
                logger_instance = TraceRootLogger(self.config)

        # Create a mock log record with all fields populated
        record = logging.LogRecord(name="test",
                                   level=logging.INFO,
                                   pathname="test.py",
                                   lineno=10,
                                   msg="Test log message",
                                   args=(),
                                   exc_info=None)

        # Add trace fields
        record.trace_id = "1-12345678-901234567890123456789012"
        record.span_id = "abcdef1234567890"
        record.parent_span_id = "1234567890abcdef"
        record.span_name = "test_operation"
        record.stack_trace = "test.py:main:10"
        record.service_name = "test-service"
        record.github_commit_hash = "test-hash"
        record.github_owner = "test-owner"
        record.github_repo_name = "test-repo"
        record.environment = "test"

        # Format the log record
        formatted = logger_instance.formatter.format(record)

        # Verify all fields are present in the formatted output
        self.assertIn("test-service", formatted)
        self.assertIn("1-12345678-901234567890123456789012", formatted)
        self.assertIn("abcdef1234567890", formatted)
        self.assertIn("1234567890abcdef", formatted)
        self.assertIn("test_operation", formatted)
        self.assertIn("Test log message", formatted)

        # Verify semicolon separation
        parts = formatted.split(';')
        self.assertGreaterEqual(
            len(parts), 12,
            "Should have at least 12 semicolon-separated fields")

        # Verify parent_span_id and span_name are at the end
        self.assertIn("1234567890abcdef", parts[-2])  # parent_span_id
        self.assertIn("test_operation", parts[-1])  # span_name


class TestSpanEventHandlerFields(unittest.TestCase):
    """Test that SpanEventHandler includes parent_span_id and span_name in
    span events
    """

    def test_span_event_includes_fields(self):
        """Test that log events added to spans include parent_span_id and
        span_name
        """
        from traceroot.logger import SpanEventHandler

        handler = SpanEventHandler()

        # Create mock span
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True

        # Create log record with new fields
        record = logging.LogRecord(name="test",
                                   level=logging.INFO,
                                   pathname="test.py",
                                   lineno=1,
                                   msg="Test message",
                                   args=(),
                                   exc_info=None)
        record.trace_id = "1-12345678-901234567890123456789012"
        record.span_id = "abcdef1234567890"
        record.parent_span_id = "1234567890abcdef"
        record.span_name = "test_operation"
        record.stack_trace = "test.py:main:1"
        record.service_name = "test-service"
        record.environment = "test"

        with patch('traceroot.logger.get_current_span',
                   return_value=mock_span):
            handler.emit(record)

        # Verify add_event was called
        mock_span.add_event.assert_called_once()

        # Get the attributes passed to add_event
        call_args = mock_span.add_event.call_args
        attributes = call_args.kwargs.get('attributes', {})

        # Verify parent_span_id and span_name are in attributes
        self.assertEqual(attributes['log.parent_span_id'], "1234567890abcdef")
        self.assertEqual(attributes['log.span_name'], "test_operation")

        # Verify other fields still work
        self.assertEqual(attributes['log.trace_id'],
                         "1-12345678-901234567890123456789012")
        self.assertEqual(attributes['log.span_id'], "abcdef1234567890")


if __name__ == '__main__':
    unittest.main()
