"""Test the centralized credential manager"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from traceroot.config import TraceRootConfig
from traceroot.credentials import CredentialManager


class TestCredentialManager(unittest.TestCase):
    """Test centralized credential management"""

    def setUp(self):
        """Set up test configuration"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="test-hash",
                                      token="test-token")

    def test_local_mode_returns_none(self):
        """Test that local mode returns None for credentials"""
        config = TraceRootConfig(service_name="test-service",
                                 github_owner="test-owner",
                                 github_repo_name="test-repo",
                                 github_commit_hash="test-hash",
                                 local_mode=True)

        manager = CredentialManager(config)
        credentials = manager.get_credentials()
        self.assertIsNone(credentials)

    @patch('traceroot.credentials.requests.get')
    def test_credential_fetching_and_config_update(self, mock_get):
        """Test that credentials are fetched and config is updated"""
        initial_time = datetime.now(timezone.utc)
        mock_credentials = {
            'aws_access_key_id':
            'TEST_KEY_123',
            'aws_secret_access_key':
            'test_secret',
            'aws_session_token':
            'test_token',
            'region':
            'us-east-1',
            'hash':
            'test-hash',
            'expiration_utc':
            (initial_time +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://test-otlp.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        manager = CredentialManager(self.config)
        credentials = manager.get_credentials()

        # Verify credentials were returned
        self.assertIsNotNone(credentials)
        self.assertEqual(credentials['aws_access_key_id'], 'TEST_KEY_123')

        # Verify config was automatically updated
        self.assertEqual(self.config._name, 'test-hash')
        self.assertEqual(self.config.otlp_endpoint, 'https://test-otlp.com')

    def test_needs_refresh_logic(self):
        """Test credential refresh timing logic"""
        manager = CredentialManager(self.config)

        # Should need refresh when no credentials cached
        self.assertTrue(manager.needs_refresh())

        # Should need refresh when force_refresh=True
        self.assertTrue(manager.needs_refresh(force_refresh=True))

    def test_credentials_near_expiry_refresh(self):
        """Test that credentials refresh when near expiration"""
        manager = CredentialManager(self.config)

        # Set up credentials that expire soon
        manager._credentials_expiry = datetime.now(
            timezone.utc) + timedelta(minutes=15)
        manager._cached_credentials = {'test': 'value'}

        # Should need refresh because < 30 minute threshold
        self.assertTrue(manager.needs_refresh())

    def test_credentials_not_near_expiry_no_refresh(self):
        """Test that credentials don't refresh when not near expiration"""
        manager = CredentialManager(self.config)

        # Set up credentials that expire in the future
        manager._credentials_expiry = datetime.now(
            timezone.utc) + timedelta(hours=2)
        manager._cached_credentials = {'test': 'value'}

        # Should not need refresh because > 30 minute threshold
        self.assertFalse(manager.needs_refresh())


if __name__ == '__main__':
    unittest.main()
