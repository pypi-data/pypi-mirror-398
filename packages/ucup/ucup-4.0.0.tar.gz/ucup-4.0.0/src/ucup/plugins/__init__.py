"""
UCUP Plugin System

Extensible plugin architecture for UCUP framework allowing dynamic
loading of benchmarks, coordinators, and custom functionality.
"""

from .base import (
    Plugin,
    PluginMetadata,
    PluginConfig,
    PluginError,
    AgentPlugin,
    StrategyPlugin,
    MonitorPlugin
)

# Import existing plugins
from .example_agent import CustomerServiceAgentPlugin
from .example_strategy import CreativeBrainstormingStrategyPlugin
from .monitoring_plugin import MetricsMonitorPlugin, TracingMonitorPlugin

# Import donation plugin
from .donation_plugin import DonationPlugin

__all__ = [
    # Base classes
    "Plugin",
    "PluginMetadata",
    "PluginConfig",
    "PluginError",

    # Existing plugins
    "CustomerServiceAgentPlugin",
    "CreativeBrainstormingStrategyPlugin",
    "MetricsMonitorPlugin",
    "TracingMonitorPlugin",

    # Donation plugin
    "DonationPlugin"
]

__version__ = "1.0.0"
