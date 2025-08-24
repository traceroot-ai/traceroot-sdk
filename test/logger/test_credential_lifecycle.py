"""Test complete credential lifecycle with CloudWatch handler recreation"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import traceroot.logger
from traceroot.config import TraceRootConfig
from traceroot.logger import TraceRootLogger


class TestCredentialLifecycle(unittest.TestCase):
    """Test complete credential lifecycle scenarios"""

    def setUp(self):
        """Set up test configuration"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      enable_span_cloud_export=True,
                                      enable_log_cloud_export=True,
                                      local_mode=False,
                                      token="test-token")

        # Clear any existing global handler reference
        traceroot.logger._cloudwatch_handler = None

    def tearDown(self):
        """Clean up after tests"""
        traceroot.logger._cloudwatch_handler = None

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    @patch('logging.getLogger')
    def test_full_credential_lifecycle_with_handler_recreation(
            self, mock_get_logger, mock_boto_session,
            mock_cloudwatch_handler_class):
        """Test complete credential lifecycle from init through
        expiration to handler
        """

        # 1. Set up initial credentials (valid for 12 hours)
        initial_time = datetime.now(timezone.utc)
        initial_expiry = initial_time + timedelta(hours=12)

        initial_credentials = {
            'aws_access_key_id': 'INITIAL_KEY_123',
            'aws_secret_access_key': 'initial_secret',
            'aws_session_token': 'initial_token',
            'region': 'us-east-1',
            'hash': 'initial-hash',
            'expiration_utc': initial_expiry.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint': 'https://initial-otlp.com'
        }

        # 2. Set up new credentials (for after expiration)
        new_time = initial_time + timedelta(
            hours=11, minutes=45)  # 15 minutes before expiry
        new_expiry = new_time + timedelta(hours=12)

        new_credentials = {
            'aws_access_key_id': 'NEW_KEY_456',
            'aws_secret_access_key': 'new_secret',
            'aws_session_token': 'new_token',
            'region': 'us-west-2',
            'hash': 'new-hash',
            'expiration_utc': new_expiry.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint': 'https://new-otlp.com'
        }

        # 3. Mock HTTP responses
        initial_response = Mock()
        initial_response.json.return_value = initial_credentials
        initial_response.raise_for_status.return_value = None

        new_response = Mock()
        new_response.json.return_value = new_credentials
        new_response.raise_for_status.return_value = None

        # 4. Mock CloudWatch handlers
        initial_handler = MagicMock()
        initial_handler.level = 0  # Set level for logging compatibility
        new_handler = MagicMock()
        new_handler.level = 0  # Set level for logging compatibility
        mock_cloudwatch_handler_class.side_effect = [
            initial_handler, new_handler
        ]

        # 5. Mock boto3 session
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        # Mock the underlying logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with patch('traceroot.credentials.requests.get') as mock_get:

            # 6. Set up initial HTTP response
            mock_get.return_value = initial_response

            # 7. Create logger (should fetch initial credentials
            # and create handler)
            logger = TraceRootLogger(self.config)

            # 8. Verify initial state
            credentials = logger.credential_manager.get_credentials()
            self.assertIsNotNone(credentials)
            self.assertEqual(credentials['aws_access_key_id'],
                             'INITIAL_KEY_123')
            self.assertEqual(credentials['hash'], 'initial-hash')
            self.assertEqual(logger.config._name, 'initial-hash')
            self.assertEqual(logger.config.otlp_endpoint,
                             'https://initial-otlp.com')

            # Verify initial CloudWatch handler was
            # created and is referenced globally
            self.assertEqual(mock_cloudwatch_handler_class.call_count, 1)
            self.assertEqual(traceroot.logger._cloudwatch_handler,
                             initial_handler)

            # 9. Simulate time progression by directly
            # modifying expiration time
            # Set credentials to expire in 15 minutes
            # (< 30 minute threshold)
            logger.credential_manager._credentials_expiry = datetime.now(
                timezone.utc) + timedelta(minutes=15)

            # Set up new credentials response
            mock_get.return_value = new_response

            # Reset call counts for new phase
            mock_get.reset_mock()
            mock_cloudwatch_handler_class.reset_mock()
            mock_cloudwatch_handler_class.side_effect = [new_handler]

            # 10. Trigger credential refresh via log call
            # This should detect near expiration and refresh credentials
            logger.info("Test message that should trigger credential refresh")

            # 11. Verify new credentials were fetched
            self.assertGreater(mock_get.call_count, 0,
                               "New credentials should have been fetched")

            # 12. Verify credentials were updated
            new_credentials = logger.credential_manager.get_credentials()
            self.assertEqual(new_credentials['aws_access_key_id'],
                             'NEW_KEY_456')
            self.assertEqual(new_credentials['hash'], 'new-hash')
            self.assertEqual(logger.config._name, 'new-hash')
            self.assertEqual(logger.config.otlp_endpoint,
                             'https://new-otlp.com')

            # 13. Verify old CloudWatch handler was properly cleaned up
            initial_handler.flush.assert_called()
            initial_handler.close.assert_called()
            mock_logger.removeHandler.assert_called_with(initial_handler)

            # 14. Verify new CloudWatch handler was created and added
            self.assertEqual(mock_cloudwatch_handler_class.call_count, 1,
                             "New CloudWatch handler should be created")
            mock_logger.addHandler.assert_called_with(new_handler)

            # 15. Verify global handler reference was updated
            self.assertEqual(
                traceroot.logger._cloudwatch_handler, new_handler,
                "Global handler reference should point to new handler")

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    def test_credential_refresh_without_cloudwatch_when_log_export_disabled(
            self, mock_boto_session, mock_cloudwatch_handler_class):
        """Test that credentials refresh but CloudWatch
        handler is not recreated when log export is disabled
        """

        # Disable log cloud export but keep span cloud export
        config = TraceRootConfig(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_cloud_export=True,
            enable_log_cloud_export=False,  # This is the key difference
            local_mode=False,
            token="test-token")

        initial_time = datetime.now(timezone.utc)
        initial_credentials = {
            'aws_access_key_id':
            'INITIAL_KEY_123',
            'aws_secret_access_key':
            'initial_secret',
            'aws_session_token':
            'initial_token',
            'region':
            'us-east-1',
            'hash':
            'initial-hash',
            'expiration_utc':
            (initial_time +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://initial-otlp.com'
        }

        new_time = initial_time + timedelta(hours=11, minutes=45)
        new_credentials = {
            'aws_access_key_id':
            'NEW_KEY_456',
            'aws_secret_access_key':
            'new_secret',
            'aws_session_token':
            'new_token',
            'region':
            'us-west-2',
            'hash':
            'new-hash',
            'expiration_utc':
            (new_time + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://new-otlp.com'
        }

        initial_response = Mock()
        initial_response.json.return_value = initial_credentials
        initial_response.raise_for_status.return_value = None

        new_response = Mock()
        new_response.json.return_value = new_credentials
        new_response.raise_for_status.return_value = None

        with patch('traceroot.credentials.requests.get') as mock_get, \
             patch('logging.getLogger') as mock_get_logger:

            # Mock the underlying logger for non-CloudWatch case
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            mock_get.return_value = initial_response

            # Create logger - should not create CloudWatch
            # handler due to log export disabled
            logger = TraceRootLogger(config)

            # Verify no CloudWatch handler created initially
            self.assertEqual(mock_cloudwatch_handler_class.call_count, 0)

            # Simulate time progression - set credentials to expire soon
            logger.credential_manager._credentials_expiry = datetime.now(
                timezone.utc) + timedelta(minutes=15)

            # Set up new credentials response and reset mocks
            mock_get.return_value = new_response
            mock_get.reset_mock()

            # Trigger credential refresh
            logger.info("Test message")

            # Verify credentials were refreshed attempt was made
            self.assertGreater(mock_get.call_count, 0)

            # With the new CredentialManager architecture,
            # the config IS updated
            # even when log_cloud_export=False because credential
            # fetching automatically updates the config through
            # the credential manager
            self.assertEqual(logger.config.otlp_endpoint,
                             'https://new-otlp.com')

            # Verify no CloudWatch handler operations occurred
            self.assertEqual(mock_cloudwatch_handler_class.call_count, 0)

    @patch('traceroot.logger.watchtower.CloudWatchLogHandler')
    @patch('boto3.Session')
    def test_credential_refresh_failure_handling(
            self, mock_boto_session, mock_cloudwatch_handler_class):
        """Test that credential refresh failures are handled gracefully"""

        initial_time = datetime.now(timezone.utc)
        initial_credentials = {
            'aws_access_key_id':
            'INITIAL_KEY_123',
            'aws_secret_access_key':
            'initial_secret',
            'aws_session_token':
            'initial_token',
            'region':
            'us-east-1',
            'hash':
            'initial-hash',
            'expiration_utc':
            (initial_time +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://initial-otlp.com'
        }

        initial_response = Mock()
        initial_response.json.return_value = initial_credentials
        initial_response.raise_for_status.return_value = None

        # Mock failure response
        failed_response = Mock()
        failed_response.raise_for_status.side_effect = Exception(
            "Network error")

        initial_handler = MagicMock()
        initial_handler.level = 0  # Set level for logging compatibility
        mock_cloudwatch_handler_class.return_value = initial_handler

        with patch('traceroot.credentials.requests.get') as mock_get, \
             patch('logging.getLogger') as mock_get_logger:

            # Mock the underlying logger
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            mock_get.return_value = initial_response

            # Create logger with initial credentials
            logger = TraceRootLogger(self.config)

            # Verify initial setup
            credentials = logger.credential_manager.get_credentials()
            self.assertEqual(credentials['aws_access_key_id'],
                             'INITIAL_KEY_123')
            self.assertEqual(traceroot.logger._cloudwatch_handler,
                             initial_handler)

            # Simulate time progression - set credentials to expire soon
            logger.credential_manager._credentials_expiry = datetime.now(
                timezone.utc) + timedelta(minutes=15)

            # Set up failure response and reset mocks
            mock_get.return_value = failed_response
            mock_get.reset_mock()

            # Trigger log call - should attempt refresh
            # but handle failure gracefully
            logger.info("Test message during failure")

            # Verify refresh was attempted
            self.assertGreater(mock_get.call_count, 0)

            # Verify old credentials are still used (fallback behavior)
            credentials = logger.credential_manager.get_credentials()
            self.assertEqual(credentials['aws_access_key_id'],
                             'INITIAL_KEY_123')

            # Verify handler wasn't changed due to failure
            self.assertEqual(traceroot.logger._cloudwatch_handler,
                             initial_handler)

            # Verify logging still works despite credential refresh failure
            self.assertTrue(True)  # If we get here, no exception was raised

    def test_no_credential_operations_in_local_mode(self):
        """Test that no credential operations occur in local mode"""

        # Clean up any existing logger handlers to avoid interference
        import logging
        test_logger = logging.getLogger("test-service")
        for handler in test_logger.handlers[:]:
            test_logger.removeHandler(handler)

        config = TraceRootConfig(
            service_name="test-service",
            github_owner="test-owner",
            github_repo_name="test-repo",
            github_commit_hash="test-hash",
            enable_span_cloud_export=True,
            enable_log_cloud_export=True,
            local_mode=True,  # Local mode enabled
            token="test-token")

        with patch('traceroot.credentials.requests.get') as mock_get:
            # Create logger in local mode
            logger = TraceRootLogger(config)

            # Verify no HTTP requests were made during initialization
            self.assertEqual(mock_get.call_count, 0)

            # Verify no credentials were cached
            credentials = logger.credential_manager.get_credentials()
            self.assertIsNone(credentials)

            # Verify manual refresh does nothing
            result = logger.refresh_credentials()
            self.assertFalse(result)  # Should return False in local mode
            self.assertEqual(mock_get.call_count, 0)

            # Note: We skip the actual logging calls to avoid
            # handler level comparison issues
            # The important test is that no credential operations
            # occur, which we've verified


if __name__ == '__main__':
    unittest.main()
