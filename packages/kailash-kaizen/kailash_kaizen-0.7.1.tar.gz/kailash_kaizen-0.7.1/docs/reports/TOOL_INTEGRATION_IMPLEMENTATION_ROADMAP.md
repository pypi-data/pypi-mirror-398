# Tool Integration Implementation Roadmap

**Date**: 2025-10-20
**Based On**: TOOL_INTEGRATION_REQUIREMENTS_ANALYSIS.md
**Status**: Ready for Implementation

---

## Quick Reference

### What We're Building
Integration of production-ready Tool Calling System (12 builtin tools, 128 passing tests) with BaseAgent to enable autonomous tool execution with approval workflows.

### Timeline
**4-6 days** (32-48 hours)

### Risk Level
**MEDIUM** - Well-tested components exist. Integration risks around API design and async handling.

---

## Implementation Sequence

### Phase 1: Foundation (Days 1-2, 16h)
**Goal**: BaseAgent can execute tools with approval workflows

**Tasks**:
1. Add tool imports to base_agent.py:36-44
2. Add `tool_registry` and `tool_executor` params to `__init__` (line 133-145)
3. Initialize tool system in `__init__` (line 222-230)
4. Implement `execute_tool()` method (after line 1590)
5. Implement `discover_tools()` method
6. Add tool cleanup to `cleanup()` (line 1941)

**Files Modified**:
- `src/kaizen/core/base_agent.py` (6 specific locations)
- `src/kaizen/core/__init__.py` (exports)

**Validation**:
```bash
# Existing tests should still pass
pytest tests/unit/core/test_base_agent.py  # 454 tests

# Quick manual test
python -c "
from kaizen.core.base_agent import BaseAgent
# Tools auto-configured via MCP



# 12 builtin tools enabled via MCP

agent = BaseAgent(config=config, tools="all"  # Enable 12 builtin tools via MCP
print(f'Agent has {len(agent.discover_tools())} tools')
"
```

---

### Phase 2: Advanced Features (Day 3, 8h)
**Goal**: Multi-tool chains and helper methods

**Tasks**:
1. Implement `execute_tool_chain()` method
2. Implement `get_tool_categories()` helper
3. Implement `get_dangerous_tools()` helper
4. Add comprehensive error handling
5. Complete docstrings with examples

**Files Modified**:
- `src/kaizen/core/base_agent.py` (3 new methods)

**Validation**:
```python
# Test tool chain
executions = [
    {"tool_name": "read_file", "params": {"path": "test.txt"}},
    {"tool_name": "bash_command", "params": {"command": "wc -l test.txt"}},
]
results = await agent.execute_tool_chain(executions)
assert all(r.success for r in results)
```

---

### Phase 3: Testing (Day 4, 12h)
**Goal**: 35+ tests (Tier 1 + Tier 2) with 100% coverage

**Test Files Created**:
1. `tests/unit/core/test_base_agent_tools.py` (Tier 1, 30 tests)
2. `tests/integration/core/test_base_agent_tools_integration.py` (Tier 2, 15 tests)

**Test Categories**:
- Tool discovery: 5 tests
- Tool execution: 8 tests
- Tool chaining: 4 tests
- Control protocol integration: 6 tests
- Edge cases: 7 tests
- Performance: 2 tests
- Real integration: 3 tests

**Validation**:
```bash
# Run all new tests
pytest tests/unit/core/test_base_agent_tools.py -v
pytest tests/integration/core/test_base_agent_tools_integration.py -v

# Verify no regressions
pytest tests/unit/core/test_base_agent.py -v  # All 454 should pass

# Total test count should be 627+
pytest tests/ -k "base_agent or tool" --collect-only | grep "test_" | wc -l
```

---

### Phase 4: Documentation (Days 5-6, 8-12h)
**Goal**: Complete documentation and examples

**Documents Created**:
1. `docs/architecture/adr/012-tool-calling-integration.md` (ADR)
2. `examples/6-tool-integration/01-basic-tool-agent.py`
3. `examples/6-tool-integration/02-tool-chain-workflow.py`
4. `examples/6-tool-integration/03-custom-tools.py`
5. `docs/reference/base-agent-api.md` (update)
6. `docs/troubleshooting/tool-integration.md` (new)

**Validation**:
```bash
# Run all examples
python examples/6-tool-integration/01-basic-tool-agent.py
python examples/6-tool-integration/02-tool-chain-workflow.py
python examples/6-tool-integration/03-custom-tools.py

# Verify documentation builds
mkdocs build  # Should build without errors
```

---

## Critical Implementation Points

### Point 1: Async Everywhere (Line 1590+)
All tool methods MUST be async. No sync convenience methods.

```python
# CORRECT
async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
    if self.tool_executor is None:
        raise RuntimeError("Tool executor not configured")
    return await self.tool_executor.execute(tool_name, params)

# WRONG - No sync version
def execute_tool_sync(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
    # Don't create this!
```

---

### Point 2: Control Protocol Integration (Line 222-230)
ToolExecutor MUST use existing control_protocol for approvals.

```python
# In __init__
if tool_registry is not None:
    self.tool_registry = tool_registry
    self.tool_executor = tool_executor or ToolExecutor(
        registry=tool_registry,
        control_protocol=control_protocol,  # CRITICAL: Reuse existing protocol
        auto_approve_safe=True,
        timeout=30.0
    )
```

---

### Point 3: Backward Compatibility (Line 133-145)
Existing agents MUST work unchanged. Tools are opt-in.

```python
# Old agents still work
agent = BaseAgent(config=config, signature=signature)
# tools="all"  # Enable tools via MCP

# New tool-enabled agents
agent = BaseAgent(config=config, signature=signature, tools="all"  # Enable 12 builtin tools via MCP
# tool methods now available
```

---

### Point 4: Cleanup (Line 1941)
Clear references, don't clear shared registry.

```python
def cleanup(self):
    # ... existing cleanup ...

    # Clear tool executor references
    if hasattr(self, "tool_executor") and self.tool_executor is not None:
        self.tool_executor = None

    if hasattr(self, "tool_registry") and self.tool_registry is not None:
        # Don't clear the registry itself (other agents may use it)
        # Just clear our reference
        self.tool_registry = None
```

---

## Testing Strategy

### Tier 1 Tests (Unit, Mocked)
**Location**: `tests/unit/core/test_base_agent_tools.py`
**Count**: 30 tests
**Runtime**: <2 seconds

**Key Tests**:
- Tool discovery with empty registry
- Tool discovery by category
- Tool execution success/failure
- Approval workflow (mocked)
- Tool chain execution
- Error handling (tool not found, invalid params)

---

### Tier 2 Tests (Integration, Real)
**Location**: `tests/integration/core/test_base_agent_tools_integration.py`
**Count**: 15 tests
**Runtime**: ~10 seconds

**Key Tests**:
- Real tool execution with ToolExecutor
- Real approval workflows with ControlProtocol
- Performance benchmarks
- Memory leak detection
- Concurrent tool execution

---

## Risk Mitigation

### Risk: Async/Sync Boundary Issues
**Mitigation**: All tool methods explicitly async, clear error messages
**Test**: `test_execute_tool_without_await_raises_error`

### Risk: Control Protocol Integration Breaks
**Mitigation**: Tier 2 tests with real ControlProtocol
**Test**: `test_tool_approval_workflow_end_to_end`

### Risk: Memory Leaks
**Mitigation**: Cleanup tests with memory profiling
**Test**: `test_tool_executor_cleanup_no_leaks`

### Risk: Tool Registry Conflicts
**Mitigation**: Document thread-safety, test concurrent access
**Test**: `test_concurrent_tool_execution_from_multiple_agents`

---

## Success Criteria

### Code Quality
- [ ] All existing tests pass (454 tests)
- [ ] 35+ new tests pass (Tier 1 + Tier 2)
- [ ] 100% code coverage for new methods
- [ ] No pylint/flake8 errors

### Documentation
- [ ] ADR-012 complete
- [ ] 3+ working examples
- [ ] API reference updated
- [ ] Troubleshooting guide created

### User Experience
- [ ] Tool integration in <5 lines
- [ ] Clear error messages
- [ ] Async requirements documented
- [ ] Common patterns demonstrated

### Performance
- [ ] Tool discovery <10ms (typical registry)
- [ ] Tool execution overhead <5ms
- [ ] Memory overhead <50MB per agent

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Add imports (line 36-44)
- [ ] Modify `__init__` signature (line 133-145)
- [ ] Initialize tool system (line 222-230)
- [ ] Implement `execute_tool()` (after line 1590)
- [ ] Implement `discover_tools()`
- [ ] Add cleanup (line 1941)
- [ ] Update exports
- [ ] Verify existing tests pass

### Phase 2: Advanced Features
- [ ] Implement `execute_tool_chain()`
- [ ] Implement `get_tool_categories()`
- [ ] Implement `get_dangerous_tools()`
- [ ] Add error handling
- [ ] Complete docstrings

### Phase 3: Testing
- [ ] Create Tier 1 test file (30 tests)
- [ ] Create Tier 2 test file (15 tests)
- [ ] Verify 100% coverage
- [ ] Run performance benchmarks
- [ ] Test all error paths

### Phase 4: Documentation
- [ ] Write ADR-012
- [ ] Create 3 examples
- [ ] Update API reference
- [ ] Write troubleshooting guide
- [ ] Verify examples run

---

## Quick Start (After Implementation)

```python
from kaizen.core.base_agent import BaseAgent
# Tools auto-configured via MCP


# Setup

# 12 builtin tools enabled via MCP

agent = BaseAgent(
    config=config,
    signature=signature,
    tools="all"  # Enable 12 builtin tools via MCP
)

# Discover tools
safe_tools = agent.discover_tools(safe_only=True)
print(f"Safe tools: {[t.name for t in safe_tools]}")

# Execute a tool
result = await agent.execute_tool(
    "read_file",
    {"path": "data.txt"}
)

if result.success:
    print(result.result)
else:
    print(f"Error: {result.error}")

# Chain tools
results = await agent.execute_tool_chain([
    {"tool_name": "read_file", "params": {"path": "input.txt"}},
    {"tool_name": "bash_command", "params": {"command": "wc -l input.txt"}},
])
```

---

## Developer Notes

### Import Order
```python
# Standard library
import logging
from typing import Any, Dict, List, Optional

# Core SDK imports
from kailash.nodes.base import Node, NodeParameter
from kailash.workflow.builder import WorkflowBuilder

# Kaizen framework imports
from kaizen.signatures import InputField, OutputField, Signature
from kaizen.tools.registry import ToolRegistry  # NEW
from kaizen.tools.executor import ToolExecutor  # NEW
from kaizen.tools.types import (  # NEW
    ToolDefinition,
    ToolResult,
    ToolCategory,
    DangerLevel,
)
```

### Error Message Templates
```python
# Tool not configured
raise RuntimeError(
    "Tool registry not configured. "
    "Pass tool_registry parameter to BaseAgent.__init__()"
)

# Tool not found
available_tools = self.tool_registry.get_tool_names()
raise ValueError(
    f"Tool '{tool_name}' not found in registry. "
    f"Available tools: {available_tools}"
)

# Invalid parameters
raise ValueError(
    f"Invalid parameters for tool '{tool_name}': {error}. "
    f"Expected parameters: {tool.parameters}"
)
```

---

## Post-Implementation Validation

```bash
# 1. All tests pass
pytest tests/ -v --cov=src/kaizen/core/base_agent.py --cov-report=term-missing

# 2. No regressions
pytest tests/unit/core/test_base_agent.py -v  # All 454 pass

# 3. New tests pass
pytest tests/unit/core/test_base_agent_tools.py -v  # 30 pass
pytest tests/integration/core/test_base_agent_tools_integration.py -v  # 15 pass

# 4. Examples run
python examples/6-tool-integration/01-basic-tool-agent.py
python examples/6-tool-integration/02-tool-chain-workflow.py
python examples/6-tool-integration/03-custom-tools.py

# 5. Documentation builds
mkdocs build

# 6. Performance benchmarks
pytest tests/integration/core/test_base_agent_tools_integration.py::test_tool_discovery_performance -v
pytest tests/integration/core/test_base_agent_tools_integration.py::test_tool_execution_overhead -v
```

---

**Ready to Start**: Phase 1 implementation
**Next Step**: Create ADR-012 or start coding Phase 1
**Questions**: See "Open Questions" in requirements analysis document
