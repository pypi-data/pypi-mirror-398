"""
Unit tests for BaseAutonomousAgent state capture and restore (TODO-168).

Tests the state persistence integration with StateManager:
- _capture_state() method
- _restore_state() method
- State helper methods (capture and restore)

Test Strategy: Tier 1 (Unit) - Mocked dependencies, fast execution
Coverage: 10 tests for Day 1 acceptance criteria
"""

from unittest.mock import Mock

from kaizen.agents.autonomous.base import AutonomousConfig, BaseAutonomousAgent
from kaizen.core.autonomy.state.manager import StateManager
from kaizen.core.autonomy.state.types import AgentState
from kaizen.signatures import InputField, OutputField, Signature


class TaskSignature(Signature):
    """Simple signature for testing"""

    task: str = InputField(description="Task to perform")
    result: str = OutputField(description="Result")


# ═══════════════════════════════════════════════════════════════
# Test: State Manager Initialization
# ═══════════════════════════════════════════════════════════════


def test_state_manager_initialized():
    """
    Test that state_manager is initialized in BaseAutonomousAgent.

    Validates:
    - state_manager field exists
    - current_step starts at 0
    - StateManager is created if not provided
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")

    # Act
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())

    # Assert
    assert hasattr(agent, "state_manager"), "Agent should have state_manager field"
    assert isinstance(
        agent.state_manager, StateManager
    ), "state_manager should be StateManager instance"
    assert agent.current_step == 0, "current_step should start at 0"


def test_state_manager_custom_provided():
    """
    Test that custom StateManager can be provided.

    Validates:
    - Custom StateManager is used when provided
    - Configuration is preserved
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    custom_manager = StateManager(checkpoint_frequency=5, retention_count=50)

    # Act
    agent = BaseAutonomousAgent(
        config=config, signature=TaskSignature(), state_manager=custom_manager
    )

    # Assert
    assert agent.state_manager is custom_manager, "Should use provided StateManager"
    assert (
        agent.state_manager.checkpoint_frequency == 5
    ), "Custom config should be preserved"
    assert (
        agent.state_manager.retention_count == 50
    ), "Custom retention should be preserved"


# ═══════════════════════════════════════════════════════════════
# Test: State Capture
# ═══════════════════════════════════════════════════════════════


def test_capture_state_basic():
    """
    Test basic state capture functionality.

    Validates:
    - _capture_state() returns AgentState
    - All required fields are populated
    - Step number is captured correctly
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent.current_step = 5

    # Act
    state = agent._capture_state()

    # Assert
    assert isinstance(state, AgentState), "Should return AgentState"
    assert state.step_number == 5, "Should capture current step"
    assert state.agent_id is not None, "Should have agent_id"
    assert state.conversation_history == [], "Should have conversation_history (empty)"
    assert state.pending_actions == [], "Should have pending_actions (empty)"


def test_capture_state_with_memory():
    """
    Test state capture with memory contents.

    Validates:
    - Conversation history is captured from memory
    - Memory contents are captured
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent.current_step = 3

    # Mock memory with messages
    mock_message = Mock()
    mock_message.role = "user"
    mock_message.content = "Test message"
    agent.memory = Mock()
    agent.memory.messages = [mock_message]
    agent.memory.metadata = {"key": "value"}

    # Act
    state = agent._capture_state()

    # Assert
    assert len(state.conversation_history) == 1, "Should capture 1 message"
    assert state.conversation_history[0]["role"] == "user", "Should capture role"
    assert (
        state.conversation_history[0]["content"] == "Test message"
    ), "Should capture content"
    assert state.memory_contents["message_count"] == 1, "Should capture message count"
    assert (
        state.memory_contents["metadata"]["key"] == "value"
    ), "Should capture metadata"


def test_capture_state_with_plan():
    """
    Test state capture with pending and completed actions.

    Validates:
    - Pending actions are captured
    - Completed actions are captured
    - Actions are filtered by status
    """
    # Arrange
    config = AutonomousConfig(
        max_cycles=10, planning_enabled=True, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0"
    )
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent.current_plan = [
        {"action": "step1", "status": "completed"},
        {"action": "step2", "status": "pending"},
        {"action": "step3", "status": "pending"},
    ]
    agent.current_step = 1

    # Act
    state = agent._capture_state()

    # Assert
    assert len(state.pending_actions) == 2, "Should capture 2 pending actions"
    assert len(state.completed_actions) == 1, "Should capture 1 completed action"
    assert (
        state.completed_actions[0]["action"] == "step1"
    ), "Should capture completed action"


def test_capture_state_with_budget():
    """
    Test state capture with budget tracking.

    Validates:
    - Budget spent is captured from execution_context
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())

    # Mock execution_context
    agent.execution_context = Mock()
    agent.execution_context.budget_used = 1.25

    # Act
    state = agent._capture_state()

    # Assert
    assert state.budget_spent_usd == 1.25, "Should capture budget spent"


# ═══════════════════════════════════════════════════════════════
# Test: State Restoration
# ═══════════════════════════════════════════════════════════════


def test_restore_state_basic():
    """
    Test basic state restoration functionality.

    Validates:
    - _restore_state() restores step number
    - Agent state is updated correctly
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())

    # Create state to restore
    state = AgentState(
        agent_id="test_agent",
        step_number=7,
        conversation_history=[],
        pending_actions=[],
        completed_actions=[],
    )

    # Act
    agent._restore_state(state)

    # Assert
    assert agent.current_step == 7, "Should restore step number"


def test_restore_state_with_memory():
    """
    Test state restoration with memory contents.

    Validates:
    - Conversation history is restored to memory
    - Memory metadata is restored
    """
    # Arrange
    config = AutonomousConfig(max_cycles=10, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0")
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())

    # Mock memory
    agent.memory = Mock()
    agent.memory.messages = []
    agent.memory.add_message = Mock()
    agent.memory.metadata = {}

    # Create state to restore
    state = AgentState(
        agent_id="test_agent",
        step_number=3,
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
        memory_contents={"metadata": {"restored": True}},
    )

    # Act
    agent._restore_state(state)

    # Assert
    assert agent.memory.add_message.call_count == 2, "Should restore 2 messages"
    assert agent.memory.metadata["restored"] is True, "Should restore metadata"


def test_restore_state_with_plan():
    """
    Test state restoration with pending and completed actions.

    Validates:
    - Pending actions are restored to current_plan
    - Completed actions are restored to current_plan
    """
    # Arrange
    config = AutonomousConfig(
        max_cycles=10, planning_enabled=True, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0"
    )
    agent = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent.current_plan = []

    # Create state to restore
    state = AgentState(
        agent_id="test_agent",
        step_number=2,
        pending_actions=[{"action": "pending1"}, {"action": "pending2"}],
        completed_actions=[{"action": "completed1"}],
    )

    # Act
    agent._restore_state(state)

    # Assert
    assert len(agent.current_plan) == 3, "Should restore 3 actions to plan"
    pending = [a for a in agent.current_plan if a["action"].startswith("pending")]
    completed = [a for a in agent.current_plan if a["action"].startswith("completed")]
    assert len(pending) == 2, "Should have 2 pending actions"
    assert len(completed) == 1, "Should have 1 completed action"


def test_capture_restore_roundtrip():
    """
    Test complete capture → restore roundtrip.

    Validates:
    - State captured can be restored
    - All critical state is preserved
    """
    # Arrange
    config = AutonomousConfig(
        max_cycles=10, planning_enabled=True, llm_provider="ollama", model="llama3.1:8b-instruct-q8_0"
    )
    agent1 = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent1.current_step = 5
    agent1.current_plan = [
        {"action": "step1", "status": "completed"},
        {"action": "step2", "status": "pending"},
    ]

    # Act: Capture state from agent1
    state = agent1._capture_state()

    # Create new agent and restore
    agent2 = BaseAutonomousAgent(config=config, signature=TaskSignature())
    agent2._restore_state(state)

    # Assert: agent2 should match agent1's state
    assert agent2.current_step == 5, "Step number should be preserved"
    assert len(agent2.current_plan) == 2, "Plan should be restored"


# ═══════════════════════════════════════════════════════════════
# Test Coverage Summary
# ═══════════════════════════════════════════════════════════════

"""
Test Coverage: 10/10 tests for Day 1 acceptance criteria

✅ State Manager Initialization (2 tests)
  - test_state_manager_initialized
  - test_state_manager_custom_provided

✅ State Capture (4 tests)
  - test_capture_state_basic
  - test_capture_state_with_memory
  - test_capture_state_with_plan
  - test_capture_state_with_budget

✅ State Restoration (3 tests)
  - test_restore_state_basic
  - test_restore_state_with_memory
  - test_restore_state_with_plan

✅ Roundtrip (1 test)
  - test_capture_restore_roundtrip

Total: 10 tests
Expected Runtime: <2 seconds (all mocked)
"""
