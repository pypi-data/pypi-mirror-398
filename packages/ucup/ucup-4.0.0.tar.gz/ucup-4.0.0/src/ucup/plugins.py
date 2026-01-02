"""
Plugin architecture for UCUP Framework extensibility.

This module provides a comprehensive plugin system that allows third-party
extensions to add new agent types, coordination strategies, monitoring tools,
and other framework components without modifying the core codebase.
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from .coordination import CoordinationAgent
from .observability import DecisionTracer
from .probabilistic import ProbabilisticAgent, ProbabilisticResult


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    entry_points: Dict[str, str] = field(default_factory=dict)
    config_schema: Optional[Dict[str, Any]] = None


class PluginInterface(ABC):
    """Base interface that all plugins must implement."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        pass

    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the plugin with optional configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Clean up plugin resources."""
        pass


class AgentPlugin(PluginInterface, ABC):
    """Plugin interface for custom agent implementations."""

    @abstractmethod
    def create_agent(self, config: Dict[str, Any]) -> ProbabilisticAgent:
        """Create and return a configured agent instance."""
        pass

    @abstractmethod
    def get_supported_capabilities(self) -> Set[str]:
        """Return the set of capabilities this agent plugin supports."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate agent configuration."""
        pass


class StrategyPlugin(PluginInterface, ABC):
    """Plugin interface for custom reasoning and coordination strategies."""

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of the strategy."""
        pass

    @abstractmethod
    def get_strategy_type(self) -> str:
        """Return strategy type ('reasoning' or 'coordination')."""
        pass

    @abstractmethod
    def execute_strategy(self, context: Dict[str, Any]) -> Any:
        """Execute the strategy with given context."""
        pass

    @abstractmethod
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if this strategy is applicable to the given context."""
        pass


class MonitorPlugin(PluginInterface, ABC):
    """Plugin interface for custom monitoring and observability tools."""

    @abstractmethod
    def get_monitor_name(self) -> str:
        """Return the name of the monitor."""
        pass

    @abstractmethod
    def start_monitoring(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """Start monitoring an agent."""
        pass

    @abstractmethod
    def stop_monitoring(self, agent_id: str) -> bool:
        """Stop monitoring an agent."""
        pass

    @abstractmethod
    def collect_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Collect metrics from monitored agent."""
        pass


class SerializerPlugin(PluginInterface, ABC):
    """Plugin interface for custom configuration serialization formats."""

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported serialization formats."""
        pass

    @abstractmethod
    def serialize(self, data: Any, format: str) -> str:
        """Serialize data to specified format."""
        pass

    @abstractmethod
    def deserialize(self, data: str, format: str) -> Any:
        """Deserialize data from specified format."""
        pass


class PluginHook:
    """Represents a hook point where plugins can extend functionality."""

    def __init__(self, name: str, signature: Callable = None):
        self.name = name
        self.signature = signature
        self.handlers: List[Callable] = []

    def register(self, handler: Callable):
        """Register a handler for this hook."""
        if self.signature and not self._matches_signature(handler):
            raise ValueError(f"Handler does not match hook signature for {self.name}")
        self.handlers.append(handler)

    def unregister(self, handler: Callable):
        """Unregister a handler from this hook."""
        if handler in self.handlers:
            self.handlers.remove(handler)

    def execute(self, *args, **kwargs) -> List[Any]:
        """Execute all registered handlers."""
        results = []
        for handler in self.handlers:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logging.warning(f"Plugin hook {self.name} handler failed: {e}")
        return results

    def _matches_signature(self, handler: Callable) -> bool:
        """Check if handler matches the required signature."""
        if not self.signature:
            return True

        try:
            sig_handler = inspect.signature(handler)
            sig_required = inspect.signature(self.signature)
            return sig_handler.parameters.keys() == sig_required.parameters.keys()
        except (ValueError, TypeError):
            return False


class PluginManager:
    """
    Central registry and manager for all plugins.

    Handles plugin discovery, loading, registration, and lifecycle management.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_types: Dict[str, List[PluginInterface]] = defaultdict(list)
        self.hooks: Dict[str, PluginHook] = {}
        self.discovery_paths: List[Path] = []

        # Initialize core hooks
        self._initialize_core_hooks()

    def _initialize_core_hooks(self):
        """Initialize core framework extension hooks."""

        # Agent lifecycle hooks
        self.hooks['agent_created'] = PluginHook(
            'agent_created',
            lambda agent, config: None
        )
        self.hooks['agent_executed'] = PluginHook(
            'agent_executed',
            lambda agent, task, result: None
        )

        # Coordination hooks
        self.hooks['coordination_started'] = PluginHook(
            'coordination_started',
            lambda coordinator, task, context: None
        )
        self.hooks['coordination_completed'] = PluginHook(
            'coordination_completed',
            lambda coordinator, result: None
        )

        # Monitoring hooks
        self.hooks['monitoring_data_collected'] = PluginHook(
            'monitoring_data_collected',
            lambda agent_id, metrics: None
        )

        # Configuration hooks
        self.hooks['config_loaded'] = PluginHook(
            'config_loaded',
            lambda config: None
        )

    def add_discovery_path(self, path: Union[str, Path]):
        """Add a path for plugin discovery."""
        self.discovery_paths.append(Path(path))

    def discover_plugins(self):
        """Discover and load plugins from configured paths."""
        for path in self.discovery_paths:
            if path.exists() and path.is_dir():
                self._discover_in_directory(path)

    def _discover_in_directory(self, directory: Path):
        """Discover plugins in a directory."""
        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                self._load_plugin_from_file(item)
            elif item.is_dir() and (item / '__init__.py').exists():
                self._load_plugin_from_package(item)

    def _load_plugin_from_file(self, file_path: Path):
        """Load a plugin from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for plugin classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        issubclass(obj, PluginInterface) and
                            obj != PluginInterface):
                        self._register_plugin_class(obj)

        except Exception as e:
            self.logger.warning(f"Failed to load plugin from {file_path}: {e}")

    def _load_plugin_from_package(self, package_path: Path):
        """Load plugins from a Python package."""
        try:
            # Add to Python path temporarily
            sys.path.insert(0, str(package_path.parent))

            module = importlib.import_module(package_path.name)

            # Look for plugin classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginInterface) and
                        obj != PluginInterface):
                    self._register_plugin_class(obj)

            # Remove from path
            sys.path.remove(str(package_path.parent))

        except Exception as e:
            self.logger.warning(f"Failed to load plugin package {package_path}: {e}")

    def register_plugin(self, plugin_type: str, plugin_class: Type[PluginInterface]):
        """Register a plugin class."""
        self._register_plugin_class(plugin_class, plugin_type)

    def _register_plugin_class(self, plugin_class: Type[PluginInterface], plugin_type: str = None):
        """Register a plugin class with the manager."""
        try:
            # Create instance to get metadata
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata

            plugin_key = f"{metadata.name}:{metadata.version}"

            if plugin_key in self.plugins:
                self.logger.warning(f"Plugin {plugin_key} already registered")
                return

            # Initialize plugin
            if plugin_instance.initialize():
                self.plugins[plugin_key] = plugin_instance

                # Determine plugin type if not specified
                if not plugin_type:
                    if isinstance(plugin_instance, AgentPlugin):
                        plugin_type = "agent"
                    elif isinstance(plugin_instance, StrategyPlugin):
                        plugin_type = "strategy"
                    elif isinstance(plugin_instance, MonitorPlugin):
                        plugin_type = "monitor"
                    elif isinstance(plugin_instance, SerializerPlugin):
                        plugin_type = "serializer"
                    else:
                        plugin_type = "generic"

                self.plugin_types[plugin_type].append(plugin_instance)

                self.logger.info(f"Registered plugin: {plugin_key} ({plugin_type})")
            else:
                self.logger.warning(f"Failed to initialize plugin {metadata.name}")

        except Exception as e:
            self.logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")

    def get_plugins(self, plugin_type: str) -> List[PluginInterface]:
        """Get all plugins of a specific type."""
        return self.plugin_types.get(plugin_type, [])

    def get_plugin(self, name: str, version: str = None) -> Optional[PluginInterface]:
        """Get a specific plugin by name and optional version."""
        if version:
            plugin_key = f"{name}:{version}"
            return self.plugins.get(plugin_key)
        else:
            # Return latest version
            matching_plugins = [
                plugin for key, plugin in self.plugins.items()
                if key.startswith(f"{name}:")
            ]
            if matching_plugins:
                # Sort by version (simple string sort for now)
                return max(matching_plugins, key=lambda p: p.metadata.version)
            return None

    def create_agent_from_plugin(self, plugin_name: str, config: Dict[str, Any]) -> Optional[ProbabilisticAgent]:
        """Create an agent using a plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin and isinstance(plugin, AgentPlugin):
            if plugin.validate_config(config):
                return plugin.create_agent(config)
        return None

    def execute_strategy_from_plugin(self, plugin_name: str, context: Dict[str, Any]) -> Any:
        """Execute a strategy using a plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin and isinstance(plugin, StrategyPlugin):
            if plugin.is_applicable(context):
                return plugin.execute_strategy(context)
        return None

    def register_hook_handler(self, hook_name: str, handler: Callable):
        """Register a handler for a plugin hook."""
        if hook_name in self.hooks:
            self.hooks[hook_name].register(handler)
        else:
            raise ValueError(f"Unknown hook: {hook_name}")

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all handlers for a hook."""
        if hook_name in self.hooks:
            return self.hooks[hook_name].execute(*args, **kwargs)
        return []

    def shutdown(self):
        """Shutdown all plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.shutdown()
            except Exception as e:
                self.logger.warning(f"Error shutting down plugin {plugin.metadata.name}: {e}")

        self.plugins.clear()
        self.plugin_types.clear()

    def list_plugins(self) -> Dict[str, List[str]]:
        """List all registered plugins by type."""
        return {
            plugin_type: [f"{p.metadata.name}:{p.metadata.version}" for p in plugins]
            for plugin_type, plugins in self.plugin_types.items()
        }


# Global plugin manager instance
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

def initialize_plugin_system(plugin_paths: List[Union[str, Path]] = None):
    """Initialize the plugin system with discovery paths."""
    manager = get_plugin_manager()

    # Add default discovery paths
    if plugin_paths:
        for path in plugin_paths:
            manager.add_discovery_path(path)
    else:
        # Default plugin directories
        manager.add_discovery_path(Path(__file__).parent / "plugins")
        manager.add_discovery_path(Path.cwd() / "plugins")

    # Discover and load plugins
    manager.discover_plugins()

    return manager
