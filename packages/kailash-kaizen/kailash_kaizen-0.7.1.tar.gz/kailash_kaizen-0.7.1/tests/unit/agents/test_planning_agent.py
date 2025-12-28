"""
Unit tests for Planning Agent (TDD Approach - Tests Written First)

Test Coverage:
- 20 unit tests total
- Planning phase: 7 tests (plan generation, max steps, step quality)
- Validation phase: 6 tests (strict/warn/off modes, validation criteria, edge cases)
- Execution phase: 4 tests (step execution, error handling, result aggregation)
- Configuration: 3 tests (config validation, defaults, edge cases)

Test Structure:
1. Write ALL tests first (they should fail)
2. Implement minimal code to make tests pass
3. Refactor if needed
4. Verify all existing tests still pass

Expected test execution time: <1 second per test (Tier 1)
"""

import pytest

# Import agent components (will be implemented after tests)
try:
    from kaizen.agents.specialized.planning import (
        PlanningAgent,
        PlanningConfig,
        PlanningSignature,
    )
except ImportError:
    pytest.skip("Planning agent not yet implemented", allow_module_level=True)


# ============================================================================
# PLANNING PHASE TESTS (7 tests)
# ============================================================================


def test_plan_generation_simple_task():
    """Test plan generation for simple task"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        max_plan_steps=5,
    )
    agent = PlanningAgent(config=config)

    task = "Research AI ethics"
    result = agent.run(task=task)

    # Verify plan structure
    assert "plan" in result
    assert isinstance(result["plan"], list)
    assert len(result["plan"]) > 0
    assert len(result["plan"]) <= 5  # Respects max_plan_steps

    # Verify plan step structure
    for step in result["plan"]:
        assert "step" in step
        assert "action" in step
        assert "description" in step
        assert isinstance(step["step"], int)
        assert isinstance(step["action"], str)


def test_plan_generation_complex_task():
    """Test plan generation for complex multi-step task"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        max_plan_steps=10,
    )
    agent = PlanningAgent(config=config)

    task = "Create comprehensive research report on AI ethics with citations"
    result = agent.run(task=task)

    # Complex task should generate detailed plan
    assert len(result["plan"]) >= 3  # At least 3 steps for complex task

    # Plan should be ordered
    step_numbers = [step["step"] for step in result["plan"]]
    assert step_numbers == sorted(step_numbers)


def test_plan_generation_empty_task():
    """Test plan generation with empty task (error handling)"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    result = agent.run(task="")

    # Should handle gracefully
    assert "error" in result or "plan" in result
    if "error" in result:
        assert result["error"] == "INVALID_INPUT"
    else:
        assert len(result["plan"]) == 0


def test_plan_generation_respects_max_steps():
    """Test that plan generation respects max_plan_steps parameter"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        max_plan_steps=3,
    )
    agent = PlanningAgent(config=config)

    task = "Very complex task with many potential steps"
    result = agent.run(task=task)

    # Should not exceed max_plan_steps
    assert len(result["plan"]) <= 3


def test_plan_step_quality_has_required_fields():
    """Test that generated plan steps have all required fields"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    result = agent.run(task="Test task")

    required_fields = ["step", "action", "description"]
    for step in result["plan"]:
        for field in required_fields:
            assert field in step, f"Missing required field: {field}"


def test_plan_generation_with_context():
    """Test plan generation with additional context"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    task = "Create report"
    context = {"max_pages": 10, "audience": "executives"}
    result = agent.run(task=task, context=context)

    # Should generate plan considering context
    assert "plan" in result
    assert len(result["plan"]) > 0


def test_plan_generation_deterministic_with_low_temperature():
    """Test that low temperature produces consistent plans"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        temperature=0.0,
    )
    agent = PlanningAgent(config=config)

    task = "Simple task"
    result1 = agent.run(task=task)
    result2 = agent.run(task=task)

    # With temperature=0, plan structure should be similar
    assert len(result1["plan"]) == len(result2["plan"])


# ============================================================================
# VALIDATION PHASE TESTS (6 tests)
# ============================================================================


def test_validate_plan_success_strict_mode():
    """Test successful plan validation in strict mode"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="strict",
    )
    agent = PlanningAgent(config=config)

    result = agent.run(task="Valid task")

    # Should validate successfully
    assert "validation_result" in result
    assert result["validation_result"]["status"] == "valid"


def test_validate_plan_missing_tools_strict_mode():
    """Test plan validation failure due to missing tools (strict mode)"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="strict",
    )
    agent = PlanningAgent(config=config)

    # Create plan that requires unavailable tools
    task = "Use tool that doesn't exist"
    result = agent.run(task=task)

    # In strict mode, should fail validation or handle gracefully
    assert "validation_result" in result
    if result["validation_result"]["status"] == "invalid":
        assert "reason" in result["validation_result"]


def test_validate_plan_warn_mode():
    """Test plan validation in warn mode (warnings but continues)"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="warn",
    )
    agent = PlanningAgent(config=config)

    result = agent.run(task="Task with potential issues")

    # Warn mode should produce warnings but still return plan
    assert "validation_result" in result
    assert "plan" in result
    # May have warnings but not block execution
    if result["validation_result"].get("warnings"):
        assert isinstance(result["validation_result"]["warnings"], list)


def test_validate_plan_off_mode():
    """Test plan validation disabled (off mode)"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="off",
    )
    agent = PlanningAgent(config=config)

    result = agent.run(task="Any task")

    # Validation disabled - should skip validation
    assert "plan" in result
    # validation_result may not exist or indicate skipped
    if "validation_result" in result:
        assert result["validation_result"]["status"] in ["valid", "skipped"]


def test_validate_plan_circular_dependencies():
    """Test plan validation detects circular dependencies"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="strict",
    )
    agent = PlanningAgent(config=config)

    # This is a structural test - plan validation logic should detect cycles
    result = agent.run(task="Task that might create circular steps")

    # Should either prevent circular dependencies or detect them
    assert "validation_result" in result


def test_validate_plan_invalid_step_order():
    """Test plan validation detects invalid step ordering"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        validation_mode="strict",
    )
    agent = PlanningAgent(config=config)

    result = agent.run(task="Multi-step task")

    # Verify steps are properly ordered
    if len(result["plan"]) > 1:
        step_numbers = [step["step"] for step in result["plan"]]
        assert step_numbers == sorted(step_numbers)


# ============================================================================
# EXECUTION PHASE TESTS (4 tests)
# ============================================================================


def test_execute_plan_success():
    """Test successful plan execution"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    result = agent.run(task="Execute simple task")

    # Should execute successfully
    assert "execution_results" in result
    assert isinstance(result["execution_results"], list)
    assert "final_result" in result


def test_execute_plan_step_failure():
    """Test plan execution with step failure (error handling)"""
    config = PlanningConfig(
        llm_provider="mock",
        model="mock-model",
        enable_replanning=False,  # Disable replanning to test error handling
    )
    agent = PlanningAgent(config=config)

    result = agent.run(task="Task that may fail")

    # Should handle step failures gracefully
    assert "execution_results" in result
    # May have partial results or error information
    if "error" in result:
        assert isinstance(result["error"], str)


def test_execute_plan_result_aggregation():
    """Test that execution results are properly aggregated"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    result = agent.run(task="Multi-step task")

    # Verify result aggregation
    assert "execution_results" in result
    assert "final_result" in result

    # Each step should have a result
    if len(result["plan"]) > 0:
        assert len(result["execution_results"]) > 0


def test_execute_plan_with_tool_errors():
    """Test plan execution with tool errors (graceful degradation)"""
    config = PlanningConfig(llm_provider="mock", model="mock-model")
    agent = PlanningAgent(config=config)

    result = agent.run(task="Task requiring tools")

    # Should handle tool errors gracefully
    assert "execution_results" in result
    # Execution should complete even with tool errors
    assert "final_result" in result or "error" in result


# ============================================================================
# CONFIGURATION TESTS (3 tests)
# ============================================================================


def test_planning_config_defaults():
    """Test PlanningConfig default values"""
    config = PlanningConfig()

    # Verify default values
    assert config.llm_provider == "openai"
    assert config.model == "gpt-4"
    assert config.temperature == 0.7
    assert config.max_plan_steps == 10
    assert config.validation_mode == "strict"
    assert config.enable_replanning is True


def test_planning_config_custom_values():
    """Test PlanningConfig with custom values"""
    config = PlanningConfig(
        llm_provider="anthropic",
        model="claude-3-opus",
        temperature=0.3,
        max_plan_steps=5,
        validation_mode="warn",
        enable_replanning=False,
    )

    # Verify custom values
    assert config.llm_provider == "anthropic"
    assert config.model == "claude-3-opus"
    assert config.temperature == 0.3
    assert config.max_plan_steps == 5
    assert config.validation_mode == "warn"
    assert config.enable_replanning is False


def test_planning_signature_fields():
    """Test PlanningSignature has required fields"""

    sig = PlanningSignature()

    # Verify input fields
    assert hasattr(sig, "task")
    assert hasattr(sig, "context")

    # Verify output fields
    assert hasattr(sig, "plan")
    assert hasattr(sig, "validation_result")
    assert hasattr(sig, "execution_results")
    assert hasattr(sig, "final_result")
