"""Tests for logger initialization behavior"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import traceroot
from traceroot.config import TraceRootConfig
from traceroot.logger import _global_logger, get_logger, initialize_logger, shutdown_logger
from traceroot.tracer import init, shutdown


class TestLoggerInitialization(unittest.TestCase):
    """Test logger initialization with YAML config and init() overrides"""
    
    def setUp(self):
        """Reset global state before each test"""
        # Reset global state
        global _global_logger
        _global_logger = None
        shutdown()
        shutdown_logger()
    
    def tearDown(self):
        """Clean up after each test"""
        shutdown()
        shutdown_logger()
    
    def test_yaml_config_affects_logger_initialization(self):
        """Test that YAML configuration affects logger initialization"""
        # Create a temporary YAML config file
        test_config = {
            'service_name': 'logger-test-service',
            'environment': 'logger-test-env',
            'github_owner': 'logger-owner',
            'github_repo_name': 'logger-repo',
            'github_commit_hash': 'loggercommit123',
            'enable_log_cloud_export': False,
            'aws_region': 'us-west-2'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / '.traceroot-config.yaml'
            
            # Write test config to YAML file
            with open(config_path, 'w') as f:
                yaml.dump(test_config, f)
            
            # Mock Path.cwd() to return our temp directory
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize traceroot (this should load YAML config and init logger)
                init()
                
                # Get the initialized logger
                logger = get_logger()
                
                # Verify that logger configuration comes from YAML
                self.assertEqual(logger.config.service_name, 'logger-test-service')
                self.assertEqual(logger.config.environment, 'logger-test-env')
                self.assertEqual(logger.config.github_owner, 'logger-owner')
                self.assertEqual(logger.config.github_repo_name, 'logger-repo')
                self.assertEqual(logger.config.github_commit_hash, 'loggercommit123')
                self.assertEqual(logger.config.enable_log_cloud_export, False)
                self.assertEqual(logger.config.aws_region, 'us-west-2')
    
    def test_init_overrides_affect_logger_config(self):
        """Test that traceroot.init() parameters override YAML for logger"""
        # Create a temporary YAML config file
        yaml_config = {
            'service_name': 'yaml-logger-service',
            'environment': 'yaml-env',
            'github_owner': 'yaml-owner',
            'github_repo_name': 'yaml-repo',
            'github_commit_hash': 'yamlloggercommit',
            'enable_log_cloud_export': True,
            'aws_region': 'us-east-1'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / '.traceroot-config.yaml'
            
            # Write YAML config
            with open(config_path, 'w') as f:
                yaml.dump(yaml_config, f)
            
            # Mock Path.cwd() to return our temp directory
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize with override parameters
                init(
                    service_name='override-logger-service',
                    environment='override-env',
                    enable_log_cloud_export=False,
                    aws_region='us-west-2'
                )
                
                # Get the initialized logger
                logger = get_logger()
                
                # Verify that init() parameters override YAML values in logger
                self.assertEqual(logger.config.service_name, 'override-logger-service')  # Overridden
                self.assertEqual(logger.config.environment, 'override-env')             # Overridden
                self.assertEqual(logger.config.github_owner, 'yaml-owner')             # From YAML
                self.assertEqual(logger.config.github_repo_name, 'yaml-repo')          # From YAML
                self.assertEqual(logger.config.github_commit_hash, 'yamlloggercommit') # From YAML
                self.assertEqual(logger.config.enable_log_cloud_export, False)         # Overridden
                self.assertEqual(logger.config.aws_region, 'us-west-2')               # Overridden
    
    def test_logger_without_yaml_config(self):
        """Test that logger initialization works without YAML configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Path.cwd() to return temp directory (no YAML file)
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize with only init() parameters
                init(
                    service_name='logger-init-only',
                    environment='logger-init-env',
                    github_owner='init-logger-owner',
                    github_repo_name='init-logger-repo',
                    github_commit_hash='initloggercommit',
                    enable_log_cloud_export=False
                )
                
                # Get the initialized logger
                logger = get_logger()
                
                # Verify that logger configuration comes from init() parameters only
                self.assertEqual(logger.config.service_name, 'logger-init-only')
                self.assertEqual(logger.config.environment, 'logger-init-env')
                self.assertEqual(logger.config.github_owner, 'init-logger-owner')
                self.assertEqual(logger.config.github_repo_name, 'init-logger-repo')
                self.assertEqual(logger.config.github_commit_hash, 'initloggercommit')
                self.assertEqual(logger.config.enable_log_cloud_export, False)
    
    def test_get_logger_before_initialization_raises_error(self):
        """Test that get_logger() raises error when called before initialization"""
        # Ensure no global logger is set
        global _global_logger
        _global_logger = None
        
        with self.assertRaises(RuntimeError) as context:
            get_logger()
        
        self.assertIn("Logger not initialized", str(context.exception))
        self.assertIn("Call traceroot.init() first", str(context.exception))
    
    def test_get_logger_with_custom_name(self):
        """Test getting logger with custom name after initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                # Initialize traceroot
                init(
                    service_name='test-service',
                    github_owner='test-owner',
                    github_repo_name='test-repo',
                    github_commit_hash='testloggercommit'
                )
                
                # Get default logger
                default_logger = get_logger()
                
                # Get custom named logger
                custom_logger = get_logger('custom-logger')
                
                # Should have the same config but different logger names
                self.assertEqual(default_logger.config.service_name, custom_logger.config.service_name)
                self.assertNotEqual(default_logger.logger.name, custom_logger.logger.name)
                self.assertEqual(custom_logger.logger.name, 'custom-logger')
    
    def test_logger_cloud_export_configuration(self):
        """Test that enable_log_cloud_export setting is properly configured"""
        test_cases = [
            {'service_name': 'test-service', 'github_owner': 'test-owner', 'github_repo_name': 'test-repo', 
             'github_commit_hash': 'testcommit', 'enable_log_cloud_export': True},
            {'service_name': 'test-service', 'github_owner': 'test-owner', 'github_repo_name': 'test-repo',
             'github_commit_hash': 'testcommit', 'enable_log_cloud_export': False}
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = Path(temp_dir) / '.traceroot-config.yaml'
                    
                    # Write test config to YAML file
                    with open(config_path, 'w') as f:
                        yaml.dump(case, f)
                    
                    # Reset state
                    shutdown()
                    shutdown_logger()
                    
                    with patch('traceroot.utils.config.Path.cwd', return_value=Path(temp_dir)):
                        # Initialize with YAML config
                        init()
                        
                        # Get logger and verify cloud export setting
                        logger = get_logger()
                        self.assertEqual(
                            logger.config.enable_log_cloud_export, 
                            case['enable_log_cloud_export']
                        )


if __name__ == '__main__':
    unittest.main()