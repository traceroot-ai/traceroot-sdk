import unittest
from unittest.mock import MagicMock, patch

from traceroot.config import TraceRootConfig
from traceroot.logger import TraceRootLogger


class TestLogger(unittest.TestCase):

    def setUp(self):
        """Reset global state before each test"""
        import traceroot.logger as logger_module
        import traceroot.tracer as tracer_module

        # Clean up tracer state first
        if tracer_module._tracer_provider:
            tracer_module._tracer_provider.shutdown()
        tracer_module._tracer_provider = None
        tracer_module._config = None

        # Clean up logger state
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

        # Clean up tracer state
        if tracer_module._tracer_provider:
            tracer_module._tracer_provider.shutdown()
        tracer_module._tracer_provider = None
        tracer_module._config = None

        # Clean up logger state
        if logger_module._global_logger:
            # Remove all handlers from existing logger
            for handler in logger_module._global_logger.logger.handlers[:]:
                logger_module._global_logger.logger.removeHandler(handler)
                if hasattr(handler, 'close'):
                    handler.close()
        logger_module._global_logger = None
        logger_module._cloudwatch_handler = None

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    def test_both_span_and_log_cloud_export_enabled(self, mock_boto_session,
                                                    mock_cloudwatch_handler):
        """Test that CloudWatch handler is created when
        both span and log cloud export are enabled
        """
        # Mock AWS session
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        # Mock CloudWatch handler
        mock_handler_instance = MagicMock()
        mock_cloudwatch_handler.return_value = mock_handler_instance

        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 enable_span_cloud_export=True,
                                 enable_log_cloud_export=True,
                                 local_mode=False)

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials',
                          return_value=None):
            logger = TraceRootLogger(config)

        # Verify CloudWatch handler was created and added
        mock_cloudwatch_handler.assert_called_once()
        # Verify the handler was added to the logger
        self.assertIn(mock_handler_instance, logger.logger.handlers)

    def test_both_span_and_log_cloud_export_disabled(self):
        """Test that no CloudWatch handler is created when
        both span and log cloud export are disabled
        """
        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 enable_span_cloud_export=False,
                                 enable_log_cloud_export=False,
                                 local_mode=False)

        with patch.object(TraceRootLogger,
                          '_setup_otlp_logging_handler') as mock_otlp:
            logger = TraceRootLogger(config)

        # Should setup OTLP handler instead of CloudWatch
        mock_otlp.assert_called_once()

        # Should not have any CloudWatch handlers
        cloudwatch_handlers = [
            h for h in logger.logger.handlers
            if 'CloudWatchLogHandler' in str(type(h))
        ]
        self.assertEqual(len(cloudwatch_handlers), 0)

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    def test_span_enabled_log_disabled(self, mock_boto_session,
                                       mock_cloudwatch_handler):
        """Test that credentials are fetched but no CloudWatch
        handler is created when span is enabled but log is disabled
        """
        # Mock AWS session
        mock_session_instance = MagicMock()
        mock_boto_session.return_value = mock_session_instance

        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 enable_span_cloud_export=True,
                                 enable_log_cloud_export=False,
                                 local_mode=False)

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials',
                          return_value=None) as mock_fetch:
            logger = TraceRootLogger(config)

        # Credentials should be fetched (needed for tracer endpoint)
        mock_fetch.assert_called_once()

        # CloudWatch handler should NOT be created (log export disabled)
        mock_cloudwatch_handler.assert_not_called()

        # Should not have any CloudWatch handlers
        cloudwatch_handlers = [
            h for h in logger.logger.handlers
            if 'CloudWatchLogHandler' in str(type(h))
        ]
        self.assertEqual(len(cloudwatch_handlers), 0)

    def test_span_disabled_log_enabled(self):
        """Test that when span cloud export is disabled, no
        cloud operations occur regardless of log setting
        """
        config = TraceRootConfig(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_cloud_export=False,
            enable_log_cloud_export=True,  # This should be ignored
            local_mode=False)

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials') as mock_fetch:
            with patch.object(TraceRootLogger,
                              '_setup_otlp_logging_handler') as mock_otlp:
                logger = TraceRootLogger(config)

        # No credentials should be fetched when span cloud export is disabled
        mock_fetch.assert_not_called()

        # Should setup OTLP handler instead
        mock_otlp.assert_called_once()

        # Should not have any CloudWatch handlers
        cloudwatch_handlers = [
            h for h in logger.logger.handlers
            if 'CloudWatchLogHandler' in str(type(h))
        ]
        self.assertEqual(len(cloudwatch_handlers), 0)

    def test_local_mode_overrides_cloud_settings(self):
        """Test that local_mode=True overrides cloud export settings"""
        config = TraceRootConfig(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_cloud_export=True,
            enable_log_cloud_export=True,
            local_mode=True  # This should override cloud settings
        )

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials') as mock_fetch:
            with patch.object(TraceRootLogger,
                              '_setup_otlp_logging_handler') as mock_otlp:
                TraceRootLogger(config)

        # No credentials should be fetched in local mode
        mock_fetch.assert_not_called()

        # Should setup OTLP handler in local mode
        mock_otlp.assert_called_once()

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    def test_credential_refresh_logic(self, mock_boto_session,
                                      mock_cloudwatch_handler):
        """Test credential refresh behavior based on export settings"""
        # Mock successful credentials
        mock_credentials = {
            'aws_access_key_id': 'test-key',
            'aws_secret_access_key': 'test-secret',
            'aws_session_token': 'test-token',
            'region': 'us-east-1',
            'hash': 'test-hash',
            'otlp_endpoint': 'http://test-endpoint'
        }

        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 enable_span_cloud_export=True,
                                 enable_log_cloud_export=True,
                                 local_mode=False)

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials',
                          return_value=mock_credentials) as mock_fetch:
            logger = TraceRootLogger(config)
            initial_call_count = mock_fetch.call_count

            # Test that credential refresh works when span
            # cloud export is enabled
            result = logger.refresh_credentials()
            self.assertTrue(result)
            # Should have made at least one additional call for refresh
            self.assertGreater(mock_fetch.call_count, initial_call_count)

            # Test that credential refresh is disabled when
            # span cloud export is disabled
            logger.config.enable_span_cloud_export = False
            result = logger.refresh_credentials()
            self.assertFalse(result)

    def test_check_and_refresh_credentials_logic(self):
        """Test _check_and_refresh_credentials behavior
        based on export settings
        """
        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 enable_span_cloud_export=True,
                                 enable_log_cloud_export=True,
                                 local_mode=False)

        with patch.object(TraceRootLogger,
                          '_fetch_aws_credentials',
                          return_value=None) as mock_fetch:
            with patch.object(TraceRootLogger, '_setup_cloudwatch_handler'):
                logger = TraceRootLogger(config)
                mock_fetch.reset_mock()

                # Should call fetch when span cloud export is enabled
                logger._check_and_refresh_credentials()
                mock_fetch.assert_called_once()

                # Should not call fetch when span cloud export is disabled
                logger.config.enable_span_cloud_export = False
                mock_fetch.reset_mock()
                logger._check_and_refresh_credentials()
                mock_fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
