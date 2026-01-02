"""
<<<<<<< HEAD:framework/src/ucup/multimodal.py
Multimodal Agent Support for UCUP Framework

This module provides advanced multimodal agent capabilities including fusion engines,
real-time streaming processors, and cross-modal knowledge graphs.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Set, Union, AsyncGenerator
from dataclasses import dataclass, field
import asyncio
import numpy as np
from datetime import datetime, timedelta
import json

from .probabilistic import ProbabilisticAgent, ProbabilisticResult, AgentState
from .validation import validate_probability, UCUPValidationError
from .observability import DecisionTracer


@dataclass
class MultimodalInput:
    """Represents multimodal input data with multiple modalities."""

    text: Optional[str] = None
    image: Optional[bytes] = None
    audio: Optional[bytes] = None
    sensor_data: Optional[Dict[str, Any]] = None
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def has_modality(self, modality: str) -> bool:
        """Check if input contains a specific modality."""
        modality_map = {
            'text': self.text,
            'image': self.image,
            'audio': self.audio,
            'sensor': self.sensor_data,
            'structured': self.structured_data
        }
        return modality_map.get(modality) is not None

    def get_available_modalities(self) -> List[str]:
        """Get list of available modalities in this input."""
        modalities = []
        if self.text: modalities.append('text')
        if self.image: modalities.append('image')
        if self.audio: modalities.append('audio')
        if self.sensor_data: modalities.append('sensor')
        if self.structured_data: modalities.append('structured')
        return modalities


@dataclass
class MultimodalInputBundle:
    """A bundle of multimodal inputs for processing."""

    inputs: List[MultimodalInput] = field(default_factory=list)
    sequence_id: str = ""
    priority: float = 1.0
    processing_deadline: Optional[datetime] = None

    def add_input(self, input_data: MultimodalInput):
        """Add an input to the bundle."""
        self.inputs.append(input_data)

    def get_modality_counts(self) -> Dict[str, int]:
        """Count occurrences of each modality across all inputs."""
        counts = {}
        for input_data in self.inputs:
            for modality in input_data.get_available_modalities():
                counts[modality] = counts.get(modality, 0) + 1
        return counts


@dataclass
class FusionResult:
    """Result of multimodal fusion processing."""

    fused_representation: Any
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    fusion_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    fusion_method: str = "weighted_average"


class MultimodalFusionEngine:
    """Advanced fusion engine for combining multiple modalities."""

    def __init__(self, fusion_strategy: str = "adaptive"):
        self.fusion_strategy = fusion_strategy
        self.modality_weights: Dict[str, float] = {
            'text': 0.4,
            'image': 0.3,
            'audio': 0.2,
            'sensor': 0.1,
            'structured': 0.2
        }
        self.fusion_history: List[FusionResult] = []

    async def fuse_modalities(self, bundle: MultimodalInputBundle) -> FusionResult:
        """Fuse multiple modalities into a unified representation."""
        start_time = asyncio.get_event_loop().time()

        # Extract features from each modality
        modality_features = {}
        confidence_scores = {}

        for modality in ['text', 'image', 'audio', 'sensor', 'structured']:
            features = await self._extract_modality_features(bundle, modality)
            if features:
                modality_features[modality] = features
                confidence_scores[modality] = await self._assess_modality_confidence(bundle, modality)

        # Apply fusion strategy
        if self.fusion_strategy == "adaptive":
            fused_result = await self._adaptive_fusion(modality_features, confidence_scores)
        elif self.fusion_strategy == "hierarchical":
            fused_result = await self._hierarchical_fusion(modality_features, confidence_scores)
        else:
            fused_result = await self._weighted_fusion(modality_features, confidence_scores)

        # Record fusion result
        processing_time = asyncio.get_event_loop().time() - start_time
        result = FusionResult(
            fused_representation=fused_result,
            confidence_scores=confidence_scores,
            fusion_metadata={
                'strategy': self.fusion_strategy,
                'modalities_used': list(modality_features.keys()),
                'input_count': len(bundle.inputs)
            },
            processing_time=processing_time,
            fusion_method=self.fusion_strategy
        )

        self.fusion_history.append(result)
        return result

    async def _extract_modality_features(self, bundle: MultimodalInputBundle, modality: str) -> Optional[Any]:
        """Extract features from a specific modality."""
        # This would integrate with actual ML models for feature extraction
        # For now, return mock features
        features = []

        for input_data in bundle.inputs:
            if input_data.has_modality(modality):
                if modality == 'text' and input_data.text:
                    # Simple text features (word count, sentiment, etc.)
                    features.append({
                        'word_count': len(input_data.text.split()),
                        'has_keywords': any(word in input_data.text.lower()
                                          for word in ['important', 'urgent', 'critical']),
                        'text_length': len(input_data.text)
                    })
                elif modality == 'image' and input_data.image:
                    # Mock image features
                    features.append({
                        'image_size': len(input_data.image),
                        'estimated_complexity': 0.8
                    })
                elif modality == 'audio' and input_data.audio:
                    # Mock audio features
                    features.append({
                        'audio_length': len(input_data.audio),
                        'estimated_clarity': 0.7
                    })
                elif modality == 'sensor' and input_data.sensor_data:
                    # Sensor features
                    features.append(input_data.sensor_data)
                elif modality == 'structured' and input_data.structured_data:
                    # Structured data features
                    features.append(input_data.structured_data)

        return features if features else None

    async def _assess_modality_confidence(self, bundle: MultimodalInputBundle, modality: str) -> float:
        """Assess confidence in a modality's data quality."""
        # Simple confidence assessment based on data completeness
        modality_inputs = [inp for inp in bundle.inputs if inp.has_modality(modality)]
        if not modality_inputs:
            return 0.0

        # Higher confidence for more recent, complete data
        completeness_scores = []
        for inp in modality_inputs:
            if modality == 'text':
                completeness = min(1.0, len(inp.text or "") / 100)  # Normalize to 100 chars
            elif modality == 'image':
                completeness = 1.0 if inp.image else 0.0
            elif modality == 'audio':
                completeness = 1.0 if inp.audio else 0.0
            elif modality == 'sensor':
                completeness = 1.0 if inp.sensor_data else 0.0
            elif modality == 'structured':
                completeness = 1.0 if inp.structured_data else 0.0
            else:
                completeness = 0.0

            # Factor in recency (newer data = higher confidence)
            age_hours = (datetime.now() - inp.timestamp).total_seconds() / 3600
            recency_factor = max(0.1, 1.0 - age_hours / 24)  # Decay over 24 hours

            completeness_scores.append(completeness * recency_factor)

        return np.mean(completeness_scores) if completeness_scores else 0.0

    async def _weighted_fusion(self, modality_features: Dict[str, Any],
                              confidence_scores: Dict[str, float]) -> Any:
        """Simple weighted fusion of modalities."""
        fused_features = {}

        for modality, features in modality_features.items():
            weight = self.modality_weights.get(modality, 0.1)
            confidence = confidence_scores.get(modality, 0.5)
            effective_weight = weight * confidence

            # Apply weighted features
            if isinstance(features, list):
                for feature_set in features:
                    for key, value in feature_set.items():
                        if key not in fused_features:
                            fused_features[key] = []
                        fused_features[key].append((value, effective_weight))

        # Aggregate weighted features
        final_features = {}
        for key, weighted_values in fused_features.items():
            weights = [w for _, w in weighted_values]
            values = [v for v, _ in weighted_values]

            if weights:
                final_features[key] = np.average(values, weights=weights)

        return final_features

    async def _adaptive_fusion(self, modality_features: Dict[str, Any],
                              confidence_scores: Dict[str, float]) -> Any:
        """Adaptive fusion that learns optimal weights."""
        # Start with weighted fusion
        base_fusion = await self._weighted_fusion(modality_features, confidence_scores)

        # Adapt weights based on recent performance
        if len(self.fusion_history) > 5:
            self._adapt_weights_from_history()

        return base_fusion

    async def _hierarchical_fusion(self, modality_features: Dict[str, Any],
                                  confidence_scores: Dict[str, float]) -> Any:
        """Hierarchical fusion with modality grouping."""
        # Group modalities by type
        perception_modalities = ['image', 'audio', 'sensor']
        cognitive_modalities = ['text', 'structured']

        perception_features = {}
        cognitive_features = {}

        for modality, features in modality_features.items():
            if modality in perception_modalities:
                perception_features[modality] = features
            elif modality in cognitive_modalities:
                cognitive_features[modality] = features

        # Fuse within groups first
        perception_fused = await self._weighted_fusion(
            perception_features,
            {k: v for k, v in confidence_scores.items() if k in perception_modalities}
        )

        cognitive_fused = await self._weighted_fusion(
            cognitive_features,
            {k: v for k, v in confidence_scores.items() if k in cognitive_modalities}
        )

        # Then fuse across groups
        group_features = {
            'perception': [perception_fused],
            'cognitive': [cognitive_fused]
        }

        group_weights = {'perception': 0.6, 'cognitive': 0.4}
        group_confidence = {
            'perception': np.mean([confidence_scores.get(m, 0) for m in perception_modalities]) if perception_modalities else 0,
            'cognitive': np.mean([confidence_scores.get(m, 0) for m in cognitive_modalities]) if cognitive_modalities else 0
        }

        return await self._weighted_fusion(group_features, group_confidence)

    def _adapt_weights_from_history(self):
        """Adapt fusion weights based on historical performance."""
        if len(self.fusion_history) < 5:
            return

        # Simple adaptation: increase weights for modalities with high confidence
        recent_results = self.fusion_history[-5:]

        for modality in self.modality_weights:
            modality_confidences = [
                result.confidence_scores.get(modality, 0)
                for result in recent_results
                if modality in result.confidence_scores
            ]

            if modality_confidences:
                avg_confidence = np.mean(modality_confidences)
                # Gradually adjust weight toward confident modalities
                adjustment = 0.01 * (avg_confidence - 0.5)
                self.modality_weights[modality] = np.clip(
                    self.modality_weights[modality] + adjustment, 0.05, 0.8
                )

        # Renormalize weights
        total_weight = sum(self.modality_weights.values())
        if total_weight > 0:
            self.modality_weights = {
                k: v / total_weight for k, v in self.modality_weights.items()
            }


class RealTimeStreamingProcessor:
    """Real-time processing for streaming multimodal data."""

    def __init__(self, buffer_size: int = 100, processing_interval: float = 0.1):
        self.buffer_size = buffer_size
        self.processing_interval = processing_interval
        self.input_buffer: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self.fusion_engine = MultimodalFusionEngine()
        self.is_processing = False
        self.processed_sequences: Dict[str, List[FusionResult]] = {}

    async def start_processing(self):
        """Start real-time processing loop."""
        self.is_processing = True
        asyncio.create_task(self._processing_loop())

    async def stop_processing(self):
        """Stop real-time processing."""
        self.is_processing = False

    async def submit_input(self, bundle: MultimodalInputBundle):
        """Submit a multimodal input bundle for processing."""
        try:
            await asyncio.wait_for(
                self.input_buffer.put(bundle),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            print(f"Warning: Input buffer full, dropping bundle {bundle.sequence_id}")

    async def _processing_loop(self):
        """Main processing loop for real-time fusion."""
        while self.is_processing:
            try:
                # Wait for input or timeout
                bundle = await asyncio.wait_for(
                    self.input_buffer.get(),
                    timeout=self.processing_interval
                )

                # Process the bundle
                fusion_result = await self.fusion_engine.fuse_modalities(bundle)

                # Store result
                if bundle.sequence_id not in self.processed_sequences:
                    self.processed_sequences[bundle.sequence_id] = []
                self.processed_sequences[bundle.sequence_id].append(fusion_result)

                # Yield result for consumers
                yield fusion_result

            except asyncio.TimeoutError:
                # No input available, continue loop
                continue
            except Exception as e:
                print(f"Error in processing loop: {e}")
                continue

    async def get_sequence_results(self, sequence_id: str) -> List[FusionResult]:
        """Get all processing results for a sequence."""
        return self.processed_sequences.get(sequence_id, [])

    def get_buffer_status(self) -> Dict[str, Any]:
        """Get current buffer status."""
        return {
            'buffer_size': self.input_buffer.qsize(),
            'max_buffer_size': self.buffer_size,
            'is_processing': self.is_processing,
            'active_sequences': len(self.processed_sequences)
        }


@dataclass
class KnowledgeNode:
    """A node in the cross-modal knowledge graph."""

    id: str
    modality: str
    content: Any
    embeddings: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    connections: Set[str] = field(default_factory=set)
    confidence: float = 1.0
    temporal_context: Optional[datetime] = None
    cross_modal_links: Dict[str, Set[str]] = field(default_factory=dict)  # modality -> linked_node_ids

    def add_connection(self, node_id: str, bidirectional: bool = True):
        """Add a connection to another node."""
        self.connections.add(node_id)
        # In a real implementation, you'd also add the reverse connection

    def add_cross_modal_link(self, target_node_id: str, target_modality: str):
        """Add a cross-modal connection to another node."""
        if target_modality not in self.cross_modal_links:
            self.cross_modal_links[target_modality] = set()
        self.cross_modal_links[target_modality].add(target_node_id)


@dataclass
class SensorDataPoint:
    """Represents a single sensor data reading."""

    sensor_id: str
    sensor_type: str  # temperature, humidity, pressure, motion, etc.
    value: Union[float, int, str, Dict[str, Any]]
    unit: str
    timestamp: datetime
    location: Optional[Dict[str, float]] = None  # lat, lon coordinates
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0  # 0.0 to 1.0

    def is_valid(self) -> bool:
        """Check if sensor data is valid."""
        return self.quality_score > 0.1 and self.value is not None


@dataclass
class SensorDataStream:
    """A stream of sensor data from multiple sensors."""

    stream_id: str
    sensors: Dict[str, str] = field(default_factory=dict)  # sensor_id -> sensor_type
    data_points: List[SensorDataPoint] = field(default_factory=list)
    sampling_rate: float = 1.0  # Hz
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_data_point(self, point: SensorDataPoint):
        """Add a data point to the stream."""
        self.data_points.append(point)
        # Keep only recent data (last 1000 points)
        if len(self.data_points) > 1000:
            self.data_points = self.data_points[-1000:]

    def get_recent_data(self, time_window_seconds: float = 60.0) -> List[SensorDataPoint]:
        """Get data points within the specified time window."""
        cutoff_time = datetime.now() - timedelta(seconds=time_window_seconds)
        return [point for point in self.data_points if point.timestamp > cutoff_time]

    def get_sensor_stats(self, sensor_id: str) -> Dict[str, Any]:
        """Get statistics for a specific sensor."""
        sensor_points = [p for p in self.data_points if p.sensor_id == sensor_id and p.is_valid()]

        if not sensor_points:
            return {'count': 0, 'valid_count': 0}

        values = [p.value for p in sensor_points if isinstance(p.value, (int, float))]

        if values:
            return {
                'count': len(sensor_points),
                'valid_count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'latest_value': sensor_points[-1].value if sensor_points else None
            }
        else:
            return {
                'count': len(sensor_points),
                'valid_count': 0,
                'latest_value': sensor_points[-1].value if sensor_points else None
            }


class CrossModalKnowledgeGraph:
    """Enhanced knowledge graph that connects information across modalities with advanced cross-modal linking."""

    def __init__(self, use_embeddings: bool = False):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.modality_clusters: Dict[str, Set[str]] = {}
        self.semantic_index: Dict[str, Set[str]] = {}
        self.temporal_index: Dict[str, Set[str]] = {}  # time_bucket -> node_ids
        self.cross_modal_index: Dict[str, Dict[str, Set[str]]] = {}  # modality -> target_modality -> node_ids
        self.use_embeddings = use_embeddings
        self.embedding_model = None  # Would integrate with sentence transformers, etc.

    def add_node(self, node: KnowledgeNode):
        """Add a node to the knowledge graph with enhanced indexing."""
        self.nodes[node.id] = node

        # Update modality clusters
        if node.modality not in self.modality_clusters:
            self.modality_clusters[node.modality] = set()
        self.modality_clusters[node.modality].add(node.id)

        # Index by semantic content
        self._index_semantic_content(node)

        # Index by temporal context
        self._index_temporal_content(node)

        # Index cross-modal links
        self._index_cross_modal_links(node)

    def _index_semantic_content(self, node: KnowledgeNode):
        """Index node by semantic content for retrieval."""
        # Enhanced keyword-based indexing
        if hasattr(node.content, 'get') and 'keywords' in node.content:
            keywords = node.content['keywords']
            if isinstance(keywords, list):
                for keyword in keywords:
                    if keyword not in self.semantic_index:
                        self.semantic_index[keyword] = set()
                    self.semantic_index[keyword].add(node.id)

        # Index by content type and structure
        if hasattr(node.content, 'get'):
            content_keys = node.content.keys()
            for key in content_keys:
                key_str = f"content:{key}"
                if key_str not in self.semantic_index:
                    self.semantic_index[key_str] = set()
                self.semantic_index[key_str].add(node.id)

    def _index_temporal_content(self, node: KnowledgeNode):
        """Index node by temporal context."""
        if node.temporal_context:
            time_bucket = node.temporal_context.strftime("%Y-%m-%d-%H")
            if time_bucket not in self.temporal_index:
                self.temporal_index[time_bucket] = set()
            self.temporal_index[time_bucket].add(node.id)

    def _index_cross_modal_links(self, node: KnowledgeNode):
        """Index cross-modal connections."""
        for target_modality, linked_nodes in node.cross_modal_links.items():
            if node.modality not in self.cross_modal_index:
                self.cross_modal_index[node.modality] = {}
            if target_modality not in self.cross_modal_index[node.modality]:
                self.cross_modal_index[node.modality][target_modality] = set()
            self.cross_modal_index[node.modality][target_modality].update(linked_nodes)

    def add_cross_modal_connection(self, source_id: str, target_id: str,
                                 relationship_type: str = "related"):
        """Add a cross-modal connection between two nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return False

        source_node = self.nodes[source_id]
        target_node = self.nodes[target_id]

        # Add bidirectional cross-modal links
        source_node.add_cross_modal_link(target_id, target_node.modality)
        target_node.add_cross_modal_link(source_id, source_node.modality)

        # Add regular connections
        source_node.add_connection(target_id)
        target_node.add_connection(source_id)

        # Update indices
        self._index_cross_modal_links(source_node)
        self._index_cross_modal_links(target_node)

        return True

    def find_related_nodes(self, node_id: str, max_depth: int = 2) -> Set[str]:
        """Find nodes related to the given node with cross-modal awareness."""
        if node_id not in self.nodes:
            return set()

        visited = set()
        to_visit = {node_id}
        related = set()

        for depth in range(max_depth):
            if not to_visit:
                break

            current_level = to_visit.copy()
            to_visit.clear()

            for current_id in current_level:
                if current_id in visited:
                    continue

                visited.add(current_id)
                node = self.nodes[current_id]

                # Regular connections
                for connected_id in node.connections:
                    if connected_id not in visited:
                        related.add(connected_id)
                        to_visit.add(connected_id)

                # Cross-modal connections
                for modality_links in node.cross_modal_links.values():
                    for linked_id in modality_links:
                        if linked_id not in visited:
                            related.add(linked_id)
                            to_visit.add(linked_id)

        return related

    def find_cross_modal_paths(self, source_modality: str, target_modality: str,
                             max_path_length: int = 3) -> List[List[str]]:
        """Find paths connecting different modalities."""
        paths = []

        # Start from source modality nodes
        start_nodes = list(self.modality_clusters.get(source_modality, set()))

        for start_node in start_nodes:
            # BFS to find paths to target modality
            queue = [(start_node, [start_node])]
            visited = set()

            while queue:
                current_node, path = queue.pop(0)

                if current_node in visited:
                    continue
                visited.add(current_node)

                if len(path) > max_path_length:
                    continue

                current_node_obj = self.nodes[current_node]
                if current_node_obj.modality == target_modality:
                    paths.append(path)
                    continue

                # Explore connections
                for neighbor in current_node_obj.connections:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))

        return paths

    def semantic_search(self, query: str, modality_filter: Optional[str] = None) -> List[KnowledgeNode]:
        """Enhanced semantic search with cross-modal awareness."""
        candidate_ids = set()

        # Keyword matching
        query_words = set(query.lower().split())
        for word in query_words:
            candidate_ids.update(self.semantic_index.get(word, set()))

        # Cross-modal expansion - if we find nodes in one modality, look for connected nodes in other modalities
        expanded_candidates = candidate_ids.copy()
        for candidate_id in candidate_ids:
            related_nodes = self.find_related_nodes(candidate_id, max_depth=2)
            expanded_candidates.update(related_nodes)

        # Filter by modality if specified
        if modality_filter:
            modality_nodes = self.modality_clusters.get(modality_filter, set())
            expanded_candidates = expanded_candidates.intersection(modality_nodes)

        # Return matching nodes sorted by confidence
        candidates = [self.nodes[node_id] for node_id in expanded_candidates if node_id in self.nodes]
        return sorted(candidates, key=lambda x: x.confidence, reverse=True)

    def get_modality_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics about modalities in the graph."""
        stats = {}
        for modality, node_ids in self.modality_clusters.items():
            nodes = [self.nodes[node_id] for node_id in node_ids]
            cross_modal_connections = sum(len(n.cross_modal_links) for n in nodes)

            stats[modality] = {
                'count': len(nodes),
                'avg_confidence': np.mean([n.confidence for n in nodes]),
                'total_connections': sum(len(n.connections) for n in nodes),
                'cross_modal_connections': cross_modal_connections,
                'temporal_coverage': len([n for n in nodes if n.temporal_context is not None])
            }
        return stats

    def get_cross_modal_statistics(self) -> Dict[str, Any]:
        """Get statistics about cross-modal connections."""
        stats = {
            'total_cross_modal_links': 0,
            'modality_pairs': {},
            'connectivity_matrix': {}
        }

        for source_modality, target_links in self.cross_modal_index.items():
            for target_modality, node_ids in target_links.items():
                pair_key = f"{source_modality}->{target_modality}"
                stats['modality_pairs'][pair_key] = len(node_ids)
                stats['total_cross_modal_links'] += len(node_ids)

        return stats


class VisionLanguageAgent(ProbabilisticAgent):
    """Agent that processes both text and images with uncertainty estimation."""

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)
        self.fusion_engine = MultimodalFusionEngine()
        self.knowledge_graph = CrossModalKnowledgeGraph()
        self.vision_processor = None  # Would integrate with vision models
        self.language_processor = None  # Would integrate with language models

    async def execute(self, inputs: Union[MultimodalInputBundle, Dict[str, Any]]) -> ProbabilisticResult:
        """Execute vision-language processing with uncertainty."""
        if isinstance(inputs, dict):
            # Convert dict to MultimodalInputBundle
            bundle = self._convert_dict_to_bundle(inputs)
        else:
            bundle = inputs

        # Fuse multimodal inputs
        fusion_result = await self.fusion_engine.fuse_modalities(bundle)

        # Process with vision-language understanding
        understanding = await self._understand_multimodal_content(fusion_result)

        # Make decision with uncertainty
        decision = await self._make_decision_with_uncertainty(understanding, bundle)

        # Update knowledge graph
        await self._update_knowledge_graph(bundle, understanding)

        return ProbabilisticResult(
            success=decision['confidence'] > self.confidence_threshold,
            confidence=decision['confidence'],
            alternatives=decision.get('alternatives', []),
            metadata={
                'fusion_result': fusion_result,
                'understanding': understanding,
                'knowledge_graph_updates': len(bundle.inputs)
            }
        )

    def _convert_dict_to_bundle(self, inputs: Dict[str, Any]) -> MultimodalInputBundle:
        """Convert dictionary input to MultimodalInputBundle."""
        bundle = MultimodalInputBundle()

        # Handle different input formats
        if 'text' in inputs:
            text_input = MultimodalInput(text=inputs['text'])
            bundle.add_input(text_input)

        if 'image' in inputs:
            image_input = MultimodalInput(image=inputs['image'])
            bundle.add_input(image_input)

        if 'audio' in inputs:
            audio_input = MultimodalInput(audio=inputs['audio'])
            bundle.add_input(audio_input)

        return bundle

    async def _understand_multimodal_content(self, fusion_result: FusionResult) -> Dict[str, Any]:
        """Understand the fused multimodal content."""
        # This would integrate with actual vision-language models
        # For now, return mock understanding
        return {
            'primary_modality': max(fusion_result.confidence_scores.items(),
                                  key=lambda x: x[1])[0],
            'content_type': 'multimodal_description',
            'key_entities': ['entity1', 'entity2'],
            'sentiment': 'neutral',
            'confidence': np.mean(list(fusion_result.confidence_scores.values()))
        }

    async def _make_decision_with_uncertainty(self, understanding: Dict[str, Any],
                                            bundle: MultimodalInputBundle) -> Dict[str, Any]:
        """Make decision with uncertainty quantification."""
        base_confidence = understanding.get('confidence', 0.5)

        # Adjust confidence based on modality agreement
        modality_count = len(bundle.get_modality_counts())
        agreement_bonus = min(0.2, modality_count * 0.05)  # Bonus for multiple modalities

        # Adjust for content complexity
        complexity_penalty = 0.1 if understanding.get('content_type') == 'complex' else 0.0

        final_confidence = min(1.0, base_confidence + agreement_bonus - complexity_penalty)

        return {
            'decision': 'process_content',
            'confidence': final_confidence,
            'reasoning': f'Processed {modality_count} modalities with {agreement_bonus:.2f} agreement bonus',
            'alternatives': [
                {'action': 'defer_processing', 'confidence': 0.1},
                {'action': 'request_clarification', 'confidence': 0.05}
            ]
        }

    async def _update_knowledge_graph(self, bundle: MultimodalInputBundle,
                                    understanding: Dict[str, Any]):
        """Update the knowledge graph with new multimodal knowledge."""
        # Create nodes for each input
        for i, input_data in enumerate(bundle.inputs):
            node_id = f"{bundle.sequence_id}_input_{i}"

            # Determine primary modality
            modalities = input_data.get_available_modalities()
            primary_modality = modalities[0] if modalities else 'unknown'

            # Create content summary
            content = {
                'modalities': modalities,
                'timestamp': input_data.timestamp.isoformat(),
                'understanding': understanding
            }

            node = KnowledgeNode(
                id=node_id,
                modality=primary_modality,
                content=content,
                confidence=understanding.get('confidence', 0.5)
            )

            self.knowledge_graph.add_node(node)

            # Connect related nodes
            if i > 0:
                prev_node_id = f"{bundle.sequence_id}_input_{i-1}"
                if prev_node_id in self.knowledge_graph.nodes:
                    node.add_connection(prev_node_id)


class StructuredDataAgent(ProbabilisticAgent):
    """Agent specialized for data analysis and processing with uncertainty."""

    def __init__(self, confidence_threshold: float = 0.75):
        super().__init__(confidence_threshold)
        self.analysis_methods = {
            'statistical': self._statistical_analysis,
            'pattern_recognition': self._pattern_analysis,
            'anomaly_detection': self._anomaly_detection,
            'correlation_analysis': self._correlation_analysis
        }

    async def analyze_dataset(self, data: Any) -> ProbabilisticResult:
        """Analyze structured data with confidence intervals."""
        # Convert data to appropriate format
        if isinstance(data, dict):
            df_data = data
        else:
            # Assume pandas-like data structure
            df_data = data

        # Perform multiple analysis methods
        analysis_results = {}
        for method_name, method_func in self.analysis_methods.items():
            try:
                result = await method_func(df_data)
                analysis_results[method_name] = result
            except Exception as e:
                analysis_results[method_name] = {'error': str(e)}

        # Aggregate results with uncertainty
        overall_confidence = self._aggregate_analysis_confidence(analysis_results)
        insights = self._extract_key_insights(analysis_results)

        return ProbabilisticResult(
            success=overall_confidence > self.confidence_threshold,
            confidence=overall_confidence,
            alternatives=[],
            metadata={
                'analysis_methods': list(analysis_results.keys()),
                'insights': insights,
                'data_shape': self._get_data_shape(df_data)
            }
        )

    async def _statistical_analysis(self, data: Dict) -> Dict[str, Any]:
        """Perform statistical analysis with confidence intervals."""
        # Mock statistical analysis
        return {
            'mean': 0.5,
            'std': 0.2,
            'confidence_interval': [0.3, 0.7],
            'sample_size': len(data) if isinstance(data, dict) else 100,
            'normality_test': {'p_value': 0.05, 'is_normal': True}
        }

    async def _pattern_analysis(self, data: Dict) -> Dict[str, Any]:
        """Identify patterns in the data."""
        # Mock pattern recognition
        return {
            'patterns_found': ['trend', 'seasonal'],
            'pattern_confidence': 0.8,
            'trend_direction': 'increasing',
            'seasonal_period': 7
        }

    async def _anomaly_detection(self, data: Dict) -> Dict[str, Any]:
        """Detect anomalies in the data."""
        # Mock anomaly detection
        return {
            'anomalies_detected': 3,
            'anomaly_score': 0.9,
            'anomaly_indices': [10, 45, 78],
            'detection_method': 'isolation_forest'
        }

    async def _correlation_analysis(self, data: Dict) -> Dict[str, Any]:
        """Analyze correlations between variables."""
        # Mock correlation analysis
        return {
            'correlation_matrix': {
                'var1_var2': 0.7,
                'var1_var3': 0.3,
                'var2_var3': 0.8
            },
            'significant_correlations': ['var2_var3'],
            'correlation_method': 'pearson'
        }

    def _aggregate_analysis_confidence(self, results: Dict[str, Any]) -> float:
        """Aggregate confidence from multiple analysis methods."""
        confidences = []

        for method, result in results.items():
            if 'error' not in result:
                # Extract confidence based on method
                if method == 'statistical':
                    conf = min(1.0, result.get('sample_size', 0) / 1000)  # Larger samples = higher confidence
                elif method == 'pattern_analysis':
                    conf = result.get('pattern_confidence', 0.5)
                elif method == 'anomaly_detection':
                    conf = result.get('anomaly_score', 0.5)
                elif method == 'correlation_analysis':
                    significant_count = len(result.get('significant_correlations', []))
                    conf = min(1.0, significant_count / 5)  # More significant correlations = higher confidence
                else:
                    conf = 0.5

                confidences.append(conf)

        return np.mean(confidences) if confidences else 0.0

    def _extract_key_insights(self, results: Dict[str, Any]) -> List[str]:
        """Extract key insights from analysis results."""
        insights = []

        for method, result in results.items():
            if 'error' in result:
                continue

            if method == 'statistical':
                ci = result.get('confidence_interval', [])
                if ci:
                    insights.append(f"95% confidence interval: [{ci[0]:.2f}, {ci[1]:.2f}]")

            elif method == 'pattern_analysis':
                patterns = result.get('patterns_found', [])
                if patterns:
                    insights.append(f"Detected patterns: {', '.join(patterns)}")

            elif method == 'anomaly_detection':
                anomalies = result.get('anomalies_detected', 0)
                if anomalies > 0:
                    insights.append(f"Found {anomalies} anomalies in the data")

            elif method == 'correlation_analysis':
                significant = result.get('significant_correlations', [])
                if significant:
                    insights.append(f"Strong correlations found: {', '.join(significant)}")

        return insights

    def _get_data_shape(self, data: Any) -> Tuple[int, int]:
        """Get the shape of the data."""
        if isinstance(data, dict):
            return (len(data), 1)
        elif hasattr(data, 'shape'):
            return data.shape
        else:
            return (1, 1)


class SensorDataIntegration:
    """Enhanced sensor data integration for IoT and sensor-based decision making."""

    def __init__(self, max_streams: int = 50, data_retention_hours: int = 24):
        self.max_streams = max_streams
        self.data_retention_hours = data_retention_hours
        self.active_streams: Dict[str, SensorDataStream] = {}
        self.sensor_networks: Dict[str, Set[str]] = {}  # network_id -> stream_ids
        self.data_quality_monitor = SensorQualityMonitor()
        self.anomaly_detector = SensorAnomalyDetector()
        self.predictive_analyzer = SensorPredictiveAnalyzer()

    async def register_sensor_stream(self, stream: SensorDataStream) -> bool:
        """Register a new sensor data stream."""
        if len(self.active_streams) >= self.max_streams:
            # Remove oldest inactive streams
            self._cleanup_inactive_streams()

        if len(self.active_streams) >= self.max_streams:
            return False

        self.active_streams[stream.stream_id] = stream

        # Register with quality monitoring
        await self.data_quality_monitor.register_stream(stream)

        return True

    async def ingest_sensor_data(self, stream_id: str, data_points: List[SensorDataPoint]) -> Dict[str, Any]:
        """Ingest sensor data points into a stream."""
        if stream_id not in self.active_streams:
            return {'success': False, 'error': 'Stream not found'}

        stream = self.active_streams[stream_id]

        # Quality check and filtering
        quality_results = await self.data_quality_monitor.process_data_points(data_points)
        valid_points = [pt for pt, quality in zip(data_points, quality_results) if quality['is_valid']]

        # Anomaly detection
        anomaly_results = await self.anomaly_detector.detect_anomalies(stream, valid_points)

        # Add valid points to stream
        for point in valid_points:
            stream.add_data_point(point)

        # Predictive analysis
        predictions = await self.predictive_analyzer.analyze_stream(stream)

        return {
            'success': True,
            'points_ingested': len(valid_points),
            'quality_stats': quality_results,
            'anomalies_detected': sum(1 for r in anomaly_results if r.get('is_anomaly', False)),
            'predictions': predictions
        }

    async def get_sensor_insights(self, stream_id: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive insights from sensor data."""
        if stream_id not in self.active_streams:
            return {'error': 'Stream not found'}

        stream = self.active_streams[stream_id]
        recent_data = stream.get_recent_data(time_window_minutes * 60)

        insights = {
            'stream_id': stream_id,
            'time_window_minutes': time_window_minutes,
            'total_points': len(recent_data),
            'sensor_stats': {},
            'anomalies': [],
            'predictions': {},
            'quality_metrics': {}
        }

        # Per-sensor statistics
        for sensor_id in stream.sensors:
            stats = stream.get_sensor_stats(sensor_id)
            insights['sensor_stats'][sensor_id] = stats

        # Recent anomalies
        anomaly_history = await self.anomaly_detector.get_recent_anomalies(stream_id, time_window_minutes)
        insights['anomalies'] = anomaly_history

        # Predictions
        predictions = await self.predictive_analyzer.analyze_stream(stream)
        insights['predictions'] = predictions

        # Quality metrics
        quality_metrics = await self.data_quality_monitor.get_stream_quality(stream_id)
        insights['quality_metrics'] = quality_metrics

        return insights

    async def create_sensor_bundle(self, stream_ids: List[str], time_window_seconds: float = 300.0) -> MultimodalInputBundle:
        """Create a multimodal input bundle from sensor data for fusion."""
        bundle = MultimodalInputBundle(sequence_id=f"sensor_bundle_{datetime.now().isoformat()}")

        for stream_id in stream_ids:
            if stream_id in self.active_streams:
                stream = self.active_streams[stream_id]
                recent_data = stream.get_recent_data(time_window_seconds)

                # Aggregate sensor data for the bundle
                sensor_summary = {
                    'stream_id': stream_id,
                    'sensor_count': len(stream.sensors),
                    'data_points': len(recent_data),
                    'time_window_seconds': time_window_seconds,
                    'sensor_stats': {sensor_id: stream.get_sensor_stats(sensor_id)
                                   for sensor_id in stream.sensors}
                }

                # Add as sensor input
                sensor_input = MultimodalInput(
                    sensor_data=sensor_summary,
                    timestamp=datetime.now()
                )
                bundle.add_input(sensor_input)

        return bundle

    def _cleanup_inactive_streams(self):
        """Remove inactive sensor streams to free up space."""
        cutoff_time = datetime.now() - timedelta(hours=self.data_retention_hours)

        inactive_streams = []
        for stream_id, stream in self.active_streams.items():
            if not stream.active:
                inactive_streams.append(stream_id)
            elif stream.data_points and stream.data_points[-1].timestamp < cutoff_time:
                stream.active = False
                inactive_streams.append(stream_id)

        for stream_id in inactive_streams:
            del self.active_streams[stream_id]


class SensorQualityMonitor:
    """Monitor and assess sensor data quality."""

    def __init__(self):
        self.quality_history: Dict[str, List[Dict[str, Any]]] = {}
        self.quality_thresholds = {
            'completeness': 0.8,
            'accuracy': 0.9,
            'timeliness': 0.95,
            'consistency': 0.85
        }

    async def register_stream(self, stream: SensorDataStream):
        """Register a stream for quality monitoring."""
        self.quality_history[stream.stream_id] = []

    async def process_data_points(self, data_points: List[SensorDataPoint]) -> List[Dict[str, Any]]:
        """Process data points and return quality assessments."""
        quality_results = []

        for point in data_points:
            quality_score = await self._assess_point_quality(point)
            quality_results.append({
                'sensor_id': point.sensor_id,
                'quality_score': quality_score,
                'is_valid': quality_score >= 0.6,
                'issues': self._identify_quality_issues(point, quality_score)
            })

        return quality_results

    async def _assess_point_quality(self, point: SensorDataPoint) -> float:
        """Assess the quality of a single data point."""
        if not point.is_valid():
            return 0.0

        score = point.quality_score

        # Check timeliness (data freshness)
        age_hours = (datetime.now() - point.timestamp).total_seconds() / 3600
        timeliness_factor = max(0.0, 1.0 - age_hours / 24)  # Decay over 24 hours
        score *= timeliness_factor

        # Check value plausibility based on sensor type
        plausibility = self._check_value_plausibility(point)
        score *= plausibility

        return min(1.0, score)

    def _check_value_plausibility(self, point: SensorDataPoint) -> float:
        """Check if the sensor value is plausible for the sensor type."""
        sensor_type = point.sensor_type
        value = point.value

        if not isinstance(value, (int, float)):
            return 0.8  # Assume plausible for non-numeric data

        # Basic plausibility checks by sensor type
        if sensor_type == 'temperature':
            return 1.0 if -50 <= value <= 100 else 0.3
        elif sensor_type == 'humidity':
            return 1.0 if 0 <= value <= 100 else 0.3
        elif sensor_type == 'pressure':
            return 1.0 if 800 <= value <= 1200 else 0.3
        elif sensor_type == 'motion':
            return 1.0 if 0 <= value <= 1 else 0.5
        else:
            return 0.9  # Default plausibility for unknown types

    def _identify_quality_issues(self, point: SensorDataPoint, quality_score: float) -> List[str]:
        """Identify specific quality issues with a data point."""
        issues = []

        if quality_score < 0.6:
            issues.append('low_quality_score')

        age_hours = (datetime.now() - point.timestamp).total_seconds() / 3600
        if age_hours > 1:
            issues.append('stale_data')

        if not self._check_value_plausibility(point) < 0.5:
            issues.append('implausible_value')

        return issues

    async def get_stream_quality(self, stream_id: str) -> Dict[str, Any]:
        """Get overall quality metrics for a stream."""
        if stream_id not in self.quality_history:
            return {'error': 'Stream not monitored'}

        history = self.quality_history[stream_id]
        if not history:
            return {'avg_quality': 0.0, 'total_assessments': 0}

        avg_quality = np.mean([h.get('quality_score', 0) for h in history])
        total_assessments = len(history)

        return {
            'avg_quality': avg_quality,
            'total_assessments': total_assessments,
            'quality_distribution': self._get_quality_distribution(history)
        }

    def _get_quality_distribution(self, history: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of quality scores."""
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}

        for assessment in history:
            score = assessment.get('quality_score', 0)
            if score >= 0.9:
                distribution['excellent'] += 1
            elif score >= 0.7:
                distribution['good'] += 1
            elif score >= 0.5:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1

        return distribution


class SensorAnomalyDetector:
    """Detect anomalies in sensor data streams."""

    def __init__(self):
        self.anomaly_history: Dict[str, List[Dict[str, Any]]] = {}
        self.baseline_models: Dict[str, Dict[str, Any]] = {}  # stream_id -> sensor_baselines

    async def detect_anomalies(self, stream: SensorDataStream, data_points: List[SensorDataPoint]) -> List[Dict[str, Any]]:
        """Detect anomalies in the provided data points."""
        results = []

        for point in data_points:
            is_anomaly, confidence, reason = await self._check_point_anomaly(stream, point)
            result = {
                'sensor_id': point.sensor_id,
                'timestamp': point.timestamp,
                'value': point.value,
                'is_anomaly': is_anomaly,
                'confidence': confidence,
                'reason': reason
            }
            results.append(result)

            # Store anomaly for history
            if stream.stream_id not in self.anomaly_history:
                self.anomaly_history[stream.stream_id] = []
            self.anomaly_history[stream.stream_id].append(result)

        return results

    async def _check_point_anomaly(self, stream: SensorDataStream, point: SensorDataPoint) -> Tuple[bool, float, str]:
        """Check if a single data point is anomalous."""
        if not isinstance(point.value, (int, float)):
            return False, 0.5, "non_numeric_value"

        # Get or establish baseline for this sensor
        sensor_key = f"{stream.stream_id}_{point.sensor_id}"
        if sensor_key not in self.baseline_models:
            await self._establish_baseline(stream, point.sensor_id)
            return False, 0.5, "baseline_establishing"  # First point can't be anomalous

        baseline = self.baseline_models[sensor_key]

        # Need minimum samples for reliable anomaly detection
        if baseline.get('sample_count', 0) < 10:
            await self._update_baseline(sensor_key, point.value)
            return False, 0.5, "insufficient_baseline"

        # Simple statistical anomaly detection
        mean = baseline.get('mean', point.value)
        std = baseline.get('std', 1.0)

        if std == 0 or std < 0.1:  # Avoid division by very small numbers
            z_score = 0
        else:
            z_score = abs(point.value - mean) / std

        # Update baseline with new point (rolling average)
        await self._update_baseline(sensor_key, point.value)

        # Anomaly threshold: 3 standard deviations, but be more lenient initially
        is_anomaly = z_score > 4.0  # Higher threshold for fewer false positives
        confidence = min(1.0, z_score / 6.0)  # Adjust confidence scaling

        reason = f"z_score_{z_score:.2f}" if is_anomaly else "normal"

        return is_anomaly, confidence, reason

    async def _establish_baseline(self, stream: SensorDataStream, sensor_id: str):
        """Establish baseline statistics for anomaly detection."""
        sensor_key = f"{stream.stream_id}_{sensor_id}"

        # Get recent data for baseline
        recent_data = stream.get_recent_data(3600)  # Last hour
        sensor_values = [pt.value for pt in recent_data
                        if pt.sensor_id == sensor_id and isinstance(pt.value, (int, float))]

        if sensor_values:
            mean = np.mean(sensor_values)
            std = np.std(sensor_values) or 1.0  # Avoid division by zero
        else:
            mean = 0.0
            std = 1.0

        self.baseline_models[sensor_key] = {
            'mean': mean,
            'std': std,
            'sample_count': len(sensor_values),
            'last_updated': datetime.now()
        }

    async def _update_baseline(self, sensor_key: str, new_value: float):
        """Update baseline with new data point using exponential moving average."""
        if sensor_key not in self.baseline_models:
            return

        baseline = self.baseline_models[sensor_key]
        alpha = 0.1  # Smoothing factor

        # Update mean
        old_mean = baseline['mean']
        baseline['mean'] = alpha * new_value + (1 - alpha) * old_mean

        # Update std (simplified)
        baseline['sample_count'] += 1
        baseline['last_updated'] = datetime.now()

    async def get_recent_anomalies(self, stream_id: str, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent anomalies for a stream."""
        if stream_id not in self.anomaly_history:
            return []

        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        return [anomaly for anomaly in self.anomaly_history[stream_id]
                if anomaly.get('timestamp', datetime.min) > cutoff_time and anomaly.get('is_anomaly', False)]


class SensorPredictiveAnalyzer:
    """Predictive analysis for sensor data streams."""

    def __init__(self):
        self.prediction_models: Dict[str, Dict[str, Any]] = {}

    async def analyze_stream(self, stream: SensorDataStream) -> Dict[str, Any]:
        """Analyze a sensor stream for predictive insights."""
        predictions = {}

        for sensor_id in stream.sensors:
            sensor_key = f"{stream.stream_id}_{sensor_id}"
            recent_data = stream.get_recent_data(1800)  # Last 30 minutes
            sensor_points = [pt for pt in recent_data if pt.sensor_id == sensor_id]

            if len(sensor_points) >= 10:  # Need minimum data for prediction
                prediction = await self._predict_sensor_values(sensor_key, sensor_points)
                predictions[sensor_id] = prediction

        return {
            'predictions': predictions,
            'trend_analysis': await self._analyze_trends(stream),
            'forecast_horizon': 300  # 5 minutes ahead
        }

    async def _predict_sensor_values(self, sensor_key: str, data_points: List[SensorDataPoint]) -> Dict[str, Any]:
        """Predict future sensor values using simple linear regression."""
        if len(data_points) < 5:
            return {'error': 'insufficient_data'}

        # Extract time series data
        times = [(pt.timestamp - data_points[0].timestamp).total_seconds()
                for pt in data_points]
        values = [pt.value for pt in data_points if isinstance(pt.value, (int, float))]

        if len(values) != len(times):
            return {'error': 'mixed_data_types'}

        # Simple linear regression for trend
        if len(times) > 1:
            slope, intercept = np.polyfit(times, values, 1)
            r_squared = np.corrcoef(times, values)[0, 1] ** 2

            # Predict next value (5 minutes ahead)
            next_time = times[-1] + 300
            predicted_value = slope * next_time + intercept

            return {
                'predicted_value': predicted_value,
                'trend_slope': slope,
                'r_squared': r_squared,
                'confidence': min(1.0, r_squared * 0.8 + 0.2),  # Boost confidence
                'prediction_horizon_seconds': 300
            }
        else:
            return {'predicted_value': values[0], 'trend_slope': 0, 'r_squared': 0, 'confidence': 0.1}

    async def _analyze_trends(self, stream: SensorDataStream) -> Dict[str, Any]:
        """Analyze overall trends across all sensors in the stream."""
        trends = {}

        for sensor_id in stream.sensors:
            recent_data = stream.get_recent_data(3600)  # Last hour
            sensor_points = [pt for pt in recent_data if pt.sensor_id == sensor_id
                           and isinstance(pt.value, (int, float))]

            if len(sensor_points) >= 10:
                values = [pt.value for pt in sensor_points]
                times = [(pt.timestamp - sensor_points[0].timestamp).total_seconds()
                        for pt in sensor_points]

                # Calculate trend
                if len(times) > 1:
                    slope, _ = np.polyfit(times, values, 1)
                    trend = 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable'
                    trends[sensor_id] = {
                        'trend': trend,
                        'slope': slope,
                        'volatility': np.std(values)
                    }

        return trends


@dataclass
class FusionWeightLearner:
    """Learns optimal fusion weights from feedback data."""

    modality_weights: Dict[str, float]
    learning_rate: float = 0.01
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, List[float]] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize performance tracking for each modality
        for modality in self.modality_weights.keys():
            self.performance_metrics[modality] = []

    async def update_weights_from_feedback(self, fusion_result: FusionResult,
                                         feedback_score: float, task_context: str = ""):
        """Update fusion weights based on feedback about fusion performance."""
        # Store feedback for analysis
        feedback_entry = {
            'timestamp': datetime.now(),
            'fusion_result': fusion_result,
            'feedback_score': feedback_score,
            'task_context': task_context,
            'modality_contributions': fusion_result.confidence_scores
        }
        self.feedback_history.append(feedback_entry)

        # Update performance metrics
        for modality, confidence in fusion_result.confidence_scores.items():
            if modality in self.performance_metrics:
                self.performance_metrics[modality].append(confidence * feedback_score)

        # Learn from feedback if we have enough history
        if len(self.feedback_history) >= 5:
            await self._learn_from_feedback_history()

    async def _learn_from_feedback_history(self):
        """Learn optimal weights from historical feedback."""
        if len(self.feedback_history) < 10:
            return

        # Analyze recent performance (last 20 feedback entries)
        recent_feedback = self.feedback_history[-20:]

        # Calculate average performance per modality
        modality_performance = {}
        for modality in self.modality_weights.keys():
            performances = []
            for feedback in recent_feedback:
                confidence = feedback['fusion_result'].confidence_scores.get(modality, 0)
                feedback_score = feedback['feedback_score']
                performances.append(confidence * feedback_score)

            if performances:
                modality_performance[modality] = np.mean(performances)
            else:
                modality_performance[modality] = 0.5  # Default

        # Adjust weights based on performance
        total_performance = sum(modality_performance.values())
        if total_performance > 0:
            for modality in self.modality_weights:
                target_weight = modality_performance[modality] / total_performance
                current_weight = self.modality_weights[modality]

                # Smooth weight adjustment
                adjustment = self.learning_rate * (target_weight - current_weight)
                self.modality_weights[modality] = np.clip(
                    current_weight + adjustment, 0.05, 0.8
                )

        # Renormalize weights
        total_weight = sum(self.modality_weights.values())
        if total_weight > 0:
            self.modality_weights = {
                k: v / total_weight for k, v in self.modality_weights.items()
            }

    def get_optimal_weights(self, task_context: str = "") -> Dict[str, float]:
        """Get optimal weights, potentially adjusted for task context."""
        # For now, return current learned weights
        # Could be extended to use task-specific weight adjustments
        return self.modality_weights.copy()

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about the learning process."""
        if not self.feedback_history:
            return {'status': 'no_feedback_yet'}

        recent_feedback = self.feedback_history[-10:] if len(self.feedback_history) > 10 else self.feedback_history

        return {
            'total_feedback_entries': len(self.feedback_history),
            'average_feedback_score': np.mean([f['feedback_score'] for f in recent_feedback]),
            'learning_progress': self._calculate_learning_progress(),
            'modality_performance': {
                modality: np.mean(scores) if scores else 0.0
                for modality, scores in self.performance_metrics.items()
            },
            'current_weights': self.modality_weights.copy()
        }

    def _calculate_learning_progress(self) -> float:
        """Calculate how much the weights have changed over time."""
        if len(self.feedback_history) < 20:
            return 0.0

        # Compare weights from first and last 10 feedback entries
        early_feedback = self.feedback_history[:10]
        late_feedback = self.feedback_history[-10:]

        # This is a simplified progress calculation
        # In practice, you'd track weight changes more systematically
        return min(1.0, len(self.feedback_history) / 100)  # Arbitrary progress metric


class AdaptiveFusionWeights:
    """Advanced adaptive fusion system that learns optimal strategies from feedback."""

    def __init__(self, base_weights: Optional[Dict[str, float]] = None):
        self.base_weights = base_weights or {
            'text': 0.4,
            'image': 0.3,
            'audio': 0.2,
            'sensor': 0.1,
            'structured': 0.2
        }

        # Multiple weight learners for different contexts
        self.context_learners: Dict[str, FusionWeightLearner] = {}
        self.global_learner = FusionWeightLearner(self.base_weights.copy())

        # Performance tracking
        self.fusion_history: List[Dict[str, Any]] = []
        self.feedback_collector = FusionFeedbackCollector()

    async def fuse_with_adaptation(self, bundle: MultimodalInputBundle,
                                 task_context: str = "general") -> FusionResult:
        """Perform fusion with adaptive weight learning."""
        # Get context-specific weights
        if task_context not in self.context_learners:
            self.context_learners[task_context] = FusionWeightLearner(self.base_weights.copy())

        learner = self.context_learners[task_context]
        optimal_weights = learner.get_optimal_weights(task_context)

        # Perform fusion with optimal weights
        fusion_engine = MultimodalFusionEngine()
        fusion_engine.modality_weights = optimal_weights

        fusion_result = await fusion_engine.fuse_modalities(bundle)

        # Store fusion result for potential feedback learning
        fusion_record = {
            'timestamp': datetime.now(),
            'bundle': bundle,
            'fusion_result': fusion_result,
            'weights_used': optimal_weights.copy(),
            'task_context': task_context,
            'feedback_pending': True
        }
        self.fusion_history.append(fusion_record)

        return fusion_result

    async def provide_feedback(self, fusion_timestamp: datetime,
                             feedback_score: float, detailed_feedback: Optional[Dict[str, Any]] = None):
        """Provide feedback about fusion performance for learning."""
        # Find the corresponding fusion result
        target_fusion = None
        for fusion_record in reversed(self.fusion_history):
            if fusion_record['timestamp'] == fusion_timestamp:
                target_fusion = fusion_record
                break

        if not target_fusion:
            return False

        # Mark as feedback received
        target_fusion['feedback_pending'] = False
        target_fusion['feedback_score'] = feedback_score
        target_fusion['detailed_feedback'] = detailed_feedback or {}

        # Update learners
        fusion_result = target_fusion['fusion_result']
        task_context = target_fusion['task_context']

        # Update context-specific learner
        if task_context in self.context_learners:
            await self.context_learners[task_context].update_weights_from_feedback(
                fusion_result, feedback_score, task_context
            )

        # Update global learner
        await self.global_learner.update_weights_from_feedback(
            fusion_result, feedback_score, task_context
        )

        # Store feedback for analysis
        await self.feedback_collector.store_feedback(fusion_result, feedback_score, detailed_feedback)

        return True

    async def get_adaptation_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights about adaptation performance."""
        insights = {
            'global_learning': self.global_learner.get_learning_insights(),
            'context_specific': {},
            'feedback_summary': await self.feedback_collector.get_feedback_summary(),
            'performance_trends': self._analyze_performance_trends()
        }

        # Context-specific insights
        for context, learner in self.context_learners.items():
            insights['context_specific'][context] = learner.get_learning_insights()

        return insights

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(self.fusion_history) < 5:
            return {'status': 'insufficient_data'}

        # Get recent fusions with feedback
        recent_fusions = [f for f in self.fusion_history[-20:]
                         if not f.get('feedback_pending', True)]

        if not recent_fusions:
            return {'status': 'no_feedback_data'}

        feedback_scores = [f['feedback_score'] for f in recent_fusions]
        timestamps = [f['timestamp'] for f in recent_fusions]

        # Calculate trend
        if len(feedback_scores) > 1:
            time_nums = [(t - timestamps[0]).total_seconds() for t in timestamps]
            slope, _ = np.polyfit(time_nums, feedback_scores, 1)
            trend = 'improving' if slope > 0.001 else 'declining' if slope < -0.001 else 'stable'
        else:
            trend = 'insufficient_data'
            slope = 0.0

        return {
            'trend': trend,
            'slope': slope,
            'avg_recent_score': np.mean(feedback_scores[-5:]) if len(feedback_scores) >= 5 else np.mean(feedback_scores),
            'volatility': np.std(feedback_scores) if len(feedback_scores) > 1 else 0.0
        }


class FusionFeedbackCollector:
    """Collects and analyzes feedback about fusion performance."""

    def __init__(self):
        self.feedback_history: List[Dict[str, Any]] = []
        self.feedback_patterns: Dict[str, List[Dict[str, Any]]] = {}

    async def store_feedback(self, fusion_result: FusionResult, feedback_score: float,
                           detailed_feedback: Optional[Dict[str, Any]] = None):
        """Store feedback data for analysis."""
        feedback_entry = {
            'timestamp': datetime.now(),
            'fusion_result': fusion_result,
            'feedback_score': feedback_score,
            'detailed_feedback': detailed_feedback or {},
            'modality_contributions': fusion_result.confidence_scores,
            'processing_time': fusion_result.processing_time
        }

        self.feedback_history.append(feedback_entry)

        # Categorize by performance level
        if feedback_score >= 0.8:
            category = 'high_performance'
        elif feedback_score >= 0.6:
            category = 'medium_performance'
        else:
            category = 'low_performance'

        if category not in self.feedback_patterns:
            self.feedback_patterns[category] = []
        self.feedback_patterns[category].append(feedback_entry)

    async def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of collected feedback."""
        if not self.feedback_history:
            return {'status': 'no_feedback'}

        recent_feedback = self.feedback_history[-20:] if len(self.feedback_history) > 20 else self.feedback_history

        return {
            'total_feedback_entries': len(self.feedback_history),
            'average_score': np.mean([f['feedback_score'] for f in recent_feedback]),
            'score_distribution': self._get_score_distribution(recent_feedback),
            'performance_patterns': self._analyze_performance_patterns(),
            'learning_opportunities': self._identify_learning_opportunities()
        }

    def _get_score_distribution(self, feedback_list: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of feedback scores."""
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}

        for feedback in feedback_list:
            score = feedback['feedback_score']
            if score >= 0.9:
                distribution['excellent'] += 1
            elif score >= 0.7:
                distribution['good'] += 1
            elif score >= 0.5:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1

        return distribution

    def _analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in fusion performance."""
        patterns = {}

        for category, feedbacks in self.feedback_patterns.items():
            if not feedbacks:
                continue

            # Analyze modality contributions for this performance level
            modality_scores = {}
            for feedback in feedbacks:
                for modality, score in feedback['modality_contributions'].items():
                    if modality not in modality_scores:
                        modality_scores[modality] = []
                    modality_scores[modality].append(score * feedback['feedback_score'])

            patterns[category] = {
                'count': len(feedbacks),
                'avg_modality_contribution': {
                    modality: np.mean(scores) if scores else 0.0
                    for modality, scores in modality_scores.items()
                }
            }

        return patterns

    def _identify_learning_opportunities(self) -> List[str]:
        """Identify opportunities for improving fusion learning."""
        opportunities = []

        if len(self.feedback_history) < 10:
            opportunities.append('collect_more_feedback')

        # Check for consistently low-performing modalities
        if self.feedback_patterns.get('low_performance'):
            low_perf_feedbacks = self.feedback_patterns['low_performance']
            modality_failures = {}

            for feedback in low_perf_feedbacks:
                for modality, score in feedback['modality_contributions'].items():
                    if score < 0.3:  # Low confidence modality
                        modality_failures[modality] = modality_failures.get(modality, 0) + 1

            for modality, failures in modality_failures.items():
                if failures > len(low_perf_feedbacks) * 0.5:  # >50% of low performance cases
                    opportunities.append(f'improve_{modality}_processing')

        # Check for feedback consistency
        recent_scores = [f['feedback_score'] for f in self.feedback_history[-10:]]
        if len(recent_scores) >= 5 and np.std(recent_scores) > 0.3:
                        opportunities.append('reduce_feedback_volatility')

        return opportunities


@dataclass
class VideoFrame:
    """Represents a single frame from a video stream."""

    frame_data: bytes
    frame_number: int
    timestamp: datetime
    duration_ms: float  # Duration this frame represents
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 1.0

    @property
    def is_valid(self) -> bool:
        """Check if the frame is valid."""
        return len(self.frame_data) > 0 and self.quality_score > 0.1


@dataclass
class VideoInput:
    """Container for video input data."""

    video_id: str
    frames: List[VideoFrame] = field(default_factory=list)
    fps: float = 30.0
    duration_seconds: float = 0.0
    resolution: Tuple[int, int] = (1920, 1080)  # width, height
    codec: str = "h264"
    metadata: Dict[str, Any] = field(default_factory=dict)
    audio_track: Optional[bytes] = None  # Associated audio if available

    def add_frame(self, frame: VideoFrame):
        """Add a frame to the video."""
        self.frames.append(frame)
        self.duration_seconds = max(self.duration_seconds,
                                  frame.timestamp.timestamp() - self.frames[0].timestamp.timestamp())

    def get_frames_in_range(self, start_time: datetime, end_time: datetime) -> List[VideoFrame]:
        """Get frames within a time range."""
        return [frame for frame in self.frames
                if start_time <= frame.timestamp <= end_time]

    def get_frame_at_time(self, target_time: datetime) -> Optional[VideoFrame]:
        """Get the frame closest to a specific time."""
        if not self.frames:
            return None

        # Find closest frame by timestamp
        closest_frame = min(self.frames,
                          key=lambda f: abs((f.timestamp - target_time).total_seconds()))
        return closest_frame

    def extract_temporal_segments(self, segment_duration_ms: int = 1000) -> List[List[VideoFrame]]:
        """Extract temporal segments from the video."""
        if not self.frames:
            return []

        segments = []
        current_segment = []
        segment_start_time = self.frames[0].timestamp

        for frame in sorted(self.frames, key=lambda f: f.timestamp):
            if (frame.timestamp - segment_start_time).total_seconds() * 1000 >= segment_duration_ms:
                if current_segment:
                    segments.append(current_segment)
                current_segment = [frame]
                segment_start_time = frame.timestamp
            else:
                current_segment.append(frame)

        if current_segment:
            segments.append(current_segment)

        return segments


class VideoFeatureExtractor:
    """
    Extracts spatial and temporal features from video data.
    """

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self.spatial_extractor = None  # Would integrate with vision models like ResNet, ViT
        self.temporal_extractor = None  # Would integrate with video models like 3D CNNs, Transformers
        self.feature_cache: Dict[str, Dict[str, Any]] = {}

    async def extract_spatial_features(self, frame: VideoFrame) -> Dict[str, Any]:
        """Extract spatial features from a single frame."""
        cache_key = f"spatial_{frame.frame_number}_{hash(frame.frame_data)}"

        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]

        # Mock spatial feature extraction
        # In practice, this would use computer vision models
        features = {
            'frame_number': frame.frame_number,
            'timestamp': frame.timestamp,
            'spatial_features': {
                'brightness': self._calculate_brightness_mock(frame),
                'contrast': self._calculate_contrast_mock(frame),
                'color_histogram': self._calculate_color_histogram_mock(frame),
                'edge_density': self._calculate_edge_density_mock(frame),
                'object_count': self._estimate_object_count_mock(frame)
            },
            'embeddings': self._generate_spatial_embeddings_mock(frame),
            'quality_metrics': {
                'blur_score': self._calculate_blur_score_mock(frame),
                'noise_level': self._calculate_noise_level_mock(frame)
            }
        }

        self.feature_cache[cache_key] = features
        return features

    async def extract_temporal_features(self, frames: List[VideoFrame]) -> Dict[str, Any]:
        """Extract temporal features from a sequence of frames."""
        if not frames:
            return {}

        sequence_key = f"temporal_{frames[0].frame_number}_{frames[-1].frame_number}_{len(frames)}"

        if sequence_key in self.feature_cache:
            return self.feature_cache[sequence_key]

        # Sort frames by timestamp
        sorted_frames = sorted(frames, key=lambda f: f.timestamp)

        # Mock temporal feature extraction
        features = {
            'sequence_length': len(frames),
            'duration_ms': (sorted_frames[-1].timestamp - sorted_frames[0].timestamp).total_seconds() * 1000,
            'temporal_features': {
                'motion_vectors': self._calculate_motion_vectors_mock(sorted_frames),
                'scene_changes': self._detect_scene_changes_mock(sorted_frames),
                'rhythm_patterns': self._analyze_rhythm_patterns_mock(sorted_frames),
                'action_sequences': self._identify_action_sequences_mock(sorted_frames)
            },
            'embeddings': self._generate_temporal_embeddings_mock(sorted_frames),
            'quality_metrics': {
                'stability_score': self._calculate_stability_score_mock(sorted_frames),
                'consistency_score': self._calculate_consistency_score_mock(sorted_frames)
            }
        }

        self.feature_cache[sequence_key] = features
        return features

    async def extract_comprehensive_features(self, video: VideoInput) -> Dict[str, Any]:
        """Extract comprehensive features from an entire video."""
        video_key = f"comprehensive_{video.video_id}"

        if video_key in self.feature_cache:
            return self.feature_cache[video_key]

        # Extract features from all frames
        spatial_features = []
        for frame in video.frames:
            spatial = await self.extract_spatial_features(frame)
            spatial_features.append(spatial)

        # Extract temporal features from segments
        temporal_segments = video.extract_temporal_segments()
        temporal_features = []
        for segment in temporal_segments:
            temporal = await self.extract_temporal_features(segment)
            temporal_features.append(temporal)

        # Combine into comprehensive representation
        comprehensive = {
            'video_id': video.video_id,
            'duration_seconds': video.duration_seconds,
            'fps': video.fps,
            'resolution': video.resolution,
            'total_frames': len(video.frames),
            'spatial_summary': self._summarize_spatial_features(spatial_features),
            'temporal_summary': self._summarize_temporal_features(temporal_features),
            'video_level_features': {
                'overall_motion': self._calculate_overall_motion(temporal_features),
                'scene_complexity': self._calculate_scene_complexity(spatial_features),
                'content_density': self._calculate_content_density(spatial_features, temporal_features),
                'emotional_content': self._analyze_emotional_content_mock(spatial_features)
            },
            'embeddings': self._generate_video_embeddings_mock(spatial_features, temporal_features),
            'quality_assessment': self._assess_video_quality(spatial_features, temporal_features)
        }

        self.feature_cache[video_key] = comprehensive
        return comprehensive

    def _calculate_brightness_mock(self, frame: VideoFrame) -> float:
        """Mock brightness calculation."""
        # In practice, would analyze pixel values
        return 0.7 + 0.3 * (hash(frame.frame_data) % 100) / 100.0

    def _calculate_contrast_mock(self, frame: VideoFrame) -> float:
        """Mock contrast calculation."""
        return 0.6 + 0.4 * (hash(frame.frame_data + b'contrast') % 100) / 100.0

    def _calculate_color_histogram_mock(self, frame: VideoFrame) -> Dict[str, int]:
        """Mock color histogram."""
        return {'red': 25, 'green': 30, 'blue': 45}

    def _calculate_edge_density_mock(self, frame: VideoFrame) -> float:
        """Mock edge density calculation."""
        return 0.4 + 0.6 * (hash(frame.frame_data + b'edges') % 100) / 100.0

    def _estimate_object_count_mock(self, frame: VideoFrame) -> int:
        """Mock object count estimation."""
        return 3 + (hash(frame.frame_data + b'objects') % 7)

    def _generate_spatial_embeddings_mock(self, frame: VideoFrame) -> List[float]:
        """Mock spatial embeddings generation."""
        # Would be actual embeddings from vision model
        return [0.1 * (i % 10) for i in range(512)]

    def _calculate_blur_score_mock(self, frame: VideoFrame) -> float:
        """Mock blur score calculation."""
        return 0.8 + 0.2 * (hash(frame.frame_data + b'blur') % 100) / 100.0

    def _calculate_noise_level_mock(self, frame: VideoFrame) -> float:
        """Mock noise level calculation."""
        return 0.1 + 0.3 * (hash(frame.frame_data + b'noise') % 100) / 100.0

    def _calculate_motion_vectors_mock(self, frames: List[VideoFrame]) -> List[Dict[str, float]]:
        """Mock motion vector calculation."""
        vectors = []
        for i in range(len(frames) - 1):
            vectors.append({
                'dx': 0.1 * (hash(frames[i].frame_data) % 20 - 10),
                'dy': 0.1 * (hash(frames[i + 1].frame_data) % 20 - 10),
                'magnitude': 0.5 + 0.5 * (hash(frames[i].frame_data + frames[i + 1].frame_data) % 100) / 100.0
            })
        return vectors

    def _detect_scene_changes_mock(self, frames: List[VideoFrame]) -> List[int]:
        """Mock scene change detection."""
        changes = []
        for i in range(1, len(frames)):
            if hash(frames[i].frame_data) % 100 > 85:  # Random scene changes
                changes.append(i)
        return changes

    def _analyze_rhythm_patterns_mock(self, frames: List[VideoFrame]) -> Dict[str, Any]:
        """Mock rhythm pattern analysis."""
        return {
            'tempo': 120 + (hash(frames[0].frame_data) % 60),
            'regularity': 0.7 + 0.3 * (hash(frames[0].frame_data + b'rhythm') % 100) / 100.0,
            'patterns': ['steady', 'intermittent']
        }

    def _identify_action_sequences_mock(self, frames: List[VideoFrame]) -> List[str]:
        """Mock action sequence identification."""
        actions = ['movement', 'interaction']
        if len(frames) > 10:
            actions.append('complex_action')
        return actions

    def _generate_temporal_embeddings_mock(self, frames: List[VideoFrame]) -> List[float]:
        """Mock temporal embeddings generation."""
        return [0.1 * (i % 10) for i in range(256)]

    def _calculate_stability_score_mock(self, frames: List[VideoFrame]) -> float:
        """Mock stability score calculation."""
        return 0.8 + 0.2 * (hash(frames[0].frame_data + b'stability') % 100) / 100.0

    def _calculate_consistency_score_mock(self, frames: List[VideoFrame]) -> float:
        """Mock consistency score calculation."""
        return 0.75 + 0.25 * (hash(frames[0].frame_data + b'consistency') % 100) / 100.0

    def _summarize_spatial_features(self, spatial_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize spatial features across all frames."""
        if not spatial_features:
            return {}

        brightness_values = [f['spatial_features']['brightness'] for f in spatial_features]
        contrast_values = [f['spatial_features']['contrast'] for f in spatial_features]

        return {
            'avg_brightness': np.mean(brightness_values),
            'brightness_variance': np.var(brightness_values),
            'avg_contrast': np.mean(contrast_values),
            'contrast_variance': np.var(contrast_values),
            'dominant_colors': self._find_dominant_colors(spatial_features),
            'avg_blur_score': np.mean([f['quality_metrics']['blur_score'] for f in spatial_features])
        }

    def _summarize_temporal_features(self, temporal_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize temporal features across all segments."""
        if not temporal_features:
            return {}

        motion_magnitudes = []
        for tf in temporal_features:
            for mv in tf['temporal_features']['motion_vectors']:
                motion_magnitudes.append(mv['magnitude'])

        return {
            'total_motion': np.sum(motion_magnitudes),
            'avg_motion': np.mean(motion_magnitudes) if motion_magnitudes else 0,
            'scene_changes': sum(len(tf['temporal_features']['scene_changes']) for tf in temporal_features),
            'rhythm_consistency': np.mean([tf['temporal_features']['rhythm_patterns']['regularity']
                                         for tf in temporal_features if 'rhythm_patterns' in tf['temporal_features']]),
            'avg_stability': np.mean([tf['quality_metrics']['stability_score'] for tf in temporal_features])
        }

    def _find_dominant_colors(self, spatial_features: List[Dict[str, Any]]) -> List[str]:
        """Find dominant colors across frames."""
        # Simplified color analysis
        return ['blue', 'green', 'red']

    def _calculate_overall_motion(self, temporal_features: List[Dict[str, Any]]) -> float:
        """Calculate overall motion in the video."""
        if not temporal_features:
            return 0.0
        return np.mean([tf['temporal_summary']['avg_motion'] for tf in temporal_features
                       if 'temporal_summary' in tf])

    def _calculate_scene_complexity(self, spatial_features: List[Dict[str, Any]]) -> float:
        """Calculate scene complexity based on spatial features."""
        if not spatial_features:
            return 0.0
        complexities = [f['spatial_features']['object_count'] * f['spatial_features']['edge_density']
                       for f in spatial_features]
        return np.mean(complexities)

    def _calculate_content_density(self, spatial_features: List[Dict[str, Any]],
                                 temporal_features: List[Dict[str, Any]]) -> float:
        """Calculate content density of the video."""
        spatial_density = self._calculate_scene_complexity(spatial_features)
        temporal_density = self._calculate_overall_motion(temporal_features)
        return (spatial_density + temporal_density) / 2.0

    def _analyze_emotional_content_mock(self, spatial_features: List[Dict[str, Any]]) -> Dict[str, float]:
        """Mock emotional content analysis."""
        return {
            'happiness': 0.3,
            'sadness': 0.1,
            'energy': 0.8,
            'calmness': 0.6
        }

    def _generate_video_embeddings_mock(self, spatial_features: List[Dict[str, Any]],
                                      temporal_features: List[Dict[str, Any]]) -> List[float]:
        """Mock video-level embeddings generation."""
        return [0.1 * (i % 10) for i in range(1024)]

    def _assess_video_quality(self, spatial_features: List[Dict[str, Any]],
                            temporal_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall video quality."""
        if not spatial_features:
            return {'overall_quality': 0.0}

        blur_scores = [f['quality_metrics']['blur_score'] for f in spatial_features]
        stability_scores = [tf['quality_metrics'].get('stability_score', 0.8)
                          for tf in temporal_features if 'quality_metrics' in tf]

        return {
            'overall_quality': np.mean(blur_scores + stability_scores),
            'sharpness_score': np.mean(blur_scores),
            'stability_score': np.mean(stability_scores) if stability_scores else 0.8,
            'recommendations': self._generate_quality_recommendations(blur_scores, stability_scores)
        }

    def _generate_quality_recommendations(self, blur_scores: List[float],
                                        stability_scores: List[float]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        avg_blur = np.mean(blur_scores)
        if avg_blur < 0.6:
            recommendations.append("Consider using image stabilization")

        avg_stability = np.mean(stability_scores) if stability_scores else 0.8
        if avg_stability < 0.7:
            recommendations.append("Video appears shaky - consider tripod or stabilization")

        return recommendations or ["Video quality is acceptable"]


class VideoLanguageAgent(VisionLanguageAgent):
    """
    Enhanced agent that processes both video and text with temporal understanding.
    """

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)
        self.video_extractor = VideoFeatureExtractor()
        self.temporal_fusion = TemporalFusionEngine()

    async def execute(self, inputs: Union[MultimodalInputBundle, Dict[str, Any]]) -> ProbabilisticResult:
        """Execute video-language processing with temporal fusion."""
        if isinstance(inputs, dict):
            bundle = self._convert_dict_to_bundle(inputs)
        else:
            bundle = inputs

        # Extract video features if present
        video_features = None
        if any(inp.has_modality('video') for inp in bundle.inputs):
            video_input = self._extract_video_from_bundle(bundle)
            if video_input:
                video_features = await self.video_extractor.extract_comprehensive_features(video_input)

        # Perform temporal fusion
        fusion_result = await self.temporal_fusion.fuse_temporal_modalities(bundle, video_features)

        # Process with video-language understanding
        understanding = await self._understand_video_language_content(fusion_result, video_features)

        # Make decision with temporal uncertainty
        decision = await self._make_temporal_decision(understanding, bundle)

        # Update knowledge graph with temporal links
        await self._update_temporal_knowledge_graph(bundle, understanding, video_features)

        return ProbabilisticResult(
            success=decision['confidence'] > self.confidence_threshold,
            confidence=decision['confidence'],
            alternatives=decision.get('alternatives', []),
            metadata={
                'fusion_result': fusion_result,
                'understanding': understanding,
                'video_features': video_features,
                'temporal_analysis': decision.get('temporal_analysis', {})
            }
        )

    def _extract_video_from_bundle(self, bundle: MultimodalInputBundle) -> Optional[VideoInput]:
        """Extract video data from multimodal bundle."""
        video_frames = []

        for inp in bundle.inputs:
            if hasattr(inp, 'video_frames'):  # Check if input contains video frames
                # Assuming video frames are stored in input metadata or as separate modality
                frames_data = inp.metadata.get('video_frames', [])
                for frame_data in frames_data:
                    frame = VideoFrame(
                        frame_data=frame_data.get('data', b''),
                        frame_number=frame_data.get('frame_number', 0),
                        timestamp=frame_data.get('timestamp', datetime.now()),
                        duration_ms=frame_data.get('duration_ms', 33.33)  # ~30fps
                    )
                    video_frames.append(frame)

        if video_frames:
            video = VideoInput(
                video_id=f"video_{bundle.sequence_id}",
                frames=video_frames,
                fps=30.0,
                duration_seconds=sum(f.duration_ms for f in video_frames) / 1000.0
            )
            return video

        return None

    async def _understand_video_language_content(self, fusion_result: FusionResult,
                                               video_features: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Understand content combining video and language features."""
        base_understanding = await self._understand_multimodal_content(fusion_result)

        if video_features:
            # Enhance understanding with video temporal information
            temporal_patterns = video_features.get('temporal_summary', {})
            scene_complexity = video_features.get('video_level_features', {}).get('scene_complexity', 0)

            base_understanding.update({
                'temporal_patterns': temporal_patterns,
                'scene_complexity': scene_complexity,
                'content_density': video_features.get('video_level_features', {}).get('content_density', 0),
                'emotional_content': video_features.get('video_level_features', {}).get('emotional_content', {}),
                'narrative_flow': self._analyze_narrative_flow(video_features)
            })

        return base_understanding

    def _analyze_narrative_flow(self, video_features: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze narrative flow in video content."""
        temporal_features = video_features.get('temporal_summary', {})

        # Analyze scene changes and motion patterns for narrative structure
        scene_changes = temporal_features.get('scene_changes', 0)
        motion_level = temporal_features.get('avg_motion', 0)

        if scene_changes > 10 and motion_level > 0.7:
            flow_type = 'action_packed'
            coherence = 0.6
        elif scene_changes < 3 and motion_level < 0.3:
            flow_type = 'static_narrative'
            coherence = 0.9
        else:
            flow_type = 'balanced_pacing'
            coherence = 0.8

        return {
            'flow_type': flow_type,
            'coherence_score': coherence,
            'scene_transitions': scene_changes,
            'rhythm_consistency': temporal_features.get('rhythm_consistency', 0)
        }

    async def _make_temporal_decision(self, understanding: Dict[str, Any],
                                    bundle: MultimodalInputBundle) -> Dict[str, Any]:
        """Make decision considering temporal aspects."""
        base_decision = await self._make_decision_with_uncertainty(understanding, bundle)

        # Adjust confidence based on temporal factors
        temporal_bonus = 0.0

        narrative_flow = understanding.get('narrative_flow', {})
        if narrative_flow.get('coherence_score', 0) > 0.8:
            temporal_bonus += 0.1  # Coherent narratives are more trustworthy

        if understanding.get('scene_complexity', 0) > 0.7:
            temporal_bonus += 0.05  # Complex scenes may indicate important content

        base_decision['confidence'] = min(1.0, base_decision['confidence'] + temporal_bonus)
        base_decision['temporal_analysis'] = {
            'narrative_coherence': narrative_flow.get('coherence_score', 0),
            'scene_complexity': understanding.get('scene_complexity', 0),
            'temporal_bonus': temporal_bonus
        }

        return base_decision

    async def _update_temporal_knowledge_graph(self, bundle: MultimodalInputBundle,
                                             understanding: Dict[str, Any],
                                             video_features: Optional[Dict[str, Any]]):
        """Update knowledge graph with temporal and video relationships."""
        await self._update_knowledge_graph(bundle, understanding)

        if video_features:
            # Add temporal nodes and connections
            for i, segment in enumerate(video_features.get('temporal_segments', [])):
                segment_node = KnowledgeNode(
                    id=f"{bundle.sequence_id}_temporal_segment_{i}",
                    modality='video_temporal',
                    content={
                        'segment_info': segment,
                        'understanding': understanding,
                        'timestamp': datetime.now()
                    },
                    confidence=understanding.get('confidence', 0.5),
                    temporal_context=datetime.now()
                )

                self.knowledge_graph.add_node(segment_node)

                # Connect to related text nodes
                for text_input in bundle.inputs:
                    if text_input.has_modality('text'):
                        # Create cross-modal link between video segment and text
                        self.knowledge_graph.add_cross_modal_connection(
                            segment_node.id,
                            f"{bundle.sequence_id}_text_{bundle.inputs.index(text_input)}",
                            'temporal_text_alignment'
                        )


class TemporalFusionEngine:
    """
    Advanced fusion engine that handles temporal aspects of multimodal data.
    """

    def __init__(self, temporal_window_seconds: float = 5.0, fusion_strategy: str = "temporal_attention"):
        self.temporal_window_seconds = temporal_window_seconds
        self.fusion_strategy = fusion_strategy
        self.temporal_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self.temporal_weights: Dict[str, Dict[str, float]] = {}

    async def fuse_temporal_modalities(self, bundle: MultimodalInputBundle,
                                     video_features: Optional[Dict[str, Any]] = None) -> FusionResult:
        """Fuse modalities with temporal awareness."""
        start_time = asyncio.get_event_loop().time()

        # Group inputs by time windows
        temporal_groups = self._group_inputs_by_time(bundle.inputs)

        # Fuse each temporal group
        temporal_fusions = []
        for time_key, inputs in temporal_groups.items():
            group_bundle = MultimodalInputBundle(
                inputs=inputs,
                sequence_id=f"{bundle.sequence_id}_temporal_{time_key}"
            )

            fusion_engine = MultimodalFusionEngine()
            fusion_result = await fusion_engine.fuse_modalities(group_bundle)
            temporal_fusions.append((time_key, fusion_result))

        # Apply temporal fusion strategy
        if self.fusion_strategy == "temporal_attention":
            final_fusion = await self._temporal_attention_fusion(temporal_fusions, video_features)
        elif self.fusion_strategy == "sequence_modeling":
            final_fusion = await self._sequence_modeling_fusion(temporal_fusions, video_features)
        else:
            final_fusion = await self._simple_temporal_fusion(temporal_fusions)

        # Update temporal weights based on fusion performance
        await self._update_temporal_weights(temporal_fusions, bundle.sequence_id)

        processing_time = asyncio.get_event_loop().time() - start_time

        return FusionResult(
            fused_representation=final_fusion,
            confidence_scores=self._aggregate_temporal_confidence(temporal_fusions),
            fusion_metadata={
                'strategy': self.fusion_strategy,
                'temporal_groups': len(temporal_groups),
                'video_enhanced': video_features is not None,
                'temporal_window': self.temporal_window_seconds
            },
            processing_time=processing_time,
            fusion_method=f"{self.fusion_strategy}_temporal"
        )

    def _group_inputs_by_time(self, inputs: List[MultimodalInput]) -> Dict[str, List[MultimodalInput]]:
        """Group inputs into temporal windows."""
        groups = {}
        window_size = timedelta(seconds=self.temporal_window_seconds)

        sorted_inputs = sorted(inputs, key=lambda x: x.timestamp)

        for inp in sorted_inputs:
            # Find which time window this input belongs to
            window_start = inp.timestamp.replace(second=0, microsecond=0)  # Align to minute boundary
            window_key = window_start.strftime("%Y%m%d%H%M%S")

            if window_key not in groups:
                groups[window_key] = []
            groups[window_key].append(inp)

        return groups

    async def _temporal_attention_fusion(self, temporal_fusions: List[Tuple[str, FusionResult]],
                                       video_features: Optional[Dict[str, Any]]) -> Any:
        """Fuse temporal segments using attention mechanism."""
        if not temporal_fusions:
            return {}

        # Extract features from each temporal segment
        segment_features = []
        for time_key, fusion_result in temporal_fusions:
            features = {
                'time_key': time_key,
                'fused_data': fusion_result.fused_representation,
                'confidence': fusion_result.confidence_scores,
                'importance_score': self._calculate_segment_importance(fusion_result, video_features)
            }
            segment_features.append(features)

        # Apply attention weights based on importance
        total_importance = sum(f['importance_score'] for f in segment_features)

        if total_importance == 0:
            # Equal weights if no importance differentiation
            weights = [1.0 / len(segment_features)] * len(segment_features)
        else:
            weights = [f['importance_score'] / total_importance for f in segment_features]

        # Weighted fusion of temporal segments
        fused_result = {}
        for i, features in enumerate(segment_features):
            weight = weights[i]
            for key, value in features['fused_data'].items():
                if isinstance(value, (int, float)):
                    if key not in fused_result:
                        fused_result[key] = 0.0
                    fused_result[key] += value * weight

        return fused_result

    async def _sequence_modeling_fusion(self, temporal_fusions: List[Tuple[str, FusionResult]],
                                      video_features: Optional[Dict[str, Any]]) -> Any:
        """Fuse using sequence modeling approach."""
        # Extract sequence of fused representations
        sequence = [fusion.fused_representation for _, fusion in temporal_fusions]

        if len(sequence) < 2:
            return sequence[0] if sequence else {}

        # Simple sequence aggregation (could be enhanced with RNN/LSTM)
        sequence_features = {}

        # Calculate trends and patterns across sequence
        for key in sequence[0].keys():
            if isinstance(sequence[0][key], (int, float)):
                values = [seq.get(key, 0) for seq in sequence if isinstance(seq.get(key), (int, float))]

                if values:
                    sequence_features[f"{key}_mean"] = np.mean(values)
                    sequence_features[f"{key}_trend"] = self._calculate_trend(values)
                    sequence_features[f"{key}_volatility"] = np.std(values) if len(values) > 1 else 0

        return sequence_features

    async def _simple_temporal_fusion(self, temporal_fusions: List[Tuple[str, FusionResult]]) -> Any:
        """Simple temporal fusion by averaging."""
        if not temporal_fusions:
            return {}

        all_features = {}
        for _, fusion_result in temporal_fusions:
            for key, value in fusion_result.fused_representation.items():
                if isinstance(value, (int, float)):
                    if key not in all_features:
                        all_features[key] = []
                    all_features[key].append(value)

        # Average values across temporal segments
        averaged_features = {}
        for key, values in all_features.items():
            averaged_features[key] = np.mean(values)

        return averaged_features

    def _calculate_segment_importance(self, fusion_result: FusionResult,
                                    video_features: Optional[Dict[str, Any]]) -> float:
        """Calculate importance score for a temporal segment."""
        base_importance = np.mean(list(fusion_result.confidence_scores.values()))

        # Boost importance based on video features if available
        if video_features:
            motion_level = video_features.get('temporal_summary', {}).get('avg_motion', 0)
            scene_changes = video_features.get('temporal_summary', {}).get('scene_changes', 0)

            # Higher motion and scene changes indicate potentially important segments
            video_bonus = (motion_level * 0.3) + (min(scene_changes, 5) * 0.1)
            base_importance += video_bonus

        return base_importance

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in a sequence of values."""
        if len(values) < 2:
            return 0.0

        # Simple linear trend
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope

    def _aggregate_temporal_confidence(self, temporal_fusions: List[Tuple[str, FusionResult]]) -> Dict[str, float]:
        """Aggregate confidence scores across temporal segments."""
        all_confidences = {}
        for _, fusion_result in temporal_fusions:
            for modality, confidence in fusion_result.confidence_scores.items():
                if modality not in all_confidences:
                    all_confidences[modality] = []
                all_confidences[modality].append(confidence)

        # Average confidence per modality
        avg_confidences = {}
        for modality, confidences in all_confidences.items():
            avg_confidences[modality] = np.mean(confidences)

        return avg_confidences

    async def _update_temporal_weights(self, temporal_fusions: List[Tuple[str, FusionResult]],
                                     sequence_id: str):
        """Update temporal fusion weights based on performance."""
        if sequence_id not in self.temporal_weights:
            self.temporal_weights[sequence_id] = {}

        # Simple learning: favor modalities that contributed to high-confidence fusions
        for time_key, fusion_result in temporal_fusions:
            for modality, confidence in fusion_result.confidence_scores.items():
                key = f"{time_key}_{modality}"
                if key not in self.temporal_weights[sequence_id]:
                    self.temporal_weights[sequence_id][key] = 0.5

                # Gradually adjust weight toward confident modalities
                current_weight = self.temporal_weights[sequence_id][key]
                adjustment = 0.01 * (confidence - 0.5)
                self.temporal_weights[sequence_id][key] = np.clip(
                    current_weight + adjustment, 0.1, 0.9
                )

    def get_temporal_stats(self, sequence_id: str) -> Dict[str, Any]:
        """Get temporal fusion statistics for a sequence."""
        weights = self.temporal_weights.get(sequence_id, {})

        return {
            'sequence_id': sequence_id,
            'learned_weights': weights,
            'avg_weight': np.mean(list(weights.values())) if weights else 0.0,
            'weight_variance': np.var(list(weights.values())) if weights else 0.0
        }
=======
Multi-modal agent support for UCUP Framework.

This module provides agents capable of processing and reasoning about
multiple modalities including text, images, audio, and structured data.
"""

import asyncio
import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

import numpy as np
from PIL import Image

from .probabilistic import AlternativePath, ProbabilisticAgent, ProbabilisticResult


class ModalityProcessor(Protocol):
    """Protocol for processing different input modalities."""

    async def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Process input data for a specific modality."""
        ...


class TextProcessor(ModalityProcessor):
    """Processes text inputs."""

    async def process(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Process text input."""
        # Basic text processing - could be enhanced with NLP
        return {
            'modality': 'text',
            'content': input_data,
            'length': len(input_data),
            'tokens': input_data.split(),  # Simple tokenization
            'sentiment': self._analyze_sentiment(input_data)
        }

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'


class ImageProcessor(ModalityProcessor):
    """Processes image inputs."""

    async def process(self, input_data: Union[str, bytes, Image.Image], **kwargs) -> Dict[str, Any]:
        """Process image input."""
        try:
            if isinstance(input_data, str):
                # Assume base64 encoded image
                image_data = base64.b64decode(input_data)
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(input_data, bytes):
                image = Image.open(io.BytesIO(input_data))
            elif isinstance(input_data, Image.Image):
                image = input_data
            else:
                raise ValueError("Unsupported image input type")

            # Basic image analysis
            width, height = image.size
            mode = image.mode

            # Convert to numpy array for further processing
            image_array = np.array(image)

            return {
                'modality': 'image',
                'dimensions': (width, height),
                'mode': mode,
                'format': image.format,
                'size_bytes': len(image.tobytes()) if hasattr(image, 'tobytes') else 0,
                'dominant_colors': self._extract_dominant_colors(image_array),
                'image_array': image_array
            }
        except Exception as e:
            return {
                'modality': 'image',
                'error': str(e),
                'processed': False
            }

    def _extract_dominant_colors(self, image_array: np.ndarray, num_colors: int = 3) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from image (simplified)."""
        try:
            # Flatten image and sample pixels
            pixels = image_array.reshape(-1, image_array.shape[-1])
            if pixels.shape[-1] >= 3:
                # Sample every 10th pixel for performance
                sampled_pixels = pixels[::10]

                # Simple clustering - just return most common colors
                # In practice, would use k-means clustering
                unique_colors, counts = np.unique(sampled_pixels, axis=0, return_counts=True)
                top_indices = np.argsort(counts)[-num_colors:]
                dominant_colors = unique_colors[top_indices]

                return [tuple(color[:3]) for color in dominant_colors]
            else:
                return []
        except:
            return []


class AudioProcessor(ModalityProcessor):
    """Processes audio inputs."""

    async def process(self, input_data: Union[str, bytes], **kwargs) -> Dict[str, Any]:
        """Process audio input."""
        try:
            # This is a placeholder - real audio processing would require librosa or similar
            if isinstance(input_data, str):
                # Assume base64 encoded audio
                audio_data = base64.b64decode(input_data)
            elif isinstance(input_data, bytes):
                audio_data = input_data
            else:
                raise ValueError("Unsupported audio input type")

            return {
                'modality': 'audio',
                'size_bytes': len(audio_data),
                'duration_seconds': None,  # Would need audio library to determine
                'sample_rate': None,       # Would need audio library to determine
                'channels': None,          # Would need audio library to determine
                'features': self._extract_audio_features(audio_data)
            }
        except Exception as e:
            return {
                'modality': 'audio',
                'error': str(e),
                'processed': False
            }

    def _extract_audio_features(self, audio_data: bytes) -> Dict[str, Any]:
        """Extract basic audio features (placeholder)."""
        # In practice, would extract MFCCs, spectrograms, etc.
        return {
            'energy': None,  # Would compute RMS energy
            'pitch': None,   # Would compute fundamental frequency
            'tempo': None    # Would estimate tempo
        }


class StructuredDataProcessor(ModalityProcessor):
    """Processes structured data inputs (JSON, CSV, etc.)."""

    async def process(self, input_data: Union[str, Dict, List], **kwargs) -> Dict[str, Any]:
        """Process structured data input."""
        try:
            if isinstance(input_data, str):
                # Try to parse as JSON
                import json
                try:
                    parsed_data = json.loads(input_data)
                except json.JSONDecodeError:
                    # Treat as CSV or plain text
                    parsed_data = input_data
            else:
                parsed_data = input_data

            return {
                'modality': 'structured_data',
                'data_type': type(parsed_data).__name__,
                'structure': self._analyze_structure(parsed_data),
                'summary': self._generate_summary(parsed_data),
                'parsed_data': parsed_data
            }
        except Exception as e:
            return {
                'modality': 'structured_data',
                'error': str(e),
                'processed': False
            }

    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of the data."""
        if isinstance(data, dict):
            return {
                'type': 'object',
                'keys': list(data.keys()),
                'depth': self._calculate_depth(data)
            }
        elif isinstance(data, list):
            return {
                'type': 'array',
                'length': len(data),
                'element_types': list(set(type(item).__name__ for item in data[:10]))  # Sample first 10
            }
        else:
            return {'type': type(data).__name__}

    def _calculate_depth(self, data: Any, max_depth: int = 10) -> int:
        """Calculate nesting depth of data structure."""
        if not isinstance(data, (dict, list)) or max_depth <= 0:
            return 0

        if isinstance(data, dict):
            return 1 + max((self._calculate_depth(value, max_depth - 1) for value in data.values()), default=0)
        elif isinstance(data, list):
            return 1 + max((self._calculate_depth(item, max_depth - 1) for item in data), default=0)

        return 0

    def _generate_summary(self, data: Any) -> Dict[str, Any]:
        """Generate a summary of the data."""
        if isinstance(data, dict):
            return {
                'num_fields': len(data),
                'field_types': {k: type(v).__name__ for k, v in data.items()}
            }
        elif isinstance(data, list):
            return {
                'num_items': len(data),
                'item_types': list(set(type(item).__name__ for item in data))
            }
        else:
            return {'value_type': type(data).__name__}


@dataclass
class MultiModalInput:
    """Container for multi-modal input data."""
    modalities: Dict[str, Any] = field(default_factory=dict)  # modality_name -> data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_modality(self, name: str, data: Any):
        """Add a modality to the input."""
        self.modalities[name] = data

    def get_modality(self, name: str) -> Any:
        """Get data for a specific modality."""
        return self.modalities.get(name)


@dataclass
class MultiModalFeatures:
    """Extracted features from multi-modal inputs."""
    text_features: Dict[str, Any] = field(default_factory=dict)
    image_features: Dict[str, Any] = field(default_factory=dict)
    audio_features: Dict[str, Any] = field(default_factory=dict)
    structured_features: Dict[str, Any] = field(default_factory=dict)
    cross_modal_features: Dict[str, Any] = field(default_factory=dict)  # Relationships between modalities


class MultiModalProcessor:
    """Processes multiple modalities and extracts cross-modal features."""

    def __init__(self):
        self.processors = {
            'text': TextProcessor(),
            'image': ImageProcessor(),
            'audio': AudioProcessor(),
            'structured_data': StructuredDataProcessor()
        }

    async def process_input(self, multimodal_input: MultiModalInput) -> MultiModalFeatures:
        """Process all modalities in the input."""
        features = MultiModalFeatures()

        # Process each modality
        processing_tasks = []
        for modality_name, data in multimodal_input.modalities.items():
            if modality_name in self.processors:
                task = self.processors[modality_name].process(data)
                processing_tasks.append((modality_name, task))

        # Execute processing tasks
        results = await asyncio.gather(*[task for _, task in processing_tasks])

        # Organize results
        for (modality_name, _), result in zip(processing_tasks, results):
            if modality_name == 'text':
                features.text_features = result
            elif modality_name == 'image':
                features.image_features = result
            elif modality_name == 'audio':
                features.audio_features = result
            elif modality_name == 'structured_data':
                features.structured_features = result

        # Extract cross-modal features
        features.cross_modal_features = self._extract_cross_modal_features(features)

        return features

    def _extract_cross_modal_features(self, features: MultiModalFeatures) -> Dict[str, Any]:
        """Extract features that relate multiple modalities."""
        cross_features = {}

        # Text-Image relationships
        if features.text_features and features.image_features:
            cross_features['text_image_alignment'] = self._analyze_text_image_alignment(
                features.text_features, features.image_features
            )

        # Text-Structured Data relationships
        if features.text_features and features.structured_features:
            cross_features['text_data_relevance'] = self._analyze_text_data_relevance(
                features.text_features, features.structured_features
            )

        # Image-Structured Data relationships
        if features.image_features and features.structured_features:
            cross_features['visual_data_correlation'] = self._analyze_visual_data_correlation(
                features.image_features, features.structured_features
            )

        return cross_features

    def _analyze_text_image_alignment(self, text_feat: Dict, image_feat: Dict) -> float:
        """Analyze how well text and image align (simplified)."""
        # This would use CLIP or similar models in practice
        # For now, return a mock alignment score
        return 0.7  # Placeholder

    def _analyze_text_data_relevance(self, text_feat: Dict, data_feat: Dict) -> float:
        """Analyze relevance between text and structured data."""
        # Simple keyword matching
        text_content = text_feat.get('content', '').lower()
        data_keys = ' '.join(data_feat.get('structure', {}).get('keys', [])).lower()

        common_words = set(text_content.split()) & set(data_keys.split())
        return len(common_words) / max(len(set(text_content.split())), 1)

    def _analyze_visual_data_correlation(self, image_feat: Dict, data_feat: Dict) -> float:
        """Analyze correlation between visual and structured data."""
        # Placeholder - would analyze if image represents the data
        return 0.5


class VisionLanguageAgent(ProbabilisticAgent):
    """
    Agent that can process both text and images for comprehensive reasoning.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multimodal_processor = MultiModalProcessor()

    async def execute(self, task: str, **kwargs) -> ProbabilisticResult:
        """Execute task with vision-language capabilities."""
        # Extract multimodal inputs
        multimodal_input = kwargs.get('multimodal_input')
        if not multimodal_input:
            # Fallback to text-only processing
            return await super().execute(task, **kwargs)

        # Process multimodal inputs
        features = await self.multimodal_processor.process_input(multimodal_input)

        # Generate reasoning prompt incorporating all modalities
        enhanced_prompt = self._create_multimodal_prompt(task, features)

        # Use LLM with multimodal context
        result, confidence = await self.llm.generate_with_confidence(enhanced_prompt)

        # Create alternatives based on different modality combinations
        alternatives = self._generate_multimodal_alternatives(task, features)

        return ProbabilisticResult(
            value=result,
            confidence=confidence,
            alternatives=alternatives,
            metadata={
                'modalities_used': list(multimodal_input.modalities.keys()),
                'multimodal_features': features.__dict__,
                'reasoning_type': 'vision_language'
            }
        )

    def _create_multimodal_prompt(self, task: str, features: MultiModalFeatures) -> str:
        """Create a prompt that incorporates multiple modalities."""
        prompt_parts = [f"Task: {task}\n"]

        # Add text context
        if features.text_features:
            text_content = features.text_features.get('content', '')
            sentiment = features.text_features.get('sentiment', 'neutral')
            prompt_parts.append(f"Text Content: {text_content}")
            prompt_parts.append(f"Text Sentiment: {sentiment}")

        # Add image context
        if features.image_features:
            dimensions = features.image_features.get('dimensions', 'unknown')
            colors = features.image_features.get('dominant_colors', [])
            prompt_parts.append(f"Image Dimensions: {dimensions}")
            if colors:
                prompt_parts.append(f"Dominant Colors: {colors}")

        # Add structured data context
        if features.structured_features:
            data_type = features.structured_features.get('data_type', 'unknown')
            structure = features.structured_features.get('structure', {})
            prompt_parts.append(f"Data Type: {data_type}")
            prompt_parts.append(f"Data Structure: {structure}")

        # Add cross-modal insights
        if features.cross_modal_features:
            alignment = features.cross_modal_features.get('text_image_alignment', 0)
            relevance = features.cross_modal_features.get('text_data_relevance', 0)
            prompt_parts.append(f"Text-Image Alignment: {alignment:.2f}")
            prompt_parts.append(f"Text-Data Relevance: {relevance:.2f}")

        prompt_parts.append("\nProvide a comprehensive answer considering all available modalities.")

        return "\n".join(prompt_parts)

    def _generate_multimodal_alternatives(self, task: str, features: MultiModalFeatures) -> List[AlternativePath]:
        """Generate alternative interpretations based on different modality combinations."""
        alternatives = []

        # Text-only alternative
        if features.text_features:
            alternatives.append(AlternativePath(
                value="Text-only analysis",
                confidence=0.6,
                reasoning_steps=["Focused solely on textual content"]
            ))

        # Image-focused alternative
        if features.image_features:
            alternatives.append(AlternativePath(
                value="Vision-focused analysis",
                confidence=0.7,
                reasoning_steps=["Prioritized visual information"]
            ))

        # Data-driven alternative
        if features.structured_features:
            alternatives.append(AlternativePath(
                value="Data-centric analysis",
                confidence=0.8,
                reasoning_steps=["Emphasized structured data insights"]
            ))

        return alternatives


class StructuredDataAgent(ProbabilisticAgent):
    """
    Agent specialized in analyzing and reasoning about structured data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_processor = StructuredDataProcessor()

    async def execute(self, task: str, **kwargs) -> ProbabilisticResult:
        """Execute task with structured data analysis capabilities."""
        data_input = kwargs.get('data_input')
        if not data_input:
            return await super().execute(task, **kwargs)

        # Process the structured data
        data_features = await self.data_processor.process(data_input)

        # Generate analysis prompt
        analysis_prompt = self._create_data_analysis_prompt(task, data_features)

        # Get analysis from LLM
        result, confidence = await self.llm.generate_with_confidence(analysis_prompt)

        # Generate alternative analyses
        alternatives = self._generate_data_alternatives(task, data_features)

        return ProbabilisticResult(
            value=result,
            confidence=confidence,
            alternatives=alternatives,
            metadata={
                'data_analysis': True,
                'data_features': data_features,
                'analysis_type': 'structured_data'
            }
        )

    def _create_data_analysis_prompt(self, task: str, data_features: Dict[str, Any]) -> str:
        """Create prompt for data analysis."""
        structure = data_features.get('structure', {})
        summary = data_features.get('summary', {})

        prompt = f"""
Task: {task}

Data Analysis Context:
- Data Type: {data_features.get('data_type', 'unknown')}
- Structure: {structure}
- Summary: {summary}

Please analyze this data and provide insights relevant to the task.
Consider patterns, trends, anomalies, and relationships within the data.
"""
        return prompt

    def _generate_data_alternatives(self, task: str, data_features: Dict[str, Any]) -> List[AlternativePath]:
        """Generate alternative data analysis approaches."""
        return [
            AlternativePath(
                value="Statistical summary approach",
                confidence=0.7,
                reasoning_steps=["Focused on descriptive statistics and distributions"]
            ),
            AlternativePath(
                value="Pattern recognition approach",
                confidence=0.6,
                reasoning_steps=["Looked for patterns and correlations in the data"]
            ),
            AlternativePath(
                value="Anomaly detection approach",
                confidence=0.5,
                reasoning_steps=["Identified outliers and unusual data points"]
            )
        ]


class AudioAnalysisAgent(ProbabilisticAgent):
    """
    Agent capable of processing and analyzing audio inputs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_processor = AudioProcessor()

    async def execute(self, task: str, **kwargs) -> ProbabilisticResult:
        """Execute task with audio analysis capabilities."""
        audio_input = kwargs.get('audio_input')
        if not audio_input:
            return await super().execute(task, **kwargs)

        # Process audio
        audio_features = await self.audio_processor.process(audio_input)

        # Create audio analysis prompt
        analysis_prompt = self._create_audio_analysis_prompt(task, audio_features)

        # Get analysis
        result, confidence = await self.llm.generate_with_confidence(analysis_prompt)

        return ProbabilisticResult(
            value=result,
            confidence=confidence,
            metadata={
                'audio_analysis': True,
                'audio_features': audio_features,
                'analysis_type': 'audio'
            }
        )

    def _create_audio_analysis_prompt(self, task: str, audio_features: Dict[str, Any]) -> str:
        """Create prompt for audio analysis."""
        return f"""
Task: {task}

Audio Context:
- Duration: {audio_features.get('duration_seconds', 'unknown')} seconds
- Sample Rate: {audio_features.get('sample_rate', 'unknown')} Hz
- Channels: {audio_features.get('channels', 'unknown')}
- Size: {audio_features.get('size_bytes', 0)} bytes

Please analyze this audio and provide insights relevant to the task.
Consider content, quality, patterns, and any notable characteristics.
"""
>>>>>>> 3e05f344029d58af444c7b0ae42852877e92eccf:src/ucup/multimodal.py
