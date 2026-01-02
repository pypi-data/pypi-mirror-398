# UCUP/src/ucup/__init__.py
"""
UCUP Framework - Unified Cognitive Uncertainty Processing

Copyright (c) 2025 UCUP Framework Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from .config import create_ucup_system, load_ucup_config
from .errors import ErrorHandler, ProbabilisticError, ValidationError, get_error_handler
from .metrics import (
    BenefitsDisplay,
    MetricsTracker,
    get_global_tracker,
    record_build_metrics,
    show_build_benefits,
    show_test_benefits,
)

# UCUP 4.0: Intelligent API Suggestions System
from .smart_suggestions import (
    SmartImportSuggester,
    get_smart_suggestions,
    suggest_related_components,
    get_component_help
)

# Smart API Discovery & Auto-Import System
from .api_discovery import (
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

# Import from multimodal submodules
from .multimodal.fusion_engine import (
    FusedAnalysis,
    MultimodalFusionEngine,
    MultimodalInputs,
    create_fusion_engine,
    fuse_multimodal,
)
from .multimodal.streaming_processor import (
    RealTimeStreamingProcessor,
    StreamChunk,
    StreamingAnalysis,
)
from .probabilistic import AlternativePath, ProbabilisticAgent, ProbabilisticResult
from .advanced_probabilistic import (
    BayesianNetwork,
    BayesianNode,
    ConditionalProbabilityTable,
    MarkovDecisionProcess,
    MDPState,
    MDPAction,
    MDPTransition,
    MonteCarloTreeSearch,
    MCTSNode,
    BayesianAgentNetwork,
    MDPBasedCoordinator,
    MCTSReasoner,
    PUCTNode,
    AlphaZeroMCTS,
    QLearningMDP,
    DeepQLearningMDP,
)
from .testing import (
    AdversarialTestGenerator,
    AgentNetworkIntegrationTester,
    AgentTestSuite,
    APITestingHarness,
    BenchmarkIntegration,
    ComparativeModelTester,
    CustomerServiceContext,
    DynamicScenarioGenerator,
    ExpectedOutcome,
    IntelligentTestGenerator,
    PerformanceDegradationTester,
    ProbabilisticAssert,
    Scenario,
    ScenarioContext,
    ScenarioGenerationResult,
    TestRun,
    TestScenario,
    UserSimulationTester,
)
from .reliability import (
    FailureDetector,
    AutomatedRecoveryPipeline,
    StateCheckpointer,
)
from .validation import ValidationReport, validate_data
from .toon.toon_formatter import (
    ToonFormatter,
    ToonSchema,
    ToonConversionResult,
    TokenMetrics,
    TOONOptimizer,
)
from .observability import (
    DecisionTracer,
    DecisionExplorer,
    DecisionVisualization,
    ReasoningVisualizer,
    LiveAgentMonitor,
)
from .memory_management import (
    MemoryMonitor,
    CacheManager,
    ProviderManager,
    get_memory_monitor,
    get_cache_manager,
    get_provider_manager,
    force_memory_cleanup,
    get_memory_report,
    cached_operation,
    monitored_operation,
)
from .feature_flags import (
    FeatureFlag,
    FeatureFlagState,
    FeatureFlagManager,
    get_feature_manager,
    is_feature_enabled,
    require_feature,
)
from .cloud_deployment import (
    CloudConfig,
    DeploymentSpec,
    DeploymentResult,
    CloudDeploymentProvider,
    AWSDeploymentProvider,
    AzureDeploymentProvider,
    GCPDeploymentProvider,
    CloudDeploymentManager,
    create_cloud_deployment_manager,
    create_deployment_spec_from_config,
    create_cloud_config_from_env,
    deploy_to_cloud,
    get_cloud_status,
    destroy_cloud_deployment,
)
from .test_environments import (
    TestEnvironment,
    TestResult,
    TestSuite,
    EnvironmentManager,
    CondaEnvironmentManager,
    VenvEnvironmentManager,
    TestRunner,
    TestEnvironmentManager,
    create_default_test_environments,
    setup_ucup_test_environment,
    run_ucup_tests,
    generate_test_template,
)

# MultimodalAgentTester is optional - import it separately if needed
# Note: testing/ dir contains additional testing utilities but is not a package
MultimodalAgentTester = None

__version__ = "4.0.0"

__all__ = [
    'load_ucup_config',
    'create_ucup_system',
    'ProbabilisticResult',
    'AlternativePath',
    'ProbabilisticAgent',
    'show_build_benefits',
    'show_test_benefits',
    'record_build_metrics',
    'get_global_tracker',
    'MetricsTracker',
    'BenefitsDisplay',
    'ProbabilisticError',
    'ValidationError',
    'ErrorHandler',
    'get_error_handler',
    'ValidationReport',
    'validate_data',
    'AgentTestSuite',
    'Scenario',
    'ExpectedOutcome',
    'TestRun',
    'ScenarioContext',
    'CustomerServiceContext',
    'AdversarialTestGenerator',
    'ProbabilisticAssert',
    'BenchmarkIntegration',
    'APITestingHarness',
    'DynamicScenarioGenerator',
    'AgentNetworkIntegrationTester',
    'PerformanceDegradationTester',
    'ComparativeModelTester',
    'UserSimulationTester',
    'MultimodalFusionEngine',
    'MultimodalInputs',
    'FusedAnalysis',
    'fuse_multimodal',
    'create_fusion_engine',
    'RealTimeStreamingProcessor',
    'StreamChunk',
    'StreamingAnalysis',
    'MultimodalAgentTester',
    'IntelligentTestGenerator',
    'TestScenario',
    'ScenarioGenerationResult',
    # Reliability and Recovery
    'FailureDetector',
    'AutomatedRecoveryPipeline',
    'StateCheckpointer',
    # TOON Token Optimization
    'BayesianNetwork',
    'BayesianNode',
    'ConditionalProbabilityTable',
    'MarkovDecisionProcess',
    'MDPState',
    'MDPAction',
    'MDPTransition',
    'MonteCarloTreeSearch',
    'MCTSNode',
    'BayesianAgentNetwork',
    'MDPBasedCoordinator',
    'MCTSReasoner',
    'PUCTNode',
    'AlphaZeroMCTS',
    'QLearningMDP',
    'DeepQLearningMDP',
    # TOON Token Optimization
    'ToonFormatter',
    'ToonSchema',
    'ToonConversionResult',
    'TokenMetrics',
    'TOONOptimizer',
    # Observability
    'DecisionTracer',
    'DecisionExplorer',
    'DecisionVisualization',
    'ReasoningVisualizer',
    'LiveAgentMonitor',
    # Memory Management
    'MemoryMonitor',
    'CacheManager',
    'ProviderManager',
    'get_memory_monitor',
    'get_cache_manager',
    'get_provider_manager',
    'force_memory_cleanup',
    'get_memory_report',
    'cached_operation',
    'monitored_operation',
    # Feature Flags
    'FeatureFlag',
    'FeatureFlagState',
    'FeatureFlagManager',
    'get_feature_manager',
    'is_feature_enabled',
    'require_feature',
    # Cloud Deployment
    'CloudConfig',
    'DeploymentSpec',
    'DeploymentResult',
    'CloudDeploymentProvider',
    'AWSDeploymentProvider',
    'AzureDeploymentProvider',
    'GCPDeploymentProvider',
    'CloudDeploymentManager',
    'create_cloud_deployment_manager',
    'create_deployment_spec_from_config',
    'create_cloud_config_from_env',
    'deploy_to_cloud',
    'get_cloud_status',
    'destroy_cloud_deployment',
    # Test Environments
    'TestEnvironment',
    'TestResult',
    'TestSuite',
    'EnvironmentManager',
    'CondaEnvironmentManager',
    'VenvEnvironmentManager',
    'TestRunner',
    'TestEnvironmentManager',
    'create_default_test_environments',
    'setup_ucup_test_environment',
    'run_ucup_tests',
    'generate_test_template',
    # Smart API Discovery & Auto-Import System
    'APIDiscoveryEngine',
    'ComponentMetadata',
    'ExportMetadata',
    'discover_ucup_api',
    'get_smart_import_suggestions',
    'search_ucup_components',
    'get_components_by_category',
    'generate_module_exports',
    'create_auto_import_map',
    'enhance_type_hints_for_module',
    'get_discovery_engine'
]
