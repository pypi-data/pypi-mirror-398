"""
Comprehensive tests for UCUP Advanced Probabilistic Models

Tests Bayesian Networks, Markov Decision Processes, and Monte Carlo Tree Search
"""

import pytest
import asyncio
import math
from unittest.mock import Mock, AsyncMock

from ucup import (
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
from ucup.errors import ValidationError


class TestBayesianNetwork:
    """Test Bayesian Network implementation."""

    def test_bayesian_node_creation(self):
        """Test creating Bayesian nodes."""
        node = BayesianNode(
            name="Weather",
            states=["sunny", "rainy"],
            parents=[],
            cpt={("sunny",): 0.8, ("rainy",): 0.2}
        )
        assert node.name == "Weather"
        assert node.states == ["sunny", "rainy"]
        assert node.parents == []

    def test_bayesian_node_validation(self):
        """Test Bayesian node validation."""
        # Valid node
        node = BayesianNode(
            name="Weather",
            states=["sunny", "rainy"],
            parents=[],
            cpt={("sunny",): 0.8, ("rainy",): 0.2}
        )
        assert node is not None

        # Invalid probabilities (don't sum to 1)
        with pytest.raises(UCUPValidationError):
            BayesianNode(
                name="Weather",
                states=["sunny", "rainy"],
                parents=[],
                cpt={("sunny",): 0.5, ("rainy",): 0.3}  # 0.8 != 1.0
            )

    def test_conditional_probability_table(self):
        """Test Conditional Probability Table operations."""
        cpt = ConditionalProbabilityTable(
            variables=["Weather", "Activity"],
            probabilities={
                ("sunny", "outdoor"): 0.9,
                ("sunny", "indoor"): 0.1,
                ("rainy", "outdoor"): 0.3,
                ("rainy", "indoor"): 0.7
            }
        )

        # Test getting probabilities
        assert cpt.get_probability(("sunny", "outdoor")) == 0.9
        assert cpt.get_probability(("rainy", "indoor")) == 0.7

        # Test evidence setting and reduction
        cpt.set_evidence({"Weather": "sunny"})
        reduced = cpt.reduce({"Weather": "sunny"})
        assert len(reduced.probabilities) == 2  # Only outdoor/indoor for sunny

    def test_bayesian_network_inference(self):
        """Test Bayesian network inference."""
        # Create simple network: Weather -> Activity
        network = BayesianNetwork()

        # Weather node (no parents)
        weather_node = BayesianNode(
            name="Weather",
            states=["sunny", "rainy"],
            parents=[],
            cpt={("sunny",): 0.8, ("rainy",): 0.2}
        )

        # Activity node (depends on weather)
        activity_node = BayesianNode(
            name="Activity",
            states=["outdoor", "indoor"],
            parents=["Weather"],
            cpt={
                ("sunny", "outdoor"): 0.9,
                ("sunny", "indoor"): 0.1,
                ("rainy", "outdoor"): 0.3,
                ("rainy", "indoor"): 0.7
            }
        )

        network.add_node(weather_node)
        network.add_node(activity_node)

        # Test marginal inference
        weather_marginal = network.compute_marginal("Weather")
        assert abs(weather_marginal["sunny"] - 0.8) < 0.001
        assert abs(weather_marginal["rainy"] - 0.2) < 0.001

        # Test inference with evidence
        network.set_evidence({"Activity": "outdoor"})
        activity_marginal = network.compute_marginal("Activity")
        # With outdoor activity observed, weather influences probability

    def test_bayesian_network_errors(self):
        """Test Bayesian network error handling."""
        network = BayesianNetwork()

        # Test adding node with non-existent parent
        with pytest.raises(UCUPValidationError):
            node = BayesianNode(
                name="Activity",
                states=["outdoor", "indoor"],
                parents=["NonExistentParent"],
                cpt={("parent_state", "outdoor"): 1.0}
            )
            network.add_node(node)

        # Test setting invalid evidence
        network.add_node(BayesianNode(
            name="Weather",
            states=["sunny", "rainy"],
            parents=[],
            cpt={("sunny",): 1.0}
        ))

        with pytest.raises(UCUPValidationError):
            network.set_evidence({"Weather": "cloudy"})  # Invalid state


class TestMarkovDecisionProcess:
    """Test Markov Decision Process implementation."""

    def test_mdp_creation(self):
        """Test creating MDP components."""
        mdp = MarkovDecisionProcess(discount_factor=0.9)

        # Add states
        start_state = MDPState("start", reward=0.0)
        goal_state = MDPState("goal", reward=1.0, is_terminal=True)

        mdp.add_state(start_state)
        mdp.add_state(goal_state)

        # Add actions
        move_action = MDPAction("move", cost=0.1)
        mdp.add_action(move_action)

        # Add transitions
        transition = MDPTransition(
            from_state="start",
            action="move",
            to_state="goal",
            probability=0.8,
            reward=1.0
        )
        mdp.add_transition(transition)

        assert len(mdp.states) == 2
        assert len(mdp.actions) == 1
        assert len(mdp.transitions) == 1

    def test_value_iteration(self):
        """Test value iteration algorithm."""
        mdp = MarkovDecisionProcess(discount_factor=0.9)

        # Simple two-state MDP
        mdp.add_state(MDPState("s1", reward=0.0))
        mdp.add_state(MDPState("s2", reward=1.0, is_terminal=True))

        mdp.add_action(MDPAction("to_s2"))

        # Deterministic transition
        mdp.add_transition(MDPTransition("s1", "to_s2", "s2", 1.0, 0.0))

        values = mdp.value_iteration(max_iterations=100)

        # s2 should have value 1.0 (terminal reward)
        assert abs(values["s2"] - 1.0) < 0.001

        # s1 should have discounted value of transition to s2
        expected_s1 = 0.9 * (0.0 + 1.0)  # discount * (reward + value_s2)
        assert abs(values["s1"] - expected_s1) < 0.001

    def test_policy_extraction(self):
        """Test policy extraction from values."""
        mdp = MarkovDecisionProcess()

        # Setup simple MDP
        mdp.add_state(MDPState("s1"))
        mdp.add_state(MDPState("s2", is_terminal=True))
        mdp.add_action(MDPAction("to_s2"))

        mdp.add_transition(MDPTransition("s1", "to_s2", "s2", 1.0, 1.0))

        values = {"s1": 0.9, "s2": 1.0}
        policy = mdp.extract_policy(values)

        assert policy["s1"] == "to_s2"
        assert policy["s2"] is None  # Terminal state

    def test_mdp_validation(self):
        """Test MDP validation."""
        mdp = MarkovDecisionProcess()

        # Test invalid discount factor
        with pytest.raises(Exception):  # Should be validation error
            MarkovDecisionProcess(discount_factor=1.5)

        # Test invalid transition probability
        with pytest.raises(UCUPValidationError):
            transition = MDPTransition("s1", "a1", "s2", 1.5, 0.0)  # Probability > 1
            mdp.add_transition(transition)


class TestMonteCarloTreeSearch:
    """Test Monte Carlo Tree Search implementation."""

    def test_mcts_node_creation(self):
        """Test MCTS node creation."""
        node = MCTSNode(state="test_state")
        assert node.state == "test_state"
        assert node.visits == 0
        assert node.value == 0.0
        assert node.children == []
        assert node.parent is None

    def test_mcts_initialization(self):
        """Test MCTS initialization."""
        mcts = MonteCarloTreeSearch(exploration_constant=1.4)
        assert mcts.exploration_constant == 1.4

    @pytest.mark.asyncio
    async def test_mcts_search(self):
        """Test basic MCTS search."""
        mcts = MonteCarloTreeSearch()

        # Mock the domain-specific methods
        original_select = mcts._select
        original_expand = mcts._expand
        original_simulate = mcts._simulate
        original_backpropagate = mcts._backpropagate

        mcts._select = Mock(return_value=MCTSNode(state="leaf", is_terminal=True))
        mcts._expand = Mock(return_value=MCTSNode(state="leaf", is_terminal=True))
        mcts._simulate = AsyncMock(return_value=1.0)
        mcts._backpropagate = Mock()

        root = await mcts.search("root_state", iterations=10)

        assert root.state == "root_state"
        # Verify methods were called
        assert mcts._select.called
        assert mcts._simulate.called
        assert mcts._backpropagate.called

    def test_ucb1_calculation(self):
        """Test UCB1 value calculation."""
        mcts = MonteCarloTreeSearch()

        # Create parent and child nodes
        parent = MCTSNode(state="parent", visits=10)
        child = MCTSNode(state="child", parent=parent, visits=3, value=2.0)

        ucb_value = mcts._ucb1_value(child)

        # UCB1 = exploitation + exploration
        exploitation = 2.0 / 3  # child.value / child.visits
        exploration = 1.4 * math.sqrt(math.log(10) / 3)  # c * sqrt(ln(N_parent)/N_child)

        expected_ucb = exploitation + exploration
        assert abs(ucb_value - expected_ucb) < 0.001


class TestBayesianAgentNetwork:
    """Test Bayesian Agent Network implementation."""

    def test_bayesian_agent_network_creation(self):
        """Test creating Bayesian agent network."""
        # Mock agents
        agent1 = Mock()
        agent1.__class__.__name__ = "Agent1"

        agent2 = Mock()
        agent2.__class__.__name__ = "Agent2"

        agents = [agent1, agent2]
        dependencies = {"Agent2": ["Agent1"]}

        network = BayesianAgentNetwork(agents, dependencies)

        assert len(network.agents) == 2
        assert "Agent1" in network.agents
        assert "Agent2" in network.agents

    @pytest.mark.asyncio
    async def test_bayesian_agent_coordination(self):
        """Test agent coordination with Bayesian network."""
        # Create mock agents with execute methods
        agent1 = Mock()
        agent1.__class__.__name__ = "Agent1"
        agent1.execute = AsyncMock(return_value=Mock(
            success=True,
            confidence=0.8,
            alternatives=[],
            metadata={}
        ))

        agent2 = Mock()
        agent2.__class__.__name__ = "Agent2"
        agent2.execute = AsyncMock(return_value=Mock(
            success=True,
            confidence=0.9,
            alternatives=[],
            metadata={}
        ))

        agents = [agent1, agent2]
        dependencies = {"Agent2": ["Agent1"]}

        network = BayesianAgentNetwork(agents, dependencies)

        result = await network.coordinate_with_uncertainty("test_task")

        assert result is not None
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'success')

        # Verify agents were called
        agent1.execute.assert_called_once()
        agent2.execute.assert_called_once()


class TestMDPBasedCoordinator:
    """Test MDP-based coordinator."""

    def test_mdp_coordinator_creation(self):
        """Test creating MDP coordinator."""
        # Mock agents
        agent1 = Mock()
        agent2 = Mock()

        coordinator = MDPBasedCoordinator([agent1, agent2])

        assert len(coordinator.agents) == 2
        assert isinstance(coordinator.mdp, MarkovDecisionProcess)

    @pytest.mark.asyncio
    async def test_mdp_policy_optimization(self):
        """Test policy optimization."""
        agent1 = Mock()
        agent2 = Mock()

        coordinator = MDPBasedCoordinator([agent1, agent2])

        environment_model = {"complexity": 0.5, "num_agents": 2}

        policy = await coordinator.optimize_policy(environment_model)

        # Should return one of the coordination strategies
        valid_strategies = ['delegate_to_best', 'parallel_execution', 'sequential_execution', 'consensus_voting']
        assert policy in valid_strategies


class TestMCTSReasoner:
    """Test MCTS-based reasoner."""

    def test_mcts_reasoner_creation(self):
        """Test creating MCTS reasoner."""
        reasoner = MCTSReasoner(max_rollout_depth=10)
        assert reasoner.max_rollout_depth == 10

    @pytest.mark.asyncio
    async def test_mcts_reasoning(self):
        """Test MCTS-based reasoning."""
        reasoner = MCTSReasoner()

        # Mock the domain methods
        original_expand = reasoner._expand
        original_simulate = reasoner._simulate

        reasoner._expand = AsyncMock(return_value="expanded_state")
        reasoner._simulate = AsyncMock(return_value=0.8)

        result = await reasoner.search("root_state", iterations=5)

        assert result is not None
        reasoner._expand.assert_called()
        reasoner._simulate.assert_called()


class TestAlphaZeroMCTS:
    """Test AlphaZero-style MCTS."""

    def test_puct_node_creation(self):
        """Test PUCT node creation."""
        node = PUCTNode(state="test_state", prior_probability=0.5)
        assert node.state == "test_state"
        assert node.prior_probability == 0.5
        assert node.visits == 0
        assert node.value_sum == 0.0

    def test_puct_selection(self):
        """Test PUCT child selection."""
        parent = PUCTNode(state="parent", visits=10)

        child1 = PUCTNode(state="child1", parent=parent, prior_probability=0.6, visits=5, value_sum=3.0)
        child2 = PUCTNode(state="child2", parent=parent, prior_probability=0.4, visits=3, value_sum=2.0)

        parent.children = [child1, child2]

        selected = parent.select_child(c_puct=1.0)

        # Should select one of the children
        assert selected in [child1, child2]

    def test_alphazero_mcts_creation(self):
        """Test AlphaZero MCTS creation."""
        mcts = AlphaZeroMCTS(c_puct=1.0)
        assert mcts.c_puct == 1.0

    @pytest.mark.asyncio
    async def test_alphazero_search(self):
        """Test AlphaZero MCTS search."""
        mcts = AlphaZeroMCTS()

        # Mock the domain methods
        mcts._evaluate_state = AsyncMock(return_value=([0.5, 0.3, 0.2], 0.6))
        mcts._get_possible_actions = AsyncMock(return_value=['a1', 'a2', 'a3'])
        mcts._run_simulation = AsyncMock()
        mcts._evaluate_leaf = AsyncMock(return_value=0.8)
        mcts._is_terminal = AsyncMock(return_value=False)
        mcts._take_action = AsyncMock(return_value="next_state")

        root = await mcts.search("root_state", num_simulations=10)

        assert root is not None
        assert root.state == "root_state"


class TestQLearningMDP:
    """Test Q-Learning MDP implementation."""

    def test_qlearning_creation(self):
        """Test Q-Learning MDP creation."""
        q_mdp = QLearningMDP(discount_factor=0.9, learning_rate=0.1, exploration_rate=0.1)

        assert q_mdp.discount_factor == 0.9
        assert q_mdp.learning_rate == 0.1
        assert q_mdp.exploration_rate == 0.1
        assert q_mdp.q_table == {}

    def test_qlearning_action_selection(self):
        """Test action selection."""
        q_mdp = QLearningMDP(exploration_rate=0.0)  # Greedy selection

        # Setup states and actions
        q_mdp.add_state(MDPState("s1"))
        q_mdp.add_action(MDPAction("a1"))
        q_mdp.add_action(MDPAction("a2"))

        # Set Q-values
        q_mdp.q_table[("s1", "a1")] = 1.0
        q_mdp.q_table[("s1", "a2")] = 0.5

        action = q_mdp.get_action("s1")

        assert action == "a1"  # Should select higher Q-value action

    def test_qlearning_learning(self):
        """Test Q-learning updates."""
        q_mdp = QLearningMDP(discount_factor=0.9, learning_rate=1.0)

        q_mdp.add_state(MDPState("s1"))
        q_mdp.add_state(MDPState("s2"))
        q_mdp.add_action(MDPAction("to_s2"))

        # Initial Q-value
        initial_q = q_mdp.q_table.get(("s1", "to_s2"), 0.0)

        # Learn from experience
        q_mdp.learn("s1", "to_s2", 1.0, "s2", done=True)

        # Q-value should be updated
        updated_q = q_mdp.q_table[("s1", "to_s2")]
        expected_q = initial_q + 1.0 * (1.0 + 0.9 * 0.0 - initial_q)  # Q-learning formula

        assert abs(updated_q - expected_q) < 0.001

    def test_qlearning_policy_extraction(self):
        """Test policy extraction."""
        q_mdp = QLearningMDP()

        q_mdp.add_state(MDPState("s1"))
        q_mdp.add_action(MDPAction("a1"))
        q_mdp.add_action(MDPAction("a2"))

        # Set Q-values
        q_mdp.q_table[("s1", "a1")] = 0.8
        q_mdp.q_table[("s1", "a2")] = 0.6

        policy = q_mdp.get_policy()

        assert policy["s1"] == "a1"  # Best action


class TestDeepQLearningMDP:
    """Test Deep Q-Learning MDP implementation."""

    def test_deep_qlearning_creation(self):
        """Test Deep Q-Learning creation."""
        dq_mdp = DeepQLearningMDP(
            discount_factor=0.9,
            learning_rate=0.001,
            exploration_rate=1.0,
            exploration_decay=0.995,
            min_exploration=0.01,
            memory_size=1000,
            batch_size=32,
            target_update_freq=100
        )

        assert dq_mdp.discount_factor == 0.9
        assert dq_mdp.learning_rate == 0.001
        assert dq_mdp.exploration_rate == 1.0
        assert dq_mdp.exploration_decay == 0.995
        assert dq_mdp.min_exploration == 0.01
        assert dq_mdp.memory_size == 1000
        assert dq_mdp.batch_size == 32
        assert dq_mdp.target_update_freq == 100
        assert dq_mdp.replay_memory.maxlen == 1000

    def test_experience_storage(self):
        """Test experience replay storage."""
        dq_mdp = DeepQLearningMDP(memory_size=10)

        # Store experience
        dq_mdp.store_experience("s1", "a1", 1.0, "s2", done=False)

        assert len(dq_mdp.replay_memory) == 1

        experience = dq_mdp.replay_memory[0]
        assert experience == ("s1", "a1", 1.0, "s2", False)

    def test_exploration_decay(self):
        """Test exploration rate decay."""
        dq_mdp = DeepQLearningMDP(exploration_rate=1.0, exploration_decay=0.9, min_exploration=0.1)

        initial_rate = dq_mdp.exploration_rate

        dq_mdp.decay_exploration()

        assert dq_mdp.exploration_rate == 0.9  # 1.0 * 0.9

        # Test minimum exploration
        dq_mdp.exploration_rate = 0.05
        dq_mdp.decay_exploration()
        assert dq_mdp.exploration_rate == 0.1  # Minimum rate

    def test_training_stats(self):
        """Test training statistics."""
        dq_mdp = DeepQLearningMDP()

        # Simulate some training
        dq_mdp.training_steps = 50
        dq_mdp.store_experience("s1", "a1", 1.0, "s2", False)
        dq_mdp.store_experience("s2", "a2", 0.5, "s3", True)

        stats = dq_mdp.get_training_stats()

        assert stats['training_steps'] == 50
        assert stats['replay_memory_size'] == 2
        assert 'exploration_rate' in stats
        assert 'q_table_stats' in stats


# Integration tests
class TestAdvancedProbabilisticIntegration:
    """Integration tests for advanced probabilistic models."""

    @pytest.mark.asyncio
    async def test_full_bayesian_agent_workflow(self):
        """Test complete Bayesian agent workflow."""
        # Create agents with different success patterns
        agent1 = Mock()
        agent1.__class__.__name__ = "ClassifierAgent"
        agent1.execute = AsyncMock(return_value=Mock(
            success=True, confidence=0.85, alternatives=[], metadata={}
        ))

        agent2 = Mock()
        agent2.__class__.__name__ = "ValidatorAgent"
        agent2.execute = AsyncMock(return_value=Mock(
            success=True, confidence=0.75, alternatives=[], metadata={}
        ))

        # Create Bayesian network with dependencies
        network = BayesianAgentNetwork([agent1, agent2], {"ValidatorAgent": ["ClassifierAgent"]})

        # Execute coordination
        result = await network.coordinate_with_uncertainty("validate_classification")

        # Verify result structure
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'success')
        assert 'agent_results' in result.metadata
        assert 'evidence' in result.metadata

    @pytest.mark.asyncio
    async def test_mcts_reasoning_workflow(self):
        """Test MCTS reasoning workflow."""
        reasoner = MCTSReasoner(max_rollout_depth=5)

        # Mock domain methods for a simple game-like scenario
        async def mock_expand(node):
            if len(node.children) == 0:
                # Create two possible moves
                child1 = MCTSNode(state=f"{node.state}_move1", parent=node)
                child2 = MCTSNode(state=f"{node.state}_move2", parent=node)
                node.children = [child1, child2]
            return node.children[0] if node.children else node

        async def mock_simulate(node):
            # Simple simulation: win if state contains 'good', lose otherwise
            return 1.0 if 'good' in str(node.state) else 0.0

        reasoner._expand = mock_expand
        reasoner._simulate = mock_simulate

        # Test reasoning
        best_action = await reasoner.search("initial_good_state", iterations=20)

        assert best_action is not None

    def test_qlearning_convergence(self):
        """Test Q-learning convergence on simple MDP."""
        q_mdp = QLearningMDP(discount_factor=0.9, learning_rate=0.1, exploration_rate=0.1)

        # Simple grid world-like MDP
        q_mdp.add_state(MDPState("start"))
        q_mdp.add_state(MDPState("goal", reward=1.0, is_terminal=True))
        q_mdp.add_state(MDPState("pit", reward=-1.0, is_terminal=True))

        q_mdp.add_action(MDPAction("right"))
        q_mdp.add_action(MDPAction("left"))

        # Deterministic transitions
        q_mdp.add_transition(MDPTransition("start", "right", "goal", 1.0, 0.0))
        q_mdp.add_transition(MDPTransition("start", "left", "pit", 1.0, 0.0))

        # Train for multiple episodes
        for episode in range(100):
            state = "start"
            done = False
            steps = 0

            while not done and steps < 10:
                action = q_mdp.get_action(state)
                if action == "right":
                    next_state, reward, done = "goal", 1.0, True
                else:
                    next_state, reward, done = "pit", -1.0, True

                q_mdp.learn(state, action, reward, next_state, done)
                state = next_state
                steps += 1

        # After training, should prefer "right" action
        policy = q_mdp.get_policy()
        assert policy["start"] == "right"

        # Check Q-values
        right_q = q_mdp.q_table.get(("start", "right"), 0.0)
        left_q = q_mdp.q_table.get(("start", "left"), 0.0)
        assert right_q > left_q  # Right should have higher Q-value


if __name__ == "__main__":
    pytest.main([__file__])
