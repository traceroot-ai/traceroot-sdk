"""Unit tests for environment variable configuration"""

import os
import unittest

from traceroot import tracer


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variable configuration functionality"""

    def setUp(self):
        """Set up test environment"""
        # Clean up any existing env vars before each test
        self._cleanup_env_vars()
        # Shutdown any existing tracer
        tracer.shutdown()

    def tearDown(self):
        """Clean up after each test"""
        self._cleanup_env_vars()
        tracer.shutdown()

    def _cleanup_env_vars(self):
        """Remove test environment variables"""
        env_vars = [
            'TRACEROOT_TOKEN', 'TRACEROOT_SERVICE_NAME',
            'TRACEROOT_ENVIRONMENT', 'TRACEROOT_LOCAL_MODE',
            'TRACEROOT_ENABLE_SPAN_CONSOLE_EXPORT', 'TRACEROOT_AWS_REGION',
            'TRACEROOT_ENABLE_LOG_CONSOLE_EXPORT'
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_env_var_loading(self):
        """Test the _load_env_config function directly"""
        # Set some test environment variables
        os.environ['TRACEROOT_TOKEN'] = 'test-token'
        os.environ['TRACEROOT_AWS_REGION'] = 'us-east-1'
        os.environ['TRACEROOT_LOCAL_MODE'] = 'true'
        os.environ['TRACEROOT_ENABLE_SPAN_CONSOLE_EXPORT'] = 'false'

        env_config = tracer._load_env_config()

        self.assertEqual(env_config['token'], 'test-token')
        self.assertEqual(env_config['aws_region'], 'us-east-1')
        self.assertTrue(
            env_config['local_mode'])  # Should be converted to boolean
        self.assertFalse(env_config['enable_span_console_export']
                         )  # Should be converted to boolean

    def test_boolean_env_var_parsing(self):
        """Test that boolean environment variables are parsed correctly"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('YES', True),
            ('on', True),
            ('ON', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('off', False),
            ('', False),
        ]

        for env_value, expected_bool in test_cases:
            with self.subTest(env_value=env_value, expected=expected_bool):
                os.environ['TRACEROOT_LOCAL_MODE'] = env_value
                env_config = tracer._load_env_config()
                self.assertEqual(env_config['local_mode'], expected_bool)
                del os.environ['TRACEROOT_LOCAL_MODE']

    def test_env_var_override_priority(self):
        """Test that environment variables override other config sources"""
        # Set some environment variables
        os.environ['TRACEROOT_TOKEN'] = 'env-token-123'
        os.environ['TRACEROOT_SERVICE_NAME'] = 'env-service'
        os.environ['TRACEROOT_ENVIRONMENT'] = 'env-environment'
        os.environ['TRACEROOT_LOCAL_MODE'] = 'true'
        os.environ['TRACEROOT_ENABLE_SPAN_CONSOLE_EXPORT'] = 'false'

        # Initialize with kwargs that should be overridden by env vars
        tracer.init(
            service_name='kwarg-service',  # Should be overridden by env
            github_owner='test-owner',
            github_repo_name='test-repo',
            github_commit_hash='abc123',
            token='kwarg-token',  # Should be overridden by env
            environment='kwarg-environment',  # Should be overridden by env
            local_mode=False,  # Should be overridden by env
            enable_span_console_export=True  # Should be overridden by env
        )

        # Get the config to verify env vars took precedence
        config = tracer.get_config()

        # Verify env vars overrode kwargs
        self.assertEqual(config.token, 'env-token-123')
        self.assertEqual(config.service_name, 'env-service')
        self.assertEqual(config.environment, 'env-environment')
        self.assertTrue(config.local_mode)
        self.assertFalse(config.enable_span_console_export)

        # Verify non-env values from kwargs still work
        self.assertEqual(config.github_owner, 'test-owner')
        self.assertEqual(config.github_repo_name, 'test-repo')
        self.assertEqual(config.github_commit_hash, 'abc123')

    def test_partial_env_var_override(self):
        """Test that only set environment variables override config"""
        # Set only some environment variables
        os.environ['TRACEROOT_TOKEN'] = 'env-token'
        os.environ['TRACEROOT_LOCAL_MODE'] = 'true'

        tracer.init(service_name='kwarg-service',
                    github_owner='test-owner',
                    github_repo_name='test-repo',
                    github_commit_hash='abc123',
                    token='kwarg-token',
                    environment='kwarg-environment',
                    local_mode=False)

        config = tracer.get_config()

        # Verify env vars overrode specific values
        self.assertEqual(config.token, 'env-token')
        self.assertTrue(config.local_mode)

        # Verify non-env values from kwargs remain
        self.assertEqual(config.service_name, 'kwarg-service')
        self.assertEqual(config.environment, 'kwarg-environment')
