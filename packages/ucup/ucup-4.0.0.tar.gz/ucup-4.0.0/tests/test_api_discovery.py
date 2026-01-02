"""
Tests for UCUP Smart API Discovery & Auto-Import System.

This module provides comprehensive testing for the intelligent API discovery,
metadata-enhanced exports, and automatic import suggestions functionality.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
import inspect
import importlib

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ucup.api_discovery import (
    APIDiscoveryEngine,
    ComponentMetadata,
    ExportMetadata,
    discover_ucup_api,
    get_smart_import_suggestions,
    search_ucup_components,
    get_components_by_category,
    generate_module_exports,
    create_auto_import_map,
    enhance_type_hints_for_module,
    get_discovery_engine
)


class TestComponentMetadata:
    """Test ComponentMetadata dataclass."""

    def test_component_metadata_creation(self):
        """Test creating ComponentMetadata instance."""
        metadata = ComponentMetadata(
            name="TestComponent",
            module="ucup.test",
            category="testing",
            description="Test component",
            version="1.0.0",
            stability="stable",
            examples=["example = TestComponent()"],
            tags={"class", "test"}
        )

        assert metadata.name == "TestComponent"
        assert metadata.module == "ucup.test"
        assert metadata.category == "testing"
        assert metadata.description == "Test component"
        assert metadata.version == "1.0.0"
        assert metadata.stability == "stable"
        assert "example = TestComponent()" in metadata.examples
        assert "class" in metadata.tags
        assert "test" in metadata.tags

    def test_component_metadata_defaults(self):
        """Test ComponentMetadata default values."""
        metadata = ComponentMetadata(
            name="TestComponent",
            module="ucup.test",
            category="testing",
            description="Test component"
        )

        assert metadata.version == "1.0.0"
        assert metadata.stability == "stable"
        assert metadata.dependencies == []
        assert metadata.related_components == []
        assert metadata.examples == []
        assert metadata.confidence_score == 1.0
        assert metadata.usage_patterns == []
        assert metadata.tags == set()


class TestExportMetadata:
    """Test ExportMetadata dataclass."""

    def test_export_metadata_creation(self):
        """Test creating ExportMetadata instance."""
        component_meta = ComponentMetadata(
            name="TestComponent",
            module="ucup.test",
            category="testing",
            description="Test component"
        )

        export_meta = ExportMetadata(
            component=component_meta,
            export_name="TestComponent",
            is_class=True,
            is_function=False,
            signature="TestComponent()",
            docstring="Test component class"
        )

        assert export_meta.component == component_meta
        assert export_meta.export_name == "TestComponent"
        assert export_meta.is_class is True
        assert export_meta.is_function is False
        assert export_meta.signature == "TestComponent()"
        assert export_meta.docstring == "Test component class"


class TestAPIDiscoveryEngine:
    """Test APIDiscoveryEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = APIDiscoveryEngine()

    def test_engine_initialization(self):
        """Test engine initialization."""
        assert self.engine.base_module == "ucup"
        assert self.engine.discovered_components == {}
        assert self.engine.export_registry == {}
        assert self.engine.module_cache == {}

    @patch('importlib.import_module')
    def test_discover_core_components(self, mock_import):
        """Test discovering core components."""
        # Mock the ucup module
        mock_module = Mock()
        mock_module.__name__ = "ucup"
        mock_module.__all__ = ["TestComponent"]

        # Mock TestComponent
        mock_component = Mock()
        mock_component.__name__ = "TestComponent"
        mock_component.__doc__ = "Test component class"

        mock_module.TestComponent = mock_component
        mock_import.return_value = mock_module

        self.engine._discover_core_components()

        # Verify component was discovered
        assert "TestComponent" in self.engine.discovered_components
        component = self.engine.discovered_components["TestComponent"]
        assert component.name == "TestComponent"
        assert component.module == "ucup"
        assert component.description == "Test component class"

    def test_infer_category_from_module(self):
        """Test category inference from module names."""
        test_cases = [
            ("probabilistic", "probabilistic"),
            ("coordination", "coordination"),
            ("testing", "testing"),
            ("multimodal", "multimodal"),
            ("deployment", "deployment"),
            ("unknown_module", "core")
        ]

        for module_name, expected_category in test_cases:
            result = self.engine._infer_category_from_module(module_name)
            assert result == expected_category

    def test_get_description(self):
        """Test description extraction from objects."""
        # Test class with docstring
        class TestClass:
            """Test class docstring."""
            pass

        result = self.engine._get_description(TestClass)
        assert result == "Test class docstring."

        # Test class without docstring
        class NoDocClass:
            pass

        result = self.engine._get_description(NoDocClass)
        assert result == "NoDocClass class for UCUP framework"

        # Test function
        def test_function():
            """Test function docstring."""
            pass

        result = self.engine._get_description(test_function)
        assert result == "Test function docstring."

    def test_infer_stability(self):
        """Test stability inference."""
        class StableClass:
            pass

        class ExperimentalClass:
            pass

        # Mock experimental class name
        ExperimentalClass.__name__ = "ExperimentalClass"

        result = self.engine._infer_stability(StableClass)
        assert result == "stable"

        result = self.engine._infer_stability(ExperimentalClass)
        assert result == "experimental"  # Detected from class name

    def test_extract_examples(self):
        """Test example extraction from docstrings."""
        docstring = """
        Test class.

        Examples:
            >>> obj = TestClass()
            >>> result = obj.do_something()

        More content here.
        """

        class TestClass:
            pass

        result = self.engine._extract_examples(TestClass)
        # Should extract examples from docstring

    def test_generate_tags(self):
        """Test tag generation."""
        class TestClass:
            pass

        def test_function():
            pass

        # Test class tags
        tags = self.engine._generate_tags(TestClass, "testing")
        assert "testing" in tags
        assert "class" in tags

        # Test function tags
        tags = self.engine._generate_tags(test_function, "core")
        assert "core" in tags
        assert "function" in tags

    def test_get_components_by_category(self):
        """Test filtering components by category."""
        # Add test components
        comp1 = ComponentMetadata(
            name="Comp1",
            module="ucup.test",
            category="testing",
            description="Test component 1"
        )
        comp2 = ComponentMetadata(
            name="Comp2",
            module="ucup.core",
            category="core",
            description="Test component 2"
        )

        self.engine.discovered_components = {
            "Comp1": comp1,
            "Comp2": comp2
        }

        testing_components = self.engine.get_components_by_category("testing")
        assert len(testing_components) == 1
        assert testing_components[0] == comp1

        core_components = self.engine.get_components_by_category("core")
        assert len(core_components) == 1
        assert core_components[0] == comp2

    def test_get_components_by_tag(self):
        """Test filtering components by tag."""
        comp1 = ComponentMetadata(
            name="Comp1",
            module="ucup.test",
            category="testing",
            description="Test component 1",
            tags={"class", "test"}
        )
        comp2 = ComponentMetadata(
            name="Comp2",
            module="ucup.core",
            category="core",
            description="Test component 2",
            tags={"function", "core"}
        )

        self.engine.discovered_components = {
            "Comp1": comp1,
            "Comp2": comp2
        }

        class_components = self.engine.get_components_by_tag("class")
        assert len(class_components) == 1
        assert class_components[0] == comp1

        test_components = self.engine.get_components_by_tag("test")
        assert len(test_components) == 1
        assert test_components[0] == comp1

    def test_search_components(self):
        """Test component search functionality."""
        comp1 = ComponentMetadata(
            name="ProbabilisticAgent",
            module="ucup.probabilistic",
            category="probabilistic",
            description="Base class for probabilistic agents",
            tags={"class", "agent"}
        )
        comp2 = ComponentMetadata(
            name="DecisionTracer",
            module="ucup.observability",
            category="observability",
            description="Decision tracing component",
            tags={"class", "tracing"}
        )

        self.engine.discovered_components = {
            "ProbabilisticAgent": comp1,
            "DecisionTracer": comp2
        }

        # Search by name
        results = self.engine.search_components("ProbabilisticAgent")
        assert len(results) == 1
        assert results[0] == comp1

        # Search by description
        results = self.engine.search_components("probabilistic")
        assert len(results) == 1
        assert results[0] == comp1

        # Search by tag
        results = self.engine.search_components("agent")
        assert len(results) == 1
        assert results[0] == comp1

    def test_get_import_suggestions(self):
        """Test import suggestion generation."""
        # Add test components with relationships
        comp1 = ComponentMetadata(
            name="ProbabilisticAgent",
            module="ucup.probabilistic",
            category="probabilistic",
            description="Base probabilistic agent",
            related_components=["DecisionTracer", "AlternativePath"]
        )
        comp2 = ComponentMetadata(
            name="DecisionTracer",
            module="ucup.observability",
            category="observability",
            description="Decision tracing component"
        )
        comp3 = ComponentMetadata(
            name="AlternativePath",
            module="ucup.probabilistic",
            category="probabilistic",
            description="Alternative reasoning paths"
        )

        self.engine.discovered_components = {
            "ProbabilisticAgent": comp1,
            "DecisionTracer": comp2,
            "AlternativePath": comp3
        }

        # Get suggestions for ProbabilisticAgent
        suggestions = self.engine.get_import_suggestions(["ProbabilisticAgent"])

        # Should suggest DecisionTracer and AlternativePath
        suggested_names = [s["component"] for s in suggestions]
        assert "DecisionTracer" in suggested_names
        assert "AlternativePath" in suggested_names

        # Verify suggestion format
        for suggestion in suggestions:
            assert "component" in suggestion
            assert "category" in suggestion
            assert "description" in suggestion
            assert "confidence" in suggestion
            assert "reason" in suggestion


class TestGlobalFunctions:
    """Test global API discovery functions."""

    @patch('ucup.api_discovery.get_discovery_engine')
    def test_discover_ucup_api(self, mock_get_engine):
        """Test discover_ucup_api function."""
        mock_engine = Mock()
        mock_components = {"Comp1": Mock(), "Comp2": Mock()}
        mock_engine.discover_all_components.return_value = mock_components
        mock_get_engine.return_value = mock_engine

        result = discover_ucup_api()

        mock_engine.discover_all_components.assert_called_once()
        assert result == mock_components

    @patch('ucup.api_discovery.get_discovery_engine')
    def test_get_smart_import_suggestions(self, mock_get_engine):
        """Test get_smart_import_suggestions function."""
        mock_engine = Mock()
        mock_suggestions = [{"component": "TestComp", "confidence": 0.8}]
        mock_engine.get_import_suggestions.return_value = mock_suggestions
        mock_get_engine.return_value = mock_engine

        result = get_smart_import_suggestions(["ExistingComp"])

        mock_engine.get_import_suggestions.assert_called_once_with(["ExistingComp"], "")
        assert result == mock_suggestions

    @patch('ucup.api_discovery.get_discovery_engine')
    def test_search_ucup_components(self, mock_get_engine):
        """Test search_ucup_components function."""
        mock_engine = Mock()
        mock_results = [Mock()]
        mock_engine.search_components.return_value = mock_results
        mock_get_engine.return_value = mock_engine

        result = search_ucup_components("query")

        mock_engine.search_components.assert_called_once_with("query")
        assert result == mock_results

    @patch('ucup.api_discovery.get_discovery_engine')
    def test_get_components_by_category(self, mock_get_engine):
        """Test get_components_by_category function."""
        mock_engine = Mock()
        mock_components = [Mock()]
        mock_engine.get_components_by_category.return_value = mock_components
        mock_get_engine.return_value = mock_engine

        result = get_components_by_category("testing")

        mock_engine.get_components_by_category.assert_called_once_with("testing")
        assert result == mock_components

    def test_get_discovery_engine_singleton(self):
        """Test that get_discovery_engine returns singleton."""
        engine1 = get_discovery_engine()
        engine2 = get_discovery_engine()

        assert engine1 is engine2
        assert isinstance(engine1, APIDiscoveryEngine)


class TestModuleExportGeneration:
    """Test module export generation functionality."""

    def test_generate_module_exports_success(self):
        """Test successful module export generation."""
        # Create a temporary module file
        import tempfile
        import textwrap

        module_content = textwrap.dedent('''
            """Test module for export generation."""

            class TestClass:
                """Test class."""
                pass

            def test_function():
                """Test function."""
                pass

            TEST_CONSTANT = "test"

            __all__ = ["TestClass", "test_function", "TEST_CONSTANT"]
        ''')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(module_content)
            temp_path = f.name

        try:
            engine = APIDiscoveryEngine()
            result = engine.generate_enhanced_all_exports(temp_path)

            assert "__all__" in result
            assert "metadata" in result
            assert len(result["__all__"]) == 3
            assert "TestClass" in result["metadata"]
            assert "test_function" in result["metadata"]

        finally:
            os.unlink(temp_path)

    def test_generate_module_exports_error(self):
        """Test error handling in module export generation."""
        engine = APIDiscoveryEngine()
        result = engine.generate_enhanced_all_exports("/nonexistent/path.py")

        assert "__all__" in result
        assert "error" in result
        assert result["__all__"] == []


class TestTypeHintEnhancement:
    """Test type hint enhancement functionality."""

    @patch('importlib.import_module')
    def test_enhance_type_hints_for_module(self, mock_import):
        """Test type hint enhancement for a module."""
        # Mock module with typed components
        mock_module = Mock()
        mock_module.__all__ = ["TestClass"]

        class MockTestClass:
            def __init__(self, value: int) -> None:
                self.value = value

            def method(self, param: str) -> bool:
                return True

        mock_module.TestClass = MockTestClass
        mock_import.return_value = mock_module

        result = enhance_type_hints_for_module("test_module")

        assert "TestClass" in result
        # Type hints should be extracted

    def test_enhance_type_hints_import_error(self):
        """Test handling of import errors in type hint enhancement."""
        result = enhance_type_hints_for_module("nonexistent_module")

        assert isinstance(result, dict)
        assert len(result) == 0


class TestIntegrationScenarios:
    """Test integration scenarios for API discovery."""

    def test_complete_discovery_workflow(self):
        """Test complete API discovery workflow."""
        engine = APIDiscoveryEngine()

        # Mock some components
        comp1 = ComponentMetadata(
            name="ProbabilisticAgent",
            module="ucup.probabilistic",
            category="probabilistic",
            description="Core probabilistic agent",
            related_components=["DecisionTracer"]
        )
        comp2 = ComponentMetadata(
            name="DecisionTracer",
            module="ucup.observability",
            category="observability",
            description="Decision tracing component"
        )

        engine.discovered_components = {
            "ProbabilisticAgent": comp1,
            "DecisionTracer": comp2
        }

        # Test various operations
        categories = engine.get_components_by_category("probabilistic")
        assert len(categories) == 1
        assert categories[0] == comp1

        search_results = engine.search_components("Probabilistic")
        assert len(search_results) == 1
        assert search_results[0] == comp1

        suggestions = engine.get_import_suggestions(["ProbabilisticAgent"])
        assert len(suggestions) >= 1
        suggested_names = [s["component"] for s in suggestions]
        assert "DecisionTracer" in suggested_names

    def test_auto_import_map_creation(self):
        """Test creation of auto-import mapping."""
        engine = APIDiscoveryEngine()

        # Add test component
        comp = ComponentMetadata(
            name="TestComponent",
            module="ucup.test",
            category="testing",
            description="Test component",
            examples=["example = TestComponent()"],
            tags={"class", "test"}
        )

        engine.discovered_components = {"TestComponent": comp}

        import_map = create_auto_import_map()

        assert "TestComponent" in import_map
        component_info = import_map["TestComponent"]
        assert component_info["module"] == "ucup.test"
        assert component_info["category"] == "testing"
        assert component_info["description"] == "Test component"
        assert "class" in component_info["tags"]
        assert "test" in component_info["tags"]
        assert "example = TestComponent()" in component_info["examples"]


if __name__ == "__main__":
    pytest.main([__file__])
