"""Tests for traceroot initialization behavior"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import traceroot
from traceroot.config import TraceRootConfig
from traceroot.tracer import _tracer_provider, init, shutdown
import traceroot.tracer


class TestTracerInitialization(unittest.TestCase):
    """Test traceroot initialization with YAML config and init() overrides"""
    
    def setUp(self):
        """Reset global state before each test"""
        # Reset global state
        traceroot.tracer._tracer_provider = None
        traceroot.tracer._config = None
        shutdown()
    
    def tearDown(self):
        """Clean up after each test"""
        shutdown()
    
    def test_yaml_config_loading_on_import(self):
        """Test that importing traceroot loads configuration from YAML file"""
        # Create a temporary YAML config file
        test_config = {
            'service_name': 'test-service-from-yaml',
            'environment': 'test-env',
            'github_owner': 'yaml-owner',
            'github_repo_name': 'yaml-repo',
            'github_commit_hash': 'abc123yaml'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / '.traceroot-config.yaml'
            
            # Write test config to YAML file
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Mock Path.cwd() to return our temp directory
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize traceroot (this should load the YAML config)
                tracer_provider = init()
                
                # Verify that configuration was loaded from YAML
                self.assertIsNotNone(traceroot.tracer._config)
                self.assertEqual(traceroot.tracer._config.service_name, 'test-service-from-yaml')
                self.assertEqual(traceroot.tracer._config.environment, 'test-env')
                self.assertEqual(traceroot.tracer._config.github_owner, 'yaml-owner')
                self.assertEqual(traceroot.tracer._config.github_repo_name, 'yaml-repo')
                self.assertEqual(traceroot.tracer._config.github_commit_hash, 'abc123yaml')
    
    def test_init_overrides_yaml_config(self):
        """Test that traceroot.init() parameters override YAML configuration"""
        # Create a temporary YAML config file
        yaml_config = {
            'service_name': 'yaml-service',
            'environment': 'yaml-env',
            'github_owner': 'yaml-owner',
            'github_repo_name': 'yaml-repo',
            'github_commit_hash': 'yamlcommit123',
            'token': 'yaml-token-123',
            'enable_log_cloud_export': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / '.traceroot-config.yaml'
            
            # Write YAML config
            with open(config_path, 'w') as f:
                yaml.dump(yaml_config, f)
            
            # Mock Path.cwd() to return our temp directory
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize with override parameters
                tracer_provider = init(
                    service_name='override-service',
                    environment='override-env',
                    github_commit_hash='overridecommit456',
                    token='override-token-456',
                    enable_log_cloud_export=False
                )
                
                # Verify that init() parameters override YAML values
                self.assertIsNotNone(traceroot.tracer._config)
                self.assertEqual(traceroot.tracer._config.service_name, 'override-service')      # Overridden
                self.assertEqual(traceroot.tracer._config.environment, 'override-env')           # Overridden
                self.assertEqual(traceroot.tracer._config.github_owner, 'yaml-owner')           # From YAML
                self.assertEqual(traceroot.tracer._config.github_repo_name, 'yaml-repo')        # From YAML
                self.assertEqual(traceroot.tracer._config.github_commit_hash, 'overridecommit456')  # Overridden
                self.assertEqual(traceroot.tracer._config.token, 'override-token-456')           # Overridden
                self.assertEqual(traceroot.tracer._config.enable_log_cloud_export, False)       # Overridden
    
    def test_init_without_yaml_config(self):
        """Test that traceroot.init() works without YAML configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Path.cwd() to return temp directory (no YAML file)
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize with only init() parameters
                tracer_provider = init(
                    service_name='init-only-service',
                    environment='init-only-env',
                    github_owner='init-owner',
                    github_repo_name='init-repo',
                    github_commit_hash='initcommit789'
                )
                
                # Verify that configuration comes from init() parameters only
                self.assertIsNotNone(traceroot.tracer._config)
                self.assertEqual(traceroot.tracer._config.service_name, 'init-only-service')
                self.assertEqual(traceroot.tracer._config.environment, 'init-only-env')
                self.assertEqual(traceroot.tracer._config.github_owner, 'init-owner')
                self.assertEqual(traceroot.tracer._config.github_repo_name, 'init-repo')
                self.assertEqual(traceroot.tracer._config.github_commit_hash, 'initcommit789')
    
    def test_multiple_init_calls_with_same_params(self):
        """Test that multiple init() calls with same parameters return the same tracer provider"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # First init call
                tracer_provider1 = init(
                    service_name='test-service',
                    github_owner='test-owner',
                    github_repo_name='test-repo',
                    github_commit_hash='testcommit123'
                )
                
                # Second init call with NO parameters (should return same instance)
                tracer_provider2 = init()
                
                # Should return the same instance (no kwargs provided)
                self.assertIs(tracer_provider1, tracer_provider2)
                
                # Configuration should remain from first call
                self.assertEqual(traceroot.tracer._config.service_name, 'test-service')
    
    def test_multiple_init_calls_with_different_params(self):
        """Test that init() calls with different parameters reinitialize"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # First init call
                tracer_provider1 = init(
                    service_name='test-service',
                    github_owner='test-owner',
                    github_repo_name='test-repo',
                    github_commit_hash='testcommit123'
                )
                
                # Second init call with different parameters - should reinitialize
                tracer_provider2 = init(
                    service_name='different-service',
                    github_owner='different-owner',
                    github_repo_name='different-repo',
                    github_commit_hash='differentcommit456'
                )
                
                # Should return different instances (reinitialization occurred)
                self.assertIsNot(tracer_provider1, tracer_provider2)
                
                # Configuration should be updated to new values
                self.assertEqual(traceroot.tracer._config.service_name, 'different-service')
    
    def test_reinitialization_with_overrides(self):
        """Test that calling init() again with kwargs reinitializes with new config"""
        yaml_config = {
            'service_name': 'yaml-service',
            'environment': 'yaml-env',
            'github_owner': 'yaml-owner',
            'github_repo_name': 'yaml-repo',
            'github_commit_hash': 'yamlcommit123',
            'token': 'yaml-token',
            'enable_log_cloud_export': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / '.traceroot-config.yaml'
            
            # Write YAML config
            with open(config_path, 'w') as f:
                yaml.dump(yaml_config, f)
            
            # Mock Path.cwd() to return our temp directory
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # First initialization (YAML only)
                tracer_provider1 = init()
                
                # Verify initial config from YAML
                self.assertIsNotNone(traceroot.tracer._config)
                self.assertEqual(traceroot.tracer._config.service_name, 'yaml-service')
                self.assertEqual(traceroot.tracer._config.token, 'yaml-token')
                self.assertEqual(traceroot.tracer._config.environment, 'yaml-env')
                
                # Second initialization with overrides - this should reinitialize
                tracer_provider2 = init(
                    service_name='reinitialized-service',
                    token='reinitialized-token',
                    environment='reinitialized-env'
                )
                
                # Verify that configuration was updated with overrides
                self.assertIsNotNone(traceroot.tracer._config)
                self.assertEqual(traceroot.tracer._config.service_name, 'reinitialized-service')  # Overridden
                self.assertEqual(traceroot.tracer._config.token, 'reinitialized-token')           # Overridden
                self.assertEqual(traceroot.tracer._config.environment, 'reinitialized-env')       # Overridden
                self.assertEqual(traceroot.tracer._config.github_owner, 'yaml-owner')             # From YAML
                
                # Should return new tracer provider
                self.assertIsNotNone(tracer_provider2)
                self.assertNotEqual(tracer_provider1, tracer_provider2)  # Different instances


if __name__ == '__main__':
    unittest.main()