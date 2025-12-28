# TODO-160: Permission System Implementation Plan

**Version**: 1.0
**Date**: 2025-10-25
**Status**: Ready for Implementation
**Owner**: Kaizen Development Team

---

## Executive Summary

### Feature
Runtime permission system for Kaizen agents enabling safe autonomous operation through tool restrictions, budget enforcement, approval gates, and audit trails.

### Complexity
**HIGH** - Multi-component system with integration across BaseAgent, Control Protocol, and future Specialist System

### Risk Level
**MEDIUM** - Performance-critical path, user experience sensitive, requires careful testing

### Estimated Effort
**10 weeks (400 hours)** - 5 phases with incremental delivery

### Current Status (2% Complete)
**Implemented**:
- PermissionMode enum (4 modes) - 100% complete
- PermissionType enum (3 types) - 100% complete
- ToolPermission dataclass - 100% complete
- PermissionRule dataclass with regex matching - 100% complete
- ExecutionContext with thread-safe budget tracking - 100% complete
- 33 unit tests passing (18 for types, 15 for context)

**Missing**:
- PermissionPolicy decision engine (0%)
- ToolApprovalManager with Control Protocol integration (0%)
- BudgetEnforcer cost estimation (0%)
- BaseAgent integration (0%)
- Integration tests (0%)
- E2E tests (0%)
- Documentation (0%)
- Examples (0%)

---

## Table of Contents

1. [Functional Requirements Breakdown](#1-functional-requirements-breakdown)
2. [Non-Functional Requirements](#2-non-functional-requirements)
3. [User Journey Mapping](#3-user-journey-mapping)
4. [Component Requirements Matrix](#4-component-requirements-matrix)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Risk Assessment](#6-risk-assessment)
7. [Integration Analysis](#7-integration-analysis)
8. [Success Criteria](#8-success-criteria)
9. [File-by-File Checklist](#9-file-by-file-checklist)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Functional Requirements Breakdown

### FR-1: Support Multiple Permission Modes

**Requirement**: Implement 4 distinct permission modes (DEFAULT, ACCEPT_EDITS, PLAN, BYPASS) with mode-specific behavior.

**Acceptance Criteria**:
- [x] PermissionMode enum defines all 4 modes (DONE)
- [ ] PermissionPolicy correctly implements mode-based decisions
- [ ] DEFAULT mode asks for risky tools (Bash, Write, Edit, PythonCode)
- [ ] ACCEPT_EDITS mode auto-approves Write/Edit, asks for Bash/PythonCode
- [ ] PLAN mode allows only read-only tools (Read, Grep, Glob)
- [ ] BYPASS mode skips all permission checks (performance: <1ms)

**SDK Mapping**: PermissionMode (types.py), PermissionPolicy (policy.py)

**Test Coverage**: 8 unit tests, 3 integration tests

**Edge Cases**:
- Mode transitions during execution
- Invalid mode values
- Mode-specific tool classification

**Risk**: MEDIUM - User confusion about mode behavior

---

### FR-2: Tool-Level Permissions

**Requirement**: Support explicit allow/deny/ask permissions per tool with regex pattern matching.

**Acceptance Criteria**:
- [x] PermissionRule dataclass with regex pattern matching (DONE)
- [x] Priority-based rule evaluation (DONE)
- [ ] PermissionPolicy evaluates rules in priority order (high → low)
- [ ] Regex patterns support wildcards (.*_file), prefixes (http_.*), exact matches
- [ ] Rules support conditional evaluation (future extension via conditions field)
- [ ] Explicit allowed_tools and disallowed_tools override rules

**SDK Mapping**: PermissionRule (types.py), PermissionPolicy (policy.py)

**Test Coverage**: 15 unit tests for PermissionRule (DONE), 12 unit tests for policy logic

**Edge Cases**:
- Multiple rules matching same tool (priority resolution)
- Invalid regex patterns (validation in __post_init__)
- Empty rule lists (default to mode behavior)
- Rule conflicts (allow vs deny for same tool)

**Risk**: LOW - Well-tested pattern matching logic

---

### FR-3: Interactive Approval Prompts

**Requirement**: Request user approval for risky operations via Control Protocol with timeout handling.

**Acceptance Criteria**:
- [ ] ToolApprovalManager sends approval requests via ControlProtocol
- [ ] Approval prompts are context-aware (Bash: show command, Write: show file path)
- [ ] Support "Approve Once", "Approve All", "Deny Once", "Deny All" actions
- [ ] Approval history caching to avoid duplicate prompts
- [ ] Timeout handling (60s default, fail-closed on timeout)
- [ ] Clear error message when approval required but Control Protocol not enabled

**SDK Mapping**: ToolApprovalManager (approval.py), ControlProtocol (existing)

**Test Coverage**: 12 unit tests (mocked protocol), 4 integration tests (real protocol)

**Edge Cases**:
- Control Protocol not enabled (RuntimeError)
- Transport connection lost during approval
- Timeout expired (fail-closed, deny by default)
- Concurrent approval requests (queue handling)
- "Approve All" → add to allowed_tools, "Deny All" → add to disallowed_tools

**Risk**: HIGH - User experience critical, approval fatigue possible

---

### FR-4: Budget Enforcement

**Requirement**: Track and enforce per-agent budget limits with real-time cost monitoring.

**Acceptance Criteria**:
- [ ] BudgetEnforcer estimates tool costs before execution
- [ ] ExecutionContext tracks cumulative cost (thread-safe)
- [ ] Pre-execution budget check (deny if estimated cost would exceed)
- [ ] Post-execution actual cost tracking (from result metadata)
- [ ] Warning threshold at 80% budget (log warning, no interrupt)
- [ ] Budget exceeded → PermissionError with clear message
- [ ] Reuse 70% of BudgetInterruptHandler logic (refactor, don't duplicate)

**SDK Mapping**: BudgetEnforcer (budget.py), ExecutionContext (context.py), BudgetInterruptHandler (interrupts/handlers/budget.py)

**Test Coverage**: 17 unit tests, 4 integration tests (real Ollama)

**Edge Cases**:
- No budget limit set (unlimited budget)
- Budget limit of 0 (deny all)
- Negative estimated cost (validation error)
- Actual cost > estimated cost (update budget, log warning)
- Cost estimation for unknown tools (default $0.00)

**Risk**: MEDIUM - Cost estimation accuracy critical for user trust

---

### FR-5: Specialist Tool Restrictions

**Requirement**: Enforce tool restrictions from SpecialistDefinition.available_tools (future integration with ADR-013).

**Acceptance Criteria**:
- [ ] ExecutionContext.allowed_tools populated from SpecialistDefinition
- [ ] Tools not in available_tools → denied automatically
- [ ] Helper method: apply_specialist_restrictions(specialist)
- [ ] Clear error message when specialist-restricted tool used
- [ ] Integration point ready for AsyncLocalRuntime.create_agent_from_specialist()

**SDK Mapping**: ExecutionContext (context.py), BaseAgent (base_agent.py)

**Test Coverage**: 5 unit tests

**Edge Cases**:
- Empty available_tools list (deny all)
- available_tools = None (allow all)
- Tool not in specialist scope (clear error message)

**Risk**: LOW - Clear contract, ready for future integration

---

### FR-6: Permission Rules with Regex Patterns

**Requirement**: Support flexible pattern-based permission rules with priority and conditions.

**Acceptance Criteria**:
- [x] PermissionRule supports regex patterns (DONE)
- [x] Priority-based evaluation (high → low) (DONE)
- [x] Pattern validation at creation time (DONE)
- [x] Compiled pattern caching for performance (DONE)
- [ ] Conditions field reserved for future extensions (cost limits, time restrictions)

**SDK Mapping**: PermissionRule (types.py)

**Test Coverage**: 15 unit tests (DONE)

**Edge Cases**: (All handled in implementation)
- [x] Invalid regex (ValueError with clear message)
- [x] Empty pattern (ValueError)
- [x] Case-sensitive matching (fullmatch, not search)
- [x] Pattern compilation caching (compiled once in __post_init__)

**Risk**: LOW - Already implemented and tested

---

### FR-7: Permission Overrides at Runtime

**Requirement**: Support dynamic permission updates during agent execution (allowed_tools, disallowed_tools).

**Acceptance Criteria**:
- [x] ExecutionContext.add_tool_permission() method (DONE)
- [x] Thread-safe updates with locking (DONE)
- [ ] "Approve All" action → add to allowed_tools
- [ ] "Deny All" action → add to disallowed_tools
- [ ] Removal from opposite list when adding (allow removes from deny, vice versa)

**SDK Mapping**: ExecutionContext (context.py), ToolApprovalManager (approval.py)

**Test Coverage**: 3 unit tests for ExecutionContext (DONE), 4 integration tests for approval actions

**Edge Cases**:
- Tool in both allowed and denied (deny takes precedence)
- Concurrent updates (thread-safe with locking)
- Clearing permissions (remove from both sets)

**Risk**: LOW - Thread safety already implemented

---

### FR-8: Audit Trail of Permission Decisions

**Requirement**: Log all permission decisions for compliance and debugging.

**Acceptance Criteria**:
- [ ] PermissionPolicy logs all decisions (tool, decision, reason, timestamp)
- [ ] Log level: INFO for denials, DEBUG for allows
- [ ] Structured logging with metadata (tool_name, permission_type, reason, cost)
- [ ] ExecutionContext.tool_usage_count tracks frequency
- [ ] Integration with existing Kaizen logging framework

**SDK Mapping**: PermissionPolicy (policy.py), ExecutionContext (context.py)

**Test Coverage**: 5 unit tests (log capture)

**Edge Cases**:
- Log rotation (handled by logging framework)
- Sensitive data in logs (sanitize tool inputs)
- High-frequency logging (performance impact minimal)

**Risk**: LOW - Standard logging, no complex state

---

## 2. Non-Functional Requirements

### NFR-1: Permission Check Latency <5ms (p95)

**Requirement**: Permission checks must not significantly slow down tool execution.

**Acceptance Criteria**:
- [ ] PermissionPolicy.can_use_tool() completes in <5ms (p95)
- [ ] Benchmark with 1,000 uncached checks
- [ ] Benchmark with 10,000 cached checks (pattern compilation cached)
- [ ] No synchronous I/O in permission check path
- [ ] Regex pattern compilation done once in __post_init__

**Validation**: Benchmark suite (benchmarks/autonomy/permissions/benchmark_permission_system.py)

**Optimization Strategies**:
- Compiled regex pattern caching (DONE)
- Early exit for BYPASS mode
- Efficient rule evaluation (priority-sorted, break on first match)
- Lock-free reads where possible (thread-safe collections)

**Risk**: MEDIUM - Performance critical path, requires profiling

---

### NFR-2: Budget Check Latency <1ms

**Requirement**: Budget checks must be instantaneous (simple arithmetic).

**Acceptance Criteria**:
- [ ] ExecutionContext.has_budget() completes in <1ms
- [ ] No complex calculations or I/O
- [ ] Thread-safe with minimal lock contention
- [ ] Benchmark with 100,000 budget checks

**Validation**: Benchmark suite

**Optimization Strategies**:
- Simple arithmetic (addition, comparison)
- Lock only for state reads (brief lock hold)
- No logging in hot path

**Risk**: LOW - Trivial arithmetic operation

---

### NFR-3: Approval Prompt Latency <50ms (via Control Protocol)

**Requirement**: Approval prompts must appear quickly to avoid user frustration.

**Acceptance Criteria**:
- [ ] ToolApprovalManager.request_approval() sends request in <50ms
- [ ] Latency measured from request creation to protocol send
- [ ] Excludes user response time (only system latency)
- [ ] Benchmark with all 4 transports (CLI, HTTP/SSE, stdio, memory)

**Validation**: Benchmark suite + integration tests

**Optimization Strategies**:
- Pre-generate prompt templates
- Minimal data serialization
- Async I/O for protocol communication

**Risk**: LOW - Control Protocol already tested and optimized

---

### NFR-4: Thread-Safe Permission State

**Requirement**: ExecutionContext must support concurrent tool execution without data corruption.

**Acceptance Criteria**:
- [x] ExecutionContext uses threading.Lock for all state mutations (DONE)
- [x] Thread safety tested with concurrent access (DONE)
- [ ] No race conditions in budget tracking
- [ ] No race conditions in tool usage counting
- [ ] No race conditions in permission updates
- [ ] Stress test with 100 concurrent threads

**Validation**: Thread safety tests (3 concurrent scenarios DONE), stress tests

**Risk**: LOW - Already implemented and tested

---

### NFR-5: Zero Permission Checks When Disabled (bypass mode)

**Requirement**: BYPASS mode must have zero overhead (performance parity with no permission system).

**Acceptance Criteria**:
- [ ] BYPASS mode: early exit in can_use_tool() (first check)
- [ ] Benchmark confirms <1ms overhead in BYPASS mode
- [ ] No logging, no budget checks, no rule evaluation in BYPASS

**Validation**: Benchmark comparing BYPASS vs no permission system

**Risk**: LOW - Simple early exit

---

## 3. User Journey Mapping

### Journey 1: Developer with Safe Agent (DEFAULT Mode)

**Persona**: Backend developer deploying autonomous code generation agent

**Steps**:
1. Install Kaizen SDK → pip install kailash-kaizen
2. Create agent with DEFAULT mode → config = BaseAgentConfig(permission_mode=PermissionMode.DEFAULT)
3. Enable Control Protocol → agent.enable_control_protocol(CLITransport())
4. Run agent on task → agent.run(task="Fix authentication bug")
5. Agent wants to use Write node → Approval prompt appears
6. Developer reviews file path → "src/auth/login.py"
7. Developer approves → Click "Approve Once"
8. Agent writes fix → File modified
9. Agent wants to run tests → Bash node, approval prompt
10. Developer approves → Click "Approve Once"
11. Tests pass → Task complete

**Success Criteria**:
- Setup complete in <5 minutes
- Approval prompts clear and actionable
- No false positives (safe tools allowed without prompts)
- Budget tracking visible (logs show cost)

**Failure Points**:
- Control Protocol setup unclear (doc improvement needed)
- Approval prompts confusing (template refinement needed)
- Too many prompts (approval fatigue → use ACCEPT_EDITS mode)

---

### Journey 2: Data Scientist with Budget Limit

**Persona**: Data scientist running research agent with limited API budget

**Steps**:
1. Create agent with budget → config = BaseAgentConfig(budget_limit_usd=5.0)
2. Run research task → agent.run(task="Analyze dataset and create report")
3. Agent makes 10 LLM calls → $2.50 spent
4. Warning at 80% budget → Logger: "Budget warning: $2.00 remaining"
5. Agent continues → $4.50 spent
6. Final LLM call estimated at $1.00 → Would exceed budget
7. Permission denied → PermissionError("Budget exceeded: $4.50 spent, $0.50 remaining, tool needs $1.00")
8. Agent gracefully stops → Returns partial results

**Success Criteria**:
- Budget enforcement prevents overspending
- Warning gives user chance to checkpoint
- Error message clear about remaining budget
- Partial results saved (not lost)

**Failure Points**:
- Cost estimation inaccurate (actual > estimated, budget overrun)
- No warning before hard stop (surprising failure)
- Partial results discarded (data loss)

---

### Journey 3: Code Reviewer with PLAN Mode

**Persona**: Senior engineer reviewing codebase for security issues

**Steps**:
1. Create agent with PLAN mode → config = BaseAgentConfig(permission_mode=PermissionMode.PLAN)
2. Run review task → agent.run(task="Find SQL injection vulnerabilities")
3. Agent uses Read node → Allowed (read-only)
4. Agent uses Grep node → Allowed (read-only)
5. Agent tries Write node → PermissionError("Plan mode: Only read-only tools allowed (tried: Write)")
6. Review complete → No files modified

**Success Criteria**:
- Review runs without modifying codebase
- Read-only tools work normally
- Clear error if execution attempted
- Confidence in read-only guarantee

**Failure Points**:
- Execution tool misclassified as read-only (false negative)
- Read-only tool misclassified as execution (false positive)
- Error message unclear about mode

---

## 4. Component Requirements Matrix

| Component | Requirements | Input | Output | Business Logic | Edge Cases | SDK Mapping |
|-----------|-------------|-------|---------|----------------|------------|-------------|
| PermissionMode | FR-1 | None | Enum value | Mode definitions | Invalid mode | types.py (DONE) |
| PermissionType | FR-2 | None | Enum value | Type definitions | Invalid type | types.py (DONE) |
| PermissionRule | FR-2, FR-6 | pattern, permission_type, reason, priority | PermissionRule | Regex compilation, pattern matching | Invalid regex, empty pattern | types.py (DONE) |
| ToolPermission | FR-8 | tool_name, permission_type, reason | ToolPermission | Permission record | Invalid types | types.py (DONE) |
| ExecutionContext | FR-4, FR-7, FR-8 | mode, budget_limit, allowed_tools, denied_tools | ExecutionContext | Budget tracking, tool usage, thread safety | Concurrent updates, budget overflow | context.py (DONE) |
| PermissionPolicy | FR-1, FR-2, FR-4, FR-8 | tool_name, tool_input, estimated_cost | (bool or None, str or None) | 8-layer decision engine | Mode conflicts, rule conflicts | policy.py (TODO) |
| ToolApprovalManager | FR-3 | tool_name, tool_input, context | bool | Approval prompt generation, Control Protocol integration | Timeout, protocol not enabled | approval.py (TODO) |
| BudgetEnforcer | FR-4 | tool_name, tool_input or result | float (cost_usd) | Cost estimation, actual cost extraction | Unknown tools, negative costs | budget.py (TODO) |
| BaseAgent Integration | FR-5, FR-7, FR-8 | tool_name, tool_input | dict (result) | execute_tool() permission flow | Approval required but no protocol | base_agent.py (TODO) |

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2, 80 hours)

**Status**: 50% complete (types and context done, policy engine pending)

#### Week 1: Types and Data Structures (COMPLETE)
- [x] Task 1.1: PermissionMode enum (DONE)
- [x] Task 1.2: PermissionRule dataclass (DONE)
- [x] Task 1.3: ExecutionContext class (DONE)
- [x] Task 1.4: Unit tests for types (33 tests passing)

**Evidence**:
- Files: types.py (245 lines), context.py (157 lines)
- Tests: test_types.py (433 lines), test_context.py (199 lines)
- Coverage: 100% for types.py and context.py

#### Week 2: Permission Policy Engine (TODO)
- [ ] Task 2.1: Implement PermissionPolicy class (~200 lines)
  - Method: can_use_tool(tool_name, tool_input, estimated_cost) → (bool | None, str | None)
  - 8-layer decision logic:
    1. BYPASS mode → (True, None)
    2. Budget check → (False, reason) if exceeded
    3. PLAN mode → (False, reason) for execution tools
    4. Explicit disallow list → (False, reason)
    5. Explicit allow list → (True, None)
    6. Permission rules (priority-sorted) → (allow | deny | ask)
    7. Mode-based defaults (DEFAULT, ACCEPT_EDITS)
    8. Fallback → (None, None) ask for approval
  - File: src/kaizen/core/autonomy/permissions/policy.py

- [ ] Task 2.2: Write unit tests for policy (~300 lines)
  - 25 tests covering all 8 decision layers
  - Test BYPASS early exit
  - Test budget enforcement
  - Test PLAN mode restrictions
  - Test rule priority evaluation
  - Test mode-based defaults
  - Edge cases: empty rules, no budget, concurrent access
  - File: tests/unit/core/autonomy/permissions/test_policy.py

**Acceptance**: 25 tests passing, 100% coverage for policy.py, <5ms latency

---

### Phase 2: Budget & Approval (Weeks 3-4, 80 hours)

#### Week 3: Budget Enforcer (TODO)
- [ ] Task 3.1: Refactor BudgetInterruptHandler (~50 lines)
  - Extract cost estimation logic into BudgetEnforcer
  - Keep interrupt triggering in BudgetInterruptHandler
  - Share cost tracking state (don't duplicate)
  - File: src/kaizen/core/autonomy/interrupts/handlers/budget.py (modify)

- [ ] Task 3.2: Implement BudgetEnforcer class (~150 lines)
  - Static method: estimate_tool_cost(tool_name, tool_input) → float
  - Static method: get_actual_cost(result: dict) → float
  - Cost table: TOOL_COSTS dict (LLM nodes, file ops, bash)
  - LLM cost estimation: tokens * $0.01/1000 (approximate)
  - File: src/kaizen/core/autonomy/permissions/budget.py

- [ ] Task 3.3: Write unit tests for BudgetEnforcer (~200 lines)
  - 17 tests: 5 LLM cost estimation, 8 non-LLM tools, 4 actual cost extraction
  - Test cost table completeness
  - Test unknown tools (default $0.00)
  - Test negative costs (validation error)
  - File: tests/unit/core/autonomy/permissions/test_budget.py

- [ ] Task 3.4: Write integration tests with Ollama (~150 lines)
  - 4 tests: end-to-end budget tracking, budget exceeded, warning threshold, budget reset
  - Use real Ollama (free) for cost tracking validation
  - File: tests/integration/autonomy/permissions/test_budget_integration.py

**Acceptance**: 21 tests passing (17 unit + 4 integration), cost estimates within 20% for LLM

---

#### Week 4: Tool Approval Manager (TODO)
- [ ] Task 4.1: Implement ToolApprovalManager class (~200 lines)
  - Method: request_approval(tool_name, tool_input, context) → bool
  - Method: _generate_approval_prompt(tool_name, tool_input, context) → str
  - Integration: ControlProtocol.send_request(type="approval")
  - Approval history caching (avoid duplicates)
  - Handle "Approve All" / "Deny All" actions
  - Timeout handling (60s, fail-closed)
  - File: src/kaizen/core/autonomy/permissions/approval.py

- [ ] Task 4.2: Implement approval prompt templates (within class)
  - Template for Bash (show command, warn about system changes)
  - Template for Write/Edit (show file path, warn about codebase changes)
  - Template for generic tools (show tool name + input)
  - Include budget info in all prompts
  - Format: human-readable with context

- [ ] Task 4.3: Write unit tests for approval manager (~250 lines)
  - 12 tests: prompt generation (5 tool types), approval history (3), timeout (2), actions (2)
  - Mock ControlProtocol for unit tests
  - File: tests/unit/core/autonomy/permissions/test_approval.py

- [ ] Task 4.4: Write integration tests with real Control Protocol (~200 lines)
  - 4 tests: CLI transport, memory transport, caching, timeout
  - Real protocol communication (no mocking)
  - File: tests/integration/autonomy/permissions/test_approval_integration.py

**Acceptance**: 16 tests passing (12 unit + 4 integration), prompts clear and user-friendly

---

### Phase 3: BaseAgent Integration (Weeks 5-6, 80 hours)

#### Week 5: BaseAgent Permission Checks (TODO)
- [ ] Task 5.1: Add permission fields to BaseAgent (~30 lines)
  - Field: execution_context: ExecutionContext | None = None
  - Field: permission_policy: PermissionPolicy | None = None
  - Field: approval_manager: ToolApprovalManager | None = None
  - Initialize in __init__() if BaseAgentConfig.permission_mode set
  - File: src/kaizen/core/base_agent.py (modify)

- [ ] Task 5.2: Add permission config to BaseAgentConfig (~30 lines)
  - Field: permission_mode: PermissionMode | None = None
  - Field: budget_limit_usd: float | None = None
  - Field: permission_rules: list[PermissionRule] = field(default_factory=list)
  - Field: allowed_tools: set[str] = field(default_factory=set)
  - Field: disallowed_tools: set[str] = field(default_factory=set)
  - File: src/kaizen/core/config.py (modify)

- [ ] Task 5.3: Modify enable_control_protocol() (~10 lines)
  - Create ToolApprovalManager when control protocol enabled
  - Pass self.control_protocol to approval manager
  - File: src/kaizen/core/base_agent.py (modify)

- [ ] Task 5.4: Modify execute_tool() for permission checks (~80 lines)
  - Step 1: Estimate cost (BudgetEnforcer.estimate_tool_cost)
  - Step 2: Check permissions (permission_policy.can_use_tool)
  - Step 3: Request approval if needed (approval_manager.request_approval)
  - Step 4: Execute tool (existing logic)
  - Step 5: Record usage and cost (execution_context.record_tool_usage)
  - Handle PermissionError gracefully (clear messages)
  - File: src/kaizen/core/base_agent.py (modify)

- [ ] Task 5.5: Write unit tests for BaseAgent permissions (~300 lines)
  - 15 tests: mode initialization (4), allowed (3), denied (3), approval (3), budget (2)
  - Mock LLM calls for unit tests
  - File: tests/unit/core/test_base_agent_permissions.py

**Acceptance**: 15 tests passing, 100% coverage for permission code paths, backward compatible

---

#### Week 6: Specialist Integration & Edge Cases (TODO)
- [ ] Task 6.1: Add specialist tool restriction support (~30 lines)
  - Helper method: apply_specialist_restrictions(specialist)
  - Apply available_tools to ExecutionContext.allowed_tools
  - File: src/kaizen/core/base_agent.py (modify)

- [ ] Task 6.2: Handle edge cases and errors (~20 lines)
  - Approval required but control protocol not enabled → RuntimeError
  - Empty allowed_tools → deny all
  - Budget limit 0 → deny all
  - Invalid permission rule regex → ValueError
  - Clear error messages for all edge cases
  - File: src/kaizen/core/autonomy/permissions/policy.py (modify)

- [ ] Task 6.3: Write integration tests for E2E flows (~250 lines)
  - 5 tests: DEFAULT mode (Ollama + CLI), ACCEPT_EDITS, PLAN, budget enforcement, specialist restrictions
  - Real infrastructure (Ollama, Control Protocol)
  - File: tests/integration/autonomy/permissions/test_permissions_e2e.py

**Acceptance**: 5 integration tests passing, edge cases handled with clear errors

---

### Phase 4: Testing & Documentation (Weeks 7-8, 80 hours)

#### Week 7: Comprehensive Testing (TODO)
- [ ] Task 7.1: Write performance benchmarks (~200 lines)
  - Benchmark: Permission check latency (target <5ms)
  - Benchmark: Budget check latency (target <1ms)
  - Benchmark: Approval prompt round-trip (target <50ms)
  - Benchmark: Thread safety (100 concurrent checks)
  - File: benchmarks/autonomy/permissions/benchmark_permission_system.py

- [ ] Task 7.2: Write Tier 3 E2E tests with real OpenAI (~200 lines)
  - 4 tests: full autonomous agent ($5 budget), approval workflow, cost accuracy, audit trail
  - Real OpenAI API calls (budget-controlled)
  - File: tests/e2e/autonomy/permissions/test_permissions_production.py

- [ ] Task 7.3: Create regression test suite (~150 lines)
  - Test backward compatibility (permission system disabled by default)
  - Test existing agents still work (182 BaseAgent tests pass)
  - Test opt-in behavior (no breaking changes)
  - File: tests/regression/test_permissions_backward_compatibility.py

- [ ] Task 7.4: Validate test coverage
  - Run coverage report for src/kaizen/core/autonomy/permissions/
  - Target: >95% line coverage, >90% branch coverage
  - Fix any coverage gaps

**Acceptance**: All benchmarks meet targets, E2E tests passing, coverage >95%

---

#### Week 8: Documentation & Examples (TODO)
- [ ] Task 8.1: Write API reference (~400 lines)
  - Document all 4 permission modes (use cases, behavior)
  - Document PermissionRule (pattern syntax, examples)
  - Document ExecutionContext (fields, methods)
  - Document PermissionPolicy (decision flow)
  - Document ToolApprovalManager (integration guide)
  - Document BudgetEnforcer (cost estimation logic)
  - File: docs/reference/permission-system-api.md

- [ ] Task 8.2: Write user guide (~300 lines)
  - Guide: Choosing the right permission mode
  - Guide: Setting up budget limits
  - Guide: Creating permission rules
  - Guide: Handling approval prompts
  - Guide: Specialist tool restrictions
  - Guide: Troubleshooting permission errors
  - File: docs/guides/permission-modes.md

- [ ] Task 8.3: Write best practices guide (~250 lines)
  - Best practice: Safe autonomous agents (use DEFAULT mode)
  - Best practice: Budget limits for production (conservative limits)
  - Best practice: Permission rules (deny risky patterns)
  - Best practice: Approval workflow design (clear prompts)
  - Best practice: Audit trail usage (compliance logging)
  - File: docs/guides/safe-autonomous-agents.md

- [ ] Task 8.4: Write troubleshooting guide (~200 lines)
  - Error: PermissionError explanations (10 common causes)
  - Error: RuntimeError (control protocol not enabled)
  - Issue: Approval prompts not showing (transport debugging)
  - Issue: Budget enforcement not working (cost tracking debug)
  - Issue: Permission rules not matching (regex debugging)
  - File: docs/reference/permission-errors.md

- [ ] Task 8.5: Update ADR-012 status (~20 lines)
  - Change status from "Proposed" to "Implemented"
  - Add implementation date
  - Add links to source code and tests
  - Add performance benchmark results
  - File: docs/architecture/adr/012-permission-system-design.md

**Acceptance**: All documentation complete, examples tested, ADR updated

---

### Phase 5: Example Applications (Weeks 9-10, 80 hours)

#### Week 9: Core Example Applications (TODO)
- [ ] Task 9.1: Example 1 - Default Mode (~150 lines)
  - Create agent with DEFAULT mode
  - Demonstrate approval prompts for Bash, Write, Edit
  - Show budget tracking in action
  - File: examples/autonomy/permissions/01_default_mode.py

- [ ] Task 9.2: Example 2 - Accept Edits Mode (~150 lines)
  - Create agent with ACCEPT_EDITS mode
  - Demonstrate auto-approval for Write/Edit
  - Show prompts still appear for Bash/PythonCode
  - File: examples/autonomy/permissions/02_accept_edits_mode.py

- [ ] Task 9.3: Example 3 - Plan Mode (~150 lines)
  - Create agent with PLAN mode
  - Demonstrate read-only tool access (Read, Grep, Glob)
  - Show denial for execution tools (Write, Bash)
  - File: examples/autonomy/permissions/03_plan_mode.py

**Acceptance**: All 3 examples run successfully, output demonstrates expected behavior

---

#### Week 10: Advanced Examples & Integration (TODO)
- [ ] Task 10.1: Example 4 - Permission Rules (~200 lines)
  - Create agent with custom permission rules
  - Demonstrate regex pattern matching
  - Show conditional rules (e.g., deny "rm -rf")
  - Show priority-based rule evaluation
  - File: examples/autonomy/permissions/04_permission_rules.py

- [ ] Task 10.2: Example 5 - Budget Enforcement (~200 lines)
  - Create agent with $5 budget limit
  - Run multiple LLM calls until budget exceeded
  - Show warning at 80% threshold
  - Show graceful shutdown at budget limit
  - File: examples/autonomy/permissions/05_budget_enforcement.py

- [ ] Task 10.3: Example 6 - Specialist Restrictions (~150 lines)
  - Create specialist with limited tool set
  - Demonstrate tool restriction enforcement
  - Show denial for tools outside specialist scope
  - File: examples/autonomy/permissions/06_specialist_restrictions.py

- [ ] Task 10.4: Create comprehensive README (~250 lines)
  - Overview of all 6 examples
  - Setup instructions (API keys, dependencies)
  - Expected output for each example
  - Common issues and troubleshooting
  - File: examples/autonomy/permissions/README.md

**Acceptance**: All 6 examples run successfully, README clear and complete

---

## 6. Risk Assessment

### HIGH Risks

#### Risk 1: Performance Impact on Tool Execution
**Description**: Permission checks add latency to every tool execution, potentially degrading user experience.

**Likelihood**: Medium
**Impact**: High (users may disable if too slow)

**Mitigation Strategies**:
- Async-first design (non-blocking)
- Pattern compilation caching (DONE)
- Early exit for BYPASS mode
- Benchmark in CI to catch regressions
- <5ms target enforced in tests

**Monitoring**:
- Performance tests in CI (fail if >5ms p95)
- Latency tracking in production logs
- User feedback on perceived slowness

**Contingency Plan**:
- If >5ms: Profile hot path, optimize rule evaluation
- If still slow: Add caching layer for permission decisions
- Last resort: Make permission checks optional per-tool

---

#### Risk 2: Approval Prompt UX Problems
**Description**: Poor prompts confuse users, cause approval fatigue, or are ignored.

**Likelihood**: Medium
**Impact**: High (users may bypass system or lose trust)

**Mitigation Strategies**:
- Clear, context-aware prompt templates
- "Approve All" option to reduce repetition
- Budget info in every prompt
- User testing before release
- Iterative template refinement based on feedback

**Monitoring**:
- User feedback surveys
- Approval rate tracking (high denial rate = confusing prompts)
- Support tickets about permission system

**Contingency Plan**:
- If prompts confusing: A/B test different templates
- If too many prompts: Document ACCEPT_EDITS mode for common cases
- If users bypass: Add prominent warnings in BYPASS mode docs

---

#### Risk 3: Budget Estimation Inaccuracy
**Description**: Inaccurate cost estimates lead to budget overruns or unnecessary denials.

**Likelihood**: Medium
**Impact**: Medium (unexpected costs or false positives)

**Mitigation Strategies**:
- Conservative estimates (overestimate by 20%)
- Actual cost tracking and comparison (log discrepancies)
- E2E tests with real API calls to validate estimates
- Refinement over time based on actual usage data
- Document estimation methodology and limitations

**Monitoring**:
- Log estimated vs actual costs
- Alert on >30% discrepancy
- Monthly review of cost estimation accuracy

**Contingency Plan**:
- If overruns common: Increase safety margin (30% buffer)
- If false positives: Decrease safety margin or warn instead of deny
- If estimation complex: Add per-model cost tables

---

### MEDIUM Risks

#### Risk 4: Control Protocol Integration Complexity
**Description**: Approval flow may have edge cases (timeout, transport failure, concurrent requests).

**Likelihood**: Low (Control Protocol well-tested)
**Impact**: Medium (approval failures)

**Mitigation Strategies**:
- Comprehensive integration tests (4 transports)
- Timeout handling with fail-closed design
- Clear error messages for protocol issues
- Reuse existing Control Protocol infrastructure (battle-tested)

**Monitoring**:
- Integration test results in CI
- Error logs for approval failures
- Timeout rate tracking

**Contingency Plan**:
- If timeout common: Increase timeout from 60s to 120s
- If transport failures: Add retry logic (3 attempts)
- If concurrent requests break: Add request queuing

---

#### Risk 5: Thread Safety Issues
**Description**: Concurrent tool execution may corrupt permission state.

**Likelihood**: Low (threading.Lock used)
**Impact**: High (incorrect permission decisions)

**Mitigation Strategies**:
- Lock-protected state (DONE in ExecutionContext)
- Concurrent tests (DONE, 3 scenarios)
- Stress testing (100 threads in benchmarks)
- Code review for race conditions

**Monitoring**:
- Thread safety tests in CI
- Stress test results
- Production errors related to state corruption

**Contingency Plan**:
- If race conditions found: Add more locks (with profiling to avoid contention)
- If contention high: Use thread-local storage where applicable
- If complex: Consider actor model for state isolation

---

#### Risk 6: Specialist Integration Gaps
**Description**: Tool restrictions may not work with all specialists or future specialist features.

**Likelihood**: Medium (specialist system not yet implemented)
**Impact**: Medium (inconsistent enforcement)

**Mitigation Strategies**:
- Clear contracts for specialist integration
- Helper method: apply_specialist_restrictions()
- Integration tests when specialist system ready
- Reserve ExecutionContext fields for future extensions

**Monitoring**:
- Integration tests with specialist system (when available)
- User reports of restrictions not working

**Contingency Plan**:
- If contract unclear: Update ADR-013 with permission requirements
- If restrictions fail: Add validation layer in specialist creation
- If complex: Add specialist-specific permission policies

---

### LOW Risks

#### Risk 7: Regex Pattern Errors
**Description**: Invalid regex patterns crash permission evaluation.

**Likelihood**: Low (validation at config time)
**Impact**: Low (clear error messages)

**Mitigation Strategies**:
- Pattern validation in PermissionRule.__post_init__ (DONE)
- Try/except with clear error messages (DONE)
- 15 unit tests for pattern matching (DONE)

**Monitoring**: Unit test results

**Contingency Plan**: Add more validation tests if patterns fail in production

---

#### Risk 8: Documentation Drift
**Description**: Docs become outdated as code evolves.

**Likelihood**: Medium (common issue)
**Impact**: Low (fixable with updates)

**Mitigation Strategies**:
- Documentation as part of PR checklist
- Example testing in CI
- Quarterly doc reviews

**Monitoring**: User reports of doc errors, example failures

**Contingency Plan**: Regular doc sprint to fix drift

---

## 7. Integration Analysis

### Reusable Components from Existing Codebase

#### Component 1: BudgetInterruptHandler
**Location**: src/kaizen/core/autonomy/interrupts/handlers/budget.py (126 lines)

**Reusable Logic** (70%):
- track_cost() method → BudgetEnforcer cost tracking
- Budget threshold logic (warning at 80%)
- Cost accumulation and comparison

**Integration Strategy**:
- Extract cost estimation into BudgetEnforcer (new)
- Keep interrupt triggering in BudgetInterruptHandler (existing)
- Share cost tracking state (ExecutionContext.budget_used)
- Don't duplicate logic

**Code Reuse**:
```python
# Reuse from BudgetInterruptHandler:
class BudgetEnforcer:
    @staticmethod
    def estimate_tool_cost(tool_name: str, tool_input: dict) -> float:
        # Reuse TOOL_COSTS logic from BudgetInterruptHandler
        if "LLM" in tool_name or "Agent" in tool_name:
            # Token estimation logic (reuse calculation)
            ...
        return cost
```

---

#### Component 2: ControlProtocol
**Location**: src/kaizen/core/autonomy/control/protocol.py (ready)

**Reusable** (100%):
- send_request() method for approval prompts
- 4 transports (CLI, HTTP/SSE, stdio, memory)
- Request/response handling
- Timeout support

**Integration Strategy**:
- Use as-is, no changes needed
- ToolApprovalManager wraps ControlProtocol
- Request type: "approval" (already supported)

**Code Reuse**:
```python
# Direct usage in ToolApprovalManager:
request = ControlRequest.create(
    type="approval",
    data={"tool_name": tool_name, "prompt": prompt}
)
response = await self.protocol.send_request(request, timeout=60.0)
```

---

#### Component 3: BaseAgent.execute_tool()
**Location**: src/kaizen/core/base_agent.py (existing)

**Modification Strategy**:
- Wrap existing tool execution with permission checks
- Add 5 steps: estimate cost, check permission, request approval, execute, record cost
- Preserve backward compatibility (permission checks opt-in)

**Code Integration**:
```python
# Before (existing):
async def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
    result = await self._execute_tool_impl(tool_name, tool_input)
    return result

# After (modified):
async def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
    # New: Permission checks (if enabled)
    if self.permission_policy:
        estimated_cost = BudgetEnforcer.estimate_tool_cost(tool_name, tool_input)
        allowed, reason = await self.permission_policy.can_use_tool(...)
        if allowed is False:
            raise PermissionError(f"Tool '{tool_name}' denied: {reason}")
        if allowed is None:  # Need approval
            approved = await self.approval_manager.request_approval(...)
            if not approved:
                raise PermissionError(f"Tool '{tool_name}' denied by user")

    # Existing: Execute tool
    result = await self._execute_tool_impl(tool_name, tool_input)

    # New: Record usage (if enabled)
    if self.execution_context:
        actual_cost = BudgetEnforcer.get_actual_cost(result)
        self.execution_context.record_tool_usage(tool_name, actual_cost)

    return result
```

---

### Integration with Existing SDK Components

#### Integration Point 1: BaseAgent
**Relationship**: BaseAgent is the primary integration point

**Changes Required**:
- Add 3 fields: execution_context, permission_policy, approval_manager
- Modify execute_tool() to add permission checks
- Modify enable_control_protocol() to create approval_manager

**Backward Compatibility**:
- All fields default to None (disabled)
- Permission checks only run if permission_mode set
- Existing tests unchanged (182 tests continue to pass)

---

#### Integration Point 2: BaseAgentConfig
**Relationship**: Configuration object for permission system

**Changes Required**:
- Add 5 fields: permission_mode, budget_limit_usd, permission_rules, allowed_tools, disallowed_tools
- All fields optional (default None or empty)

**Backward Compatibility**:
- New fields optional
- Existing configs unchanged

---

#### Integration Point 3: Control Protocol
**Relationship**: Bidirectional communication for approval prompts

**Changes Required**: None (already supports "approval" request type)

**Integration**:
- ToolApprovalManager uses existing send_request() API
- Approval prompts sent via existing transports
- No protocol modifications needed

---

#### Integration Point 4: Specialist System (Future - ADR-013)
**Relationship**: Apply tool restrictions from SpecialistDefinition

**Preparation Required**:
- Helper method: apply_specialist_restrictions(specialist)
- ExecutionContext.allowed_tools populated from SpecialistDefinition.available_tools
- Clear contract for specialist integration

**Integration Strategy** (when ADR-013 implemented):
```python
# In AsyncLocalRuntime:
agent = BaseAgent.from_specialist(specialist)
if specialist.available_tools:
    agent.execution_context.allowed_tools = set(specialist.available_tools)
```

---

#### Integration Point 5: Hooks System (Future - ADR-014)
**Relationship**: Hooks for custom permission logic

**Preparation Required**:
- Reserve hook points: PRE_PERMISSION_CHECK, POST_PERMISSION_CHECK
- Document hook signatures in ADR-012

**Integration Strategy** (when ADR-014 implemented):
```python
# In PermissionPolicy.can_use_tool():
# PRE_PERMISSION_CHECK hook fires before permission evaluation
await hooks.fire("PRE_PERMISSION_CHECK", tool_name=tool_name)

# POST_PERMISSION_CHECK hook fires after permission decision
await hooks.fire("POST_PERMISSION_CHECK", decision=allowed, reason=reason)
```

---

## 8. Success Criteria

### Functional Success Criteria

- [x] FR-1: All 4 permission modes implemented with correct behavior (50% - modes defined, policy pending)
- [ ] FR-2: Tool-level permissions with regex patterns working
- [ ] FR-3: Interactive approval prompts via Control Protocol
- [ ] FR-4: Budget enforcement with accurate cost tracking
- [ ] FR-5: Specialist tool restrictions ready for integration
- [x] FR-6: Permission rules with priority and pattern matching (100%)
- [x] FR-7: Runtime permission overrides thread-safe (100%)
- [ ] FR-8: Audit trail logging all permission decisions

### Non-Functional Success Criteria

- [ ] NFR-1: Permission check latency <5ms (p95) - **MEASURED**
- [ ] NFR-2: Budget check latency <1ms - **MEASURED**
- [ ] NFR-3: Approval prompt latency <50ms - **MEASURED**
- [x] NFR-4: Thread-safe permission state - **TESTED** (3 concurrent scenarios)
- [ ] NFR-5: BYPASS mode has <1ms overhead - **MEASURED**

### Quality Targets

- [ ] Test Coverage: >95% line coverage, >90% branch coverage
- [ ] Test Count: >80 tests (current: 33, target: 80+)
  - Tier 1 (Unit): 50+ tests (current: 33)
  - Tier 2 (Integration): 20+ tests (current: 0)
  - Tier 3 (E2E): 10+ tests (current: 0)
- [ ] Documentation: 5 guides complete (~1,600 lines)
- [ ] Examples: 6 working examples (~1,250 lines)
- [ ] Performance: All benchmarks meet targets
- [ ] Backward Compatibility: All existing tests pass (182 BaseAgent tests)

### Integration Success Criteria

- [ ] BaseAgent integration complete (execute_tool modified)
- [ ] Control Protocol integration tested (approval prompts work)
- [ ] BudgetEnforcer reuses BudgetInterruptHandler logic (no duplication)
- [ ] Ready for Specialist System integration (contracts defined)
- [ ] Ready for Hooks System integration (hook points documented)

---

## 9. File-by-File Checklist

### Source Files (7 files, ~1,100 lines total)

#### 1. types.py (245 lines)
**Status**: ✅ COMPLETE (100%)
- [x] PermissionMode enum (4 modes with docstrings)
- [x] PermissionType enum (3 types)
- [x] ToolPermission dataclass
- [x] PermissionRule dataclass with regex matching
- [x] Pattern validation and compilation

**Evidence**: File exists, 18 unit tests passing, 100% coverage

---

#### 2. context.py (157 lines)
**Status**: ✅ COMPLETE (100%)
- [x] ExecutionContext class
- [x] Thread-safe budget tracking
- [x] Tool usage counting
- [x] Permission list management (allowed/denied)
- [x] add_tool_permission() method

**Evidence**: File exists, 15 unit tests passing, 100% coverage

---

#### 3. policy.py (~200 lines)
**Status**: ❌ TODO (0%)
- [ ] PermissionPolicy class
- [ ] can_use_tool() with 8-layer decision logic
- [ ] BYPASS mode early exit
- [ ] Budget check integration
- [ ] PLAN mode restrictions
- [ ] Explicit allow/deny list checks
- [ ] Permission rule evaluation (priority-sorted)
- [ ] Mode-based defaults (DEFAULT, ACCEPT_EDITS)
- [ ] Structured logging for audit trail

**Target**: Week 2, Task 2.1

---

#### 4. approval.py (~200 lines)
**Status**: ❌ TODO (0%)
- [ ] ToolApprovalManager class
- [ ] request_approval() method
- [ ] _generate_approval_prompt() method
- [ ] Approval prompt templates (Bash, Write/Edit, generic)
- [ ] Control Protocol integration
- [ ] Approval history caching
- [ ] "Approve All" / "Deny All" handling
- [ ] Timeout handling (fail-closed)

**Target**: Week 4, Task 4.1-4.2

---

#### 5. budget.py (~150 lines)
**Status**: ❌ TODO (0%)
- [ ] BudgetEnforcer class
- [ ] estimate_tool_cost() static method
- [ ] get_actual_cost() static method
- [ ] TOOL_COSTS dict (LLM nodes, file ops, bash)
- [ ] LLM cost estimation (token-based)
- [ ] Refactor BudgetInterruptHandler (extract cost logic)

**Target**: Week 3, Task 3.1-3.2

---

#### 6. base_agent.py (modified, +110 lines)
**Status**: ❌ TODO (0%)
- [ ] Add execution_context field
- [ ] Add permission_policy field
- [ ] Add approval_manager field
- [ ] Modify __init__() to initialize permission components
- [ ] Modify enable_control_protocol() to create approval_manager
- [ ] Modify execute_tool() for 5-step permission flow
- [ ] apply_specialist_restrictions() helper method

**Target**: Week 5, Task 5.1-5.4; Week 6, Task 6.1

---

#### 7. config.py (modified, +30 lines)
**Status**: ❌ TODO (0%)
- [ ] Add permission_mode field
- [ ] Add budget_limit_usd field
- [ ] Add permission_rules field
- [ ] Add allowed_tools field
- [ ] Add disallowed_tools field

**Target**: Week 5, Task 5.2

---

### Test Files (10 files, ~2,300 lines total)

#### Unit Tests (6 files, ~1,400 lines)

**1. test_types.py (433 lines)** - ✅ COMPLETE
- [x] 18 tests for PermissionMode, PermissionType, ToolPermission, PermissionRule

**2. test_context.py (199 lines)** - ✅ COMPLETE
- [x] 15 tests for ExecutionContext

**3. test_policy.py (~300 lines)** - ❌ TODO
- [ ] 25 tests for PermissionPolicy (all 8 decision layers)

**4. test_budget.py (~200 lines)** - ❌ TODO
- [ ] 17 tests for BudgetEnforcer (cost estimation, actual cost)

**5. test_approval.py (~250 lines)** - ❌ TODO
- [ ] 12 tests for ToolApprovalManager (prompts, caching, timeout)

**6. test_base_agent_permissions.py (~300 lines)** - ❌ TODO
- [ ] 15 tests for BaseAgent permission integration

---

#### Integration Tests (3 files, ~600 lines)

**7. test_budget_integration.py (~150 lines)** - ❌ TODO
- [ ] 4 tests with real Ollama (budget tracking, exceeded, warning, reset)

**8. test_approval_integration.py (~200 lines)** - ❌ TODO
- [ ] 4 tests with real Control Protocol (CLI, memory, caching, timeout)

**9. test_permissions_e2e.py (~250 lines)** - ❌ TODO
- [ ] 5 tests for end-to-end flows (modes, budget, specialist)

---

#### E2E Tests (1 file, ~200 lines)

**10. test_permissions_production.py (~200 lines)** - ❌ TODO
- [ ] 4 tests with real OpenAI (budget limit, approval, cost accuracy, audit)

---

#### Regression Tests (1 file, ~150 lines)

**11. test_permissions_backward_compatibility.py (~150 lines)** - ❌ TODO
- [ ] Backward compatibility tests (permission system disabled by default)

---

### Documentation Files (5 files, ~1,600 lines)

**1. permission-system-api.md (~400 lines)** - ❌ TODO
- [ ] API reference for all components

**2. permission-modes.md (~300 lines)** - ❌ TODO
- [ ] User guide for permission modes

**3. safe-autonomous-agents.md (~250 lines)** - ❌ TODO
- [ ] Best practices guide

**4. permission-errors.md (~200 lines)** - ❌ TODO
- [ ] Troubleshooting guide

**5. 012-permission-system-design.md (modified, +20 lines)** - ❌ TODO
- [ ] Update ADR status to "Implemented"

---

### Example Files (7 files, ~1,500 lines)

**1. 01_default_mode.py (~150 lines)** - ❌ TODO
**2. 02_accept_edits_mode.py (~150 lines)** - ❌ TODO
**3. 03_plan_mode.py (~150 lines)** - ❌ TODO
**4. 04_permission_rules.py (~200 lines)** - ❌ TODO
**5. 05_budget_enforcement.py (~200 lines)** - ❌ TODO
**6. 06_specialist_restrictions.py (~150 lines)** - ❌ TODO
**7. README.md (~250 lines)** - ❌ TODO

---

### Benchmark Files (1 file, ~200 lines)

**1. benchmark_permission_system.py (~200 lines)** - ❌ TODO
- [ ] Permission check latency benchmark (<5ms target)
- [ ] Budget check latency benchmark (<1ms target)
- [ ] Approval prompt latency benchmark (<50ms target)
- [ ] Thread safety stress test (100 concurrent threads)

---

## 10. Testing Strategy

### 3-Tier Testing Approach

#### Tier 1: Unit Tests (50+ tests)
**Purpose**: Fast, isolated component testing with mocked dependencies

**Coverage**:
- [x] PermissionMode, PermissionType, ToolPermission (DONE - 8 tests)
- [x] PermissionRule pattern matching (DONE - 15 tests)
- [x] ExecutionContext budget tracking, thread safety (DONE - 15 tests)
- [ ] PermissionPolicy decision logic (TODO - 25 tests)
- [ ] BudgetEnforcer cost estimation (TODO - 17 tests)
- [ ] ToolApprovalManager prompt generation (TODO - 12 tests)
- [ ] BaseAgent permission integration (TODO - 15 tests)

**Mocking Strategy**:
- Mock ControlProtocol for ToolApprovalManager
- Mock LLM calls for BaseAgent tests
- No mocking of permission system internals

**Execution Time**: <5 seconds

---

#### Tier 2: Integration Tests (20+ tests)
**Purpose**: Real infrastructure validation (NO MOCKING)

**Coverage**:
- [ ] Budget tracking with real Ollama (TODO - 4 tests)
- [ ] Approval prompts with real Control Protocol (TODO - 4 tests)
- [ ] End-to-end permission flows (TODO - 5 tests)

**Infrastructure**:
- Ollama: Local LLM (free, no API key)
- Control Protocol: CLI, HTTP/SSE, stdio, memory transports
- Real file I/O, real bash execution (in sandbox)

**Execution Time**: <30 seconds

---

#### Tier 3: E2E Tests (10+ tests)
**Purpose**: Production-like validation with real paid APIs

**Coverage**:
- [ ] Full autonomous agent with budget limit (TODO - 1 test)
- [ ] Approval workflow with real OpenAI (TODO - 1 test)
- [ ] Cost tracking accuracy (estimated vs actual) (TODO - 1 test)
- [ ] Permission audit trail (TODO - 1 test)

**Infrastructure**:
- OpenAI API (real API calls, budget-controlled)
- Budget limit: $5 per test
- Real file modifications (in isolated directory)

**Execution Time**: <2 minutes

**Budget**: ~$10 total for E2E suite

---

### Test Coverage Targets

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Line Coverage | >95% | 100% (types, context) | Need policy, approval, budget |
| Branch Coverage | >90% | ~85% (types, context) | Need edge case tests |
| Unit Tests | 50+ | 33 | +17 tests |
| Integration Tests | 20+ | 0 | +20 tests |
| E2E Tests | 10+ | 0 | +10 tests |
| Total Tests | 80+ | 33 | +47 tests |

---

### Performance Benchmarks

**Required Benchmarks** (all must meet targets):

1. **Permission Check Latency**
   - Target: <5ms (p95)
   - Test: 1,000 uncached checks
   - Validation: Benchmark suite

2. **Budget Check Latency**
   - Target: <1ms
   - Test: 100,000 budget checks
   - Validation: Benchmark suite

3. **Approval Prompt Latency**
   - Target: <50ms (p95)
   - Test: 100 approval requests via each transport
   - Validation: Integration tests + benchmark

4. **Thread Safety Stress Test**
   - Target: 100% correctness
   - Test: 100 concurrent threads, 1,000 operations each
   - Validation: Thread safety tests

5. **BYPASS Mode Overhead**
   - Target: <1ms
   - Test: Compare BYPASS vs no permission system
   - Validation: Benchmark suite

---

### Regression Testing

**Backward Compatibility Requirements**:

1. **Permission System Disabled by Default**
   - All existing agents work unchanged
   - No permission checks if permission_mode = None
   - 182 existing BaseAgent tests pass

2. **Opt-In Behavior**
   - Permission system only active if explicitly enabled
   - No breaking changes to BaseAgentConfig
   - No breaking changes to BaseAgent API

3. **Zero Breaking Changes**
   - All existing examples run unchanged
   - All existing tests pass
   - No deprecations introduced

**Validation**: Regression test suite runs all existing tests

---

## Appendix A: Detailed Task Breakdown

### Week 1: Types and Data Structures (COMPLETE)

**Summary**: Foundation types for permission system

**Status**: ✅ 100% COMPLETE

**Deliverables**:
- types.py (245 lines) ✅
- context.py (157 lines) ✅
- test_types.py (433 lines) ✅
- test_context.py (199 lines) ✅

**Tests Passing**: 33/33 (100%)

**Coverage**: 100% for types.py and context.py

---

### Week 2: Permission Policy Engine (TODO)

**Summary**: Decision engine for tool permissions

**Implementation Details**:

**PermissionPolicy.can_use_tool() - 8 Decision Layers**:

```python
async def can_use_tool(
    self, tool_name: str, tool_input: dict, estimated_cost: float
) -> tuple[bool | None, str | None]:
    """
    Returns:
        (True, None): Allow tool
        (False, reason): Deny tool with reason
        (None, None): Ask user for approval
    """

    # Layer 1: BYPASS mode (skip all checks)
    if self.context.mode == PermissionMode.BYPASS:
        return True, None

    # Layer 2: Budget check
    if not self.context.has_budget(estimated_cost):
        return False, f"Budget exceeded: ${self.context.budget_used:.2f} spent..."

    # Layer 3: PLAN mode (read-only)
    if self.context.mode == PermissionMode.PLAN:
        if tool_name not in READ_ONLY_TOOLS:
            return False, f"Plan mode: Only read-only tools allowed (tried: {tool_name})"
        return True, None

    # Layer 4: Explicit disallow list
    if tool_name in self.context.denied_tools:
        return False, f"Tool '{tool_name}' is explicitly disallowed"

    # Layer 5: Explicit allow list
    if tool_name in self.context.allowed_tools:
        return True, None

    # Layer 6: Permission rules (priority-sorted)
    for rule in sorted(self.context.rules, key=lambda r: r.priority, reverse=True):
        if rule.matches(tool_name):
            if rule.permission_type == PermissionType.ALLOW:
                return True, None
            elif rule.permission_type == PermissionType.DENY:
                return False, f"Denied by rule: {rule.pattern}"
            elif rule.permission_type == PermissionType.ASK:
                return None, None

    # Layer 7: Mode-based defaults
    if self.context.mode == PermissionMode.ACCEPT_EDITS:
        if tool_name in {"Write", "Edit"}:
            return True, None
        if tool_name in {"Bash", "PythonCode"}:
            return None, None
        return True, None

    elif self.context.mode == PermissionMode.DEFAULT:
        if tool_name in RISKY_TOOLS:
            return None, None
        return True, None

    # Layer 8: Fallback (ask)
    return None, None
```

**Test Coverage** (25 tests):
- 1 test for BYPASS mode early exit
- 3 tests for budget enforcement
- 2 tests for PLAN mode restrictions
- 2 tests for explicit allow/deny lists
- 10 tests for permission rule evaluation
- 4 tests for mode-based defaults
- 3 tests for edge cases

**Acceptance**: 25 tests passing, <5ms latency

---

## Appendix B: ADR Update Summary

**ADR-012 Status Update**:

**Current Status**: Proposed (awaiting implementation)

**Changes Required**:
1. Status: "Proposed" → "Implemented"
2. Add implementation date: 2025-10-25 to 2025-12-XX
3. Add links to source code and tests
4. Add performance benchmark results
5. Add lessons learned section

**Updated Status Block**:
```markdown
## Status
**Implemented** - 2025-12-XX

**Performance Metrics**:
- Permission check latency: X.Xms (p95) [target: <5ms] ✅
- Budget check latency: X.Xms [target: <1ms] ✅
- Approval prompt latency: XXms (p95) [target: <50ms] ✅
- BYPASS mode overhead: X.Xms [target: <1ms] ✅

**Test Coverage**:
- Unit tests: 50+ passing
- Integration tests: 20+ passing
- E2E tests: 10+ passing
- Total coverage: 95% line, 90% branch

**Source Code**:
- Implementation: src/kaizen/core/autonomy/permissions/ (5 files, ~1,100 lines)
- Tests: tests/*/autonomy/permissions/ (10 files, ~2,300 lines)
- Documentation: docs/guides/, docs/reference/ (5 files, ~1,600 lines)
- Examples: examples/autonomy/permissions/ (7 files, ~1,500 lines)
```

---

## Appendix C: Key Design Decisions

### Decision 1: Opt-In by Default
**Rationale**: Backward compatibility, zero breaking changes
**Implementation**: permission_mode: PermissionMode | None = None (default None)
**Trade-off**: Users must explicitly enable (good for safety, bad for discoverability)

### Decision 2: Fail-Closed on Timeout
**Rationale**: Security first, prevent unauthorized operations
**Implementation**: timeout=60.0, catch exceptions, return False
**Trade-off**: False positives on network issues, but safer

### Decision 3: Reuse BudgetInterruptHandler
**Rationale**: Avoid duplication, maintain consistency
**Implementation**: Extract cost logic into BudgetEnforcer, share state
**Trade-off**: Refactoring existing code (small risk), but cleaner architecture

### Decision 4: Control Protocol for Approvals
**Rationale**: Reuse battle-tested infrastructure
**Implementation**: ControlProtocol.send_request(type="approval")
**Trade-off**: Dependency on Control Protocol, but well-tested

### Decision 5: Thread-Safe State
**Rationale**: Support concurrent tool execution
**Implementation**: threading.Lock for all state mutations
**Trade-off**: Lock contention possible, but necessary for correctness

---

## Summary

**Implementation Plan Status**: Ready for execution

**Current Progress**: 2% complete (foundation types done, policy engine pending)

**Next Steps**:
1. Week 2: Implement PermissionPolicy (25 tests)
2. Week 3: Implement BudgetEnforcer (21 tests)
3. Week 4: Implement ToolApprovalManager (16 tests)
4. Week 5-6: BaseAgent integration (20 tests)
5. Week 7-8: Testing & documentation
6. Week 9-10: Examples

**Critical Path**: PermissionPolicy → BudgetEnforcer → ToolApprovalManager → BaseAgent Integration

**Success Criteria**: 80+ tests passing, >95% coverage, all performance benchmarks met, 6 working examples

**Risk Level**: MEDIUM (performance and UX sensitive, but mitigated with thorough testing)

**Estimated Completion**: 10 weeks from start

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Author**: Requirements Analysis Specialist
**Status**: Ready for TDD Implementer
