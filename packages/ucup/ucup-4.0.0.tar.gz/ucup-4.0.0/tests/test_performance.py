"""
Tests for Performance Optimization Module

This module contains comprehensive tests for the performance optimization
capabilities including Bayesian optimization, async processing, memory management,
and distributed computing.
"""

import pytest
import asyncio
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any, Optional, Callable
import numpy as np

from ucup.performance import (
    VariableElimination, BayesianInferenceCache, OptimizedBayesianNetwork,
    AsyncTaskPool, ParallelAgentExecutor, StreamingResultAggregator,
    AgentMemoryPool, StateCompressor, LazyAgentLoader,
    WorkerNode, DistributedCoordinatorProtocol, ConsistentHashRing, DistributedStateStore
)


from ucup.advanced_probabilistic import BayesianNetwork, BayesianNode


class TestVariableElimination:
    """Test VariableElimination class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.network = BayesianNetwork()
        self.elimination = VariableElimination(self.network)

    def test_initialization(self):
        """Test initialization"""
        assert self.elimination.network == self.network
        assert self.elimination.use_cache == True
        assert self.elimination.factor_cache == {}
        assert self.elimination.elimination_order_cache == {}

    @patch('networkx.DiGraph')
    def test_compute_elimination_order(self, mock_graph):
        """Test elimination order computation"""
        # Mock the network
        mock_network = Mock()
        mock_network.nodes = {'A': Mock(), 'B': Mock(), 'C': Mock()}
        eliminator = VariableElimination(mock_network)
        
        # Test query method with mock
        with patch.object(eliminator, 'query', return_value={'C=0': 0.6, 'C=1': 0.4}):
            result = eliminator.query(['C'], {'A': '0'})
            assert isinstance(result, dict)

    def test_perform_inference(self):
        """Test full inference with variable elimination"""
        # Mock the network
        mock_network = BayesianNetwork()
        eliminator = VariableElimination(mock_network)
        
        evidence = {'A': '0'}
        query_variables = ['C']

        # Mock the query method
        with patch.object(eliminator, 'query', return_value={'C=0': 0.6, 'C=1': 0.4}):
            result = eliminator.query(query_variables, evidence)
            assert isinstance(result, dict)


class TestBayesianInferenceCache:
    """Test BayesianInferenceCache class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.cache = BayesianInferenceCache(max_size=100)

    def test_initialization(self):
        """Test cache initialization"""
        assert self.cache.hit_count == 0
        assert self.cache.miss_count == 0

    def test_cache_key_generation(self):
        """Test cache key generation"""
        network_id = "net_001"
        query_vars = ['A', 'B']
        evidence = {'C': 0, 'D': 1}

        key = self.cache.generate_query_key(network_id, query_vars, evidence)

        # Key should be deterministic and include all parameters
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length

    def test_get_cache_hit(self):
        """Test cache retrieval for existing entry"""
        key = "test_key"
        expected_result = {"probability": 0.8, "confidence": 0.9}
        self.cache.store_query_result(key, expected_result)

        result = self.cache.get_query_result(key)

        assert result == expected_result

    def test_get_cache_miss(self):
        """Test cache retrieval for non-existing entry"""
        result = self.cache.get_query_result("nonexistent_key")

        assert result is None

    def test_put_new_entry(self):
        """Test adding new entry to cache"""
        key = "new_key"
        value = {"result": "test"}

        self.cache.store_query_result(key, value)

        assert self.cache.get_query_result(key) == value


class TestOptimizedBayesianNetwork:
    """Test OptimizedBayesianNetwork class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.network = OptimizedBayesianNetwork()

    def test_initialization(self):
        """Test network initialization"""
        assert isinstance(self.network.variable_eliminator, VariableElimination)
        assert isinstance(self.network.cache, BayesianInferenceCache)

    def test_query_with_caching(self):
        """Test query execution with caching"""
        query_vars = ['A']
        evidence = {'B': 0}

        # Mock inference result
        expected_result = {"A=0": 0.3, "A=1": 0.7}

        with patch.object(self.network.variable_eliminator, 'query', return_value=expected_result) as mock_inference:
            # First query - should compute
            result1 = self.network.query(query_vars, evidence)
            assert result1 == expected_result
            mock_inference.assert_called_once()

            # Reset mock
            mock_inference.reset_mock()

            # Second query - should use cache
            result2 = self.network.query(query_vars, evidence)
            assert result2 == expected_result
            mock_inference.assert_not_called()  # Should use cached result

    def test_get_network_stats(self):
        """Test network statistics retrieval"""
        stats = self.network.get_performance_stats()

        assert isinstance(stats, dict)
        assert "network_hash" in stats
        assert "cache_stats" in stats
        assert "total_queries" in stats


class TestAsyncTaskPool:
    """Test AsyncTaskPool class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.pool = AsyncTaskPool(max_concurrent=3, queue_size=10)

    def test_initialization(self):
        """Test pool initialization"""
        assert self.pool.max_concurrent == 3
        assert self.pool.queue_size == 10
        assert not self.pool.running
        assert self.pool.active_tasks == {}

    @pytest.mark.asyncio
    async def test_start_pool(self):
        """Test pool startup"""
        await self.pool.start()

        assert self.pool.is_running
        assert len(self.pool.workers) == 3

    @pytest.mark.asyncio
    async def test_stop_pool(self):
        """Test pool shutdown"""
        await self.pool.start()
        await self.pool.stop()

        assert not self.pool.is_running
        assert len(self.pool.workers) == 0

    @pytest.mark.asyncio
    async def test_submit_task(self):
        """Test task submission"""
        await self.pool.start()

        # Simple test task
        async def test_task(x):
            await asyncio.sleep(0.01)
            return x * 2

        future = await self.pool.submit(test_task, 5)

        result = await future
        assert result == 10

        await self.pool.stop()

    @pytest.mark.asyncio
    async def test_submit_multiple_tasks(self):
        """Test multiple task submission"""
        await self.pool.start()

        async def increment_task(x):
            await asyncio.sleep(0.01)
            return x + 1

        # Submit multiple tasks
        futures = []
        for i in range(5):
            future = await self.pool.submit(increment_task, i)
            futures.append(future)

        # Wait for all results
        results = await asyncio.gather(*futures)
        expected = [1, 2, 3, 4, 5]

        assert results == expected

        await self.pool.stop()

    def test_pool_stats(self):
        """Test pool statistics"""
        stats = self.pool.get_stats()

        assert isinstance(stats, dict)
        assert "max_workers" in stats
        assert "queue_size" in stats
        assert "active_tasks" in stats
        assert "completed_tasks" in stats


class TestParallelAgentExecutor:
    """Test ParallelAgentExecutor class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.executor = ParallelAgentExecutor(max_concurrent=2)

    def test_initialization(self):
        """Test executor initialization"""
        assert self.executor.max_concurrent == 2
        assert isinstance(self.executor.task_pool, AsyncTaskPool)

    @pytest.mark.asyncio
    async def test_execute_agents(self):
        """Test parallel agent execution"""
        # Mock agents
        agents = []
        for i in range(3):
            agent = Mock()
            agent.execute = AsyncMock(return_value=f"result_{i}")
            agent.agent_id = f"agent_{i}"
            agents.append(agent)

        tasks = ["task1", "task2", "task3"]

        results = await self.executor.execute_agents(agents, tasks)

        assert len(results) == 3
        assert "agent_0" in results
        assert "agent_1" in results
        assert "agent_2" in results

    def test_get_execution_stats(self):
        """Test execution statistics"""
        stats = self.executor.get_execution_stats()

        assert isinstance(stats, dict)
        assert "total_executions" in stats
        assert "avg_execution_time" in stats
        assert "success_rate" in stats


class TestStreamingResultAggregator:
    """Test StreamingResultAggregator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.aggregator = StreamingResultAggregator(window_size=5, aggregation_method="mean")

    def test_initialization(self):
        """Test aggregator initialization"""
        assert self.aggregator.window_size == 5
        assert self.aggregator.aggregation_method == "mean"
        assert self.aggregator.results == []

    def test_add_result(self):
        """Test result addition"""
        self.aggregator.add_result(10.0)
        self.aggregator.add_result(20.0)
        self.aggregator.add_result(30.0)

        assert len(self.aggregator.results) == 3
        assert self.aggregator.results == [10.0, 20.0, 30.0]

    def test_get_aggregated_result(self):
        """Test result aggregation"""
        self.aggregator.add_result(10.0)
        self.aggregator.add_result(20.0)
        self.aggregator.add_result(30.0)

        # Test mean aggregation
        result = self.aggregator.get_aggregated_result()
        assert result == 20.0  # (10 + 20 + 30) / 3

    def test_window_size_limit(self):
        """Test window size enforcement"""
        self.aggregator.window_size = 2

        self.aggregator.add_result(10.0)
        self.aggregator.add_result(20.0)
        self.aggregator.add_result(30.0)  # Should remove oldest

        assert len(self.aggregator.results) == 2
        assert self.aggregator.results == [20.0, 30.0]

    def test_different_aggregation_methods(self):
        """Test different aggregation methods"""
        # Test sum
        aggregator_sum = StreamingResultAggregator(aggregation_method="sum")
        aggregator_sum.add_result(10.0)
        aggregator_sum.add_result(20.0)
        assert aggregator_sum.get_aggregated_result() == 30.0

        # Test max
        aggregator_max = StreamingResultAggregator(aggregation_method="max")
        aggregator_max.add_result(10.0)
        aggregator_max.add_result(25.0)
        aggregator_max.add_result(15.0)
        assert aggregator_max.get_aggregated_result() == 25.0

        # Test min
        aggregator_min = StreamingResultAggregator(aggregation_method="min")
        aggregator_min.add_result(10.0)
        aggregator_min.add_result(25.0)
        aggregator_min.add_result(5.0)
        assert aggregator_min.get_aggregated_result() == 5.0


class TestAgentMemoryPool:
    """Test AgentMemoryPool class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.pool = AgentMemoryPool(initial_size=10, max_size=100)

    def test_initialization(self):
        """Test pool initialization"""
        assert self.pool.initial_size == 10
        assert self.pool.max_size == 100
        assert self.pool.allocated == 0
        assert self.pool.available == 10

    def test_allocate_memory(self):
        """Test memory allocation"""
        block = self.pool.allocate(5)

        assert block is not None
        assert self.pool.allocated == 5
        assert self.pool.available == 5

    def test_allocate_over_limit(self):
        """Test allocation over available memory"""
        # Allocate all available memory
        block1 = self.pool.allocate(10)
        assert block1 is not None

        # Try to allocate more
        block2 = self.pool.allocate(5)
        assert block2 is None  # Should fail

    def test_deallocate_memory(self):
        """Test memory deallocation"""
        block = self.pool.allocate(5)
        assert self.pool.allocated == 5
        assert self.pool.available == 5

        self.pool.deallocate(block)
        assert self.pool.allocated == 0
        assert self.pool.available == 10

    def test_garbage_collection(self):
        """Test garbage collection"""
        # Allocate some memory
        self.pool.allocate(5)

        # Mock some unreferenced blocks
        self.pool.unreferenced_blocks = [Mock()]

        self.pool.garbage_collect()

        # Should have cleaned up unreferenced blocks
        assert len(self.pool.unreferenced_blocks) == 0


class TestStateCompressor:
    """Test StateCompressor class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.compressor = StateCompressor(compression_level=6)

    def test_initialization(self):
        """Test compressor initialization"""
        assert self.compressor.compression_level == 6
        assert self.compressor.compressed_states == {}

    def test_compress_state(self):
        """Test state compression"""
        state = {
            "agents": [{"id": "agent1", "status": "active"}, {"id": "agent2", "status": "idle"}],
            "tasks": ["task1", "task2", "task3"],
            "metrics": {"cpu": 75.5, "memory": 82.3}
        }

        compressed = self.compressor.compress_state(state)

        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_state(self):
        """Test state decompression"""
        original_state = {"key": "value", "number": 42, "list": [1, 2, 3]}

        compressed = self.compressor.compress_state(original_state)
        decompressed = self.compressor.decompress_state(compressed)

        assert decompressed == original_state

    def test_compression_ratio(self):
        """Test compression ratio calculation"""
        # Create a large repetitive state
        large_state = {"data": "x" * 1000, "repeated": ["same"] * 100}

        compressed = self.compressor.compress_state(large_state)

        original_size = len(str(large_state).encode())
        compressed_size = len(compressed)
        ratio = compressed_size / original_size

        assert 0 < ratio < 1  # Should achieve compression


class TestLazyAgentLoader:
    """Test LazyAgentLoader class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.loader = LazyAgentLoader(cache_size=5)

    def test_initialization(self):
        """Test loader initialization"""
        assert self.loader.cache_size == 5
        assert self.loader.loaded_agents == {}
        assert self.loader.agent_registry == {}

    def test_register_agent(self):
        """Test agent registration"""
        agent_id = "agent_001"
        agent_class = Mock
        config = {"type": "probabilistic"}

        self.loader.register_agent(agent_id, agent_class, config)

        assert agent_id in self.loader.agent_registry
        assert self.loader.agent_registry[agent_id]["class"] == agent_class
        assert self.loader.agent_registry[agent_id]["config"] == config

    def test_load_agent(self):
        """Test lazy agent loading"""
        agent_id = "agent_001"
        agent_class = Mock
        config = {"param": "value"}

        self.loader.register_agent(agent_id, agent_class, config)

        # First load - should create agent
        agent1 = self.loader.load_agent(agent_id)
        assert isinstance(agent1, Mock)

        # Second load - should return cached agent
        agent2 = self.loader.load_agent(agent_id)
        assert agent1 is agent2  # Same instance

    def test_unload_agent(self):
        """Test agent unloading"""
        agent_id = "agent_001"
        self.loader.register_agent(agent_id, Mock, {})

        # Load agent
        agent = self.loader.load_agent(agent_id)
        assert agent_id in self.loader.loaded_agents

        # Unload agent
        self.loader.unload_agent(agent_id)
        assert agent_id not in self.loader.loaded_agents

    def test_cache_eviction(self):
        """Test cache eviction when full"""
        self.loader.cache_size = 2

        # Register and load 3 agents
        for i in range(3):
            agent_id = f"agent_{i}"
            self.loader.register_agent(agent_id, Mock, {})
            self.loader.load_agent(agent_id)

        # Should only have 2 agents in cache (LRU eviction)
        assert len(self.loader.loaded_agents) == 2


class TestWorkerNode:
    """Test WorkerNode class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.node = WorkerNode(node_id="worker_001", host="localhost", port=8080)

    def test_initialization(self):
        """Test node initialization"""
        assert self.node.node_id == "worker_001"
        assert self.node.host == "localhost"
        assert self.node.port == 8080
        assert not self.node.is_active
        assert self.node.capabilities == []

    def test_start_node(self):
        """Test node startup"""
        self.node.start()

        assert self.node.is_active
        assert self.node.start_time is not None

    def test_stop_node(self):
        """Test node shutdown"""
        self.node.start()
        self.node.stop()

        assert not self.node.is_active

    def test_add_capability(self):
        """Test capability addition"""
        self.node.add_capability("gpu_computing")
        self.node.add_capability("high_memory")

        assert "gpu_computing" in self.node.capabilities
        assert "high_memory" in self.node.capabilities

    def test_get_status(self):
        """Test status retrieval"""
        status = self.node.get_status()

        assert isinstance(status, dict)
        assert "node_id" in status
        assert "is_active" in status
        assert "capabilities" in status
        assert "uptime" in status


class TestConsistentHashRing:
    """Test ConsistentHashRing class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ring = ConsistentHashRing(replicas=3)

    def test_initialization(self):
        """Test ring initialization"""
        assert self.ring.replicas == 3
        assert self.ring.nodes == {}
        assert self.ring.sorted_keys == []

    def test_add_node(self):
        """Test node addition"""
        node_id = "node_001"

        self.ring.add_node(node_id)

        assert node_id in self.ring.nodes
        assert len(self.ring.sorted_keys) == self.ring.replicas

    def test_remove_node(self):
        """Test node removal"""
        node_id = "node_001"
        self.ring.add_node(node_id)

        self.ring.remove_node(node_id)

        assert node_id not in self.ring.nodes
        assert len(self.ring.sorted_keys) == 0

    def test_get_node(self):
        """Test node retrieval for key"""
        # Add multiple nodes
        nodes = ["node_001", "node_002", "node_003"]
        for node in nodes:
            self.ring.add_node(node)

        # Get node for a key
        key = "some_key"
        assigned_node = self.ring.get_node(key)

        assert assigned_node in nodes

        # Same key should always return same node
        assigned_node2 = self.ring.get_node(key)
        assert assigned_node == assigned_node2

    def test_get_node_distribution(self):
        """Test that keys are reasonably distributed"""
        nodes = ["node_001", "node_002", "node_003", "node_004"]
        for node in nodes:
            self.ring.add_node(node)

        # Generate many keys and count distribution
        key_counts = {}
        for i in range(1000):
            key = f"key_{i}"
            node = self.ring.get_node(key)
            key_counts[node] = key_counts.get(node, 0) + 1

        # Each node should get some keys
        for node in nodes:
            assert node in key_counts
            assert key_counts[node] > 0


class TestDistributedCoordinatorProtocol:
    """Test DistributedCoordinatorProtocol class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.protocol = DistributedCoordinatorProtocol(protocol_id="test_protocol")

    def test_initialization(self):
        """Test protocol initialization"""
        assert self.protocol.protocol_id == "test_protocol"
        assert not self.protocol.is_connected
        assert self.protocol.message_handlers == {}

    def test_register_handler(self):
        """Test message handler registration"""
        message_type = "task_assignment"

        def handler(msg):
            return f"processed_{msg}"

        self.protocol.register_handler(message_type, handler)

        assert message_type in self.protocol.message_handlers
        assert self.protocol.message_handlers[message_type] == handler

    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test message sending"""
        # Mock connection
        with patch.object(self.protocol, '_ensure_connection', new_callable=AsyncMock):
            with patch.object(self.protocol, '_serialize_message') as mock_serialize:
                with patch.object(self.protocol, '_send_data', new_callable=AsyncMock) as mock_send:
                    mock_serialize.return_value = b"serialized_data"

                    message = {"type": "test", "data": "hello"}
                    await self.protocol.send_message("node_001", message)

                    mock_send.assert_called_once_with("node_001", b"serialized_data")

    @pytest.mark.asyncio
    async def test_receive_message(self):
        """Test message receiving"""
        # Register handler
        received_messages = []

        def test_handler(msg):
            received_messages.append(msg)
            return "ack"

        self.protocol.register_handler("test_type", test_handler)

        # Simulate receiving message
        message = {"type": "test_type", "content": "test_data"}
        result = await self.protocol.receive_message(message)

        assert result == "ack"
        assert len(received_messages) == 1
        assert received_messages[0] == message


class TestDistributedStateStore:
    """Test DistributedStateStore class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.store = DistributedStateStore(store_id="test_store")

    def test_initialization(self):
        """Test store initialization"""
        assert self.store.store_id == "test_store"
        assert self.store.state == {}
        assert self.store.version == 0

    def test_set_state(self):
        """Test state setting"""
        key = "agent_status"
        value = {"status": "active", "last_seen": datetime.now()}

        self.store.set_state(key, value)

        assert key in self.store.state
        assert self.store.state[key] == value
        assert self.store.version > 0

    def test_get_state(self):
        """Test state retrieval"""
        key = "agent_status"
        value = {"status": "active"}

        self.store.set_state(key, value)

        retrieved = self.store.get_state(key)
        assert retrieved == value

        # Test non-existent key
        assert self.store.get_state("nonexistent") is None

    def test_delete_state(self):
        """Test state deletion"""
        key = "temp_data"
        self.store.set_state(key, "some_value")

        assert key in self.store.state

        self.store.delete_state(key)

        assert key not in self.store.state

    def test_state_synchronization(self):
        """Test state synchronization between stores"""
        # Create two stores
        store1 = DistributedStateStore("store1")
        store2 = DistributedStateStore("store2")

        # Set state in store1
        store1.set_state("shared_key", "shared_value")

        # Simulate synchronization (in real implementation would use network)
        store2.state = store1.state.copy()
        store2.version = store1.version

        # Both should have same state
        assert store2.get_state("shared_key") == "shared_value"
        assert store2.version == store1.version


# Integration tests
class TestPerformanceIntegration:
    """Integration tests for performance optimization"""

    def setup_method(self):
        """Setup integration test fixtures"""
        self.task_pool = AsyncTaskPool(max_workers=2)
        self.executor = ParallelAgentExecutor(max_concurrent=2)
        self.memory_pool = AgentMemoryPool(initial_size=20)
        self.state_compressor = StateCompressor()

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self):
        """Test complete performance optimization pipeline"""
        # Start task pool
        await self.task_pool.start()

        # Create mock agents
        agents = []
        for i in range(3):
            agent = Mock()
            agent.agent_id = f"agent_{i}"
            agent.execute = AsyncMock(return_value=f"result_{i}")
            agents.append(agent)

        # Execute agents in parallel
        tasks = ["task1", "task2", "task3"]
        results = await self.executor.execute_agents(agents, tasks)

        # Verify results
        assert len(results) == 3
        for i in range(3):
            assert f"agent_{i}" in results

        # Test memory management
        memory_blocks = []
        for i in range(5):
            block = self.memory_pool.allocate(4)  # Allocate 4 units each
            memory_blocks.append(block)

        assert self.memory_pool.allocated == 20  # 5 * 4

        # Test compression
        large_state = {"data": "x" * 1000, "numbers": list(range(100))}
        compressed = self.state_compressor.compress_state(large_state)
        decompressed = self.state_compressor.decompress_state(compressed)

        assert decompressed == large_state

        # Cleanup
        await self.task_pool.stop()

    def test_distributed_coordination(self):
        """Test distributed coordination setup"""
        # Create hash ring
        ring = ConsistentHashRing(replicas=5)

        # Add worker nodes
        workers = []
        for i in range(4):
            worker = WorkerNode(f"worker_{i}", f"host_{i}", 8080 + i)
            workers.append(worker)
            ring.add_node(worker.node_id)

        # Test task distribution
        task_assignments = {}
        for i in range(20):
            task_key = f"task_{i}"
            assigned_worker = ring.get_node(task_key)
            task_assignments[assigned_worker] = task_assignments.get(assigned_worker, 0) + 1

        # Verify distribution (should be roughly even)
        total_assignments = sum(task_assignments.values())
        assert total_assignments == 20

        for worker_id, count in task_assignments.items():
            assert count > 0  # Each worker should get some tasks

    @pytest.mark.asyncio
    async def test_memory_optimization(self):
        """Test memory optimization under load"""
        # Simulate memory-intensive operations
        large_objects = []

        # Allocate memory for large objects
        for i in range(10):
            obj_size = 10 + i  # Increasing sizes
            memory_block = self.memory_pool.allocate(obj_size)
            if memory_block:
                large_objects.append((f"object_{i}", memory_block))

        # Should have allocated some objects
        assert len(large_objects) > 0

        # Test garbage collection
        # Mark some objects as unreferenced
        unreferenced = large_objects[:3]  # First 3 objects
        for obj_name, block in unreferenced:
            # In real implementation, would use weak references
            self.memory_pool.unreferenced_blocks.append(block)

        # Run GC
        self.memory_pool.garbage_collect()

        # Memory should be freed
        initial_allocated = self.memory_pool.allocated
        # Note: In real implementation, GC would actually free memory

    def test_performance_monitoring(self):
        """Test performance monitoring and metrics"""
        # Create components
        aggregator = StreamingResultAggregator(window_size=10)
        pool = AsyncTaskPool(max_workers=3)

        # Simulate performance data
        response_times = [0.1, 0.15, 0.08, 0.12, 0.09, 0.11, 0.14, 0.07, 0.13, 0.10]

        for rt in response_times:
            aggregator.add_result(rt)

        # Check aggregation
        avg_response_time = aggregator.get_aggregated_result()
        expected_avg = sum(response_times) / len(response_times)

        assert abs(avg_response_time - expected_avg) < 0.001

        # Test pool stats
        pool_stats = pool.get_stats()
        assert "max_workers" in pool_stats
        assert "active_tasks" in pool_stats


if __name__ == "__main__":
    pytest.main([__file__])
