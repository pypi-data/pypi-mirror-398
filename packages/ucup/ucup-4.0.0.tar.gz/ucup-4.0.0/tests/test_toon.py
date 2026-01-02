"""
Comprehensive tests for UCUP TOON (Token-Oriented Object Notation) library.

Tests TOON formatting, token optimization, schema handling, and cost savings.
"""

import json
import pytest
from typing import Dict, List, Any

from ucup import (
    ToonFormatter,
    ToonSchema,
    ToonConversionResult,
    TokenMetrics,
)
from ucup.errors import UCUPValidationError


class TestToonFormatter:
    """Test TOON formatter functionality."""

    @pytest.fixture
    def formatter(self):
        """Create TOON formatter instance."""
        return ToonFormatter()

    @pytest.fixture
    def sample_agent_data(self) -> Dict[str, Any]:
        """Sample agent decision data for testing."""
        return {
            "session_id": "test_session_001",
            "agent_type": "trading_bot",
            "decisions": [
                {
                    "decision_id": "dec_001",
                    "step": 1,
                    "action": "analyze_market_data",
                    "confidence_score": 0.87,
                    "reasoning": "Clear upward trend detected",
                    "alternatives": ["hold_position", "sell_assets"],
                    "timestamp": "2025-01-08T14:30:00Z",
                    "processing_time_ms": 1250
                },
                {
                    "decision_id": "dec_002",
                    "step": 2,
                    "action": "execute_trade",
                    "confidence_score": 0.76,
                    "reasoning": "Risk within acceptable parameters",
                    "alternatives": ["wait_for_better_setup"],
                    "timestamp": "2025-01-08T14:31:15Z",
                    "processing_time_ms": 890
                }
            ],
            "performance_metrics": {
                "total_return_pct": 2.34,
                "sharpe_ratio": 1.67,
                "max_drawdown_pct": 0.89
            }
        }

    def test_toon_formatter_creation(self, formatter):
        """Test creating TOON formatter."""
        assert formatter is not None
        assert hasattr(formatter, 'schemas')
        assert hasattr(formatter, 'conversion_history')
        assert 'decision_trace' in formatter.schemas

    def test_format_choice_auto(self, formatter, sample_agent_data):
        """Test automatic format choice."""
        result = formatter.format_with_choice(sample_agent_data, preferred_format="auto")

        assert result.format_choice in ["toon", "json"]
        assert result.metrics.savings_percentage >= 0
        assert result.metrics.compression_ratio >= 1.0
        assert len(result.recommendations) > 0

    def test_format_choice_toon(self, formatter, sample_agent_data):
        """Test forced TOON format."""
        result = formatter.format_with_choice(sample_agent_data, preferred_format="toon")

        assert result.format_choice == "toon"
        assert result.toon_output is not None
        assert result.metrics.toon_tokens > 0

    def test_format_choice_json(self, formatter, sample_agent_data):
        """Test forced JSON format."""
        result = formatter.format_with_choice(sample_agent_data, preferred_format="json")

        assert result.format_choice == "json"
        assert result.json_output is not None
        assert result.metrics.json_tokens > 0

    def test_json_to_toon_conversion(self, formatter, sample_agent_data):
        """Test JSON to TOON conversion."""
        result = formatter.json_to_toon(sample_agent_data)

        assert result.toon_output is not None
        assert result.metrics.toon_tokens < result.metrics.json_tokens
        assert result.metrics.savings_percentage > 0
        assert len(result.recommendations) > 0

    def test_uniform_array_table_format(self, formatter):
        """Test table format for uniform object arrays."""
        uniform_data = [
            {"name": "Alice", "age": 30, "city": "NYC", "salary": 75000},
            {"name": "Bob", "age": 25, "city": "LA", "salary": 68000},
            {"name": "Charlie", "age": 35, "city": "Chicago", "salary": 82000}
        ]

        result = formatter.json_to_toon(uniform_data)

        # Should use table format for uniform arrays
        assert "|" in result.toon_output  # Table separator
        assert "name" in result.toon_output
        assert "age" in result.toon_output

    def test_token_metrics_calculation(self, formatter):
        """Test token metrics calculation."""
        json_data = {"test": "value", "number": 123, "array": [1, 2, 3]}
        result = formatter.json_to_toon(json_data)

        metrics = result.metrics

        assert metrics.json_tokens > 0
        assert metrics.toon_tokens > 0
        assert metrics.savings_percentage >= 0
        assert metrics.compression_ratio >= 1.0
        assert metrics.estimated_cost_savings >= 0

    def test_schema_creation(self, formatter, sample_agent_data):
        """Test custom schema creation."""
        schema = formatter.create_custom_schema(
            schema_name="test_agent",
            sample_data=sample_agent_data,
            description="Test agent schema"
        )

        assert schema.name == "test_agent"
        assert schema.description == "Test agent schema"
        assert len(schema.fields) > 0
        assert "session_id" in schema.fields

        # Schema should be added to formatter
        assert "test_agent" in formatter.schemas

    def test_schema_based_optimization(self, formatter):
        """Test schema-based TOON optimization."""
        # Create a schema for decision data
        decision_schema = ToonSchema(
            name="decision_optimization",
            description="Optimized decision schema",
            fields=["decision_id", "action", "confidence_score"],
            array_fields=["decisions"],
            optimizations=["compact_arrays", "omit_nulls", "short_field_names"]
        )

        formatter.schemas["decision_optimization"] = decision_schema

        data = {
            "decisions": [
                {"decision_id": "d1", "action": "buy", "confidence_score": 0.85, "notes": None},
                {"decision_id": "d2", "action": "sell", "confidence_score": 0.72, "notes": None}
            ]
        }

        result = formatter.json_to_toon(data, schema_name="decision_optimization")

        # Should apply optimizations
        assert result.schema_used == decision_schema
        assert "notes" not in result.toon_output  # omit_nulls optimization

    def test_token_savings_report(self, formatter):
        """Test token savings report generation."""
        # Add some conversions to history
        for i in range(3):
            data = {"test": f"value_{i}", "count": i}
            formatter.json_to_toon(data)

        report = formatter.get_token_savings_report()

        assert "total_conversions" in report
        assert "average_savings_percentage" in report
        assert "total_token_savings" in report
        assert report["total_conversions"] == 3
        assert report["average_savings_percentage"] >= 0

    def test_invalid_format_choice(self, formatter):
        """Test invalid format choice handling."""
        data = {"test": "value"}

        with pytest.raises(UCUPValidationError):
            formatter.format_with_choice(data, preferred_format="invalid")

    def test_empty_data_handling(self, formatter):
        """Test handling of empty data."""
        result = formatter.json_to_toon({})

        assert result.toon_output == ""
        assert result.metrics.json_tokens == 0
        assert result.metrics.toon_tokens == 0

    def test_nested_object_formatting(self, formatter):
        """Test formatting of deeply nested objects."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "count": 42
                    },
                    "array": [1, 2, {"nested": "item"}]
                }
            }
        }

        result = formatter.json_to_toon(nested_data)

        # Should format nested structure properly
        assert "level1:" in result.toon_output
        assert "level2:" in result.toon_output
        assert "level3:" in result.toon_output

    def test_array_of_primitives(self, formatter):
        """Test formatting arrays of primitive values."""
        primitive_array = ["apple", "banana", "cherry", 1, 2, 3, True, False]

        result = formatter.json_to_toon(primitive_array)

        # Should use YAML-style list format
        assert "- apple" in result.toon_output
        assert "- banana" in result.toon_output
        assert "- 1" in result.toon_output


class TestToonSchema:
    """Test TOON schema functionality."""

    def test_schema_creation(self):
        """Test creating TOON schemas."""
        schema = ToonSchema(
            name="test_schema",
            description="Test schema",
            fields=["id", "name", "value"],
            array_fields=["items"],
            optimizations=["compact_arrays", "omit_nulls"]
        )

        assert schema.name == "test_schema"
        assert schema.description == "Test schema"
        assert "id" in schema.fields
        assert "items" in schema.array_fields
        assert "compact_arrays" in schema.optimizations

    def test_schema_validation(self):
        """Test schema validation."""
        # Valid schema
        schema = ToonSchema(
            name="valid_schema",
            fields=["field1", "field2"],
            array_fields=["array1"]
        )
        assert schema is not None

        # Schema without required name should still work (optional)
        schema2 = ToonSchema(
            fields=["field1"]
        )
        assert schema2 is not None


class TestTokenMetrics:
    """Test token metrics functionality."""

    def test_metrics_creation(self):
        """Test creating token metrics."""
        metrics = TokenMetrics(
            json_tokens=100,
            toon_tokens=80
        )

        assert metrics.json_tokens == 100
        assert metrics.toon_tokens == 80
        assert metrics.savings_percentage == 20.0
        assert metrics.compression_ratio == 1.25
        assert metrics.estimated_cost_savings == 0.00004  # (20/1000) * 0.002

    def test_metrics_calculation(self):
        """Test automatic metrics calculation."""
        metrics = TokenMetrics(json_tokens=200, toon_tokens=120)
        metrics.calculate_savings()

        assert metrics.savings_percentage == 40.0
        assert metrics.compression_ratio == 200/120
        assert metrics.estimated_cost_savings == (200-120) * 0.000002

    def test_zero_token_handling(self):
        """Test handling of zero tokens."""
        metrics = TokenMetrics(json_tokens=0, toon_tokens=0)
        metrics.calculate_savings()

        assert metrics.savings_percentage == 0.0
        assert metrics.compression_ratio == 1.0


class TestToonConversionResult:
    """Test TOON conversion result."""

    def test_result_creation(self):
        """Test creating conversion results."""
        result = ToonConversionResult(
            original_json='{"test": "value"}',
            toon_output='test: value',
            json_output='{\n  "test": "value"\n}',
            metrics=TokenMetrics(json_tokens=10, toon_tokens=8),
            recommendations=["Consider using TOON for better efficiency"]
        )

        assert result.original_json == '{"test": "value"}'
        assert result.toon_output == 'test: value'
        assert result.metrics.savings_percentage == 20.0
        assert len(result.recommendations) == 1


class TestToonIntegration:
    """Integration tests for TOON functionality."""

    def test_ucup_decision_trace_toon(self):
        """Test converting UCUP decision traces to TOON."""
        formatter = ToonFormatter()

        # Simulate UCUP decision trace
        decision_trace = {
            "session_id": "trace_123",
            "decisions": [
                {
                    "decision_id": "d1",
                    "action": "analyze",
                    "confidence": 0.85,
                    "timestamp": "2025-01-08T10:00:00Z",
                    "token_usage": 150
                },
                {
                    "decision_id": "d2",
                    "action": "decide",
                    "confidence": 0.92,
                    "timestamp": "2025-01-08T10:01:00Z",
                    "token_usage": 200
                }
            ],
            "total_tokens": 350,
            "successful_decisions": 2
        }

        result = formatter.json_to_toon(decision_trace, schema_name="decision_trace")

        assert result.metrics.savings_percentage > 0
        assert "session_id:" in result.toon_output
        assert "decisions:" in result.toon_output

    def test_probabilistic_analysis_toon(self):
        """Test converting probabilistic analysis to TOON."""
        formatter = ToonFormatter()

        prob_data = {
            "analysis_type": "confidence_distribution",
            "confidence_scores": [0.85, 0.92, 0.78, 0.89, 0.76],
            "entropy": 0.892,
            "decision_pressure": 0.42,
            "risk_indicators": [
                {"level": "low", "probability": 0.3},
                {"level": "medium", "probability": 0.5},
                {"level": "high", "probability": 0.2}
            ]
        }

        result = formatter.json_to_toon(prob_data, schema_name="probabilistic_analysis")

        assert result.metrics.toon_tokens < result.metrics.json_tokens
        assert "confidence_scores:" in result.toon_output
        assert "risk_indicators:" in result.toon_output

    def test_cost_savings_calculation(self):
        """Test cost savings calculations."""
        formatter = ToonFormatter()

        # Large dataset simulation
        large_data = {
            "records": [
                {"id": i, "name": f"item_{i}", "value": i * 10, "category": f"cat_{i%5}"}
                for i in range(100)
            ],
            "metadata": {
                "total_records": 100,
                "categories": ["cat_0", "cat_1", "cat_2", "cat_3", "cat_4"],
                "processing_time": 45.67,
                "quality_score": 0.89
            }
        }

        result = formatter.json_to_toon(large_data)

        # Should show significant savings for structured data
        assert result.metrics.savings_percentage > 10

        # Estimate monthly savings
        monthly_conversions = 10000
        avg_savings_pct = result.metrics.savings_percentage / 100
        estimated_monthly_tokens = monthly_conversions * result.metrics.json_tokens
        estimated_tokens_saved = estimated_monthly_tokens * avg_savings_pct

        assert estimated_tokens_saved > 0

    def test_toon_to_json_roundtrip(self):
        """Test TOON to JSON conversion (basic)."""
        formatter = ToonFormatter()

        original_data = {
            "name": "test",
            "value": 123,
            "items": ["a", "b", "c"],
            "nested": {"key": "value"}
        }

        result = formatter.json_to_toon(original_data)
        reconstructed = formatter.toon_to_json(result.toon_output)

        # Basic structure should be preserved (exact match depends on TOON parser completeness)
        assert isinstance(reconstructed, dict)
        assert "name" in reconstructed
        assert "value" in reconstructed

    def test_performance_optimization(self):
        """Test performance optimizations."""
        formatter = ToonFormatter()

        # Test with different optimization settings
        data = {
            "users": [
                {"id": 1, "name": "Alice", "email": None, "active": True},
                {"id": 2, "name": "Bob", "email": None, "active": False},
                {"id": 3, "name": "Charlie", "email": "charlie@test.com", "active": True}
            ],
            "total_count": 3,
            "last_updated": "2025-01-08T12:00:00Z"
        }

        # Test with optimization
        result_optimized = formatter.json_to_toon(data, optimize=True)

        # Should omit null email fields and use compact format
        assert "email" not in result_optimized.toon_output or "null" not in result_optimized.toon_output
        assert result_optimized.metrics.savings_percentage > 0


if __name__ == "__main__":
    pytest.main([__file__])
