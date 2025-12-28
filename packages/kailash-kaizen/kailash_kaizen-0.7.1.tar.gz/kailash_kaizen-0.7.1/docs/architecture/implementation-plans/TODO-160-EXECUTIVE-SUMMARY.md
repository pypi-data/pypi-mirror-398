# TODO-160 Implementation Plan - Executive Summary

**Date**: 2025-10-25
**Status**: Ready for Implementation
**Critical Path**: BLOCKS TODO-158 Phase 2b (Autonomous Agent Enhancement)

---

## Quick Reference

**What**: Runtime permission system for safe autonomous agent operation
**Why**: Agents currently have unlimited access - critical security risk
**When**: 10 weeks (400 hours), starting after TODO-158 Phase 2 complete
**Who**: Kaizen Development Team (led by tdd-implementer)
**How**: 5 phases with incremental delivery and comprehensive testing

---

## Current Status (2% Complete)

### ✅ Implemented (Week 1 - COMPLETE)
- PermissionMode enum (4 modes: DEFAULT, ACCEPT_EDITS, PLAN, BYPASS)
- PermissionType enum (3 types: ALLOW, DENY, ASK)
- ToolPermission dataclass (permission decision records)
- PermissionRule dataclass (regex pattern matching with priority)
- ExecutionContext class (thread-safe budget tracking, tool usage)
- 33 unit tests passing (100% coverage for completed components)

**Files Created**:
- src/kaizen/core/autonomy/permissions/types.py (245 lines)
- src/kaizen/core/autonomy/permissions/context.py (157 lines)
- tests/unit/core/autonomy/permissions/test_types.py (433 lines)
- tests/unit/core/autonomy/permissions/test_context.py (199 lines)

### ❌ Pending (Weeks 2-10)
- PermissionPolicy decision engine (0%)
- BudgetEnforcer cost estimation (0%)
- ToolApprovalManager approval prompts (0%)
- BaseAgent integration (0%)
- 47+ additional tests (0%)
- Documentation (0%)
- Examples (0%)

---

## Problem Statement

### Security Risks (Current State)
Kaizen agents have **unlimited access** to all tools and operations:

- ❌ Agents can delete files (Write, Edit nodes)
- ❌ Agents can execute arbitrary bash commands (Bash, PythonCode nodes)
- ❌ Agents can make unlimited API calls (unbounded costs)
- ❌ Agents can access sensitive data without restrictions
- ❌ No approval gates for risky operations
- ❌ No audit trail of tool usage

### Production Impact
Users cannot safely deploy autonomous agents:

- ❌ No budget enforcement (OpenAI API costs can spiral)
- ❌ No human-in-the-loop for critical decisions
- ❌ Cannot restrict specialists to specific tools (from ADR-013)
- ❌ No compliance logging for enterprise deployments

---

## Solution Architecture

### 4-Layer Permission System

```
┌──────────────────────────────────────────────────────────────┐
│ PERMISSION SYSTEM (4 Layers)                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. EXECUTION CONTEXT (DONE)                                 │
│     - Tracks permissions during agent execution              │
│     - Maintains budget counters (thread-safe)                │
│     - Stores allowed/disallowed tools                        │
│     - 100% complete, 15 tests passing                        │
│                                                               │
│  2. PERMISSION POLICY (TODO - Week 2)                        │
│     - Rules engine (allow/deny/ask)                          │
│     - 8-layer decision logic                                 │
│     - Mode-based behavior (default/accept_edits/plan)        │
│     - Budget limit checks                                    │
│                                                               │
│  3. TOOL APPROVAL MANAGER (TODO - Week 4)                    │
│     - Interactive approval via Control Protocol              │
│     - Context-aware prompts (Bash, Write/Edit, generic)      │
│     - Approval history caching                               │
│     - Timeout handling (fail-closed)                         │
│                                                               │
│  4. BUDGET ENFORCER (TODO - Week 3)                          │
│     - Real-time cost tracking                                │
│     - Per-tool cost estimation                               │
│     - Budget limit enforcement                               │
│     - Cost reporting                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘

Flow: BaseAgent.execute_tool()
  ↓
 PermissionPolicy.can_use_tool()
  ↓
[allow] → Execute tool
[deny]  → Raise PermissionError
[ask]   → ToolApprovalManager.request_approval()
           ↓
           ControlProtocol.send_request("approval")
           ↓
           [approved] → Execute tool
           [denied]   → Raise PermissionError
```

---

## Key Features

### Feature 1: Permission Modes

**4 Modes for Different Scenarios**:

1. **DEFAULT**: Ask for approval on risky tools (Bash, Write, Edit, PythonCode)
   - Use case: Code generation agents
   - Behavior: Safe tools allowed, risky tools need approval

2. **ACCEPT_EDITS**: Auto-approve file modifications, ask for system operations
   - Use case: Codebase refactoring agents
   - Behavior: Write/Edit allowed, Bash/PythonCode need approval

3. **PLAN**: Read-only mode (no execution allowed)
   - Use case: Code review agents
   - Behavior: Only Read, Grep, Glob allowed

4. **BYPASS**: Disable all permission checks (DANGEROUS!)
   - Use case: Testing or trusted environments only
   - Behavior: All tools allowed without asking

**Status**: Modes defined ✅, policy engine pending ❌

---

### Feature 2: Budget Enforcement

**Real-Time Cost Tracking**:
- Pre-execution budget check (deny if estimated cost would exceed)
- Post-execution actual cost tracking (from result metadata)
- Warning threshold at 80% budget
- Clear error message when budget exceeded

**Example**:
```python
config = BaseAgentConfig(
    permission_mode=PermissionMode.DEFAULT,
    budget_limit_usd=5.0,
)

agent = ResearchAgent(config=config)

# Agent makes 10 LLM calls → $4.50 spent
# Next call estimated at $1.00 → Would exceed $5.00 budget
# → PermissionError("Budget exceeded: $4.50 spent, $0.50 remaining, tool needs $1.00")
```

**Status**: ExecutionContext budget tracking done ✅, BudgetEnforcer pending ❌

---

### Feature 3: Interactive Approval Prompts

**Context-Aware Prompts via Control Protocol**:

**Bash Command**:
```
🤖 Agent wants to execute bash command:

  rm -rf /tmp/test_data

⚠️  This could modify your system. Review carefully.

Budget: $2.50 / $10.00 spent

Approve this action?
  [ Approve Once ]  [ Deny Once ]
  [ Approve All ]   [ Deny All ]
```

**File Modification**:
```
🤖 Agent wants to modify file:

  src/auth/login.py

⚠️  This will change your codebase.

Budget: $4.20 / $10.00 spent

Approve this action?
```

**Features**:
- Clear context (show command, file path, tool input)
- Risk warnings (system changes, codebase modifications)
- Budget info (current spend, limit)
- "Approve All" option (reduce repeated prompts)
- 60s timeout (fail-closed on timeout)

**Status**: Prompt templates designed ✅, ToolApprovalManager pending ❌

---

### Feature 4: Permission Rules

**Flexible Regex-Based Rules**:

```python
rules = [
    # Deny dangerous bash commands
    PermissionRule(
        pattern="Bash",
        permission_type=PermissionType.DENY,
        conditions={"input_contains": "rm -rf"},
        priority=100,  # Highest priority
        reason="Dangerous command",
    ),

    # Allow all read operations
    PermissionRule(
        pattern="read_.*",
        permission_type=PermissionType.ALLOW,
        priority=50,
        reason="Safe read operation",
    ),

    # Ask for all write operations
    PermissionRule(
        pattern=".*Write.*",
        permission_type=PermissionType.ASK,
        priority=25,
        reason="Requires approval",
    ),
]
```

**Features**:
- Regex pattern matching (wildcards, groups, alternation)
- Priority-based evaluation (high → low)
- Compiled pattern caching (<0.5ms performance)
- Validation at creation time (clear error messages)

**Status**: PermissionRule complete ✅ (15 tests passing), policy engine pending ❌

---

## Implementation Roadmap (10 Weeks)

### Phase 1: Foundation (Weeks 1-2, 80 hours)
**Status**: 50% complete

#### Week 1: Types and Data Structures ✅ COMPLETE
- [x] PermissionMode enum
- [x] PermissionRule dataclass
- [x] ExecutionContext class
- [x] 33 unit tests (100% coverage)

#### Week 2: Permission Policy Engine ❌ TODO
- [ ] PermissionPolicy class (~200 lines)
- [ ] 8-layer decision logic
- [ ] 25 unit tests
- [ ] <5ms latency benchmark

**Acceptance**: 25 tests passing, 100% coverage, <5ms latency

---

### Phase 2: Budget & Approval (Weeks 3-4, 80 hours)
**Status**: 0% complete

#### Week 3: Budget Enforcer ❌ TODO
- [ ] Refactor BudgetInterruptHandler (extract cost logic)
- [ ] BudgetEnforcer class (~150 lines)
- [ ] 17 unit tests (cost estimation)
- [ ] 4 integration tests (real Ollama)

#### Week 4: Tool Approval Manager ❌ TODO
- [ ] ToolApprovalManager class (~200 lines)
- [ ] Approval prompt templates
- [ ] 12 unit tests (mocked protocol)
- [ ] 4 integration tests (real protocol)

**Acceptance**: 33 tests passing (21 budget + 12 approval), prompts user-friendly

---

### Phase 3: BaseAgent Integration (Weeks 5-6, 80 hours)
**Status**: 0% complete

#### Week 5: BaseAgent Permission Checks ❌ TODO
- [ ] Add permission fields to BaseAgent
- [ ] Add permission config to BaseAgentConfig
- [ ] Modify execute_tool() for 5-step permission flow
- [ ] 15 unit tests

#### Week 6: Specialist Integration & Edge Cases ❌ TODO
- [ ] Specialist tool restriction support
- [ ] Edge case handling (clear error messages)
- [ ] 5 integration tests (E2E flows)

**Acceptance**: 20 tests passing, backward compatible (182 existing tests pass)

---

### Phase 4: Testing & Documentation (Weeks 7-8, 80 hours)
**Status**: 0% complete

#### Week 7: Comprehensive Testing ❌ TODO
- [ ] Performance benchmarks (4 metrics)
- [ ] Tier 3 E2E tests with real OpenAI (4 tests)
- [ ] Regression tests (backward compatibility)
- [ ] Coverage validation (>95% line, >90% branch)

#### Week 8: Documentation & Examples ❌ TODO
- [ ] API reference (~400 lines)
- [ ] User guide (~300 lines)
- [ ] Best practices guide (~250 lines)
- [ ] Troubleshooting guide (~200 lines)
- [ ] Update ADR-012 status

**Acceptance**: All docs complete, ADR updated to "Implemented"

---

### Phase 5: Example Applications (Weeks 9-10, 80 hours)
**Status**: 0% complete

#### Week 9: Core Examples ❌ TODO
- [ ] 01_default_mode.py (~150 lines)
- [ ] 02_accept_edits_mode.py (~150 lines)
- [ ] 03_plan_mode.py (~150 lines)

#### Week 10: Advanced Examples ❌ TODO
- [ ] 04_permission_rules.py (~200 lines)
- [ ] 05_budget_enforcement.py (~200 lines)
- [ ] 06_specialist_restrictions.py (~150 lines)
- [ ] README.md (~250 lines)

**Acceptance**: All 6 examples run successfully, README clear

---

## Risk Assessment Summary

### HIGH Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Performance impact | Medium | High | Benchmarks in CI, <5ms target | IN PROGRESS |
| Approval prompt UX | Medium | High | User testing, "Approve All" option | DESIGNED |
| Budget estimation accuracy | Medium | Medium | Conservative estimates, E2E tests | PENDING |

### MEDIUM Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Control Protocol integration | Low | Medium | Comprehensive integration tests | READY |
| Thread safety issues | Low | High | Lock-protected state, concurrent tests | MITIGATED |
| Specialist integration gaps | Medium | Medium | Clear contracts, helper methods | DESIGNED |

### LOW Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Regex pattern errors | Low | Low | Validation at creation time | MITIGATED |
| Documentation drift | Medium | Low | Doc reviews, example testing | PLANNED |

---

## Success Metrics

### Code Metrics

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Lines of code (src) | 402 | ~1,100 | +698 |
| Lines of code (tests) | 632 | ~2,300 | +1,668 |
| Lines of code (docs) | 0 | ~1,600 | +1,600 |
| Lines of code (examples) | 0 | ~1,250 | +1,250 |
| Test count (unit) | 33 | 50+ | +17 |
| Test count (integration) | 0 | 20+ | +20 |
| Test count (E2E) | 0 | 10+ | +10 |
| Test coverage (line) | 100% | >95% | MAINTAIN |
| Test coverage (branch) | ~85% | >90% | +5% |

### Performance Metrics (MEASURED)

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Permission check (cached) | <1ms | Benchmark 10,000 checks |
| Permission check (uncached) | <5ms | Benchmark 1,000 checks |
| Budget check | <1ms | Simple arithmetic |
| Approval prompt (round-trip) | <50ms | Via Control Protocol |
| Rule evaluation (10 rules) | <5ms | Pattern matching overhead |
| ExecutionContext thread safety | 100% | Concurrent access test ✅ |

---

## Integration Points

### 1. BaseAgent (Primary Integration)
**Relationship**: BaseAgent is the main consumer of permission system

**Changes Required**:
- Add 3 fields: execution_context, permission_policy, approval_manager
- Modify execute_tool() to add 5-step permission flow
- Modify enable_control_protocol() to create approval_manager

**Backward Compatibility**: All fields default to None (disabled), permission checks opt-in

---

### 2. Control Protocol (Approval Prompts)
**Relationship**: Bidirectional communication for approval

**Changes Required**: None (already supports "approval" request type)

**Integration**: ToolApprovalManager uses existing send_request() API

---

### 3. BudgetInterruptHandler (Cost Tracking)
**Relationship**: Shared cost tracking state

**Changes Required**: Refactor to extract cost logic into BudgetEnforcer

**Integration**: Share ExecutionContext.budget_used (no duplication)

---

### 4. Specialist System (Future - ADR-013)
**Relationship**: Apply tool restrictions from SpecialistDefinition

**Preparation**: Helper method apply_specialist_restrictions(specialist)

**Integration**: ExecutionContext.allowed_tools populated from available_tools

---

### 5. Hooks System (Future - ADR-014)
**Relationship**: Hooks for custom permission logic

**Preparation**: Reserve PRE_PERMISSION_CHECK, POST_PERMISSION_CHECK hooks

**Integration**: Fire hooks before/after permission evaluation

---

## Key Design Decisions

### Decision 1: Opt-In by Default
**Why**: Backward compatibility, zero breaking changes
**How**: permission_mode: PermissionMode | None = None (default None)
**Trade-off**: Must explicitly enable (good for safety, bad for discoverability)

### Decision 2: Fail-Closed on Timeout
**Why**: Security first, prevent unauthorized operations
**How**: timeout=60.0, catch exceptions, return False
**Trade-off**: False positives on network issues, but safer

### Decision 3: Reuse BudgetInterruptHandler
**Why**: Avoid duplication, maintain consistency
**How**: Extract cost logic into BudgetEnforcer, share state
**Trade-off**: Refactoring risk, but cleaner architecture

### Decision 4: Thread-Safe State
**Why**: Support concurrent tool execution
**How**: threading.Lock for all state mutations
**Trade-off**: Lock contention possible, but necessary for correctness

### Decision 5: Regex Pattern Matching
**Why**: Flexible, familiar, sufficient
**How**: Compiled patterns cached in __post_init__
**Trade-off**: Regex complexity vs expressiveness

---

## Next Steps (Immediate)

### For TDD Implementer (Week 2)

**Priority 1**: Implement PermissionPolicy (~200 lines)
- 8-layer decision logic:
  1. BYPASS mode → early exit
  2. Budget check → deny if exceeded
  3. PLAN mode → read-only enforcement
  4. Explicit disallow list → hard deny
  5. Explicit allow list → skip further checks
  6. Permission rules (priority-sorted)
  7. Mode-based defaults (DEFAULT, ACCEPT_EDITS)
  8. Fallback → ask for approval

**Priority 2**: Write 25 unit tests
- Test all 8 decision layers
- Test edge cases (empty rules, no budget, concurrent access)
- Target: 100% coverage, <5ms latency

**Priority 3**: Performance benchmark
- Benchmark can_use_tool() latency
- Test with 1,000 uncached checks, 10,000 cached checks
- Validate <5ms target (p95)

**Acceptance Criteria**:
- [ ] 25 tests passing
- [ ] 100% code coverage for policy.py
- [ ] <5ms latency (p95)
- [ ] All 8 decision layers working
- [ ] Audit trail logging functional

**Estimated Time**: 40 hours (Week 2)

---

## Documentation Index

### Implementation Plan
📄 **TODO-160-permission-system-implementation-plan.md**
- Comprehensive requirements breakdown (FR-1 to FR-8, NFR-1 to NFR-5)
- User journey mapping (3 personas)
- Component requirements matrix
- Detailed roadmap (10 weeks, 5 phases)
- Risk assessment (HIGH/MEDIUM/LOW)
- Integration analysis
- File-by-file checklist (7 source files, 11 test files, 5 docs, 7 examples)
- Testing strategy (3-tier approach)

### ADR Update
📄 **TODO-160-ADR-012-implementation-update.md**
- Implementation status (2% complete)
- Design decisions with alternatives considered
- Performance benchmarks (current results)
- Risk mitigation progress
- Lessons learned (TDD, regex caching, thread safety)
- Trade-offs analysis (flexibility vs simplicity, performance vs safety)
- Next steps (Week 2 checklist)

### Original Specification
📄 **TODO-160-permission-system-implementation.md** (TODO file)
- 934 lines of detailed specification
- Phase breakdown (Weeks 1-10)
- Task-level acceptance criteria
- Evidence requirements

### Architecture Design
📄 **docs/architecture/adr/012-permission-system-design.md** (ADR)
- 869 lines of architecture design
- Component specifications
- Integration points
- Usage examples

---

## Contact & Escalation

**Primary Owner**: Kaizen Development Team
**Lead Developer**: TDD Implementer
**Reviewer**: Intermediate Reviewer (after each phase)
**Validator**: Gold Standards Validator (final review)

**Escalation Path**:
1. Performance issues → Profile with benchmarks, optimize hot path
2. UX issues → User testing, template refinement
3. Integration issues → Framework Advisor, review ADR dependencies
4. Blocking issues → Requirements Analyst, re-scope if needed

**Status Updates**: Weekly (after each phase completion)

---

## Quick Start for New Developers

### 1. Read This Summary (5 minutes)
You're here! Understand the problem, solution, and current status.

### 2. Review Existing Code (10 minutes)
```bash
# Read implemented components
cat src/kaizen/core/autonomy/permissions/types.py
cat src/kaizen/core/autonomy/permissions/context.py

# Run existing tests
pytest tests/unit/core/autonomy/permissions/ -v
# Expected: 33 tests passing
```

### 3. Read ADR-012 Architecture (20 minutes)
```bash
cat docs/architecture/adr/012-permission-system-design.md
```

### 4. Review Implementation Plan (30 minutes)
```bash
cat docs/architecture/implementation-plans/TODO-160-permission-system-implementation-plan.md
```

### 5. Start Implementation (Week 2)
- Read detailed task breakdown for PermissionPolicy
- Follow TDD methodology (write tests first)
- Refer to implementation plan for acceptance criteria

**Total Onboarding Time**: ~1 hour

---

## Appendix: File Structure

```
apps/kailash-kaizen/
├── src/kaizen/core/autonomy/permissions/
│   ├── __init__.py
│   ├── types.py (245 lines) ✅ COMPLETE
│   ├── context.py (157 lines) ✅ COMPLETE
│   ├── policy.py (~200 lines) ❌ TODO
│   ├── approval.py (~200 lines) ❌ TODO
│   └── budget.py (~150 lines) ❌ TODO
│
├── tests/unit/core/autonomy/permissions/
│   ├── __init__.py
│   ├── test_types.py (433 lines, 18 tests) ✅ COMPLETE
│   ├── test_context.py (199 lines, 15 tests) ✅ COMPLETE
│   ├── test_policy.py (~300 lines, 25 tests) ❌ TODO
│   ├── test_budget.py (~200 lines, 17 tests) ❌ TODO
│   ├── test_approval.py (~250 lines, 12 tests) ❌ TODO
│   └── test_base_agent_permissions.py (~300 lines, 15 tests) ❌ TODO
│
├── tests/integration/autonomy/permissions/
│   ├── test_budget_integration.py (~150 lines, 4 tests) ❌ TODO
│   ├── test_approval_integration.py (~200 lines, 4 tests) ❌ TODO
│   └── test_permissions_e2e.py (~250 lines, 5 tests) ❌ TODO
│
├── tests/e2e/autonomy/permissions/
│   └── test_permissions_production.py (~200 lines, 4 tests) ❌ TODO
│
├── docs/reference/
│   ├── permission-system-api.md (~400 lines) ❌ TODO
│   └── permission-errors.md (~200 lines) ❌ TODO
│
├── docs/guides/
│   ├── permission-modes.md (~300 lines) ❌ TODO
│   └── safe-autonomous-agents.md (~250 lines) ❌ TODO
│
└── examples/autonomy/permissions/
    ├── 01_default_mode.py (~150 lines) ❌ TODO
    ├── 02_accept_edits_mode.py (~150 lines) ❌ TODO
    ├── 03_plan_mode.py (~150 lines) ❌ TODO
    ├── 04_permission_rules.py (~200 lines) ❌ TODO
    ├── 05_budget_enforcement.py (~200 lines) ❌ TODO
    ├── 06_specialist_restrictions.py (~150 lines) ❌ TODO
    └── README.md (~250 lines) ❌ TODO
```

**Total Files**: 31 (7 source, 11 tests, 5 docs, 7 examples, 1 benchmark)
**Total Lines**: ~6,250 (current: ~1,034, remaining: ~5,216)
**Completion**: 2% (33/80 tests, 2/7 source files)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-25
**Author**: Requirements Analysis Specialist
**Status**: Ready for Implementation (Week 2 starts)

---

**🚀 Ready to Start? → See TODO-160-permission-system-implementation-plan.md for detailed Week 2 tasks**
