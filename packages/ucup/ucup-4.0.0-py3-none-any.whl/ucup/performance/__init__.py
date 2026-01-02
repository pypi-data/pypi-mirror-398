"""
Performance Optimization Module for UCUP Framework

This module provides performance enhancements including Bayesian inference optimization,
asynchronous processing, memory management, and distributed computing capabilities.
"""

from .bayesian_optimizer import VariableElimination, BayesianInferenceCache, OptimizedBayesianNetwork
from .async_processing import AsyncTaskPool, ParallelAgentExecutor, StreamingResultAggregator
from .memory_manager import AgentMemoryPool, StateCompressor, LazyAgentLoader
from .distributed import WorkerNode, DistributedCoordinatorProtocol, ConsistentHashRing, DistributedStateStore

__all__ = [
    # Bayesian optimization
    'VariableElimination',
    'BayesianInferenceCache',
    'OptimizedBayesianNetwork',

    # Async processing
    'AsyncTaskPool',
    'ParallelAgentExecutor',
    'StreamingResultAggregator',

    # Memory management
    'AgentMemoryPool',
    'StateCompressor',
    'LazyAgentLoader',

    # Distributed computing
    'WorkerNode',
    'DistributedCoordinatorProtocol',
    'ConsistentHashRing',
    'DistributedStateStore'
]
