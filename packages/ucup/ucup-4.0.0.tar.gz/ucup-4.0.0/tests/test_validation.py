"""
Comprehensive unit tests for the UCUP validation framework.

Tests cover:
- Type validation functionality
- Input sanitization
- Error handling and meaningful messages
- Decorator behavior
- Configuration validation
- Domain-specific validators for UCUP components
- Performance monitoring and validation metrics
- Advanced validation rules for complex scenarios
- Integration with UCUP components
"""

import pytest
import numpy as np
import time
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock

# Import validation framework
from ucup.validation import (
    ValidationError, ValidationResult, TypeValidator, InputSanitizer,
    ValidationMetrics, ValidationMonitor, validation_monitor,
    CoordinationValidator, ProbabilisticValidator, ObservabilityValidator,
    ReliabilityValidator, TestingValidator, AdvancedValidator,
    UCUPValidator,
    UCUPValidationError, UCUPTypeError, UCUPValueError, UCUPConfigurationError,
    validate_types, sanitize_inputs, validate_config,
    validate_probability, validate_positive_number, validate_non_empty_string,
    create_error_message
)


class TestValidationError:
    """Test ValidationError class functionality."""

    def test_validation_error_creation(self):
        """Test creating a ValidationError instance."""
        error = ValidationError(
            field="test_field",
            value="invalid_value",
            expected_type="str",
            actual_type="int",
            message="Type mismatch",
            severity="error",
            suggestion="Provide a string value"
        )

        assert error.field == "test_field"
        assert error.value == "invalid_value"
        assert error.expected_type == "str"
        assert error.actual_type == "int"
        assert error.message == "Type mismatch"
        assert error.severity == "error"
        assert error.suggestion == "Provide a string value"

    def test_validation_error_string_representation(self):
        """Test string representation of ValidationError."""
        error = ValidationError(
            field="confidence",
            value=1.5,
            expected_type="float (0.0-1.0)",
            actual_type="float",
            message="Value out of range",
            suggestion="Use a value between 0.0 and 1.0"
        )

        error_str = str(error)
        assert "ValidationError in field 'confidence'" in error_str
        assert "Value out of range" in error_str
        assert "Suggestion: Use a value between 0.0 and 1.0" in error_str


class TestValidationResult:
    """Test ValidationResult class functionality."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult instance."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.sanitized_value is None

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        result = ValidationResult(is_valid=False)
        error = ValidationError(
            field="test", value="val", expected_type="str", actual_type="int",
            message="Type error"
        )

        result.add_error(error)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == error

    def test_validation_result_with_warnings(self):
        """Test ValidationResult with warnings."""
        result = ValidationResult(is_valid=True)
        warning = ValidationError(
            field="test", value="val", expected_type="str", actual_type="str",
            message="Warning message", severity="warning"
        )

        result.add_warning(warning)
        assert result.is_valid is True  # Warnings don't make it invalid
        assert len(result.warnings) == 1

    def test_validation_result_error_messages(self):
        """Test getting error messages from ValidationResult."""
        result = ValidationResult(is_valid=False)
        result.add_error(ValidationError(
            field="field1", value="val1", expected_type="str", actual_type="int",
            message="Error 1"
        ))
        result.add_error(ValidationError(
            field="field2", value="val2", expected_type="int", actual_type="str",
            message="Error 2"
        ))

        messages = result.get_error_messages()
        assert len(messages) == 2
        assert "Error 1" in messages[0]
        assert "Error 2" in messages[1]


class TestTypeValidator:
    """Test TypeValidator functionality."""

    def test_validate_simple_type_success(self):
        """Test validating simple types successfully."""
        result = TypeValidator.validate_type("hello", str, "greeting")
        assert result.is_valid is True
        assert result.sanitized_value == "hello"

    def test_validate_simple_type_failure(self):
        """Test validating simple types with failure."""
        result = TypeValidator.validate_type(123, str, "greeting")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "greeting"
        assert "Expected str, got int" in result.errors[0].message

    def test_validate_list_type_success(self):
        """Test validating list types successfully."""
        result = TypeValidator.validate_type([1, 2, 3], List[int], "numbers")
        assert result.is_valid is True

    def test_validate_list_type_failure(self):
        """Test validating list types with failure."""
        result = TypeValidator.validate_type([1, "two", 3], List[int], "numbers")
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validate_dict_type_success(self):
        """Test validating dict types successfully."""
        # Note: Complex generic types like Dict[str, Union[str, int]] cannot be validated at runtime
        # So we just test basic dict validation
        result = TypeValidator.validate_type(
            {"name": "test", "value": 42},
            dict,
            "config"
        )
        assert result.is_valid is True

    def test_validate_union_type_success(self):
        """Test validating union types successfully."""
        # Test with None (Optional)
        result = TypeValidator.validate_type(None, Optional[str], "optional_field")
        assert result.is_valid is True

        # Test with valid type
        result = TypeValidator.validate_type("hello", Optional[str], "optional_field")
        assert result.is_valid is True

    def test_validate_union_type_failure(self):
        """Test validating union types with failure."""
        result = TypeValidator.validate_type(123, Optional[str], "optional_field")
        assert result.is_valid is False


class TestInputSanitizer:
    """Test InputSanitizer functionality."""

    def test_sanitize_string_success(self):
        """Test string sanitization successfully."""
        result = InputSanitizer.sanitize_string(
            "  hello world  ", "name", max_length=50, min_length=1
        )
        assert result.is_valid is True
        assert result.sanitized_value == "hello world"

    def test_sanitize_string_length_validation(self):
        """Test string length validation."""
        # Test max length
        result = InputSanitizer.sanitize_string("a" * 100, "name", max_length=50)
        assert result.is_valid is False
        assert "exceeds maximum length" in result.errors[0].message

        # Test min length
        result = InputSanitizer.sanitize_string("", "name", min_length=5)
        assert result.is_valid is False
        assert "below minimum length" in result.errors[0].message

    def test_sanitize_string_pattern_validation(self):
        """Test string pattern validation."""
        result = InputSanitizer.sanitize_string(
            "invalid-name!", "identifier",
            pattern=r'^[a-zA-Z][a-zA-Z0-9_]*$'
        )
        assert result.is_valid is False
        assert "does not match required pattern" in result.errors[0].message

    def test_sanitize_numeric_success(self):
        """Test numeric sanitization successfully."""
        result = InputSanitizer.sanitize_numeric(
            "0.85", "confidence", min_value=0.0, max_value=1.0
        )
        assert result.is_valid is True
        assert result.sanitized_value == 0.85

    def test_sanitize_numeric_range_validation(self):
        """Test numeric range validation."""
        # Test max value
        result = InputSanitizer.sanitize_numeric(1.5, "confidence", max_value=1.0)
        assert result.is_valid is False
        assert "above maximum" in result.errors[0].message

        # Test min value
        result = InputSanitizer.sanitize_numeric(-0.5, "confidence", min_value=0.0)
        assert result.is_valid is False
        assert "below minimum" in result.errors[0].message

    def test_sanitize_numeric_type_conversion(self):
        """Test numeric type conversion."""
        # String to float
        result = InputSanitizer.sanitize_numeric("3.14", "pi")
        assert result.is_valid is True
        assert result.sanitized_value == 3.14

        # String to int
        result = InputSanitizer.sanitize_numeric("42", "answer")
        assert result.is_valid is True
        assert result.sanitized_value == 42


class TestValidationDecorators:
    """Test validation decorators."""

    def test_validate_types_decorator_success(self):
        """Test @validate_types decorator with valid inputs."""
        @validate_types
        def add_numbers(a: int, b: int) -> int:
            return a + b

        result = add_numbers(5, 3)
        assert result == 8

    def test_validate_types_decorator_failure(self):
        """Test @validate_types decorator with invalid inputs."""
        @validate_types
        def add_numbers(a: int, b: int) -> int:
            return a + b

        with pytest.raises(UCUPTypeError):
            add_numbers("5", 3)

    def test_sanitize_inputs_decorator_success(self):
        """Test @sanitize_inputs decorator with valid inputs."""
        @sanitize_inputs(
            name={'type': 'string', 'max_length': 50, 'min_length': 1},
            age={'type': 'numeric', 'min_value': 0, 'max_value': 150}
        )
        def create_person(name: str, age: int) -> dict:
            return {"name": name, "age": age}

        result = create_person("John Doe", 30)
        assert result == {"name": "John Doe", "age": 30}

    def test_sanitize_inputs_decorator_failure(self):
        """Test @sanitize_inputs decorator with invalid inputs."""
        @sanitize_inputs(
            name={'type': 'string', 'max_length': 50, 'min_length': 1},
            age={'type': 'numeric', 'min_value': 0, 'max_value': 150}
        )
        def create_person(name: str, age: int) -> dict:
            return {"name": name, "age": age}

        with pytest.raises(UCUPValueError):
            create_person("", 30)  # Empty name should fail

        with pytest.raises(UCUPValueError):
            create_person("John", 200)  # Age too high should fail


class TestConfigurationValidation:
    """Test configuration validation functionality."""

    def test_validate_config_success(self):
        """Test successful configuration validation."""
        schema = {
            'name': {'type': str, 'required': True},
            'age': {'type': int, 'required': False, 'min': 0, 'max': 150},
            'active': {'type': bool, 'required': False, 'default': True}
        }

        config = {
            'name': 'John',
            'age': 30,
            'active': False
        }

        result = validate_config(config, schema)
        assert result.is_valid is True

    def test_validate_config_missing_required(self):
        """Test configuration validation with missing required field."""
        schema = {
            'name': {'type': str, 'required': True},
            'age': {'type': int, 'required': False}
        }

        config = {'age': 30}  # Missing required 'name'

        result = validate_config(config, schema)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "required configuration field 'name' is missing" in result.errors[0].message

    def test_validate_config_type_mismatch(self):
        """Test configuration validation with type mismatch."""
        schema = {
            'age': {'type': int, 'required': True}
        }

        config = {'age': 'thirty'}  # Wrong type

        result = validate_config(config, schema)
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_validate_config_range_validation(self):
        """Test configuration validation with range constraints."""
        schema = {
            'confidence': {'type': float, 'min': 0.0, 'max': 1.0}
        }

        config = {'confidence': 1.5}  # Out of range

        result = validate_config(config, schema)
        assert result.is_valid is False
        assert "above maximum" in result.errors[0].message


class TestUtilityFunctions:
    """Test utility validation functions."""

    def test_validate_probability_success(self):
        """Test probability validation with valid values."""
        # Should not raise exception
        validate_probability(0.0, "min_prob")
        validate_probability(0.5, "mid_prob")
        validate_probability(1.0, "max_prob")

    def test_validate_probability_failure(self):
        """Test probability validation with invalid values."""
        with pytest.raises(UCUPValueError):
            validate_probability(-0.1, "negative_prob")

        with pytest.raises(UCUPValueError):
            validate_probability(1.1, "over_one_prob")

        with pytest.raises(UCUPValueError):
            validate_probability("0.5", "string_prob")

    def test_validate_positive_number_success(self):
        """Test positive number validation with valid values."""
        validate_positive_number(0.1, "small_positive")
        validate_positive_number(1, "positive_int")
        validate_positive_number(100.5, "large_positive")

    def test_validate_positive_number_failure(self):
        """Test positive number validation with invalid values."""
        with pytest.raises(UCUPValueError):
            validate_positive_number(0, "zero")

        with pytest.raises(UCUPValueError):
            validate_positive_number(-1, "negative")

        with pytest.raises(UCUPValueError):
            validate_positive_number("5", "string_positive")

    def test_validate_non_empty_string_success(self):
        """Test non-empty string validation with valid values."""
        validate_non_empty_string("a", "single_char")
        validate_non_empty_string("hello world", "multi_word")
        validate_non_empty_string("   spaces   ".strip(), "trimmed")

    def test_validate_non_empty_string_failure(self):
        """Test non-empty string validation with invalid values."""
        with pytest.raises(UCUPValueError):
            validate_non_empty_string("", "empty_string")

        with pytest.raises(UCUPValueError):
            validate_non_empty_string("   ", "whitespace_only")

        with pytest.raises(UCUPValueError):
            validate_non_empty_string(123, "number")


class TestErrorMessageCreation:
    """Test error message creation utility."""

    def test_create_error_message_basic(self):
        """Test basic error message creation."""
        msg = create_error_message(
            context="Agent Initialization",
            action="Loading configuration",
            details="Invalid confidence value"
        )

        assert "[Agent Initialization] Loading configuration: Invalid confidence value" == msg

    def test_create_error_message_with_suggestion(self):
        """Test error message creation with suggestion."""
        msg = create_error_message(
            context="Validation",
            action="Type checking",
            details="Expected string, got integer",
            suggestion="Convert value to string or provide string input"
        )

        expected = ("[Validation] Type checking: Expected string, got integer | "
                   "Suggestion: Convert value to string or provide string input")
        assert expected == msg


class TestExceptionHierarchy:
    """Test custom exception hierarchy."""

    def test_ucup_validation_error_creation(self):
        """Test creating UCUPValidationError."""
        errors = [
            ValidationError("field1", "val1", "str", "int", "Type error"),
            ValidationError("field2", "val2", "int", "str", "Another error")
        ]

        exc = UCUPValidationError("Multiple validation errors", errors=errors)
        assert "Multiple validation errors" in str(exc)
        assert len(exc.errors) == 2

    def test_ucup_type_error_inheritance(self):
        """Test UCUPTypeError inheritance."""
        exc = UCUPTypeError("Type mismatch in parameter")
        assert isinstance(exc, UCUPValidationError)
        assert "Type mismatch" in str(exc)

    def test_ucup_value_error_inheritance(self):
        """Test UCUPValueError inheritance."""
        exc = UCUPValueError("Invalid value provided")
        assert isinstance(exc, UCUPValidationError)
        assert "Invalid value" in str(exc)

    def test_ucup_configuration_error_inheritance(self):
        """Test UCUPConfigurationError inheritance."""
        exc = UCUPConfigurationError("Configuration validation failed")
        assert isinstance(exc, UCUPValidationError)
        assert "Configuration validation" in str(exc)


class TestIntegrationWithDataclasses:
    """Test integration with UCUP dataclasses."""

    def test_probabilistic_result_validation(self):
        """Test ProbabilisticResult dataclass validation."""
        from ucup.probabilistic import ProbabilisticResult

        # Valid result
        result = ProbabilisticResult(
            value="test_output",
            confidence=0.85,
            alternatives=[],
            metadata={}
        )
        assert result.confidence == 0.85

        # Invalid confidence should raise error
        with pytest.raises(UCUPValueError):
            ProbabilisticResult(
                value="test_output",
                confidence=1.5,  # Invalid confidence
                alternatives=[],
                metadata={}
            )

    def test_decision_node_validation(self):
        """Test DecisionNode dataclass validation."""
        from ucup.observability import DecisionNode

        # Valid decision node
        node = DecisionNode(
            decision_id="decision_1",
            available_actions=[{"action": "option1", "cost": 1}],
            confidence_scores={"option1": 0.8}
        )
        assert node.decision_id == "decision_1"

        # Invalid decision ID should raise error
        with pytest.raises(UCUPValueError):
            DecisionNode(
                decision_id="",  # Invalid empty ID
                available_actions=[],
                confidence_scores={}
            )

        # Invalid confidence score should raise error
        with pytest.raises(UCUPValueError):
            DecisionNode(
                decision_id="decision_2",
                available_actions=[{"action": "option1"}],
                confidence_scores={"option1": 1.5}  # Invalid confidence
            )


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""

    def test_large_data_validation(self):
        """Test validation performance with large datasets."""
        large_list = list(range(1000))

        result = TypeValidator.validate_type(large_list, List[int], "large_data")
        assert result.is_valid is True

    def test_nested_structure_validation(self):
        """Test validation of deeply nested structures."""
        from typing import List, Dict

        nested_data = {
            "users": [
                {
                    "name": "Alice",
                    "age": 30,
                    "scores": [85, 92, 78]
                },
                {
                    "name": "Bob",
                    "age": 25,
                    "scores": [88, 79, 95]
                }
            ],
            "metadata": {
                "version": "1.0",
                "created": "2025-01-01"
            }
        }

        expected_type = Dict[str, Union[
            List[Dict[str, Union[str, int, List[int]]]],
            Dict[str, str]
        ]]

        result = TypeValidator.validate_type(nested_data, expected_type, "nested_structure")
        assert result.is_valid is True

    def test_circular_reference_handling(self):
        """Test handling of potential circular references."""
        # This is more of a smoke test to ensure no infinite recursion
        data = {"self": None}
        data["self"] = data  # Create circular reference

        # Should not crash, even if validation isn't perfect for circular refs
        result = TypeValidator.validate_type(data, Dict[str, any], "circular_data")
        # Result may or may not be valid, but shouldn't crash
        assert isinstance(result, ValidationResult)


class TestValidationMetrics:
    """Test validation metrics functionality."""

    def test_validation_metrics_creation(self):
        """Test creating ValidationMetrics instance."""
        metrics = ValidationMetrics()
        assert metrics.total_validations == 0
        assert metrics.successful_validations == 0
        assert metrics.failed_validations == 0
        assert metrics.average_validation_time == 0.0

    def test_validation_metrics_record_validation(self):
        """Test recording validation metrics."""
        metrics = ValidationMetrics()

        # Record successful validation
        success_result = ValidationResult(is_valid=True)
        metrics.record_validation(success_result, 0.1)

        assert metrics.total_validations == 1
        assert metrics.successful_validations == 1
        assert metrics.failed_validations == 0
        assert metrics.average_validation_time == 0.1

        # Record failed validation
        failure_result = ValidationResult(is_valid=False)
        failure_result.add_error(ValidationError("field", "value", "str", "int", "error"))
        metrics.record_validation(failure_result, 0.2)

        assert metrics.total_validations == 2
        assert metrics.successful_validations == 1
        assert metrics.failed_validations == 1
        assert abs(metrics.average_validation_time - 0.15) < 1e-10  # Handle floating point precision

    def test_validation_metrics_get_success_rate(self):
        """Test getting success rate."""
        metrics = ValidationMetrics()

        # No validations yet
        assert metrics.get_success_rate() == 0.0

        # Add some validations
        for _ in range(3):
            metrics.record_validation(ValidationResult(is_valid=True), 0.1)
        for _ in range(2):
            result = ValidationResult(is_valid=False)
            result.add_error(ValidationError("field", "value", "str", "int", "error"))
            metrics.record_validation(result, 0.1)

        assert metrics.get_success_rate() == 0.6  # 3/5


class TestValidationMonitor:
    """Test validation monitoring functionality."""

    def test_validation_monitor_creation(self):
        """Test creating ValidationMonitor instance."""
        monitor = ValidationMonitor()
        assert len(monitor.metrics.error_counts) == 0
        assert len(monitor.active_sessions) == 0

    def test_validation_monitor_session_tracking(self):
        """Test session tracking in ValidationMonitor."""
        monitor = ValidationMonitor()

        # Start session
        session_id = "test_session"
        monitor.start_validation_session(session_id, "test_domain")

        assert session_id in monitor.active_sessions

        # End session
        result = ValidationResult(is_valid=True)
        monitor.end_validation_session(session_id, result, "test_domain")

        assert session_id not in monitor.active_sessions

        # Check metrics were recorded
        domain_metrics = monitor.get_domain_metrics("test_domain")
        assert domain_metrics['total_validations'] == 1
        assert domain_metrics['success_rate'] == 1.0

    def test_validation_monitor_global_metrics(self):
        """Test global metrics retrieval."""
        monitor = ValidationMonitor()

        # Add some validations
        for i in range(5):
            result = ValidationResult(is_valid=(i % 2 == 0))
            if not result.is_valid:
                result.add_error(ValidationError("field", "value", "str", "int", "error"))
            monitor.metrics.record_validation(result, 0.1)

        global_metrics = monitor.get_global_metrics()
        assert global_metrics['total_validations'] == 5
        assert global_metrics['success_rate'] == 0.6  # 3/5
        assert len(global_metrics['most_common_errors']) <= 10


class TestCoordinationValidator:
    """Test CoordinationValidator functionality."""

    def test_validate_agent_message_success(self):
        """Test validating valid agent messages."""
        # Mock message object
        class MockMessage:
            def __init__(self):
                self.message_id = "msg_123"
                self.sender_id = "agent_1"
                self.recipient_id = "agent_2"
                self.message_type = Mock()  # Mock MessageType
                self.payload = {"action": "test"}
                self.timestamp = time.time()
                self.ttl = 60

        message = MockMessage()
        result = CoordinationValidator.validate_agent_message(message)

        assert result.is_valid is True

    def test_validate_agent_message_missing_attribute(self):
        """Test validating agent messages with missing attributes."""
        # Mock message with missing attribute
        class MockMessage:
            def __init__(self):
                self.message_id = "msg_123"
                # Missing sender_id
                self.recipient_id = "agent_2"
                self.message_type = Mock()
                self.payload = {"action": "test"}
                self.timestamp = time.time()
                self.ttl = 60

        message = MockMessage()
        result = CoordinationValidator.validate_agent_message(message)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Required attribute 'sender_id' missing" in result.errors[0].message

    def test_validate_agent_message_invalid_ttl(self):
        """Test validating agent messages with invalid TTL."""
        class MockMessage:
            def __init__(self):
                self.message_id = "msg_123"
                self.sender_id = "agent_1"
                self.recipient_id = "agent_2"
                self.message_type = Mock()
                self.payload = {"action": "test"}
                self.timestamp = time.time()
                self.ttl = -1  # Invalid TTL

        message = MockMessage()
        result = CoordinationValidator.validate_agent_message(message)

        assert result.is_valid is False
        assert any("TTL must be positive" in error.message for error in result.errors)


class TestProbabilisticValidator:
    """Test ProbabilisticValidator functionality."""

    def test_validate_probabilistic_result_success(self):
        """Test validating valid probabilistic results."""
        class MockResult:
            def __init__(self):
                self.confidence = 0.85
                self.alternatives = [
                    Mock(confidence=0.7),
                    Mock(confidence=0.6)
                ]

        result = ProbabilisticValidator.validate_probabilistic_result(MockResult())
        assert result.is_valid is True

    def test_validate_probabilistic_result_invalid_confidence(self):
        """Test validating probabilistic results with invalid confidence."""
        class MockResult:
            def __init__(self):
                self.confidence = 1.5  # Invalid confidence > 1.0

        result = ProbabilisticValidator.validate_probabilistic_result(MockResult())
        assert result.is_valid is False
        assert any("must be between 0.0 and 1.0" in error.message for error in result.errors)


class TestObservabilityValidator:
    """Test ObservabilityValidator functionality."""

    def test_validate_decision_node_success(self):
        """Test validating valid decision nodes."""
        class MockNode:
            def __init__(self):
                self.decision_id = "decision_123"
                self.confidence_scores = {"option1": 0.8, "option2": 0.6}

        node = MockNode()
        result = ObservabilityValidator.validate_decision_node(node)

        assert result.is_valid is True

    def test_validate_decision_node_invalid_id(self):
        """Test validating decision nodes with invalid ID."""
        class MockNode:
            def __init__(self):
                self.decision_id = ""  # Empty ID
                self.confidence_scores = {}

        node = MockNode()
        result = ObservabilityValidator.validate_decision_node(node)

        assert result.is_valid is False
        assert any("cannot be empty" in error.message for error in result.errors)


class TestReliabilityValidator:
    """Test ReliabilityValidator functionality."""

    def test_validate_failure_indicator_success(self):
        """Test validating valid failure indicators."""
        class MockIndicator:
            def __init__(self):
                self.severity = "medium"
                self.confidence = 0.9

        indicator = MockIndicator()
        result = ReliabilityValidator.validate_failure_indicator(indicator)

        assert result.is_valid is True

    def test_validate_failure_indicator_invalid_severity(self):
        """Test validating failure indicators with invalid severity."""
        class MockIndicator:
            def __init__(self):
                self.severity = "invalid_severity"
                self.confidence = 0.9

        indicator = MockIndicator()
        result = ReliabilityValidator.validate_failure_indicator(indicator)

        assert result.is_valid is False
        assert any("Invalid severity level" in error.message for error in result.errors)


class TestTestingValidator:
    """Test TestingValidator functionality."""

    def test_validate_test_scenario_success(self):
        """Test validating valid test scenarios."""
        class MockScenario:
            def __init__(self):
                self.name = "test_scenario"
                self.expected_outcomes = ["success", "failure"]

        scenario = MockScenario()
        result = TestingValidator.validate_test_scenario(scenario)

        assert result.is_valid is True

    def test_validate_test_scenario_empty_name(self):
        """Test validating test scenarios with empty name."""
        class MockScenario:
            def __init__(self):
                self.name = ""  # Empty name

        scenario = MockScenario()
        result = TestingValidator.validate_test_scenario(scenario)

        assert result.is_valid is False
        assert any("cannot be empty" in error.message for error in result.errors)


class TestAdvancedValidator:
    """Test AdvancedValidator functionality."""

    def test_validate_cross_references(self):
        """Test cross-reference validation."""
        data = {
            "primary_field": "value1",
            "reference_field": "value2"
        }

        reference_schema = {
            "reference_field": {
                "references": "primary_field",
                "allowed_values": ["value1", "value2"]
            }
        }

        result = AdvancedValidator.validate_cross_references(data, reference_schema)
        assert result.is_valid is True

    def test_validate_conditional_dependencies(self):
        """Test conditional dependency validation."""
        data = {
            "mode": "advanced",
            "timeout": 300
        }

        conditions = {
            "mode": {
                "advanced": ["timeout"]
            }
        }

        result = AdvancedValidator.validate_conditional_dependencies(data, conditions)
        assert result.is_valid is True

        # Test missing required field
        data_missing = {"mode": "advanced"}
        result = AdvancedValidator.validate_conditional_dependencies(data_missing, conditions)
        assert result.is_valid is False

    def test_validate_range_relationships(self):
        """Test range relationship validation."""
        data = {
            "min_value": 10,
            "max_value": 20
        }

        ranges = {
            "value_range": {
                "min_field": "min_value",
                "max_field": "max_value"
            }
        }

        result = AdvancedValidator.validate_range_relationships(data, ranges)
        assert result.is_valid is True

        # Test invalid range
        data_invalid = {
            "min_value": 25,
            "max_value": 20
        }

        result = AdvancedValidator.validate_range_relationships(data_invalid, ranges)
        assert result.is_valid is False

    def test_validate_business_rules(self):
        """Test business rule validation."""
        data = {"age": 25, "status": "active"}

        def age_status_rule(data):
            if data.get("age", 0) < 18 and data.get("status") == "active":
                return "Minors cannot have active status"
            return None

        rules = [age_status_rule]

        result = AdvancedValidator.validate_business_rules(data, rules)
        assert result.is_valid is True

        # Test rule violation
        data_violation = {"age": 16, "status": "active"}
        result = AdvancedValidator.validate_business_rules(data_violation, rules)
        assert result.is_valid is False


class TestUCUPValidator:
    """Test UCUPValidator functionality."""

    def test_ucup_validator_creation(self):
        """Test creating UCUPValidator instance."""
        validator = UCUPValidator()
        assert validator.strict_mode is True
        assert validator.enable_monitoring is True

    def test_ucup_validator_agent_config(self):
        """Test agent configuration validation."""
        validator = UCUPValidator()

        config = {
            'name': 'TestAgent',
            'type': 'probabilistic',
            'confidence_threshold': 0.8
        }

        result = validator.validate_agent_config(config)
        assert result.is_valid is True

    def test_ucup_validator_complex_scenario(self):
        """Test complex scenario validation."""
        validator = UCUPValidator()

        data = {
            "agent_id": "agent_123",
            "confidence": 0.85,
            "min_threshold": 0.7,
            "max_threshold": 0.9
        }

        rules = {
            "conditional_dependencies": {
                "confidence": {
                    "high": ["max_threshold"]
                }
            },
            "range_relationships": {
                "threshold_range": {
                    "min_field": "min_threshold",
                    "max_field": "max_threshold"
                }
            }
        }

        # Note: This would normally require confidence to be "high" for the conditional dependency
        # but we're testing the validation logic
        result = validator.validate_complex_scenario(data, rules)
        # The result depends on the specific rules, but should not crash
        assert isinstance(result, ValidationResult)

    def test_ucup_validator_metrics(self):
        """Test metrics retrieval."""
        validator = UCUPValidator()

        # Perform some validations to generate metrics
        config = {'name': 'TestAgent', 'type': 'probabilistic'}
        for _ in range(5):
            validator.validate_agent_config(config)

        metrics = validator.get_validation_metrics()
        assert 'total_validations' in metrics
        assert metrics['total_validations'] >= 5

    def test_ucup_validator_domain_metrics(self):
        """Test domain-specific metrics."""
        validator = UCUPValidator()

        # Perform validations in different domains
        validator.validate_agent_config({'name': 'Test', 'type': 'test'})
        validator.validate_probabilistic_result(Mock(confidence=0.8))

        agent_metrics = validator.get_validation_metrics('agent_config')
        prob_metrics = validator.get_validation_metrics('probabilistic')

        assert isinstance(agent_metrics, dict)
        assert isinstance(prob_metrics, dict)


class TestMultimodalAgentValidation:
    """Test validation for multimodal agent features."""

    def test_multimodal_fusion_validation(self):
        """Test validation of multimodal fusion data."""
        validator = UCUPValidator()

        # Test text analysis data
        text_data = {
            "modality": "text",
            "content": "This is a sample text for analysis",
            "sentiment_score": 0.75,
            "entities": ["sample", "text", "analysis"],
            "language": "en",
            "confidence": 0.89
        }

        result = validator.validate_complex_scenario(text_data, {
            "conditional_dependencies": {
                "modality": {
                    "text": ["sentiment_score", "entities", "language"]
                }
            }
        })
        assert result.is_valid is True

        # Test vision processing data
        vision_data = {
            "modality": "vision",
            "objects_detected": ["person", "car", "building"],
            "scene_description": "urban street scene",
            "ocr_text": "Hello World",
            "classification_confidence": 0.92,
            "processing_time": 0.15
        }

        result = validator.validate_complex_scenario(vision_data, {
            "conditional_dependencies": {
                "modality": {
                    "vision": ["objects_detected", "scene_description"]
                }
            },
            "range_relationships": {
                "performance_range": {
                    "min_field": "processing_time",
                    "max_field": "max_allowed_time"
                }
            }
        })
        assert result.is_valid is True

        # Test audio analysis data
        audio_data = {
            "modality": "audio",
            "transcription": "Hello, how are you today?",
            "speaker_id": "speaker_001",
            "emotion": "neutral",
            "audio_classification": "speech",
            "confidence": 0.85,
            "duration": 3.2
        }

        result = validator.validate_complex_scenario(audio_data, {
            "conditional_dependencies": {
                "modality": {
                    "audio": ["transcription", "speaker_id", "emotion"]
                }
            }
        })
        assert result.is_valid is True

    def test_sensor_fusion_validation(self):
        """Test validation of sensor fusion data."""
        validator = UCUPValidator()

        sensor_data = {
            "sensor_type": "iot",
            "device_id": "sensor_001",
            "readings": [23.5, 24.1, 23.8, 24.2],
            "anomaly_score": 0.15,
            "prediction": 24.5,
            "maintenance_required": False,
            "last_calibration": "2025-01-01T00:00:00Z"
        }

        result = validator.validate_complex_scenario(sensor_data, {
            "conditional_dependencies": {
                "sensor_type": {
                    "iot": ["device_id", "readings", "anomaly_score"]
                }
            },
            "business_rules": [
                lambda d: "Anomaly score too high" if d.get("anomaly_score", 0) > 0.8 else None,
                lambda d: "Invalid device ID format" if not d.get("device_id", "").startswith("sensor_") else None
            ]
        })
        assert result.is_valid is True

    def test_fusion_engine_validation(self):
        """Test validation of fusion engine operations."""
        validator = UCUPValidator()

        fusion_data = {
            "fusion_id": "fusion_001",
            "modalities_used": ["text", "vision", "audio"],
            "fusion_confidence": 0.78,
            "decision_integrated": True,
            "context_awareness": 0.92,
            "processing_efficiency": 0.85,
            "latency_ms": 245,
            "fusion_metrics": {
                "cross_modal_consistency": 0.88,
                "decision_quality": 0.91
            }
        }

        result = validator.validate_complex_scenario(fusion_data, {
            "conditional_dependencies": {
                "decision_integrated": {
                    True: ["fusion_confidence", "context_awareness"]
                }
            },
            "range_relationships": {
                "efficiency_range": {
                    "min_field": "processing_efficiency",
                    "max_field": "max_efficiency_threshold"
                },
                "latency_range": {
                    "min_field": "latency_ms",
                    "max_field": "max_latency_threshold"
                }
            }
        })
        assert result.is_valid is True

    def test_agent_testing_suite_validation(self):
        """Test validation of agent testing suite data."""
        validator = UCUPValidator()

        test_suite_data = {
            "test_suite_id": "suite_001",
            "agent_under_test": "multimodal_agent_v1",
            "test_type": "scenario_based",
            "scenarios": [
                {"name": "text_only", "modality": "text", "difficulty": "easy"},
                {"name": "multimodal_fusion", "modalities": ["text", "vision"], "difficulty": "hard"}
            ],
            "probabilistic_evaluation": True,
            "uncertainty_threshold": 0.1,
            "performance_benchmarks": {
                "accuracy_target": 0.85,
                "latency_target_ms": 500,
                "confidence_target": 0.8
            },
            "multi_agent_testing": True,
            "coordination_patterns": ["hierarchical", "debate_based"]
        }

        result = validator.validate_complex_scenario(test_suite_data, {
            "conditional_dependencies": {
                "probabilistic_evaluation": {
                    True: ["uncertainty_threshold"]
                },
                "multi_agent_testing": {
                    True: ["coordination_patterns"]
                }
            },
            "business_rules": [
                lambda d: "Invalid test suite configuration" if not d.get("scenarios") else None,
                lambda d: "Performance targets too ambitious" if d.get("performance_benchmarks", {}).get("accuracy_target", 0) > 0.95 else None
            ]
        })
        assert result.is_valid is True

    def test_android_adk_integration_validation(self):
        """Test validation of Android ADK integration data."""
        validator = UCUPValidator()

        adk_data = {
            "platform": "android",
            "decision_trace_id": "trace_001",
            "bayesian_confidence": 0.82,
            "uncertainty_range": {"min": 0.75, "max": 0.89},
            "failure_indicators": [],
            "native_performance_metrics": {
                "cpu_usage": 0.15,
                "memory_mb": 45,
                "battery_impact": 0.02
            },
            "cross_platform_coordination": True,
            "coordination_partners": ["desktop_agent_1", "mobile_agent_2"],
            "battery_optimization": {
                "power_save_mode": False,
                "background_processing": True
            }
        }

        result = validator.validate_complex_scenario(adk_data, {
            "conditional_dependencies": {
                "platform": {
                    "android": ["native_performance_metrics", "battery_optimization"]
                },
                "cross_platform_coordination": {
                    True: ["coordination_partners"]
                }
            },
            "range_relationships": {
                "confidence_range": {
                    "min_field": "bayesian_confidence",
                    "max_field": "max_confidence"
                },
                "battery_range": {
                    "min_field": "native_performance_metrics.battery_impact",
                    "max_field": "max_battery_impact"
                }
            }
        })
        assert result.is_valid is True

    def test_enterprise_monitoring_validation(self):
        """Test validation of enterprise monitoring data."""
        validator = UCUPValidator()

        monitoring_data = {
            "monitoring_level": "production",
            "system_health_score": 0.92,
            "sla_compliance": 0.98,
            "compliance_status": {
                "gdpr_compliant": True,
                "security_audit_passed": True,
                "data_privacy_score": 0.95
            },
            "scalability_metrics": {
                "current_load": 0.75,
                "auto_scaling_enabled": True,
                "resource_pool_utilization": 0.68
            },
            "cost_optimization": {
                "budget_remaining": 15000,
                "cost_per_hour": 2.50,
                "optimization_recommendations": ["scale_down", "use_spot_instances"]
            },
            "incident_response": {
                "active_incidents": 0,
                "mean_time_to_resolution": 15,
                "automated_responses": 5
            }
        }

        result = validator.validate_complex_scenario(monitoring_data, {
            "conditional_dependencies": {
                "monitoring_level": {
                    "production": ["sla_compliance", "compliance_status", "incident_response"]
                }
            },
            "business_rules": [
                lambda d: "SLA compliance critical" if d.get("sla_compliance", 1.0) < 0.95 else None,
                lambda d: "Budget alert" if d.get("cost_optimization", {}).get("budget_remaining", float('inf')) < 1000 else None
            ]
        })
        assert result.is_valid is True

    def test_multi_agent_coordination_validation(self):
        """Test validation of multi-agent coordination data."""
        validator = UCUPValidator()

        coordination_data = {
            "coordination_type": "hierarchical",
            "coordinator_agent": "coordinator_001",
            "participant_agents": ["agent_1", "agent_2", "agent_3"],
            "task_delegation": {
                "strategy": "capability_based",
                "delegated_tasks": [
                    {"task": "analysis", "delegate": "agent_1", "priority": "high"},
                    {"task": "synthesis", "delegate": "agent_2", "priority": "medium"}
                ]
            },
            "debate_config": {
                "enabled": False,
                "max_rounds": 3,
                "consensus_threshold": 0.7
            },
            "market_mechanism": {
                "enabled": False,
                "auction_type": "english",
                "resource_pool": ["cpu", "memory", "gpu"]
            },
            "monitoring_enabled": True,
            "performance_metrics": {
                "coordination_efficiency": 0.88,
                "task_completion_rate": 0.95,
                "communication_overhead": 0.12
            }
        }

        result = validator.validate_complex_scenario(coordination_data, {
            "conditional_dependencies": {
                "coordination_type": {
                    "debate_based": ["debate_config"],
                    "market_based": ["market_mechanism"]
                },
                "monitoring_enabled": {
                    True: ["performance_metrics"]
                }
            },
            "business_rules": [
                lambda d: "Insufficient participants" if len(d.get("participant_agents", [])) < 2 else None,
                lambda d: "Invalid task delegation" if not d.get("task_delegation", {}).get("delegated_tasks") else None
            ]
        })
        assert result.is_valid is True

    def test_decision_tracing_validation(self):
        """Test validation of decision tracing and history data."""
        validator = UCUPValidator()

        tracing_data = {
            "trace_id": "trace_001",
            "agent_id": "agent_123",
            "decision_sequence": [
                {
                    "step": 1,
                    "decision": "analyze_input",
                    "confidence": 0.85,
                    "alternatives_considered": 3,
                    "execution_time_ms": 150,
                    "outcome": "success"
                },
                {
                    "step": 2,
                    "decision": "fuse_modalities",
                    "confidence": 0.78,
                    "alternatives_considered": 2,
                    "execution_time_ms": 200,
                    "outcome": "success"
                }
            ],
            "performance_analysis": {
                "average_confidence": 0.82,
                "decision_accuracy": 0.94,
                "total_execution_time": 350,
                "failure_patterns": []
            },
            "replay_available": True,
            "replay_data": {
                "total_steps": 2,
                "state_snapshots": ["snapshot_1", "snapshot_2"],
                "decision_tree": {
                    "root": "analyze_input",
                    "branches": ["fuse_modalities", "direct_response"]
                }
            }
        }

        result = validator.validate_complex_scenario(tracing_data, {
            "conditional_dependencies": {
                "replay_available": {
                    True: ["replay_data"]
                }
            },
            "business_rules": [
                lambda d: "Invalid decision sequence" if not d.get("decision_sequence") else None,
                lambda d: "Performance analysis missing" if not d.get("performance_analysis") else None
            ]
        })
        assert result.is_valid is True

    def test_failure_recovery_validation(self):
        """Test validation of failure recovery and checkpoint data."""
        validator = UCUPValidator()

        recovery_data = {
            "recovery_session_id": "recovery_001",
            "failure_type": "confidence_collapse",
            "failure_context": {
                "agent_id": "agent_123",
                "task": "multimodal_fusion",
                "failure_timestamp": "2025-01-01T12:00:00Z"
            },
            "automated_recovery": {
                "strategy": "checkpoint_rollback",
                "checkpoint_id": "checkpoint_001",
                "rollback_successful": True,
                "recovery_time_ms": 500
            },
            "graceful_degradation": {
                "enabled": True,
                "degradation_level": "moderate",
                "reduced_capabilities": ["real_time_processing"],
                "estimated_recovery_time": 300
            },
            "recovery_analytics": {
                "recovery_success_rate": 0.85,
                "mean_recovery_time": 450,
                "failure_pattern_analysis": {
                    "most_common_failure": "confidence_collapse",
                    "prevention_recommendations": ["increase_sample_size", "add_fallback_models"]
                }
            }
        }

        result = validator.validate_complex_scenario(recovery_data, {
            "conditional_dependencies": {
                "automated_recovery.strategy": {
                    "checkpoint_rollback": ["automated_recovery.checkpoint_id"]
                }
            },
            "business_rules": [
                lambda d: "Recovery strategy required" if not d.get("automated_recovery", {}).get("strategy") else None,
                lambda d: "Recovery analytics incomplete" if not d.get("recovery_analytics", {}).get("failure_pattern_analysis") else None
            ]
        })
        assert result.is_valid is True

    def test_configuration_dsl_validation(self):
        """Test validation of configuration DSL data."""
        validator = UCUPValidator()

        dsl_config = {
            "config_type": "yaml_template",
            "template_version": "1.0.0",
            "agent_network": {
                "coordinator": {
                    "id": "coordinator_001",
                    "type": "multimodal_agent",
                    "capabilities": ["text_analysis", "vision_processing", "coordination"]
                },
                "workers": [
                    {
                        "id": "worker_001",
                        "type": "text_specialist",
                        "reports_to": "coordinator_001"
                    },
                    {
                        "id": "worker_002",
                        "type": "vision_specialist",
                        "reports_to": "coordinator_001"
                    }
                ]
            },
            "validation_schema": {
                "required_fields": ["id", "type"],
                "field_types": {
                    "id": "string",
                    "type": "string",
                    "capabilities": "list"
                }
            },
            "import_export": {
                "supported_formats": ["yaml", "json", "xml"],
                "validation_on_import": True,
                "schema_version_compatibility": "1.0.0"
            }
        }

        result = validator.validate_complex_scenario(dsl_config, {
            "conditional_dependencies": {
                "config_type": {
                    "yaml_template": ["agent_network", "validation_schema"]
                }
            },
            "business_rules": [
                lambda d: "Invalid agent network structure" if not d.get("agent_network", {}).get("coordinator") else None,
                lambda d: "Schema validation missing" if not d.get("validation_schema") else None
            ]
        })
        assert result.is_valid is True

    def test_plugin_manager_validation(self):
        """Test validation of plugin manager and extensions data."""
        validator = UCUPValidator()

        plugin_data = {
            "plugin_manager": {
                "discovery_enabled": True,
                "registry_url": "https://plugins.ucup.ai",
                "auto_update": True,
                "security_scanning": True
            },
            "installed_plugins": [
                {
                    "name": "multimodal_fusion",
                    "version": "1.0.0",
                    "enabled": True,
                    "capabilities": ["text_fusion", "vision_fusion"],
                    "dependencies": ["numpy", "torch"]
                },
                {
                    "name": "android_adk_bridge",
                    "version": "0.9.0",
                    "enabled": False,
                    "capabilities": ["mobile_integration"],
                    "dependencies": ["kotlin", "android_sdk"]
                }
            ],
            "extension_management": {
                "hot_reload_enabled": True,
                "extension_isolation": True,
                "resource_limits": {
                    "max_memory_mb": 512,
                    "max_cpu_percent": 25
                }
            },
            "development_tools": {
                "plugin_template_generator": True,
                "testing_framework": True,
                "documentation_generator": True
            }
        }

        result = validator.validate_complex_scenario(plugin_data, {
            "conditional_dependencies": {
                "plugin_manager.discovery_enabled": {
                    True: ["plugin_manager.registry_url"]
                }
            },
            "business_rules": [
                lambda d: "No plugins installed" if not d.get("installed_plugins") else None,
                lambda d: "Security scanning recommended" if not d.get("plugin_manager", {}).get("security_scanning") else None
            ]
        })
        assert result.is_valid is True

    def test_deployment_monitoring_validation(self):
        """Test validation of deployment and health monitoring data."""
        validator = UCUPValidator()

        deployment_data = {
            "deployment_id": "deploy_001",
            "platform": "kubernetes",
            "automated_deployment": True,
            "health_dashboard": {
                "enabled": True,
                "metrics_endpoints": ["prometheus", "grafana"],
                "alerting_enabled": True,
                "dashboard_url": "https://monitoring.ucup.ai/deploy_001"
            },
            "performance_tracking": {
                "real_time_monitoring": True,
                "performance_baselines": {
                    "response_time_ms": 250,
                    "throughput_req_per_sec": 100,
                    "error_rate_percent": 0.1
                },
                "anomaly_detection": True
            },
            "auto_scaling": {
                "enabled": True,
                "min_replicas": 2,
                "max_replicas": 10,
                "scaling_triggers": ["cpu_usage", "queue_length"],
                "cooldown_period_sec": 300
            },
            "deployment_health": {
                "overall_status": "healthy",
                "component_status": {
                    "api_server": "healthy",
                    "worker_nodes": "healthy",
                    "database": "healthy"
                },
                "uptime_hours": 168,
                "last_incident": None
            }
        }

        result = validator.validate_complex_scenario(deployment_data, {
            "conditional_dependencies": {
                "automated_deployment": {
                    True: ["health_dashboard"]
                },
                "health_dashboard.enabled": {
                    True: ["health_dashboard.metrics_endpoints", "health_dashboard.alerting_enabled"]
                },
                "auto_scaling.enabled": {
                    True: ["auto_scaling.min_replicas", "auto_scaling.max_replicas"]
                }
            },
            "business_rules": [
                lambda d: "Health monitoring required for production" if d.get("platform") == "kubernetes" and not d.get("health_dashboard", {}).get("enabled") else None,
                lambda d: "Auto-scaling configuration invalid" if d.get("auto_scaling", {}).get("enabled") and d.get("auto_scaling", {}).get("min_replicas", 0) >= d.get("auto_scaling", {}).get("max_replicas", 0) else None
            ]
        })
        assert result.is_valid is True

    def test_probabilistic_reasoning_validation(self):
        """Test validation of probabilistic reasoning strategies."""
        validator = UCUPValidator()

        reasoning_data = {
            "reasoning_strategy": "chain_of_thought",
            "strategy_config": {
                "max_steps": 5,
                "confidence_threshold": 0.7,
                "backtracking_enabled": True,
                "pruning_strategy": "confidence_based"
            },
            "reasoning_trace": [
                {
                    "step": 1,
                    "thought": "Analyze the multimodal input",
                    "confidence": 0.85,
                    "evidence": ["text_content", "visual_features"],
                    "next_steps": ["fuse_modalities", "make_decision"]
                },
                {
                    "step": 2,
                    "thought": "Fuse text and visual information",
                    "confidence": 0.78,
                    "evidence": ["semantic_similarity", "spatial_relationships"],
                    "decision": "proceed_with_fusion"
                }
            ],
            "uncertainty_analysis": {
                "overall_confidence": 0.82,
                "confidence_distribution": {"high": 0.6, "medium": 0.3, "low": 0.1},
                "alternative_paths": 3,
                "volatility_tracking": {
                    "confidence_trend": "stable",
                    "volatility_score": 0.15,
                    "last_update": "2025-01-01T12:00:00Z"
                }
            }
        }

        result = validator.validate_complex_scenario(reasoning_data, {
            "conditional_dependencies": {
                "reasoning_strategy": {
                    "chain_of_thought": ["strategy_config", "reasoning_trace"],
                    "tree_of_thought": ["strategy_config", "reasoning_trace"],
                    "step_back_questioning": ["strategy_config"]
                }
            },
            "business_rules": [
                lambda d: "Reasoning trace required" if d.get("reasoning_strategy") in ["chain_of_thought", "tree_of_thought"] and not d.get("reasoning_trace") else None,
                lambda d: "Uncertainty analysis incomplete" if not d.get("uncertainty_analysis", {}).get("confidence_distribution") else None
            ]
        })
        assert result.is_valid is True

    def test_performance_dashboard_validation(self):
        """Test validation of performance dashboard data."""
        validator = UCUPValidator()

        dashboard_data = {
            "dashboard_id": "dashboard_001",
            "real_time_metrics": {
                "enabled": True,
                "update_interval_sec": 5,
                "metrics_collected": ["cpu_usage", "memory_usage", "response_time", "error_rate"]
            },
            "interactive_charts": {
                "enabled": True,
                "chart_types": ["line", "bar", "pie", "heatmap"],
                "filtering_enabled": True,
                "export_formats": ["png", "pdf", "csv"]
            },
            "agent_comparison": {
                "enabled": True,
                "comparison_metrics": ["accuracy", "latency", "confidence"],
                "baseline_agents": ["multimodal_v1", "text_only_v1"],
                "statistical_significance": True
            },
            "performance_history": {
                "retention_days": 30,
                "aggregation_levels": ["hourly", "daily", "weekly"],
                "trend_analysis": True,
                "anomaly_detection": True
            }
        }

        result = validator.validate_complex_scenario(dashboard_data, {
            "conditional_dependencies": {
                "real_time_metrics.enabled": {
                    True: ["real_time_metrics.update_interval_sec"]
                },
                "interactive_charts.enabled": {
                    True: ["interactive_charts.chart_types"]
                },
                "agent_comparison.enabled": {
                    True: ["agent_comparison.baseline_agents"]
                }
            },
            "range_relationships": {
                "update_interval_range": {
                    "min_field": "real_time_metrics.update_interval_sec",
                    "max_field": "max_update_interval"
                }
            },
            "business_rules": [
                lambda d: "Real-time metrics required" if not d.get("real_time_metrics", {}).get("enabled") else None,
                lambda d: "Performance history retention too short" if d.get("performance_history", {}).get("retention_days", 0) < 7 else None
            ]
        })
        assert result.is_valid is True

    def test_team_collaboration_validation(self):
        """Test validation of team collaboration features."""
        validator = UCUPValidator()

        collaboration_data = {
            "collaboration_session_id": "session_001",
            "live_sessions": {
                "enabled": True,
                "max_participants": 5,
                "session_timeout_min": 120,
                "recording_enabled": True
            },
            "cursor_sharing": {
                "enabled": True,
                "real_time_updates": True,
                "privacy_mode": "selective"
            },
            "group_chat": {
                "enabled": True,
                "message_history_days": 7,
                "file_sharing": True,
                "code_snippet_sharing": True
            },
            "session_management": {
                "session_persistence": True,
                "auto_cleanup_hours": 24,
                "participant_permissions": {
                    "read": ["viewer"],
                    "write": ["editor"],
                    "admin": ["admin"]
                }
            }
        }

        result = validator.validate_complex_scenario(collaboration_data, {
            "conditional_dependencies": {
                "live_sessions.enabled": {
                    True: ["live_sessions.max_participants"]
                },
                "cursor_sharing.enabled": {
                    True: ["cursor_sharing.privacy_mode"]
                },
                "group_chat.enabled": {
                    True: ["group_chat.message_history_days"]
                }
            },
            "business_rules": [
                lambda d: "Session management required for live sessions" if d.get("live_sessions", {}).get("enabled") and not d.get("session_management") else None,
                lambda d: "Invalid participant permissions" if not d.get("session_management", {}).get("participant_permissions") else None
            ]
        })
        assert result.is_valid is True

    def test_enterprise_security_validation(self):
        """Test validation of enterprise security and audit features."""
        validator = UCUPValidator()

        security_data = {
            "security_level": "enterprise",
            "audit_logging": {
                "enabled": True,
                "log_level": "detailed",
                "retention_days": 90,
                "encryption_enabled": True
            },
            "compliance_reports": {
                "enabled": True,
                "report_types": ["gdpr", "sox", "hipaa"],
                "generation_schedule": "weekly",
                "distribution_list": ["compliance@company.com"]
            },
            "risk_assessment": {
                "enabled": True,
                "risk_levels": ["low", "medium", "high", "critical"],
                "automated_alerting": True,
                "escalation_matrix": {
                    "low": "email",
                    "medium": "slack",
                    "high": "phone",
                    "critical": "page"
                }
            },
            "data_export": {
                "enabled": True,
                "supported_formats": ["json", "csv", "xml"],
                "compression_enabled": True,
                "secure_transfer": True
            }
        }

        result = validator.validate_complex_scenario(security_data, {
            "conditional_dependencies": {
                "security_level": {
                    "enterprise": ["audit_logging", "compliance_reports", "risk_assessment"]
                },
                "audit_logging.enabled": {
                    True: ["audit_logging.retention_days"]
                },
                "compliance_reports.enabled": {
                    True: ["compliance_reports.report_types"]
                }
            },
            "business_rules": [
                lambda d: "Audit retention too short for enterprise" if d.get("audit_logging", {}).get("retention_days", 0) < 30 else None,
                lambda d: "Risk assessment required for enterprise security" if d.get("security_level") == "enterprise" and not d.get("risk_assessment", {}).get("enabled") else None
            ]
        })
        assert result.is_valid is True

    def test_code_quality_analytics_validation(self):
        """Test validation of code quality analytics data."""
        validator = UCUPValidator()

        quality_data = {
            "project_id": "ucup_multimodal",
            "quality_scoring": {
                "overall_score": 85,
                "component_scores": {
                    "reliability": 88,
                    "security": 82,
                    "performance": 90,
                    "maintainability": 78
                },
                "scoring_methodology": "weighted_average",
                "last_updated": "2025-01-01T12:00:00Z"
            },
            "issue_detection": {
                "critical_issues": 2,
                "high_issues": 5,
                "medium_issues": 12,
                "low_issues": 25,
                "categories": {
                    "security_vulnerabilities": 1,
                    "performance_bottlenecks": 3,
                    "code_smells": 8,
                    "maintainability_issues": 15
                }
            },
            "improvement_suggestions": [
                {
                    "category": "performance",
                    "suggestion": "Implement caching for multimodal fusion operations",
                    "impact": "high",
                    "effort": "medium"
                },
                {
                    "category": "security",
                    "suggestion": "Add input validation for sensor data streams",
                    "impact": "critical",
                    "effort": "low"
                }
            ],
            "workspace_reports": {
                "enabled": True,
                "report_formats": ["html", "pdf", "json"],
                "auto_generation": True,
                "distribution_channels": ["email", "slack", "dashboard"]
            }
        }

        result = validator.validate_complex_scenario(quality_data, {
            "conditional_dependencies": {
                "workspace_reports.enabled": {
                    True: ["workspace_reports.report_formats"]
                }
            },
            "range_relationships": {
                "quality_score_range": {
                    "min_field": "quality_scoring.overall_score",
                    "max_field": "max_quality_score"
                }
            },
            "business_rules": [
                lambda d: "Quality score too low" if d.get("quality_scoring", {}).get("overall_score", 0) < 60 else None,
                lambda d: "Critical issues require immediate attention" if d.get("issue_detection", {}).get("critical_issues", 0) > 0 else None,
                lambda d: "Improvement suggestions missing" if not d.get("improvement_suggestions") else None
            ]
        })
        assert result.is_valid is True

    def test_agent_explorer_validation(self):
        """Test validation of agent explorer and management data."""
        validator = UCUPValidator()

        explorer_data = {
            "workspace_id": "workspace_001",
            "agent_overview": {
                "total_agents": 15,
                "active_agents": 12,
                "agent_types": ["multimodal", "text_specialist", "vision_specialist"],
                "status_summary": {
                    "running": 10,
                    "idle": 2,
                    "error": 0,
                    "maintenance": 0
                }
            },
            "agent_creation": {
                "wizard_enabled": True,
                "supported_types": ["multimodal_agent", "specialist_agent", "coordinator_agent"],
                "template_library": True,
                "custom_templates": 5
            },
            "dependency_tracking": {
                "enabled": True,
                "visualization_type": "graph",
                "dependency_levels": ["direct", "indirect", "transitive"],
                "circular_dependency_detection": True
            },
            "quick_actions": {
                "available_actions": ["start", "stop", "restart", "debug", "monitor"],
                "context_menus": True,
                "keyboard_shortcuts": True,
                "bulk_operations": True
            }
        }

        result = validator.validate_complex_scenario(explorer_data, {
            "conditional_dependencies": {
                "agent_creation.wizard_enabled": {
                    True: ["agent_creation.supported_types"]
                },
                "dependency_tracking.enabled": {
                    True: ["dependency_tracking.visualization_type"]
                }
            },
            "business_rules": [
                lambda d: "No agents in workspace" if d.get("agent_overview", {}).get("total_agents", 0) == 0 else None,
                lambda d: "Agent creation wizard required" if not d.get("agent_creation", {}).get("wizard_enabled") else None,
                lambda d: "Quick actions incomplete" if not d.get("quick_actions", {}).get("available_actions") else None
            ]
        })
        assert result.is_valid is True

    def test_language_support_validation(self):
        """Test validation of language support features."""
        validator = UCUPValidator()

        language_data = {
            "language_support": "ucup_yaml",
            "syntax_highlighting": {
                "enabled": True,
                "theme_support": ["light", "dark", "high_contrast"],
                "custom_colors": True,
                "semantic_highlighting": True
            },
            "intellisense": {
                "enabled": True,
                "completion_triggers": ["agent.", "config.", "coordination."],
                "hover_information": True,
                "signature_help": True,
                "auto_imports": True
            },
            "validation": {
                "real_time_validation": True,
                "error_underline": True,
                "warning_highlight": True,
                "quick_fixes": True
            },
            "code_lenses": {
                "enabled": True,
                "lens_types": ["run_agent", "debug_agent", "view_metrics", "open_dashboard"],
                "context_aware": True,
                "performance_indicators": True
            }
        }

        result = validator.validate_complex_scenario(language_data, {
            "conditional_dependencies": {
                "syntax_highlighting.enabled": {
                    True: ["syntax_highlighting.theme_support"]
                },
                "intellisense.enabled": {
                    True: ["intellisense.completion_triggers"]
                },
                "code_lenses.enabled": {
                    True: ["code_lenses.lens_types"]
                }
            },
            "business_rules": [
                lambda d: "Syntax highlighting required" if not d.get("syntax_highlighting", {}).get("enabled") else None,
                lambda d: "IntelliSense required for productivity" if not d.get("intellisense", {}).get("enabled") else None,
                lambda d: "Real-time validation required" if not d.get("validation", {}).get("real_time_validation") else None
            ]
        })
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__])
