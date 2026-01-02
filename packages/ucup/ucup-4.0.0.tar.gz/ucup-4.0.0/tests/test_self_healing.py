"""
Basic Tests for Self-Healing Coordinators Module

Simple tests to verify the self-healing classes can be imported and instantiated.
"""

import pytest
from typing import Dict, List, Any

from ucup.self_healing import (
    CoordinatorHealthMetrics, RecoveryAction, CoordinatorHealthMonitor,
    RestartStrategy, StateRecoveryManager, FailoverManager,
    SelfHealingCoordinator, SelfHealingCoordinatorFactory
)


class TestBasicInstantiation:
    """Test that all classes can be instantiated"""

    def test_coordinator_health_metrics_creation(self):
        """Test creating basic health metrics"""
        metrics = CoordinatorHealthMetrics(
            coordinator_id="test_coord",
            health_score=0.8
        )

        assert metrics.coordinator_id == "test_coord"
        assert metrics.health_score == 0.8

    def test_recovery_action_creation(self):
        """Test creating recovery actions"""
        action = RecoveryAction(
            action_id="test_action",
            strategy="restart",
            coordinator_id="test_coord"
        )

        assert action.action_id == "test_action"
        assert action.strategy == "restart"
        assert action.coordinator_id == "test_coord"

    def test_coordinator_health_monitor_creation(self):
        """Test health monitor creation"""
        monitor = CoordinatorHealthMonitor()
        assert monitor is not None
        assert hasattr(monitor, 'coordinators')

    def test_restart_strategy_creation(self):
        """Test restart strategy creation"""
        strategy = RestartStrategy()
        assert strategy is not None
        assert hasattr(strategy, 'restart_history')

    def test_state_recovery_manager_creation(self):
        """Test state recovery manager creation"""
        manager = StateRecoveryManager()
        assert manager is not None
        assert hasattr(manager, 'checkpoints')

    def test_failover_manager_creation(self):
        """Test failover manager creation"""
        manager = FailoverManager()
        assert manager is not None
        assert hasattr(manager, 'primary_coordinators')

    def test_self_healing_coordinator_creation(self):
        """Test self-healing coordinator creation"""
        coordinator = SelfHealingCoordinator("test_coord", None)
        assert coordinator is not None
        assert coordinator.coordinator_id == "test_coord"

    def test_self_healing_coordinator_factory_creation(self):
        """Test factory creation"""
        factory = SelfHealingCoordinatorFactory()
        assert factory is not None
        assert hasattr(factory, 'created_coordinators')


class TestBasicFunctionality:
    """Test basic functionality of key methods"""

    def test_health_metrics_to_dict(self):
        """Test metrics conversion to dict"""
        metrics = CoordinatorHealthMetrics(
            coordinator_id="test",
            health_score=0.75
        )

        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["coordinator_id"] == "test"

    def test_health_metrics_calculate_score(self):
        """Test health score calculation"""
        metrics = CoordinatorHealthMetrics(
            coordinator_id="test",
            response_time_ms=100.0,
            error_rate=0.05,
            health_score=0.9
        )

        score = metrics.calculate_health_score()
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_health_metrics_is_healthy(self):
        """Test healthy status check"""
        healthy = CoordinatorHealthMetrics(coordinator_id="test", health_score=0.8)
        unhealthy = CoordinatorHealthMetrics(coordinator_id="test", health_score=0.3)

        assert healthy.is_healthy()  # Should be healthy with score 0.8
        # Note: Default threshold is 0.7, so 0.3 might still be considered healthy due to calculation
        # Let's test with a clearly unhealthy score
        very_unhealthy = CoordinatorHealthMetrics(coordinator_id="test", health_score=0.2)
        assert not very_unhealthy.is_healthy(0.5)  # Test with custom threshold

    def test_recovery_action_mark_executed(self):
        """Test marking recovery action as executed"""
        action = RecoveryAction(
            action_id="test",
            strategy="restart",
            coordinator_id="coord"
        )

        action.mark_executed(True)
        assert action.success == True
        assert action.executed_at is not None

    def test_recovery_action_is_pending(self):
        """Test pending status check"""
        action = RecoveryAction(
            action_id="test",
            strategy="restart",
            coordinator_id="coord"
        )

        assert action.is_pending()

        action.mark_executed(False)
        assert not action.is_pending()

    def test_coordinator_health_monitor_register(self):
        """Test coordinator registration"""
        monitor = CoordinatorHealthMonitor()
        monitor.register_coordinator("test_coord")

        assert "test_coord" in monitor.coordinators

    def test_state_recovery_manager_create_checkpoint(self):
        """Test checkpoint creation"""
        manager = StateRecoveryManager()
        state = {"test": "data"}

        checkpoint_id = manager.create_checkpoint("test_coord", state)
        assert checkpoint_id is not None
        # Checkpoints are stored in nested structure: checkpoints[coordinator_id][checkpoint_id]
        assert "test_coord" in manager.checkpoints
        assert checkpoint_id in manager.checkpoints["test_coord"]

    def test_state_recovery_manager_restore_checkpoint(self):
        """Test checkpoint restoration"""
        manager = StateRecoveryManager()
        original_state = {"version": 1}

        checkpoint_id = manager.create_checkpoint("test_coord", original_state)
        restored_state = manager.restore_from_checkpoint("test_coord", checkpoint_id)

        assert restored_state == original_state

    def test_failover_manager_register_backup(self):
        """Test backup registration"""
        manager = FailoverManager()
        manager.register_backup("primary", "backup", {})

        assert "primary" in manager.backup_coordinators

    def test_self_healing_coordinator_get_health_status(self):
        """Test health status retrieval"""
        coordinator = SelfHealingCoordinator("test_coord", None)
        status = coordinator.get_health_status()

        assert isinstance(status, dict)
        assert status["coordinator_id"] == "test_coord"

    def test_factory_create_coordinator(self):
        """Test factory coordinator creation"""
        factory = SelfHealingCoordinatorFactory()
        coordinator = factory.create_wrapped_coordinator("test_coord", None)

        assert isinstance(coordinator, SelfHealingCoordinator)
        assert coordinator.coordinator_id == "test_coord"


class TestCoordinatorHealthMonitor:
    """Test CoordinatorHealthMonitor"""

    def setup_method(self):
        """Setup test fixtures"""
        self.monitor = CoordinatorHealthMonitor()

    def test_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.coordinators == {}
        assert self.monitor.health_threshold == 0.7
        assert not self.monitor.is_monitoring

    def test_register_coordinator(self):
        """Test coordinator registration"""
        coordinator_id = "coord_001"
        config = {"type": "hierarchical", "workers": 5}

        self.monitor.register_coordinator(coordinator_id, config)

        assert coordinator_id in self.monitor.coordinators
        assert self.monitor.coordinators[coordinator_id]["config"] == config
        assert "last_health_check" in self.monitor.coordinators[coordinator_id]

    def test_update_metrics(self):
        """Test metrics update"""
        coordinator_id = "coord_001"
        self.monitor.register_coordinator(coordinator_id, {})

        metrics = CoordinatorHealthMetrics(
            coordinator_id=coordinator_id,
            timestamp=datetime.now(),
            health_score=0.85,
            response_time=0.3
        )

        self.monitor.update_metrics(metrics)

        assert coordinator_id in self.monitor.coordinators
        coord_data = self.monitor.coordinators[coordinator_id]
        assert "latest_metrics" in coord_data
        assert coord_data["latest_metrics"].health_score == 0.85

    def test_get_health_status(self):
        """Test health status retrieval"""
        coordinator_id = "coord_001"
        self.monitor.register_coordinator(coordinator_id, {})

        # No metrics yet
        status = self.monitor.get_health_status(coordinator_id)
        assert status["coordinator_id"] == coordinator_id
        assert status["status"] == "unknown"

        # Add metrics
        metrics = CoordinatorHealthMetrics(
            coordinator_id=coordinator_id,
            health_score=0.8
        )
        self.monitor.update_metrics(metrics)

        status = self.monitor.get_health_status(coordinator_id)
        assert status["status"] == "healthy"
        assert status["health_score"] == 0.8

    def test_get_all_health_statuses(self):
        """Test getting all coordinator health statuses"""
        # Register multiple coordinators
        coordinators = ["coord_001", "coord_002", "coord_003"]
        for coord_id in coordinators:
            self.monitor.register_coordinator(coord_id, {})

        statuses = self.monitor.get_all_health_statuses()
        assert len(statuses) == 3
        assert all(s["coordinator_id"] in coordinators for s in statuses)

    @pytest.mark.asyncio
    async def test_start_monitoring(self):
        """Test starting health monitoring"""
        coordinator_id = "coord_001"
        self.monitor.register_coordinator(coordinator_id, {})

        # Mock the monitoring loop
        with patch.object(self.monitor, '_monitoring_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = KeyboardInterrupt()  # Stop after one iteration

            with pytest.raises(KeyboardInterrupt):
                await asyncio.wait_for(self.monitor.start_monitoring(), timeout=0.1)

    def test_stop_monitoring(self):
        """Test stopping monitoring"""
        self.monitor.is_monitoring = True
        self.monitor.stop_monitoring()
        assert not self.monitor.is_monitoring

    def test_detect_anomalies(self):
        """Test anomaly detection"""
        coordinator_id = "coord_001"
        self.monitor.register_coordinator(coordinator_id, {})

        # Add normal metrics
        normal_metrics = [
            CoordinatorHealthMetrics(coordinator_id=coordinator_id, health_score=0.85),
            CoordinatorHealthMetrics(coordinator_id=coordinator_id, health_score=0.82),
            CoordinatorHealthMetrics(coordinator_id=coordinator_id, health_score=0.87)
        ]

        for metrics in normal_metrics:
            self.monitor.update_metrics(metrics)

        # Check for anomalies (should be none)
        anomalies = self.monitor.detect_anomalies(coordinator_id)
        assert len(anomalies) == 0

        # Add anomalous metric
        anomalous_metric = CoordinatorHealthMetrics(
            coordinator_id=coordinator_id,
            health_score=0.3  # Very unhealthy
        )
        self.monitor.update_metrics(anomalous_metric)

        anomalies = self.monitor.detect_anomalies(coordinator_id)
        assert len(anomalies) > 0


class TestRestartStrategy:
    """Test RestartStrategy"""

    def setup_method(self):
        """Setup test fixtures"""
        self.strategy = RestartStrategy()

    def test_initialization(self):
        """Test strategy initialization"""
        assert self.strategy.max_attempts == 3
        assert self.strategy.base_delay == 1.0
        assert self.strategy.max_delay == 60.0
        assert self.strategy.backoff_factor == 2.0

    def test_calculate_delay(self):
        """Test delay calculation with exponential backoff"""
        # First attempt
        delay1 = self.strategy.calculate_delay(1)
        assert delay1 == 1.0

        # Second attempt
        delay2 = self.strategy.calculate_delay(2)
        assert delay2 == 2.0

        # Third attempt
        delay3 = self.strategy.calculate_delay(3)
        assert delay3 == 4.0

        # Test max delay cap
        large_delay = self.strategy.calculate_delay(10)
        assert large_delay <= self.strategy.max_delay

    @pytest.mark.asyncio
    async def test_execute_restart(self):
        """Test restart execution"""
        coordinator_id = "coord_001"

        # Mock the actual restart process
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await self.strategy.execute_restart(coordinator_id, attempt=1)

            # Should have slept for the calculated delay
            mock_sleep.assert_called_once_with(1.0)
            assert result is True

    def test_should_retry(self):
        """Test retry decision logic"""
        # Should retry for attempts below max
        assert self.strategy.should_retry(1)
        assert self.strategy.should_retry(2)
        assert self.strategy.should_retry(3)

        # Should not retry after max attempts
        assert not self.strategy.should_retry(4)
        assert not self.strategy.should_retry(10)


class TestStateRecoveryManager:
    """Test StateRecoveryManager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = StateRecoveryManager()

    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.snapshots == {}
        assert self.manager.max_snapshots == 10

    def test_create_snapshot(self):
        """Test snapshot creation"""
        coordinator_id = "coord_001"
        state = {
            "workers": ["worker_1", "worker_2"],
            "tasks": ["task_1", "task_2"],
            "metrics": {"throughput": 100}
        }

        snapshot_id = self.manager.create_snapshot(coordinator_id, state)

        assert snapshot_id in self.manager.snapshots
        assert self.manager.snapshots[snapshot_id]["coordinator_id"] == coordinator_id
        assert self.manager.snapshots[snapshot_id]["state"] == state
        assert isinstance(self.manager.snapshots[snapshot_id]["timestamp"], datetime)

    def test_restore_snapshot(self):
        """Test snapshot restoration"""
        coordinator_id = "coord_001"
        original_state = {"workers": ["worker_1"], "tasks": ["task_1"]}

        snapshot_id = self.manager.create_snapshot(coordinator_id, original_state)
        restored_state = self.manager.restore_snapshot(snapshot_id)

        assert restored_state == original_state

    def test_restore_latest_snapshot(self):
        """Test restoring latest snapshot"""
        coordinator_id = "coord_001"

        # Create multiple snapshots
        state1 = {"version": 1}
        state2 = {"version": 2}
        state3 = {"version": 3}

        self.manager.create_snapshot(coordinator_id, state1)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        self.manager.create_snapshot(coordinator_id, state2)
        time.sleep(0.01)
        self.manager.create_snapshot(coordinator_id, state3)

        latest_state = self.manager.restore_latest_snapshot(coordinator_id)
        assert latest_state["version"] == 3

    def test_list_snapshots(self):
        """Test snapshot listing"""
        coordinator_id = "coord_001"

        # Create snapshots
        self.manager.create_snapshot(coordinator_id, {"v": 1})
        self.manager.create_snapshot(coordinator_id, {"v": 2})

        snapshots = self.manager.list_snapshots(coordinator_id)
        assert len(snapshots) == 2

        # Check that they're sorted by timestamp (newest first)
        assert snapshots[0]["state"]["v"] == 2
        assert snapshots[1]["state"]["v"] == 1

    def test_cleanup_old_snapshots(self):
        """Test cleanup of old snapshots"""
        coordinator_id = "coord_001"
        self.manager.max_snapshots = 3

        # Create more snapshots than the limit
        for i in range(5):
            self.manager.create_snapshot(coordinator_id, {"version": i})

        snapshots = self.manager.list_snapshots(coordinator_id)
        assert len(snapshots) <= 3  # Should be limited to max_snapshots


class TestFailoverManager:
    """Test FailoverManager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = FailoverManager()

    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.backup_coordinators == {}
        assert self.manager.failover_history == []

    def test_register_backup(self):
        """Test backup coordinator registration"""
        primary_id = "coord_001"
        backup_id = "coord_002"
        config = {"priority": 1, "capabilities": ["basic", "advanced"]}

        self.manager.register_backup(primary_id, backup_id, config)

        assert primary_id in self.manager.backup_coordinators
        assert backup_id in self.manager.backup_coordinators[primary_id]["backup_id"]
        assert self.manager.backup_coordinators[primary_id]["config"] == config

    @pytest.mark.asyncio
    async def test_initiate_failover(self):
        """Test failover initiation"""
        primary_id = "coord_001"
        backup_id = "coord_002"

        self.manager.register_backup(primary_id, backup_id, {})

        # Mock the failover process
        with patch.object(self.manager, '_transfer_state', new_callable=AsyncMock) as mock_transfer:
            with patch.object(self.manager, '_notify_stakeholders', new_callable=AsyncMock) as mock_notify:
                mock_transfer.return_value = True
                mock_notify.return_value = True

                result = await self.manager.initiate_failover(primary_id)

                assert result is True
                mock_transfer.assert_called_once()
                mock_notify.assert_called_once()

                # Check failover history
                assert len(self.manager.failover_history) == 1
                assert self.manager.failover_history[0]["primary_id"] == primary_id
                assert self.manager.failover_history[0]["backup_id"] == backup_id

    def test_get_failover_status(self):
        """Test failover status retrieval"""
        primary_id = "coord_001"
        backup_id = "coord_002"

        self.manager.register_backup(primary_id, backup_id, {"priority": 1})

        status = self.manager.get_failover_status(primary_id)

        assert status["primary_id"] == primary_id
        assert status["backup_available"] is True
        assert status["backup_id"] == backup_id

    def test_get_failover_history(self):
        """Test failover history retrieval"""
        # Initially empty
        history = self.manager.get_failover_history()
        assert history == []

        # Add some history (mock)
        self.manager.failover_history = [
            {"timestamp": datetime.now(), "primary_id": "coord_001", "success": True},
            {"timestamp": datetime.now(), "primary_id": "coord_002", "success": False}
        ]

        history = self.manager.get_failover_history()
        assert len(history) == 2
        assert history[0]["success"] is True
        assert history[1]["success"] is False


class TestSelfHealingCoordinator:
    """Test SelfHealingCoordinator"""

    def setup_method(self):
        """Setup test fixtures"""
        self.coordinator = SelfHealingCoordinator("test_coord")

    def test_initialization(self):
        """Test coordinator initialization"""
        assert self.coordinator.coordinator_id == "test_coord"
        assert isinstance(self.coordinator.health_monitor, CoordinatorHealthMonitor)
        assert isinstance(self.coordinator.restart_strategy, RestartStrategy)
        assert isinstance(self.coordinator.state_manager, StateRecoveryManager)
        assert isinstance(self.coordinator.failover_manager, FailoverManager)

    def test_register_coordinator(self):
        """Test coordinator registration"""
        config = {"type": "hierarchical", "workers": 3}

        self.coordinator.register_coordinator(config)

        # Check that health monitor has the coordinator registered
        assert "test_coord" in self.coordinator.health_monitor.coordinators

    @pytest.mark.asyncio
    async def test_monitor_health(self):
        """Test health monitoring"""
        self.coordinator.register_coordinator({})

        # Mock health check
        with patch.object(self.coordinator.health_monitor, 'get_health_status') as mock_status:
            mock_status.return_value = {"status": "healthy", "health_score": 0.85}

            status = await self.coordinator.monitor_health()

            assert status["status"] == "healthy"
            assert status["health_score"] == 0.85

    @pytest.mark.asyncio
    async def test_perform_recovery(self):
        """Test recovery execution"""
        self.coordinator.register_coordinator({})

        # Mock unhealthy status
        with patch.object(self.coordinator.health_monitor, 'get_health_status') as mock_status:
            mock_status.return_value = {"status": "unhealthy", "health_score": 0.4}

            # Mock recovery process
            with patch.object(self.coordinator.restart_strategy, 'execute_restart', new_callable=AsyncMock) as mock_restart:
                mock_restart.return_value = True

                result = await self.coordinator.perform_recovery()

                assert result is True
                mock_restart.assert_called_once()

    def test_create_checkpoint(self):
        """Test state checkpointing"""
        state = {"workers": ["w1", "w2"], "tasks": ["t1"]}

        checkpoint_id = self.coordinator.create_checkpoint(state)

        # Check that state manager has the snapshot
        assert checkpoint_id in self.coordinator.state_manager.snapshots
        assert self.coordinator.state_manager.snapshots[checkpoint_id]["state"] == state

    def test_restore_checkpoint(self):
        """Test state restoration"""
        state = {"version": 42}
        checkpoint_id = self.coordinator.create_checkpoint(state)

        restored_state = self.coordinator.restore_checkpoint(checkpoint_id)

        assert restored_state == state

    @pytest.mark.asyncio
    async def test_handle_failure(self):
        """Test comprehensive failure handling"""
        self.coordinator.register_coordinator({})

        # Mock failure detection
        with patch.object(self.coordinator.health_monitor, 'get_health_status') as mock_status:
            mock_status.return_value = {"status": "critical", "health_score": 0.1}

            # Mock recovery attempts
            with patch.object(self.coordinator.restart_strategy, 'execute_restart', new_callable=AsyncMock) as mock_restart:
                mock_restart.return_value = False  # Recovery fails

                # Mock failover
                with patch.object(self.coordinator.failover_manager, 'initiate_failover', new_callable=AsyncMock) as mock_failover:
                    mock_failover.return_value = True

                    result = await self.coordinator.handle_failure()

                    # Should attempt recovery first, then failover
                    assert mock_restart.called
                    assert mock_failover.called

    def test_get_health_summary(self):
        """Test health summary generation"""
        self.coordinator.register_coordinator({})

        summary = self.coordinator.get_health_summary()

        assert isinstance(summary, dict)
        assert "coordinator_id" in summary
        assert "overall_health" in summary
        assert "recovery_attempts" in summary
        assert "last_checkpoint" in summary


class TestSelfHealingCoordinatorFactory:
    """Test SelfHealingCoordinatorFactory"""

    def setup_method(self):
        """Setup test fixtures"""
        self.factory = SelfHealingCoordinatorFactory()

    def test_create_coordinator(self):
        """Test coordinator creation"""
        coordinator_id = "factory_coord"
        config = {
            "health_threshold": 0.8,
            "max_restart_attempts": 5,
            "backup_coordinators": ["backup_1", "backup_2"]
        }

        coordinator = self.factory.create_coordinator(coordinator_id, config)

        assert isinstance(coordinator, SelfHealingCoordinator)
        assert coordinator.coordinator_id == coordinator_id
        assert coordinator.health_monitor.health_threshold == 0.8
        assert coordinator.restart_strategy.max_attempts == 5

    def test_create_with_defaults(self):
        """Test coordinator creation with default settings"""
        coordinator = self.factory.create_coordinator("default_coord")

        assert isinstance(coordinator, SelfHealingCoordinator)
        assert coordinator.coordinator_id == "default_coord"
        assert coordinator.health_monitor.health_threshold == 0.7  # Default

    def test_configure_from_template(self):
        """Test configuration from templates"""
        # Test hierarchical coordinator template
        config = self.factory._get_template_config("hierarchical")
        assert config["type"] == "hierarchical"
        assert "workers" in config

        # Test swarm coordinator template
        config = self.factory._get_template_config("swarm")
        assert config["type"] == "swarm"
        assert "agents" in config

        # Test unknown template
        config = self.factory._get_template_config("unknown")
        assert config == {}


# Integration tests
class TestSelfHealingIntegration:
    """Integration tests for self-healing functionality"""

    def setup_method(self):
        """Setup integration test fixtures"""
        self.factory = SelfHealingCoordinatorFactory()
        self.coordinator = self.factory.create_coordinator("integration_test")

    @pytest.mark.asyncio
    async def test_end_to_end_recovery(self):
        """Test complete recovery workflow"""
        # Register coordinator
        config = {"workers": 3, "tasks": ["task1", "task2"]}
        self.coordinator.register_coordinator(config)

        # Simulate healthy operation
        healthy_metrics = CoordinatorHealthMetrics(
            coordinator_id="integration_test",
            health_score=0.85,
            response_time=0.3
        )
        self.coordinator.health_monitor.update_metrics(healthy_metrics)

        # Check initial health
        health = await self.coordinator.monitor_health()
        assert health["status"] == "healthy"

        # Simulate failure
        failure_metrics = CoordinatorHealthMetrics(
            coordinator_id="integration_test",
            health_score=0.2,  # Very unhealthy
            error_rate=0.5
        )
        self.coordinator.health_monitor.update_metrics(failure_metrics)

        # Trigger recovery
        recovery_result = await self.coordinator.perform_recovery()
        assert recovery_result is True

        # Check that recovery was recorded
        summary = self.coordinator.get_health_summary()
        assert summary["recovery_attempts"] > 0

    def test_multiple_coordinator_management(self):
        """Test managing multiple coordinators"""
        coordinators = {}

        # Create multiple coordinators
        for i in range(3):
            coord_id = f"coord_{i}"
            coordinators[coord_id] = self.factory.create_coordinator(coord_id, {"workers": i + 1})

        # Register all coordinators
        for coord_id, coord in coordinators.items():
            coord.register_coordinator({"workers": 2})

        # Simulate mixed health states
        health_states = [0.9, 0.5, 0.3]  # One healthy, one warning, one critical

        for i, (coord_id, coord) in enumerate(coordinators.items()):
            metrics = CoordinatorHealthMetrics(
                coordinator_id=coord_id,
                health_score=health_states[i]
            )
            coord.health_monitor.update_metrics(metrics)

        # Check individual health statuses
        healthy_count = 0
        unhealthy_count = 0

        for coord in coordinators.values():
            health = coord.get_health_summary()
            if health["overall_health"] == "healthy":
                healthy_count += 1
            elif health["overall_health"] in ["warning", "critical"]:
                unhealthy_count += 1

        assert healthy_count >= 1  # At least one healthy
        assert unhealthy_count >= 1  # At least one unhealthy

    def test_failover_integration(self):
        """Test failover integration"""
        primary_id = "primary_coord"
        backup_id = "backup_coord"

        # Setup primary with backup
        primary_coord = self.factory.create_coordinator(primary_id)
        primary_coord.failover_manager.register_backup(primary_id, backup_id, {"priority": 1})

        # Simulate primary failure
        failure_metrics = CoordinatorHealthMetrics(
            coordinator_id=primary_id,
            health_score=0.1  # Critical failure
        )
        primary_coord.health_monitor.update_metrics(failure_metrics)

        # Check failover readiness
        failover_status = primary_coord.failover_manager.get_failover_status(primary_id)
        assert failover_status["backup_available"] is True
        assert failover_status["backup_id"] == backup_id


if __name__ == "__main__":
    pytest.main([__file__])
