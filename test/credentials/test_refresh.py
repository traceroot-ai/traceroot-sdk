"""Unit tests for credential refresh functionality in TraceRootLogger"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests

from traceroot.config import TraceRootConfig
from traceroot.logger import TraceRootLogger


class TestCredentialRefresh(unittest.TestCase):
    """Test credential refresh functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = TraceRootConfig(service_name="test-service",
                                      github_owner="test-owner",
                                      github_repo_name="test-repo",
                                      github_commit_hash="abc123",
                                      token="test-token",
                                      aws_region="us-east-1",
                                      local_mode=True,
                                      enable_log_console_export=False)

        # Create logger in local mode to avoid CloudWatch
        # complications during setup
        self.logger = TraceRootLogger(self.config)

        # Reset to non-local mode for testing
        self.logger.config.local_mode = False

    def test_fetch_aws_credentials_caching(self):
        """Test that credentials are cached and reused when not expired"""
        # Mock credentials response with future expiration (2 hours from now)
        future_expiration = (datetime.now(timezone.utc) +
                             timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_credentials = {
            'aws_access_key_id': 'AKIATEST123',
            'aws_secret_access_key': 'secret123',
            'aws_session_token': 'token123',
            'region': 'us-east-1',
            'hash': 'test-hash',
            'expiration_utc': future_expiration,
            'otlp_endpoint': 'https://otlp.test.com'
        }

        # Mock requests.get to return our test credentials
        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response) as mock_get:
            # First call should make an HTTP request
            result1 = self.logger._fetch_aws_credentials()
            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(result1['aws_access_key_id'], 'AKIATEST123')

            # Second call should use cached credentials
            # (no additional HTTP request)
            result2 = self.logger._fetch_aws_credentials()
            self.assertEqual(mock_get.call_count, 1)  # No additional call
            self.assertEqual(result2['aws_access_key_id'], 'AKIATEST123')

    def test_fetch_aws_credentials_refresh_on_expiry(self):
        """Test that credentials are refreshed when near expiration"""
        # Set up initial expired credentials
        expired_time = datetime.now(timezone.utc) + timedelta(
            minutes=20)  # Expires in 20 minutes
        self.logger._cached_credentials = {
            'aws_access_key_id': 'EXPIRED123',
            'aws_secret_access_key': 'expired_secret',
            'aws_session_token': 'expired_token',
            'region': 'us-east-1',
            'hash': 'expired-hash',
            'expiration_utc': expired_time.isoformat() + 'Z',
            'otlp_endpoint': 'https://otlp.test.com'
        }
        self.logger._credentials_expiry = expired_time

        # Mock new credentials response
        new_credentials = {
            'aws_access_key_id':
            'NEWKEY123',
            'aws_secret_access_key':
            'new_secret',
            'aws_session_token':
            'new_token',
            'region':
            'us-east-1',
            'hash':
            'new-hash',
            'expiration_utc':
            (datetime.now(timezone.utc) +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = new_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response):
            # Should refresh credentials because they expire in 20 minutes
            # (< 30 minute threshold)
            result = self.logger._fetch_aws_credentials()
            self.assertEqual(result['aws_access_key_id'], 'NEWKEY123')

    def test_fetch_aws_credentials_no_refresh_when_not_expiring(self):
        """Test that credentials are not refreshed when they
        have plenty of time left
        """
        # Set up credentials that expire in 2 hours
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        self.logger._cached_credentials = {
            'aws_access_key_id': 'VALIDKEY123',
            'aws_secret_access_key': 'valid_secret',
            'aws_session_token': 'valid_token',
            'region': 'us-east-1',
            'hash': 'valid-hash',
            'expiration_utc': future_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint': 'https://otlp.test.com'
        }
        self.logger._credentials_expiry = future_time

        with patch('traceroot.logger.requests.get') as mock_get:
            # Should use cached credentials without making HTTP request
            result = self.logger._fetch_aws_credentials()
            mock_get.assert_not_called()
            self.assertEqual(result['aws_access_key_id'], 'VALIDKEY123')

    def test_fetch_aws_credentials_force_refresh(self):
        """Test that force_refresh parameter bypasses cache"""
        # Set up cached credentials
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        self.logger._cached_credentials = {
            'aws_access_key_id': 'CACHEDKEY123',
            'aws_secret_access_key': 'cached_secret',
            'aws_session_token': 'cached_token',
            'region': 'us-east-1',
            'hash': 'cached-hash',
            'expiration_utc': future_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint': 'https://otlp.test.com'
        }
        self.logger._credentials_expiry = future_time

        # Mock new credentials response
        new_credentials = {
            'aws_access_key_id':
            'FORCEKEY123',
            'aws_secret_access_key':
            'force_secret',
            'aws_session_token':
            'force_token',
            'region':
            'us-east-1',
            'hash':
            'force-hash',
            'expiration_utc':
            (datetime.now(timezone.utc) +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = new_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response) as mock_get:
            # Force refresh should bypass cache and make HTTP request
            result = self.logger._fetch_aws_credentials(force_refresh=True)
            mock_get.assert_called_once()
            self.assertEqual(result['aws_access_key_id'], 'FORCEKEY123')

    def test_fetch_aws_credentials_http_error(self):
        """Test handling of HTTP errors during credential fetch"""
        with patch('traceroot.logger.requests.get') as mock_get:
            # Mock HTTP error
            mock_get.side_effect = requests.RequestException("Network error")

            result = self.logger._fetch_aws_credentials()
            self.assertIsNone(result)

    def test_fetch_aws_credentials_returns_cached_on_error(self):
        """Test that cached credentials are returned when refresh fails"""
        # Set up cached credentials
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        cached_creds = {
            'aws_access_key_id': 'CACHEDKEY123',
            'aws_secret_access_key': 'cached_secret',
            'aws_session_token': 'cached_token',
            'region': 'us-east-1',
            'hash': 'cached-hash',
            'expiration_utc': future_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint': 'https://otlp.test.com'
        }
        self.logger._cached_credentials = cached_creds
        self.logger._credentials_expiry = future_time

        with patch('traceroot.logger.requests.get') as mock_get:
            # Mock HTTP error
            mock_get.side_effect = requests.RequestException("Network error")

            # Should return cached credentials despite error
            result = self.logger._fetch_aws_credentials(force_refresh=True)
            self.assertEqual(result, cached_creds)

    def test_refresh_credentials_success(self):
        """Test successful manual credential refresh"""
        mock_credentials = {
            'aws_access_key_id':
            'REFRESHKEY123',
            'aws_secret_access_key':
            'refresh_secret',
            'aws_session_token':
            'refresh_token',
            'region':
            'us-east-1',
            'hash':
            'refresh-hash',
            'expiration_utc':
            (datetime.now(timezone.utc) +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response), \
             patch.object(self.logger,
                          '_setup_cloudwatch_handler') as mock_setup:

            result = self.logger.refresh_credentials()
            self.assertTrue(result)
            # Should recreate CloudWatch handler in non-local mode
            mock_setup.assert_called_once()

    def test_refresh_credentials_failure(self):
        """Test failed manual credential refresh"""
        with patch('traceroot.logger.requests.get') as mock_get:
            # Mock HTTP error
            mock_get.side_effect = requests.RequestException("Network error")

            result = self.logger.refresh_credentials()
            self.assertFalse(result)

    def test_refresh_credentials_local_mode_skip(self):
        """Test that refresh_credentials skips CloudWatch
        handler setup in local mode
        """
        self.logger.config.local_mode = True

        mock_credentials = {
            'aws_access_key_id':
            'LOCALKEY123',
            'aws_secret_access_key':
            'local_secret',
            'aws_session_token':
            'local_token',
            'region':
            'us-east-1',
            'hash':
            'local-hash',
            'expiration_utc':
            (datetime.now(timezone.utc) +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response), \
             patch.object(self.logger,
                          '_setup_cloudwatch_handler') as mock_setup:

            result = self.logger.refresh_credentials()
            self.assertTrue(result)
            # Should NOT recreate CloudWatch handler in local mode
            mock_setup.assert_not_called()

    def test_check_and_refresh_credentials_local_mode_skip(self):
        """Test that _check_and_refresh_credentials skips in local mode"""
        self.logger.config.local_mode = True

        with patch.object(self.logger, '_fetch_aws_credentials') as mock_fetch:
            self.logger._check_and_refresh_credentials()
            # Should not fetch credentials in local mode
            mock_fetch.assert_not_called()

    def test_check_and_refresh_credentials_non_local_mode(self):
        """Test that _check_and_refresh_credentials works
        in non-local mode
        """
        self.logger.config.local_mode = False

        mock_credentials = {
            'aws_access_key_id':
            'CHECKKEY123',
            'aws_secret_access_key':
            'check_secret',
            'aws_session_token':
            'check_token',
            'region':
            'us-east-1',
            'hash':
            'check-hash',
            'expiration_utc':
            (datetime.now(timezone.utc) +
             timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'otlp_endpoint':
            'https://otlp.test.com'
        }

        with patch.object(self.logger,
                          '_fetch_aws_credentials',
                          return_value=mock_credentials) as mock_fetch:
            self.logger._check_and_refresh_credentials()
            # Should fetch credentials in non-local mode
            mock_fetch.assert_called_once()

    def test_logging_methods_call_credential_check(self):
        """Test that logging methods call credential check"""
        with patch.object(self.logger,
                          '_check_and_refresh_credentials') as mock_check, \
             patch.object(self.logger, '_increment_span_log_count'):

            # Test each logging method
            self.logger.debug("test debug")
            mock_check.assert_called()

            mock_check.reset_mock()
            self.logger.info("test info")
            mock_check.assert_called()

            mock_check.reset_mock()
            self.logger.warning("test warning")
            mock_check.assert_called()

            mock_check.reset_mock()
            self.logger.error("test error")
            mock_check.assert_called()

            mock_check.reset_mock()
            self.logger.critical("test critical")
            mock_check.assert_called()

    def test_expiration_parsing_with_z_suffix(self):
        """Test parsing expiration time with Z suffix"""
        future_expiration = (datetime.now(timezone.utc) +
                             timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_credentials = {
            'aws_access_key_id': 'PARSEKEY123',
            'aws_secret_access_key': 'parse_secret',
            'aws_session_token': 'parse_token',
            'region': 'us-east-1',
            'hash': 'parse-hash',
            'expiration_utc': future_expiration,
            'otlp_endpoint': 'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response):
            result = self.logger._fetch_aws_credentials()
            # Should successfully parse the expiration time and cache it
            self.assertIsNotNone(self.logger._credentials_expiry)
            self.assertEqual(result['expiration_utc'], future_expiration)

    def test_expiration_parsing_fallback(self):
        """Test fallback expiration when no expiration_utc provided"""
        mock_credentials = {
            'aws_access_key_id': 'FALLBACKKEY123',
            'aws_secret_access_key': 'fallback_secret',
            'aws_session_token': 'fallback_token',
            'region': 'us-east-1',
            'hash': 'fallback-hash',
            # No expiration_utc provided
            'otlp_endpoint': 'https://otlp.test.com'
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_credentials
        mock_response.raise_for_status.return_value = None

        with patch('traceroot.logger.requests.get',
                   return_value=mock_response):
            self.logger._fetch_aws_credentials()
            # Should set fallback expiration (12 hours from now)
            self.assertIsNotNone(self.logger._credentials_expiry)
            expected_expiry = datetime.now(timezone.utc) + timedelta(hours=12)
            # Allow 1 minute tolerance for test execution time
            self.assertLess(
                abs((self.logger._credentials_expiry -
                     expected_expiry).total_seconds()), 60)


if __name__ == '__main__':
    unittest.main()
