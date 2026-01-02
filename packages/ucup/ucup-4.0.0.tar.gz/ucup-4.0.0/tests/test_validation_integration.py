"""
Integration tests for UCUP validation and error handling systems.

This module tests the comprehensive validation and error handling
functionality added to the UCUP framework.
"""

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import yaml
from pathlib import Path

# Import UCUP modules
from ucup.validation import (
    UCUPValidator,
    ProbabilisticResultValidator,
    AgentConfigurationValidator,
    CoordinationConfigurationValidator,
    PluginConfigurationValidator,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity
)
from ucup.errors import (
    UCUPError,
    ValidationError,
    ConfigurationError,
    RuntimeError,
    ErrorHandler,
    ErrorSeverity as ErrorSeverityEnum,
    ErrorCategory
)
from ucup.config import load_ucup_config, create_ucup_system


class TestValidationSystem:
    """Test the comprehensive data validation system."""

    def test_ucup_validator_creation(self):
        """Test creating a UCUP validator instance."""
        validator = UCUPValidator()
        assert validator is not None
        assert hasattr(validator, 'validate')

    def test_probabilistic_result_validation(self):
        """Test validation of probabilistic results."""
        validator = ProbabilisticResultValidator()

        # Valid result
        valid_result = {
            'value': 'test_output',
            'confidence': 0.85,
            'alternatives': [{'value': 'alt1', 'confidence': 0.6}],
            'metadata': {'source': 'test'}
        }

        report = validator.validate(valid_result)
        assert report.is_valid
        assert len(report.issues) == 0

        # Invalid confidence
        invalid_result = {
            'value': 'test_output',
            'confidence': 1.5,  # Invalid: > 1.0
            'alternatives': [],
            'metadata': {}
        }

        report = validator.validate(invalid_result)
        assert not report.is_valid
        assert len(report.errors) > 0

    def test_agent_configuration_validation(self):
        """Test validation of agent configurations."""
        validator = AgentConfigurationValidator()

        # Valid config
        valid_config = {
            'type': 'ProbabilisticAgent',
            'capabilities': ['analysis', 'reasoning']
        }

        report = validator.validate(valid_config)
        assert report.is_valid

        # Missing required field
        invalid_config = {
            'capabilities': ['analysis']  # Missing 'type'
        }

        report = validator.validate(invalid_config)
        assert not report.is_valid
        assert len(report.errors) > 0

    def test_coordination_configuration_validation(self):
        """Test validation of coordination configurations."""
        validator = CoordinationConfigurationValidator()

        # Valid hierarchical config
        valid_config = {
            'type': 'hierarchical',
            'manager': '!ref:agents.manager',
            'workers': ['!ref:agents.worker1', '!ref:agents.worker2']
        }

        full_config = {
            'agents': {
                'manager': {'type': 'ProbabilisticAgent'},
                'worker1': {'type': 'ProbabilisticAgent'},
                'worker2': {'type': 'ProbabilisticAgent'}
            }
        }

        report = validator.validate(valid_config, full_config)
        assert report.is_valid

        # Invalid: missing required field
        invalid_config = {
            'type': 'hierarchical'
            # Missing manager and workers
        }

        report = validator.validate(invalid_config)
        assert not report.is_valid

    def test_plugin_configuration_validation(self):
        """Test validation of plugin configurations."""
        validator = PluginConfigurationValidator()

        # Valid config
        valid_config = {
            'metadata': {
                'name': 'test-plugin',
                'version': '1.0.0'
            },
            'config': {'setting': 'value'}
        }

        report = validator.validate(valid_config)
        assert report.is_valid

        # Invalid version format
        invalid_config = {
            'metadata': {
                'name': 'test-plugin',
                'version': '1.0'  # Invalid format
            }
        }

        report = validator.validate(invalid_config)
        assert not report.is_valid

    def test_ucup_config_validation(self):
        """Test validation of complete UCUP configurations."""
        validator = UCUPValidator()

        # Valid full config
        valid_config = {
            'version': '1.0.0',
            'agents': {
                'agent1': {
                    'type': 'ProbabilisticAgent',
                    'capabilities': ['analysis']
                }
            },
            'coordination': {
                'type': 'hierarchical',
                'manager': '!ref:agents.agent1',
                'workers': []
            }
        }

        report = validator.validate_config(valid_config)
        assert report.is_valid

        # Invalid config: missing version
        invalid_config = {
            'agents': {
                'agent1': {'type': 'ProbabilisticAgent'}
            }
        }

        report = validator.validate_config(invalid_config)
        assert not report.is_valid


class TestErrorHandlingSystem:
    """Test the comprehensive error handling system."""

    def test_ucup_error_creation(self):
        """Test creating UCUP error instances."""
        context = {
            'component': 'test_component',
            'operation': 'test_operation'
        }

        error = UCUPError(
            message="Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverityEnum.MEDIUM,
            error_code="TEST_ERROR",
            context=context
        )

        assert error.message == "Test error"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverityEnum.MEDIUM

    def test_validation_error_creation(self):
        """Test creating validation error instances."""
        error = ValidationError(
            message="Invalid field value",
            field="test_field",
            value="invalid_value",
            expected_type=str,
            suggested_fix="Use a string value"
        )

        assert error.field == "test_field"
        assert error.expected_type == str
        assert error.suggested_fix == "Use a string value"
        assert error.category == ErrorCategory.VALIDATION

    def test_configuration_error_creation(self):
        """Test creating configuration error instances."""
        error = ConfigurationError(
            message="Config file not found",
            config_file="/path/to/config.yaml"
        )

        assert error.config_file == "/path/to/config.yaml"
        assert error.category == ErrorCategory.CONFIGURATION
        assert len(error.recovery_strategies) > 0

    def test_runtime_error_creation(self):
        """Test creating runtime error instances."""
        error = RuntimeError(
            message="Operation failed",
            operation="test_operation",
            component="test_component",
            can_retry=True
        )

        assert error.can_retry
        assert error.operation == "test_operation"
        assert error.category == ErrorCategory.RUNTIME

    def test_error_recovery_strategies(self):
        """Test error recovery strategies."""
        error = ConfigurationError("Config error")

        strategies = error.get_recovery_suggestions()
        assert len(strategies) > 0

        # Check if auto-recoverable
        can_auto_recover = error.can_auto_recover()
        assert isinstance(can_auto_recover, bool)

    def test_error_handler_functionality(self):
        """Test error handler functionality."""
        handler = ErrorHandler()

        error = ValidationError(
            message="Test validation error",
            field="test",
            value="bad"
        )

        # Test error handling
        result = handler.handle_error(error)
        assert result is not None  # May return context or None

        # Check error history
        assert len(handler.error_history) > 0
        assert handler.error_history[-1] == error

    def test_error_to_dict_conversion(self):
        """Test converting errors to dictionaries."""
        error = ValidationError(
            message="Test error",
            field="test_field",
            value="bad_value"
        )

        error_dict = error.to_dict()
        assert isinstance(error_dict, dict)
        assert error_dict['category'] == 'validation'
        assert error_dict['severity'] == 'medium'


class TestIntegrationWithConfig:
    """Test integration of validation and error handling with config system."""

    def test_config_loading_with_validation(self):
        """Test loading config with validation."""
        config_data = {
            'version': '1.0.0',
            'agents': {
                'test_agent': {
                    'type': 'ProbabilisticAgent',
                    'capabilities': ['analysis']
                }
            }
        }

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            # This should work without errors
            config = load_ucup_config(config_path)
            assert config is not None
            assert config['version'] == '1.0.0'

        finally:
            Path(config_path).unlink()

    def test_config_loading_with_errors(self):
        """Test loading config that has validation errors."""
        invalid_config_data = {
            # Missing version
            'agents': {
                'test_agent': {
                    # Missing type field
                    'capabilities': ['analysis']
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config_data, f)
            config_path = f.name

        try:
            # This should raise an exception
            with pytest.raises(ValueError):
                load_ucup_config(config_path)

        finally:
            Path(config_path).unlink()

    @patch('ucup.config.get_plugin_manager')
    def test_plugin_system_integration(self, mock_get_plugin_manager):
        """Test plugin system integration in config resolver."""
        # Mock plugin manager
        mock_pm = MagicMock()
        mock_get_plugin_manager.return_value = mock_pm

        config = {
            'agents': {
                'plugin_agent': {
                    'type': 'ProbabilisticAgent',
                    'config': {'key': 'value'}
                }
            }
        }

        from ucup.config import ConfigResolver
        resolver = ConfigResolver(config)

        # Plugin manager should be initialized
        assert resolver.plugin_manager == mock_pm


class TestErrorDecorator:
    """Test the error handling decorator."""

    @pytest.mark.asyncio
    async def test_error_handler_decorator_async(self):
        """Test the error handler decorator with async functions."""
        from ucup.errors import error_handler

        @error_handler()
        async def failing_async_function():
            raise ValueError("Test error")

        # This should not raise an exception, but handle the error
        result = await failing_async_function()
        assert result is not None  # Error was handled

    def test_error_handler_decorator_sync(self):
        """Test the error handler decorator with sync functions."""
        from ucup.errors import error_handler

        @error_handler()
        def failing_sync_function():
            raise ValueError("Test error")

        # This should not raise an exception, but handle the error
        result = failing_sync_function()
        assert result is not None  # Error was handled


if __name__ == "__main__":
    pytest.main([__file__])
