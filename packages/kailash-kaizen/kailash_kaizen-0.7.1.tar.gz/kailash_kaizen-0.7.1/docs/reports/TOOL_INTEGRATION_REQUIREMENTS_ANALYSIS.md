# Tool Calling System Integration with BaseAgent - Requirements Analysis

**Date**: 2025-10-20
**Status**: Requirements Analysis Complete
**Author**: Claude Code (Requirements Analysis Specialist)
**Version**: 1.0

---

## Executive Summary

### Feature
Integration of production-ready Tool Calling System with BaseAgent to enable autonomous tool execution capabilities.

### Complexity
**HIGH** - Multi-component integration with async/sync compatibility, approval workflow coordination, and test strategy design.

### Risk Level
**MEDIUM** - Well-tested components exist independently. Integration risks primarily around API design and async/sync boundary handling.

### Estimated Effort
**4-6 days** (32-48 hours)
- Day 1-2: BaseAgent API design and implementation (16h)
- Day 3: Integration patterns and helper methods (8h)
- Day 4: Testing infrastructure (Tier 1 + Tier 2) (12h)
- Day 5-6: Documentation, examples, validation (8-12h)

---

## 1. Functional Requirements

### REQ-001: Tool Discovery from BaseAgent
**Priority**: CRITICAL
**Description**: BaseAgent instances must be able to discover available tools from ToolRegistry.

| Aspect | Details |
|--------|---------|
| Input | `registry: Optional[ToolRegistry]` in `__init__` |
| Output | List of available tools via `get_available_tools()` method |
| Business Logic | If registry provided, expose tools; if None, no tools available |
| Edge Cases | - Empty registry<br>- Registry with dangerous tools<br>- Registry passed after init |
| SDK Mapping | `ToolRegistry.list_all()`, `ToolRegistry.list_by_category()` |

**Implementation Location**: `src/kaizen/core/base_agent.py:133-145` (`__init__` method)

**Specific Code Change**:
```python
# Line 133-145: Add to __init__ parameters
def __init__(
    self,
    config: Any,
    signature: Optional[Signature] = None,
    strategy: Optional[Any] = None,
    memory: Optional[Any] = None,
    shared_memory: Optional[Any] = None,
    agent_id: Optional[str] = None,
    control_protocol: Optional[Any] = None,
    tool_registry: Optional[ToolRegistry] = None,  # NEW
    tool_executor: Optional[ToolExecutor] = None,  # NEW
    **kwargs,
):
```

---

### REQ-002: Tool Execution from BaseAgent
**Priority**: CRITICAL
**Description**: BaseAgent instances must execute tools with approval workflows.

| Aspect | Details |
|--------|---------|
| Input | `tool_name: str`, `params: Dict[str, Any]`, `timeout: Optional[float]` |
| Output | `ToolResult` with execution status |
| Business Logic | 1. Validate tool exists<br>2. Request approval (if needed)<br>3. Execute tool<br>4. Return standardized result |
| Edge Cases | - Tool not found<br>- Approval denied<br>- Tool execution failure<br>- Timeout during execution |
| SDK Mapping | `ToolExecutor.execute()` |

**Implementation Location**: New method in `src/kaizen/core/base_agent.py` (after line 1590)

**Method Signature**:
```python
async def execute_tool(
    self,
    tool_name: str,
    params: Dict[str, Any],
    timeout: Optional[float] = None,
) -> ToolResult:
    """
    Execute a tool with approval workflow.

    Uses ToolExecutor to execute registered tools with automatic
    approval requests based on danger level.

    Args:
        tool_name: Name of tool to execute
        params: Parameters to pass to tool
        timeout: Optional approval timeout (uses default if None)

    Returns:
        ToolResult with execution status and result/error

    Raises:
        RuntimeError: If tool_registry not configured

    Example:
        >>> agent = BaseAgent(
        ...     config=config,
        ...     signature=signature,
        ...     tools="all"  # Enable 12 builtin tools via MCP
        ...     tool_executor=executor
        ... )
        >>> result = await agent.execute_tool(
        ...     "read_file",
        ...     {"path": "data.txt"}
        ... )
        >>> if result.success:
        ...     print(result.result)
    """
```

---

### REQ-003: Tool Selection Based on Task
**Priority**: HIGH
**Description**: BaseAgent should help select appropriate tools for specific tasks.

| Aspect | Details |
|--------|---------|
| Input | `task_description: str`, `category: Optional[ToolCategory]` |
| Output | List[ToolDefinition] ranked by relevance |
| Business Logic | 1. Search tools by keywords<br>2. Filter by category (if provided)<br>3. Filter by danger level (optional)<br>4. Return ranked list |
| Edge Cases | - No matching tools<br>- Multiple equally relevant tools<br>- Task requires tool chaining |
| SDK Mapping | `ToolRegistry.search()`, `ToolRegistry.list_by_category()` |

**Implementation Location**: New method in `src/kaizen/core/base_agent.py` (after `execute_tool`)

**Method Signature**:
```python
def discover_tools(
    self,
    query: Optional[str] = None,
    category: Optional[ToolCategory] = None,
    danger_level: Optional[DangerLevel] = None,
    safe_only: bool = False,
) -> List[ToolDefinition]:
    """
    Discover available tools by query, category, or danger level.

    Args:
        query: Optional search query for tool names/descriptions
        category: Optional category filter
        danger_level: Optional danger level filter
        safe_only: If True, only return SAFE tools (default: False)

    Returns:
        List of matching ToolDefinition objects

    Example:
        >>> # Find all file tools
        >>> tools = agent.discover_tools(category=ToolCategory.SYSTEM)
        >>>
        >>> # Search for specific functionality
        >>> tools = agent.discover_tools(query="file read")
        >>>
        >>> # Get only safe tools
        >>> safe_tools = agent.discover_tools(safe_only=True)
    """
```

---

### REQ-004: Tool Chaining for Multi-Step Operations
**Priority**: MEDIUM
**Description**: Execute multiple tools in sequence for complex operations.

| Aspect | Details |
|--------|---------|
| Input | `executions: List[Dict[str, Any]]` (list of tool calls) |
| Output | `List[ToolResult]` (one per execution) |
| Business Logic | Execute tools sequentially, optionally passing results between tools |
| Edge Cases | - Execution fails mid-chain<br>- Result transformation between tools<br>- Approval denial stops chain |
| SDK Mapping | `ToolExecutor.execute_batch()` |

**Implementation Location**: New method in `src/kaizen/core/base_agent.py` (after `execute_tool`)

**Method Signature**:
```python
async def execute_tool_chain(
    self,
    executions: List[Dict[str, Any]],
    stop_on_error: bool = True,
    timeout: Optional[float] = None,
) -> List[ToolResult]:
    """
    Execute multiple tools in sequence.

    Args:
        executions: List of dicts with "tool_name" and "params" keys
        stop_on_error: Stop execution if a tool fails (default: True)
        timeout: Optional approval timeout for each tool

    Returns:
        List of ToolResult objects (one per execution)

    Example:
        >>> executions = [
        ...     {"tool_name": "read_file", "params": {"path": "input.txt"}},
        ...     {"tool_name": "bash_command", "params": {"command": "wc -l input.txt"}},
        ... ]
        >>> results = await agent.execute_tool_chain(executions)
    """
```

---

### REQ-005: Integration with ControlProtocol
**Priority**: CRITICAL
**Description**: Tool approval requests must integrate with existing ControlProtocol.

| Aspect | Details |
|--------|---------|
| Input | `control_protocol: Optional[ControlProtocol]` (already exists in BaseAgent) |
| Output | Approval workflows route through ControlProtocol |
| Business Logic | If control_protocol exists, ToolExecutor uses it for approvals |
| Edge Cases | - No control_protocol (autonomous mode)<br>- Control protocol fails/times out<br>- User denies approval |
| SDK Mapping | `ToolExecutor.__init__(control_protocol=...)` |

**Implementation Location**: `src/kaizen/core/base_agent.py:222` (in `__init__`)

**Specific Code Change**:
```python
# Line 222-230: After setting control_protocol
self.control_protocol = control_protocol

# NEW: Create ToolExecutor with control protocol integration
if tool_registry is not None:
    self.tool_registry = tool_registry
    self.tool_executor = tool_executor or ToolExecutor(
        registry=tool_registry,
        control_protocol=control_protocol,
        auto_approve_safe=True,
        timeout=30.0
    )
else:
    self.tool_registry = None
    self.tool_executor = None
```

---

## 2. Non-Functional Requirements

### Performance Requirements
- **Tool Discovery Latency**: <10ms for registry queries (cached category/danger level lookups)
- **Tool Execution Overhead**: <5ms for approval workflow logic (excluding tool execution time)
- **Memory per Agent**: <50MB additional memory for tool registry reference and executor state

### Security Requirements
- **Approval Enforcement**: Dangerous tools (HIGH/CRITICAL) MUST require approval when control_protocol available
- **Parameter Validation**: All tool parameters MUST be validated before execution
- **Audit Trail**: Tool executions MUST be logged with timestamps, parameters, and results
- **Fail-Safe**: If approval request fails, default to DENY (no silent auto-approve)

### Scalability Requirements
- **Concurrent Execution**: ToolExecutor must support concurrent tool calls from multiple agents
- **Registry Sharing**: Single ToolRegistry instance can be shared across multiple agents
- **Async-First**: All tool execution methods must be async for non-blocking operation

---

## 3. User Journey Mapping

### Developer Journey: Basic Tool Integration

**Steps**:
1. Create BaseAgent with tool support
   ```python
   from kaizen.core.base_agent import BaseAgent
   # Tools auto-configured via MCP, ToolExecutor



   # 12 builtin tools enabled via MCP

   agent = BaseAgent(
       config=config,
       signature=signature,
       tools="all"  # Enable 12 builtin tools via MCP
   )
   ```

2. Discover available tools
   ```python
   safe_tools = agent.discover_tools(safe_only=True)
   print(f"Safe tools: {[t.name for t in safe_tools]}")
   ```

3. Execute a tool
   ```python
   result = await agent.execute_tool(
       "read_file",
       {"path": "data.txt"}
   )

   if result.success:
       print(result.result)
   ```

4. Handle approval workflows
   ```python
   from kaizen.core.autonomy.control.protocol import ControlProtocol

   agent = BaseAgent(
       config=config,
       signature=signature,
       tools="all"  # Enable 12 builtin tools via MCP
       control_protocol=protocol  # Approvals route here
   )

   # Dangerous tool requires approval
   result = await agent.execute_tool(
       "bash_command",
       {"command": "rm temp.txt"}
   )

   if not result.approved:
       print("User denied approval")
   ```

**Success Criteria**:
- Tool integration in <5 lines of code
- Clear error messages for common mistakes
- Approval workflow transparent to developer
- Results consistently structured

**Failure Points**:
- Forgetting to register tools → Clear error: "Tool registry not configured"
- Using sync context for async tools → Runtime error with guidance
- Invalid tool parameters → Validation error with parameter requirements

---

### Developer Journey: Advanced Tool Usage

**Steps**:
1. Create custom tools
   ```python
   from kaizen.tools.types import ToolDefinition, ToolParameter, ToolCategory, DangerLevel

   def my_tool_impl(text: str) -> dict:
       return {"result": text.upper()}

   registry.register(
       name="uppercase",
       description="Convert text to uppercase",
       category=ToolCategory.DATA,
       danger_level=DangerLevel.SAFE,
       parameters=[ToolParameter("text", str, "Input text")],
       returns={"result": "str"},
       executor=my_tool_impl
   )
   ```

2. Chain multiple tools
   ```python
   results = await agent.execute_tool_chain([
       {"tool_name": "read_file", "params": {"path": "input.txt"}},
       {"tool_name": "uppercase", "params": {"text": results[0].result["content"]}},
       {"tool_name": "write_file", "params": {"path": "output.txt", "content": ...}}
   ])
   ```

3. Integrate with agent strategies
   ```python
   class ToolEnabledAgent(BaseAgent):
       async def process(self, task: str):
           # Agent decides which tool to use
           tools = self.discover_tools(query=task)

           if tools:
               result = await self.execute_tool(tools[0].name, {...})
               return result.result
   ```

**Success Criteria**:
- Custom tools registered in <10 lines
- Tool chains execute sequentially with clear results
- Agent strategies can leverage tools seamlessly

**Failure Points**:
- Tool executor not provided → Clear error with setup instructions
- Invalid tool chain (missing tool) → Detailed error with available tools
- Approval timeout → Configurable timeout with clear timeout message

---

## 4. Architecture Decision

See **ADR-012** (to be created) for complete architectural decision record.

### Decision Summary

**Approach**: Extend BaseAgent with optional tool capabilities via dependency injection.

**Key Components**:
1. **Optional Dependencies**: `tool_registry` and `tool_executor` parameters in `__init__`
2. **Backward Compatibility**: Existing agents work unchanged (tools are opt-in)
3. **Control Protocol Integration**: Reuse existing `control_protocol` for approvals
4. **Async-First API**: All tool methods are async for non-blocking execution

**Integration Points**:
- `BaseAgent.__init__`: Accept `tool_registry` and `tool_executor` parameters
- `BaseAgent.execute_tool()`: Main tool execution method
- `BaseAgent.discover_tools()`: Tool discovery helper
- `BaseAgent.execute_tool_chain()`: Multi-tool execution
- `BaseAgent.cleanup()`: Clean up tool executor resources

**Design Principles**:
1. **Opt-In**: Tools are optional, not required for all agents
2. **Composable**: Tool system integrates with existing BaseAgent features
3. **Type-Safe**: Leverage existing ToolDefinition and ToolResult types
4. **Testable**: Clear separation enables unit and integration testing

---

## 5. Consequences

### Positive
- **Autonomous Capabilities**: Agents can execute bash, file, API, web operations autonomously
- **Safe by Default**: Approval workflows prevent dangerous operations without oversight
- **Developer UX**: Simple API for common use cases, powerful for advanced scenarios
- **Reusable Infrastructure**: Tool system works across all BaseAgent subclasses
- **Production Ready**: Built on 128 passing tests (Tier 1 + Tier 2)

### Negative
- **Additional Complexity**: Agents now have tool execution capabilities (more to learn)
- **Async Requirement**: Tool methods must be awaited (no sync convenience methods)
- **Memory Overhead**: Each agent holds reference to registry and executor
- **Breaking Change Risk**: If not carefully designed, could break existing agents

---

## 6. Alternatives Considered

### Option 1: Mixin-Based Approach
**Description**: Create `ToolExecutionMixin` that agents inherit from.

**Pros**:
- Clear separation of tool functionality
- Easy to add/remove tool capabilities
- Follows existing mixin pattern in BaseAgent

**Cons**:
- Multiple inheritance complexity
- Harder to compose with other mixins
- Runtime mixin application doesn't work well

**Why Rejected**: Dependency injection is simpler and more flexible than mixin composition.

---

### Option 2: Separate ToolAgent Class
**Description**: Create dedicated `ToolAgent` class that inherits from BaseAgent.

**Pros**:
- Complete separation of concerns
- No changes to BaseAgent
- Clear specialization

**Cons**:
- Code duplication across agent types
- Harder to add tools to existing agents
- Violates DRY principle

**Why Rejected**: Goes against BaseAgent's goal of being universal foundation. Tools should be composable capability, not separate agent type.

---

### Option 3: Strategy-Based Tool Selection
**Description**: Let strategies handle tool selection and execution.

**Pros**:
- Aligns with existing strategy pattern
- Strategies can implement custom tool selection logic
- More flexible for complex workflows

**Cons**:
- Every strategy needs tool awareness
- Complicates strategy implementation
- Not all strategies need tools

**Why Rejected**: Tools are agent capability, not strategy responsibility. Strategies should focus on execution patterns, not tool selection.

---

## 7. Implementation Plan

### Phase 1: Foundation (Day 1-2, 16 hours)

**Tasks**:
1. Add `tool_registry` and `tool_executor` parameters to `BaseAgent.__init__`
2. Implement `execute_tool()` method with ControlProtocol integration
3. Implement `discover_tools()` method for tool discovery
4. Add tool cleanup to `cleanup()` method
5. Update `__all__` exports

**Files Modified**:
- `src/kaizen/core/base_agent.py`: Lines 133-145 (init), new methods after line 1590
- `src/kaizen/core/__init__.py`: Update exports

**Success Criteria**:
- [ ] BaseAgent accepts tool_registry parameter
- [ ] execute_tool() method implemented and functional
- [ ] discover_tools() method implemented
- [ ] Tool executor integrates with control_protocol
- [ ] All existing tests still pass (no regressions)

---

### Phase 2: Advanced Features (Day 3, 8 hours)

**Tasks**:
1. Implement `execute_tool_chain()` for multi-tool execution
2. Add helper method `get_tool_categories()` for category discovery
3. Add helper method `get_dangerous_tools()` for safety awareness
4. Document tool integration patterns

**Files Modified**:
- `src/kaizen/core/base_agent.py`: New methods after execute_tool()

**Success Criteria**:
- [ ] Tool chain execution works sequentially
- [ ] Helper methods provide useful tool filtering
- [ ] Error handling covers all failure modes
- [ ] Docstrings complete with examples

---

### Phase 3: Testing Infrastructure (Day 4, 12 hours)

**Tasks**:
1. Create Tier 1 tests for tool integration (unit tests, mocked)
2. Create Tier 2 tests for real tool execution (integration tests, real ToolExecutor)
3. Test approval workflows with mock ControlProtocol
4. Test error cases (tool not found, approval denied, execution failure)
5. Test async/sync boundary handling

**Files Created**:
- `tests/unit/core/test_base_agent_tools.py` (Tier 1, 20+ tests)
- `tests/integration/core/test_base_agent_tools_integration.py` (Tier 2, 15+ tests)

**Test Categories**:
1. **Tool Discovery**: 5 tests (empty registry, category filtering, search)
2. **Tool Execution**: 8 tests (success, failure, approval, timeout)
3. **Tool Chaining**: 4 tests (sequential, stop on error, pass results)
4. **Control Protocol Integration**: 6 tests (approval granted/denied, timeout, no protocol)
5. **Edge Cases**: 7 tests (tool not found, invalid params, executor not set)

**Success Criteria**:
- [ ] 35+ tests passing (Tier 1 + Tier 2)
- [ ] 100% code coverage for new methods
- [ ] All error paths tested
- [ ] Real ToolExecutor validated in Tier 2

---

### Phase 4: Documentation & Examples (Day 5-6, 8-12 hours)

**Tasks**:
1. Create ADR-012 (Tool Calling System Integration)
2. Update BaseAgent docstrings with tool examples
3. Create example: `examples/tool-enabled-agent.py`
4. Create example: `examples/tool-chain-workflow.py`
5. Update `docs/reference/base-agent-api.md` with tool methods
6. Create troubleshooting guide for tool integration

**Files Created/Modified**:
- `docs/architecture/adr/012-tool-calling-integration.md`
- `examples/6-tool-integration/01-basic-tool-agent.py`
- `examples/6-tool-integration/02-tool-chain-workflow.py`
- `examples/6-tool-integration/03-custom-tools.py`
- `docs/reference/base-agent-api.md`: Add tool methods section
- `docs/troubleshooting/tool-integration.md`: New guide

**Success Criteria**:
- [ ] ADR documents decision rationale
- [ ] 3+ working examples demonstrating tool usage
- [ ] API reference complete for all tool methods
- [ ] Troubleshooting guide covers common issues

---

## 8. Risk Assessment

### High Probability, High Impact (CRITICAL)

#### Risk 1: Async/Sync Boundary Issues
**Description**: Tool methods are async, but some agents may call them from sync contexts.

**Mitigation**:
1. All tool methods explicitly async (force developers to use await)
2. Clear error messages when called without await
3. Documentation emphasizes async requirement
4. Test async/sync boundary explicitly

**Prevention**:
- Enforce async everywhere in API design
- No sync convenience methods (avoids confusion)

**Impact if Not Mitigated**: Runtime errors, confusing stack traces, frustrated developers.

---

#### Risk 2: Control Protocol Integration Breaks
**Description**: ToolExecutor approval requests might not integrate correctly with existing ControlProtocol.

**Mitigation**:
1. Test with real ControlProtocol in Tier 2 tests
2. Validate approval flow end-to-end
3. Handle timeout/failure cases explicitly

**Prevention**:
- Integration tests with real ControlProtocol
- Test approval granted, denied, timeout scenarios

**Impact if Not Mitigated**: Approval workflows fail silently, dangerous tools execute without oversight.

---

### Medium Probability, High Impact (MONITOR)

#### Risk 3: Tool Registry Sharing Conflicts
**Description**: Multiple agents sharing single ToolRegistry might cause conflicts.

**Mitigation**:
1. Document that ToolRegistry is thread-safe for reads
2. Warn against modifying registry after agent creation
3. Test concurrent tool execution from multiple agents

**Prevention**:
- Clear documentation on registry lifecycle
- Tests for concurrent access

**Impact if Not Mitigated**: Race conditions, tool registration conflicts, unpredictable behavior.

---

#### Risk 4: Memory Leaks from Tool Executor
**Description**: ToolExecutor might hold references preventing agent cleanup.

**Mitigation**:
1. Add tool executor cleanup to `BaseAgent.cleanup()`
2. Test cleanup with memory profiling
3. Ensure weak references where appropriate

**Prevention**:
- Cleanup tests in Tier 1
- Memory profiling in Tier 2

**Impact if Not Mitigated**: Memory leaks in long-running applications, resource exhaustion.

---

### Low Probability, Medium Impact (ACCEPT)

#### Risk 5: Tool Discovery Performance Degradation
**Description**: Large tool registries (100+ tools) might slow down discovery.

**Mitigation**:
1. Benchmark discovery performance
2. Optimize search if needed (caching, indexing)
3. Document performance characteristics

**Prevention**:
- Performance tests in Tier 2
- Caching for expensive operations

**Impact if Not Mitigated**: Slow tool discovery, degraded user experience with large registries.

---

## 9. Integration with Existing SDK

### Reusable Components (Can Reuse Directly)

#### ToolRegistry (src/kaizen/tools/registry.py)
- **Status**: Production-ready, 128 tests passing
- **Usage**: Create instance and pass to BaseAgent
- **Integration**: `BaseAgent.__init__(tools="all"  # Enable 12 builtin tools via MCP

#### ToolExecutor (src/kaizen/tools/executor.py)
- **Status**: Production-ready, approval workflows tested
- **Usage**: Automatically created by BaseAgent if registry provided
- **Integration**: `ToolExecutor(registry, control_protocol, ...)`

#### ControlProtocol (src/kaizen/core/autonomy/control/protocol.py)
- **Status**: Production-ready (ADR-011)
- **Usage**: Already in BaseAgent, reuse for tool approvals
- **Integration**: Pass to ToolExecutor for approval workflows

---

### Components Need Modification

#### BaseAgent.__init__ (src/kaizen/core/base_agent.py:133-145)
**Modification**: Add `tool_registry` and `tool_executor` parameters

**Before**:
```python
def __init__(
    self,
    config: Any,
    signature: Optional[Signature] = None,
    strategy: Optional[Any] = None,
    memory: Optional[Any] = None,
    shared_memory: Optional[Any] = None,
    agent_id: Optional[str] = None,
    control_protocol: Optional[Any] = None,
    **kwargs,
):
```

**After**:
```python
def __init__(
    self,
    config: Any,
    signature: Optional[Signature] = None,
    strategy: Optional[Any] = None,
    memory: Optional[Any] = None,
    shared_memory: Optional[Any] = None,
    agent_id: Optional[str] = None,
    control_protocol: Optional[Any] = None,
    tool_registry: Optional[ToolRegistry] = None,  # NEW
    tool_executor: Optional[ToolExecutor] = None,  # NEW
    **kwargs,
):
```

---

#### BaseAgent.cleanup() (src/kaizen/core/base_agent.py:1899-1949)
**Modification**: Add tool executor cleanup

**Addition** (after line 1941):
```python
# Clear tool executor references
if hasattr(self, "tool_executor") and self.tool_executor is not None:
    self.tool_executor = None

if hasattr(self, "tool_registry") and self.tool_registry is not None:
    # Don't clear the registry itself (other agents may use it)
    # Just clear our reference
    self.tool_registry = None
```

---

### Components Must Build New

#### BaseAgent.execute_tool() (NEW)
- **Location**: After line 1590 in base_agent.py
- **Purpose**: Main tool execution method with approval workflow
- **Dependencies**: ToolExecutor, ControlProtocol
- **Estimated Size**: 40-50 lines with full error handling

#### BaseAgent.discover_tools() (NEW)
- **Location**: After execute_tool()
- **Purpose**: Tool discovery with filtering
- **Dependencies**: ToolRegistry
- **Estimated Size**: 30-40 lines

#### BaseAgent.execute_tool_chain() (NEW)
- **Location**: After discover_tools()
- **Purpose**: Multi-tool sequential execution
- **Dependencies**: ToolExecutor
- **Estimated Size**: 50-60 lines

---

## 10. Success Criteria

### Functional Criteria
- [ ] BaseAgent accepts `tool_registry` parameter without breaking existing agents
- [ ] `execute_tool()` successfully executes safe tools
- [ ] `execute_tool()` requests approval for dangerous tools
- [ ] `discover_tools()` filters tools by category, danger level, query
- [ ] `execute_tool_chain()` executes multiple tools sequentially
- [ ] Tool execution results consistently structured as ToolResult

### Quality Criteria
- [ ] 35+ tests passing (Tier 1 + Tier 2)
- [ ] 100% code coverage for new methods
- [ ] No regressions in existing BaseAgent tests (454 tests still passing)
- [ ] All public methods have docstrings with examples
- [ ] ADR-012 documents architectural decision

### User Experience Criteria
- [ ] Tool integration requires <5 lines of code
- [ ] Error messages clear and actionable
- [ ] 3+ working examples demonstrate tool usage
- [ ] Troubleshooting guide covers common issues

### Performance Criteria
- [ ] Tool discovery <10ms for typical registries (12-50 tools)
- [ ] Tool execution overhead <5ms (excluding actual tool time)
- [ ] Memory overhead <50MB per agent with tools

---

## 11. Open Questions

### Q1: Should tool execution be recorded in agent memory?
**Options**:
1. Automatically record all tool calls in memory (if memory enabled)
2. Require explicit `store_in_memory=True` parameter
3. No automatic recording, let developers handle it

**Recommendation**: Option 2 (explicit opt-in) for flexibility and memory control.

---

### Q2: How should tool results integrate with shared memory?
**Current**: Agents can write insights to shared memory manually.
**Question**: Should tool results automatically become insights?

**Recommendation**: No automatic insights. Let agents decide what's insight-worthy.

---

### Q3: Should tool discovery use LLM-based semantic matching?
**Current**: Keyword-based search in tool names and descriptions.
**Question**: Use LLM embeddings for semantic tool matching?

**Recommendation**: Start with keyword search (simple, fast). Add semantic search in Phase 2 if needed.

---

### Q4: How to handle tool execution in workflows?
**Current**: BaseAgent has `to_workflow()` for Core SDK integration.
**Question**: Should tool execution be exposed as workflow nodes?

**Recommendation**: Phase 1 focuses on imperative API. Workflow integration in Phase 2.

---

## 12. File-Specific Implementation Guide

### File 1: src/kaizen/core/base_agent.py

**Line 36-44: Add imports**
```python
# Existing imports...
from kailash.workflow.builder import WorkflowBuilder

# NEW: Tool system imports
from kaizen.tools.registry import ToolRegistry
from kaizen.tools.executor import ToolExecutor
from kaizen.tools.types import (
    ToolDefinition,
    ToolResult,
    ToolCategory,
    DangerLevel,
)
```

**Line 133-145: Modify __init__ signature**
```python
def __init__(
    self,
    config: Any,
    signature: Optional[Signature] = None,
    strategy: Optional[Any] = None,
    memory: Optional[Any] = None,
    shared_memory: Optional[Any] = None,
    agent_id: Optional[str] = None,
    control_protocol: Optional[Any] = None,
    tool_registry: Optional[ToolRegistry] = None,  # NEW
    tool_executor: Optional[ToolExecutor] = None,  # NEW
    **kwargs,
):
    """
    Initialize BaseAgent with lazy loading pattern.

    Args:
        # ... existing args ...
        tool_registry: Optional tool registry for tool execution
        tool_executor: Optional tool executor (auto-created if registry provided)
        **kwargs: Additional arguments passed to Node.__init__
    """
```

**Line 222-230: Initialize tool system**
```python
# Set control protocol (Week 10 addition)
self.control_protocol = control_protocol

# NEW: Initialize tool system (Tool Integration)
if tool_registry is not None:
    self.tool_registry = tool_registry
    self.tool_executor = tool_executor or ToolExecutor(
        registry=tool_registry,
        control_protocol=control_protocol,
        auto_approve_safe=True,
        timeout=30.0
    )
else:
    self.tool_registry = None
    self.tool_executor = None
```

**After line 1590: Add new methods**
```python
# =============================================================================
# TOOL CALLING INTEGRATION
# =============================================================================

async def execute_tool(
    self,
    tool_name: str,
    params: Dict[str, Any],
    timeout: Optional[float] = None,
) -> ToolResult:
    """Execute a tool with approval workflow."""
    # Implementation...

def discover_tools(
    self,
    query: Optional[str] = None,
    category: Optional[ToolCategory] = None,
    danger_level: Optional[DangerLevel] = None,
    safe_only: bool = False,
) -> List[ToolDefinition]:
    """Discover available tools."""
    # Implementation...

async def execute_tool_chain(
    self,
    executions: List[Dict[str, Any]],
    stop_on_error: bool = True,
    timeout: Optional[float] = None,
) -> List[ToolResult]:
    """Execute multiple tools in sequence."""
    # Implementation...

def get_tool_categories(self) -> List[ToolCategory]:
    """Get list of all tool categories with registered tools."""
    # Implementation...

def get_dangerous_tools(self) -> List[ToolDefinition]:
    """Get all dangerous tools (HIGH and CRITICAL danger levels)."""
    # Implementation...
```

**Line 1941: Add cleanup**
```python
# Clear tool executor references
if hasattr(self, "tool_executor") and self.tool_executor is not None:
    self.tool_executor = None

if hasattr(self, "tool_registry") and self.tool_registry is not None:
    # Don't clear the registry itself (other agents may use it)
    # Just clear our reference
    self.tool_registry = None
```

---

### File 2: tests/unit/core/test_base_agent_tools.py (NEW)

**Purpose**: Tier 1 unit tests for tool integration (mocked, fast)

**Test Categories**:
1. Tool discovery (5 tests)
2. Tool execution (8 tests)
3. Tool chaining (4 tests)
4. Control protocol integration (6 tests)
5. Edge cases (7 tests)

**Example Test**:
```python
@pytest.mark.asyncio
async def test_execute_tool_success(agent_with_tools):
    """Test successful tool execution."""
    result = await agent_with_tools.execute_tool(
        "read_file",
        {"path": "test.txt"}
    )

    assert result.success is True
    assert result.tool_name == "read_file"
    assert result.result is not None
```

---

### File 3: tests/integration/core/test_base_agent_tools_integration.py (NEW)

**Purpose**: Tier 2 integration tests with real ToolExecutor and ControlProtocol

**Test Categories**:
1. Real tool execution (5 tests)
2. Approval workflows (5 tests)
3. Error handling (3 tests)
4. Performance benchmarks (2 tests)

---

### File 4: docs/architecture/adr/012-tool-calling-integration.md (NEW)

**Sections**:
- Status: Accepted
- Context: Tool system exists, needs BaseAgent integration
- Decision: Dependency injection approach
- Consequences: Positive and negative impacts
- Alternatives Considered: Mixin, separate class, strategy-based

---

### File 5: examples/6-tool-integration/01-basic-tool-agent.py (NEW)

**Purpose**: Demonstrate basic tool integration

**Content**:
```python
"""
Basic Tool-Enabled Agent

Demonstrates how to create an agent with tool calling capabilities.
"""

from kaizen.core.base_agent import BaseAgent
# Tools auto-configured via MCP


# Create registry with builtin tools

# 12 builtin tools enabled via MCP

# Create agent with tools
agent = BaseAgent(
    config=config,
    signature=signature,
    tools="all"  # Enable 12 builtin tools via MCP
)

# Discover available tools
tools = agent.discover_tools(safe_only=True)
print(f"Safe tools: {[t.name for t in tools]}")

# Execute a tool
result = await agent.execute_tool(
    "read_file",
    {"path": "data.txt"}
)

if result.success:
    print(result.result)
```

---

## 13. Validation Checklist

### Pre-Implementation
- [ ] Requirements reviewed by team
- [ ] API design approved
- [ ] Test strategy defined
- [ ] Risk mitigation plans in place

### During Implementation
- [ ] Code follows Kaizen style guide
- [ ] All methods have docstrings with examples
- [ ] Error messages are clear and actionable
- [ ] Type hints complete for all public APIs

### Post-Implementation
- [ ] All tests passing (Tier 1 + Tier 2)
- [ ] No regressions in existing tests
- [ ] Documentation complete (ADR, API reference, examples)
- [ ] Code review complete
- [ ] Performance benchmarks meet targets

---

## 14. Next Steps

1. **Create ADR-012**: Document architectural decision for tool integration
2. **Start Phase 1**: Implement foundation (BaseAgent modifications)
3. **Parallel Task**: Create test fixtures and infrastructure
4. **Review Checkpoint**: After Phase 1, validate API design with examples
5. **Complete Phases 2-4**: Advanced features, tests, documentation

---

## Appendix A: Code Locations Reference

| Component | File | Line Range |
|-----------|------|------------|
| BaseAgent.__init__ | src/kaizen/core/base_agent.py | 133-145 |
| BaseAgent imports | src/kaizen/core/base_agent.py | 36-44 |
| BaseAgent tool init | src/kaizen/core/base_agent.py | 222-230 |
| BaseAgent new methods | src/kaizen/core/base_agent.py | After 1590 |
| BaseAgent.cleanup | src/kaizen/core/base_agent.py | 1941 (modify) |
| ToolExecutor | src/kaizen/tools/executor.py | Complete file |
| ToolRegistry | src/kaizen/tools/registry.py | Complete file |
| ToolDefinition | src/kaizen/tools/types.py | 184-318 |
| ToolResult | src/kaizen/tools/types.py | 320-416 |
| ControlProtocol | src/kaizen/core/autonomy/control/protocol.py | 56-94 |

---

## Appendix B: Test Strategy Matrix

| Test Type | Location | Count | Coverage |
|-----------|----------|-------|----------|
| Unit (Tier 1) | tests/unit/core/test_base_agent_tools.py | 30+ | Tool methods |
| Integration (Tier 2) | tests/integration/core/test_base_agent_tools_integration.py | 15+ | Real executor |
| Existing Regressions | tests/unit/core/test_base_agent.py | 454 | BaseAgent |
| Tool System Tests | tests/unit/tools/ | 128 | Tool system |
| **Total** | - | **627+** | **Complete** |

---

## Appendix C: Dependency Graph

```
BaseAgent
    ├── ToolRegistry (optional, passed via __init__)
    │   └── List[ToolDefinition]
    │       ├── ToolParameter (validation)
    │       └── ToolExecutorFunc (implementation)
    ├── ToolExecutor (optional, auto-created)
    │   ├── ToolRegistry (for tool lookup)
    │   └── ControlProtocol (for approvals)
    │       └── Transport (for I/O)
    └── ControlProtocol (existing, reused)
        └── Transport (existing)
```

**Key Insight**: Tool system integrates cleanly with existing ControlProtocol, minimal new dependencies.

---

**End of Requirements Analysis**

**Status**: COMPLETE
**Ready for**: ADR creation and Phase 1 implementation
**Estimated Start Date**: 2025-10-21
**Estimated Completion**: 2025-10-27 (6 days)
