"""
Tests for Predictive Failure Detection Module

This module contains comprehensive tests for the predictive failure detection
capabilities including ML models, feature extraction, and failure prediction.
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

from ucup.predictive_failure import (
    FailurePrediction, FeatureVector, FailureFeatureExtractor,
    FailurePredictionModel, GradientBoostingFailurePredictor,
    NeuralFailurePredictor, PredictiveFailureDetector, FailureTrainingPipeline
)


class TestFailurePrediction:
    """Test FailurePrediction dataclass"""

    def test_creation(self):
        """Test creating a failure prediction"""
        prediction = FailurePrediction(
            failure_type="memory_leak",
            probability=0.85,
            confidence=0.92,
            predicted_time=datetime.now() + timedelta(hours=2),
            feature_importance={"memory_usage": 0.6, "error_rate": 0.3, "cpu_usage": 0.1}
        )

        assert prediction.failure_type == "memory_leak"
        assert prediction.probability == 0.85
        assert prediction.confidence == 0.92
        assert isinstance(prediction.predicted_time, datetime)
        assert len(prediction.feature_importance) == 3

    def test_to_dict(self):
        """Test conversion to dictionary"""
        prediction = FailurePrediction(
            failure_type="network_timeout",
            probability=0.78,
            confidence=0.89,
            predicted_time=datetime(2024, 1, 1, 12, 0),
            feature_importance={"latency": 0.5, "packet_loss": 0.3}
        )

        result = prediction.to_dict()
        assert result["failure_type"] == "network_timeout"
        assert result["probability"] == 0.78
        assert result["confidence"] == 0.89
        assert "predicted_time" in result
        assert "feature_importance" in result


class TestFeatureVector:
    """Test FeatureVector dataclass"""

    def test_creation(self):
        """Test creating a feature vector"""
        features = {
            "cpu_usage": 85.5,
            "memory_usage": 92.1,
            "error_rate": 0.05,
            "response_time": 2.3,
            "throughput": 150.0
        }

        vector = FeatureVector(
            features=features,
            timestamp=datetime.now(),
            session_id="test_session_001",
            metadata={"environment": "test"}
        )

        assert vector.features == features
        assert isinstance(vector.timestamp, datetime)
        assert vector.session_id == "test_session_001"
        assert vector.metadata["environment"] == "test"

    def test_feature_validation(self):
        """Test feature validation"""
        # Valid features
        features = {"cpu_usage": 50.0, "memory_usage": 60.0}
        vector = FeatureVector(features=features, timestamp=datetime.now())
        assert len(vector.features) == 2

        # Test with invalid feature types (should be numeric)
        with pytest.raises(ValueError):
            FeatureVector(features={"invalid": "string"}, timestamp=datetime.now())


class TestFailureFeatureExtractor:
    """Test FailureFeatureExtractor class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.extractor = FailureFeatureExtractor()

    def test_extract_from_agent_session(self):
        """Test feature extraction from agent session data"""
        session_data = {
            "agent_id": "agent_001",
            "session_start": datetime.now() - timedelta(hours=1),
            "session_end": datetime.now(),
            "operations": [
                {"type": "inference", "duration": 0.5, "success": True, "confidence": 0.9},
                {"type": "inference", "duration": 1.2, "success": False, "error": "timeout"},
                {"type": "training", "duration": 10.0, "success": True, "loss": 0.1}
            ],
            "metrics": {
                "cpu_usage": [45.0, 67.0, 89.0],
                "memory_usage": [60.0, 75.0, 85.0],
                "error_rate": 0.1,
                "avg_response_time": 0.8
            }
        }

        features = self.extractor.extract_from_agent_session(session_data)

        assert isinstance(features, dict)
        assert "session_duration" in features
        assert "operation_count" in features
        assert "success_rate" in features
        assert "error_rate" in features
        assert "avg_cpu_usage" in features
        assert "avg_memory_usage" in features
        assert "avg_response_time" in features

        # Check that values are reasonable
        assert features["success_rate"] == 2/3  # 2 successful out of 3 operations
        assert features["operation_count"] == 3

    def test_extract_from_system_metrics(self):
        """Test feature extraction from system metrics"""
        metrics_data = {
            "timestamp": datetime.now(),
            "system_metrics": {
                "cpu_percent": 75.5,
                "memory_percent": 82.3,
                "disk_usage_percent": 45.0,
                "network_io": {"bytes_sent": 1024, "bytes_recv": 2048},
                "process_count": 42
            },
            "application_metrics": {
                "active_connections": 15,
                "queue_length": 5,
                "error_count": 3,
                "response_time_avg": 1.2
            }
        }

        features = self.extractor.extract_from_system_metrics(metrics_data)

        assert isinstance(features, dict)
        assert "cpu_percent" in features
        assert "memory_percent" in features
        assert "disk_usage_percent" in features
        assert "network_bytes_total" in features
        assert "process_count" in features
        assert "active_connections" in features
        assert "queue_length" in features
        assert "error_count" in features
        assert "response_time_avg" in features

    def test_extract_temporal_features(self):
        """Test temporal feature extraction"""
        # Create time series data
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(10, 0, -1)]
        values = [50 + i + np.random.normal(0, 5) for i in range(10)]

        time_series = list(zip(timestamps, values))

        features = self.extractor.extract_temporal_features(time_series, "test_metric")

        assert isinstance(features, dict)
        assert "test_metric_mean" in features
        assert "test_metric_std" in features
        assert "test_metric_trend" in features
        assert "test_metric_volatility" in features

    def test_normalize_features(self):
        """Test feature normalization"""
        raw_features = {
            "cpu_usage": 85.0,
            "memory_usage": 92.0,
            "error_rate": 0.05,
            "response_time": 2.5
        }

        normalized = self.extractor.normalize_features(raw_features)

        assert isinstance(normalized, dict)
        # Check that all features are in [0, 1] range after normalization
        for key, value in normalized.items():
            assert 0.0 <= value <= 1.0, f"Feature {key} not properly normalized: {value}"


class TestGradientBoostingFailurePredictor:
    """Test GradientBoostingFailurePredictor"""

    def setup_method(self):
        """Setup test fixtures"""
        self.predictor = GradientBoostingFailurePredictor()

    @patch('sklearn.ensemble.GradientBoostingClassifier')
    def test_train(self, mock_gb):
        """Test model training"""
        # Mock the sklearn model
        mock_model = Mock()
        mock_gb.return_value = mock_model
        mock_model.fit.return_value = mock_model
        mock_model.score.return_value = 0.85

        # Training data
        X_train = np.random.rand(100, 5)
        y_train = np.random.randint(0, 2, 100)

        self.predictor.train(X_train, y_train)

        assert mock_model.fit.called
        assert self.predictor.is_trained

    @patch('sklearn.ensemble.GradientBoostingClassifier')
    def test_predict(self, mock_gb):
        """Test prediction"""
        # Setup trained model
        mock_model = Mock()
        mock_gb.return_value = mock_model
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7], [0.8, 0.2]])

        self.predictor.model = mock_model
        self.predictor.is_trained = True

        # Test data
        X_test = np.random.rand(2, 5)
        predictions = self.predictor.predict(X_test)

        assert len(predictions) == 2
        assert 0.0 <= predictions[0] <= 1.0
        assert 0.0 <= predictions[1] <= 1.0

    def test_predict_untrained(self):
        """Test prediction with untrained model"""
        X_test = np.random.rand(2, 5)

        with pytest.raises(RuntimeError, match="Model not trained"):
            self.predictor.predict(X_test)

    def test_get_feature_importance(self):
        """Test feature importance retrieval"""
        # Mock trained model
        mock_model = Mock()
        mock_model.feature_importances_ = np.array([0.3, 0.2, 0.25, 0.15, 0.1])

        self.predictor.model = mock_model
        self.predictor.is_trained = True
        self.predictor.feature_names = ['cpu', 'memory', 'disk', 'network', 'errors']

        importance = self.predictor.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) == 5
        assert importance['cpu'] == 0.3
        assert importance['memory'] == 0.2


class TestNeuralFailurePredictor:
    """Test NeuralFailurePredictor"""

    def setup_method(self):
        """Setup test fixtures"""
        self.predictor = NeuralFailurePredictor()

    @patch('torch.nn.Module')
    @patch('torch.optim.Adam')
    def test_train(self, mock_optimizer, mock_module):
        """Test neural network training"""
        # Mock PyTorch components
        mock_model = Mock()
        mock_module.return_value = mock_model
        mock_model.parameters.return_value = []

        mock_opt = Mock()
        mock_optimizer.return_value = mock_opt

        # Mock training loop
        with patch('torch.tensor') as mock_tensor:
            mock_tensor.return_value = Mock()

            X_train = np.random.rand(50, 10)
            y_train = np.random.randint(0, 2, 50)

            self.predictor.train(X_train, y_train, epochs=5)

            assert self.predictor.is_trained

    def test_predict_untrained(self):
        """Test prediction with untrained model"""
        X_test = np.random.rand(2, 10)

        with pytest.raises(RuntimeError, match="Model not trained"):
            self.predictor.predict(X_test)


class TestPredictiveFailureDetector:
    """Test PredictiveFailureDetector"""

    def setup_method(self):
        """Setup test fixtures"""
        self.detector = PredictiveFailureDetector()

    def test_initialization(self):
        """Test detector initialization"""
        assert self.detector.models == {}
        assert self.detector.failure_threshold == 0.7
        assert not self.detector.is_active

    def test_add_model(self):
        """Test adding prediction models"""
        model = GradientBoostingFailurePredictor()
        self.detector.add_model("memory_failure", model)

        assert "memory_failure" in self.detector.models
        assert self.detector.models["memory_failure"] == model

    @patch('asyncio.Queue')
    async def test_start_monitoring(self, mock_queue):
        """Test starting monitoring"""
        mock_queue_instance = Mock()
        mock_queue.return_value = mock_queue_instance
        mock_queue_instance.get.side_effect = [Mock(), KeyboardInterrupt()]

        # Add a mock model
        model = Mock()
        model.predict.return_value = np.array([0.8])
        self.detector.add_model("test_failure", model)

        # This will run until KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            await asyncio.wait_for(self.detector.start_monitoring(), timeout=0.1)

    def test_analyze_session_data(self):
        """Test session data analysis"""
        session_data = {
            "agent_id": "agent_001",
            "operations": [
                {"success": True, "duration": 0.5},
                {"success": False, "duration": 2.0},
                {"success": True, "duration": 0.8}
            ],
            "metrics": {
                "cpu_usage": [50.0, 75.0, 90.0],
                "memory_usage": [60.0, 80.0, 95.0]
            }
        }

        features = self.detector.analyze_session_data(session_data)

        assert isinstance(features, dict)
        assert "session_duration" in features
        assert "success_rate" in features
        assert "avg_cpu_usage" in features

    def test_detect_failures(self):
        """Test failure detection"""
        # Mock model
        model = Mock()
        model.predict.return_value = np.array([0.85])  # High failure probability
        model.get_feature_importance.return_value = {"cpu": 0.6, "memory": 0.4}

        self.detector.add_model("high_load_failure", model)

        features = {"cpu_usage": 95.0, "memory_usage": 90.0}

        predictions = self.detector.detect_failures(features)

        assert len(predictions) == 1
        assert predictions[0].failure_type == "high_load_failure"
        assert predictions[0].probability == 0.85

    def test_get_health_status(self):
        """Test health status retrieval"""
        status = self.detector.get_health_status()

        assert isinstance(status, dict)
        assert "is_active" in status
        assert "models_count" in status
        assert "last_analysis" in status

    def test_stop_monitoring(self):
        """Test stopping monitoring"""
        self.detector.is_active = True
        self.detector.stop_monitoring()

        assert not self.detector.is_active


class TestFailureTrainingPipeline:
    """Test FailureTrainingPipeline"""

    def setup_method(self):
        """Setup test fixtures"""
        self.pipeline = FailureTrainingPipeline()

    @patch('pandas.read_csv')
    def test_load_training_data(self, mock_read_csv):
        """Test loading training data"""
        # Mock DataFrame
        mock_df = Mock()
        mock_df.shape = (1000, 10)
        mock_read_csv.return_value = mock_df

        data = self.pipeline.load_training_data("fake_path.csv")

        assert data == mock_df
        mock_read_csv.assert_called_once_with("fake_path.csv")

    def test_preprocess_data(self):
        """Test data preprocessing"""
        # Create mock data
        data = pd.DataFrame({
            'cpu_usage': [50, 75, 90, None, 85],
            'memory_usage': [60, 80, 95, 70, 88],
            'is_failure': [0, 0, 1, 0, 1]
        })

        X, y = self.pipeline.preprocess_data(data)

        assert X.shape[0] == 5  # All rows kept
        assert len(y) == 5
        assert list(y) == [0, 0, 1, 0, 1]

    @patch('sklearn.model_selection.train_test_split')
    def test_split_data(self, mock_split):
        """Test data splitting"""
        mock_split.return_value = (Mock(), Mock(), Mock(), Mock())

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)

        X_train, X_test, y_train, y_test = self.pipeline.split_data(X, y, test_size=0.2)

        mock_split.assert_called_once()
        assert X_train is not None
        assert X_test is not None

    def test_train_models(self):
        """Test training multiple models"""
        X_train = np.random.rand(80, 5)
        y_train = np.random.randint(0, 2, 80)

        results = self.pipeline.train_models(X_train, y_train)

        assert isinstance(results, dict)
        assert "gradient_boosting" in results
        assert "neural_network" in results

        # Check that models are trained
        for model_name, model_info in results.items():
            assert "model" in model_info
            assert "accuracy" in model_info

    def test_evaluate_models(self):
        """Test model evaluation"""
        # Mock trained models
        models = {
            "gradient_boosting": {"model": Mock()},
            "neural_network": {"model": Mock()}
        }

        X_test = np.random.rand(20, 5)
        y_test = np.random.randint(0, 2, 20)

        # Mock predict methods
        for model_info in models.values():
            model_info["model"].predict.return_value = y_test  # Perfect predictions
            model_info["model"].predict_proba.return_value = np.random.rand(20, 2)

        results = self.pipeline.evaluate_models(models, X_test, y_test)

        assert isinstance(results, dict)
        for model_name in models.keys():
            assert model_name in results
            assert "accuracy" in results[model_name]
            assert "precision" in results[model_name]
            assert "recall" in results[model_name]
            assert "f1_score" in results[model_name]

    def test_save_models(self):
        """Test model saving"""
        models = {
            "test_model": {"model": Mock(), "accuracy": 0.85}
        }

        with patch('joblib.dump') as mock_dump:
            self.pipeline.save_models(models, "test_dir")

            # Should be called for each model
            assert mock_dump.call_count == 1

    def test_run_pipeline(self):
        """Test complete pipeline execution"""
        # This is an integration test that would require more extensive mocking
        # For now, just test that the method exists and can be called
        assert hasattr(self.pipeline, 'run_pipeline')
        assert callable(self.pipeline.run_pipeline)


# Integration tests
class TestPredictiveFailureIntegration:
    """Integration tests for predictive failure detection"""

    def setup_method(self):
        """Setup integration test fixtures"""
        self.detector = PredictiveFailureDetector()
        self.pipeline = FailureTrainingPipeline()

    def test_end_to_end_prediction(self):
        """Test end-to-end failure prediction workflow"""
        # 1. Create training data
        np.random.seed(42)
        n_samples = 1000
        n_features = 5

        X = np.random.rand(n_samples, n_features)
        # Create synthetic failure patterns
        y = ((X[:, 0] > 0.8) & (X[:, 1] > 0.8)).astype(int)  # Failures when CPU and memory are high

        # 2. Train a model
        model = GradientBoostingFailurePredictor()
        model.train(X, y)

        # 3. Add to detector
        self.detector.add_model("resource_failure", model)

        # 4. Test prediction
        test_features = {
            "feature_0": 0.9,  # High CPU
            "feature_1": 0.9,  # High memory
            "feature_2": 0.5,
            "feature_3": 0.3,
            "feature_4": 0.7
        }

        # Convert to feature vector format
        feature_vector = np.array([test_features[f"feature_{i}"] for i in range(n_features)])

        predictions = self.detector.detect_failures(feature_vector)

        assert len(predictions) == 1
        assert predictions[0].failure_type == "resource_failure"
        assert isinstance(predictions[0].probability, (int, float))
        assert 0.0 <= predictions[0].probability <= 1.0

    def test_multiple_failure_types(self):
        """Test detection of multiple failure types"""
        # Create models for different failure types
        models = {
            "memory_leak": GradientBoostingFailurePredictor(),
            "cpu_overload": GradientBoostingFailurePredictor(),
            "network_failure": GradientBoostingFailurePredictor()
        }

        # Train each model (simplified)
        np.random.seed(42)
        X = np.random.rand(500, 3)
        for name, model in models.items():
            if name == "memory_leak":
                y = (X[:, 1] > 0.85).astype(int)  # Memory-related failures
            elif name == "cpu_overload":
                y = (X[:, 0] > 0.9).astype(int)   # CPU-related failures
            else:
                y = (X[:, 2] > 0.95).astype(int)  # Network-related failures

            model.train(X, y)
            self.detector.add_model(name, model)

        # Test with high values across all metrics
        test_features = np.array([0.95, 0.95, 0.95])  # High CPU, memory, network

        predictions = self.detector.detect_failures(test_features)

        # Should detect multiple potential failures
        assert len(predictions) >= 1

        # Check that predictions are sorted by probability
        probabilities = [p.probability for p in predictions]
        assert probabilities == sorted(probabilities, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__])
