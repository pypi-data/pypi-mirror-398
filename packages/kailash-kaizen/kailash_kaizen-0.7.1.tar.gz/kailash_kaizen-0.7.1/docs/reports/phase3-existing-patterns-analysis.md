# Phase 3 Lifecycle Management - Existing Patterns Analysis

**Date**: 2025-10-25
**Purpose**: Identify existing patterns, implementations, and best practices for hooks, state persistence, and interrupts in the Kailash SDK ecosystem to inform Phase 3 implementation (TODO-167, TODO-168, TODO-169).

---

## Executive Summary

**Key Finding**: Phase 3 (Lifecycle Management) infrastructure is **ALREADY IMPLEMENTED** in Kaizen with production-ready patterns. We can **REUSE and EXTEND** rather than build from scratch.

### Infrastructure Status

| Component | Status | Location | Completeness |
|-----------|--------|----------|--------------|
| **Hooks System** | ✅ IMPLEMENTED | `src/kaizen/core/autonomy/hooks/` | 90% complete |
| **State Persistence** | ✅ IMPLEMENTED | `src/kaizen/core/autonomy/state/` | 95% complete |
| **Interrupt Mechanism** | ✅ IMPLEMENTED | `src/kaizen/core/autonomy/interrupts/` | 85% complete |
| **Event System (Nexus)** | ✅ IMPLEMENTED | Nexus framework | v1.0 ready |

### Implementation Recommendation

**DO NOT** implement from scratch. **EXTEND** existing infrastructure with BaseAgent integration.

---

## 1. Hooks System Patterns

### ✅ Existing Implementation

**Location**: `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/src/kaizen/core/autonomy/hooks/`

**Components**:
- `manager.py` (426 lines) - HookManager with priority-based execution
- `types.py` (85 lines) - HookEvent, HookPriority, HookContext, HookResult
- `protocol.py` (89 lines) - HookHandler protocol, BaseHook base class
- `builtin/` - 6 built-in hooks (audit, tracing, logging, metrics, cost tracking, performance profiler)

### Registration Patterns

#### Pattern 1: Direct Function Registration
```python
from kaizen.core.autonomy.hooks.manager import HookManager
from kaizen.core.autonomy.hooks.types import HookEvent

hook_manager = HookManager()

# Register async function directly
@hook_manager.register
async def my_hook(context: HookContext) -> HookResult:
    print(f"Agent: {context.agent_id}, Event: {context.event_type.value}")
    return HookResult(success=True)

# Programmatic registration
hook_manager.register(
    event_type=HookEvent.PRE_TOOL_USE,
    handler=my_hook,
    priority=HookPriority.NORMAL
)
```
**File**: `src/kaizen/core/autonomy/hooks/manager.py:54-90`

#### Pattern 2: Class-Based Hook Registration
```python
from kaizen.core.autonomy.hooks.protocol import BaseHook
from kaizen.core.autonomy.hooks.types import HookEvent, HookContext, HookResult

class AuditHook(BaseHook):
    # Declare which events this hook handles
    events: ClassVar[list[HookEvent]] = [
        HookEvent.PRE_TOOL_USE,
        HookEvent.POST_TOOL_USE
    ]

    def __init__(self, audit_provider):
        super().__init__(name="audit_hook")
        self.audit_provider = audit_provider

    async def handle(self, context: HookContext) -> HookResult:
        # Implementation
        return HookResult(success=True, data={"audit_id": "..."})

    async def on_error(self, error: Exception, context: HookContext) -> None:
        # Optional error handler
        logger.error(f"Hook failed: {error}")

# Register with auto-discovery
hook_manager.register_hook(audit_hook, priority=HookPriority.CRITICAL)
```
**File**: `src/kaizen/core/autonomy/hooks/builtin/audit_hook.py:16-103`

#### Pattern 3: Filesystem Hook Discovery
```python
# Discover and load hooks from directory
hooks_dir = Path("~/.kaizen/hooks")
discovered_count = await hook_manager.discover_filesystem_hooks(hooks_dir)
print(f"Loaded {discovered_count} hooks from {hooks_dir}")
```
**File**: `src/kaizen/core/autonomy/hooks/manager.py:338-418`

### Execution Patterns

#### Async Execution with Timeout
```python
# Trigger all hooks for an event
results = await hook_manager.trigger(
    event_type=HookEvent.PRE_TOOL_USE,
    agent_id="agent_123",
    data={"tool": "web_search", "query": "..."},
    timeout=5.0,  # Per-hook timeout in seconds
    metadata={"session_id": "..."},
    trace_id="trace_abc123"
)

# Results include success/failure for each hook
for result in results:
    if not result.success:
        print(f"Hook failed: {result.error}")
```
**File**: `src/kaizen/core/autonomy/hooks/manager.py:187-249`

#### Priority-Based Ordering
```python
# Hooks execute in priority order:
# CRITICAL (0) → HIGH (1) → NORMAL (2) → LOW (3)

hook_manager.register(HookEvent.PRE_TOOL_USE, audit_hook, HookPriority.CRITICAL)
hook_manager.register(HookEvent.PRE_TOOL_USE, metrics_hook, HookPriority.HIGH)
hook_manager.register(HookEvent.PRE_TOOL_USE, logging_hook, HookPriority.NORMAL)
hook_manager.register(HookEvent.PRE_TOOL_USE, notification_hook, HookPriority.LOW)

# Execution order: audit → metrics → logging → notification
```
**File**: `src/kaizen/core/autonomy/hooks/types.py:37-44`

### Built-in Hooks

**Available Hooks**:
1. **AuditHook** - PostgreSQL-backed audit trail for compliance
2. **TracingHook** - Distributed tracing (OpenTelemetry)
3. **LoggingHook** - Structured logging to file/console
4. **MetricsHook** - Prometheus metrics collection
5. **CostTrackingHook** - LLM cost tracking and budgets
6. **PerformanceProfilerHook** - Performance profiling and bottleneck detection

**Location**: `src/kaizen/core/autonomy/hooks/builtin/`

### Hook Events

**Available Events** (from `types.py:14-35`):
```python
class HookEvent(Enum):
    # Tool execution lifecycle
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"

    # Agent execution lifecycle
    PRE_AGENT_LOOP = "pre_agent_loop"
    POST_AGENT_LOOP = "post_agent_loop"

    # Specialist invocation lifecycle
    PRE_SPECIALIST_INVOKE = "pre_specialist_invoke"
    POST_SPECIALIST_INVOKE = "post_specialist_invoke"

    # Permission system integration
    PRE_PERMISSION_CHECK = "pre_permission_check"
    POST_PERMISSION_CHECK = "post_permission_check"

    # State persistence integration
    PRE_CHECKPOINT_SAVE = "pre_checkpoint_save"
    POST_CHECKPOINT_SAVE = "post_checkpoint_save"
```

### Integration with BaseAgent

**TODO-167 Implementation Strategy**:
1. **Add hook_manager to BaseAgent** - Instance variable in `__init__`
2. **Trigger hooks in run()** - Wrap execution with PRE/POST hooks
3. **Add hook registration API** - `agent.register_hook()` method
4. **Enable filesystem discovery** - `agent.discover_hooks(hooks_dir)`

**No new infrastructure needed** - extend existing HookManager

---

## 2. State Persistence Patterns

### ✅ Existing Implementation

**Location**: `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/src/kaizen/core/autonomy/state/`

**Components**:
- `manager.py` (305 lines) - StateManager for checkpoint orchestration
- `storage.py` (299 lines) - FilesystemStorage (JSONL format)
- `types.py` (171 lines) - AgentState, CheckpointMetadata, StateSnapshot

### Checkpoint Patterns

#### Pattern 1: Automatic Checkpointing
```python
from kaizen.core.autonomy.state.manager import StateManager
from kaizen.core.autonomy.state.types import AgentState

state_manager = StateManager(
    checkpoint_frequency=10,  # Every N steps
    checkpoint_interval=60.0,  # OR every M seconds
    retention_count=100        # Keep last N checkpoints
)

# Automatic checkpoint decision
if state_manager.should_checkpoint(agent_id, current_step, current_time):
    checkpoint_id = await state_manager.save_checkpoint(state)
```
**File**: `src/kaizen/core/autonomy/state/manager.py:49-115`

#### Pattern 2: Manual Checkpointing
```python
# Force checkpoint immediately
state = AgentState(
    agent_id="agent_123",
    step_number=42,
    conversation_history=[...],
    memory_contents={...},
    budget_spent_usd=2.5,
    workflow_state={...}
)

checkpoint_id = await state_manager.save_checkpoint(state, force=True)
print(f"Checkpoint saved: {checkpoint_id}")
```
**File**: `src/kaizen/core/autonomy/state/manager.py:75-115`

#### Pattern 3: Resume from Checkpoint
```python
# Resume from latest checkpoint
state = await state_manager.resume_from_latest(agent_id="agent_123")

if state:
    print(f"Resumed from step {state.step_number}")
    print(f"Budget spent: ${state.budget_spent_usd:.2f}")
else:
    print("No checkpoint found, starting fresh")
```
**File**: `src/kaizen/core/autonomy/state/manager.py:134-159`

#### Pattern 4: Fork from Checkpoint
```python
# Create new branch from checkpoint
original_checkpoint_id = "ckpt_abc123"
forked_state = await state_manager.fork_from_checkpoint(original_checkpoint_id)

print(f"Forked: {original_checkpoint_id} → {forked_state.checkpoint_id}")
print(f"Parent: {forked_state.parent_checkpoint_id}")
```
**File**: `src/kaizen/core/autonomy/state/manager.py:161-196`

### Storage Patterns

#### JSONL Storage (Production-Ready)
```python
from kaizen.core.autonomy.state.storage import FilesystemStorage

# Initialize storage backend
storage = FilesystemStorage(
    base_dir=".kaizen/checkpoints",
    compress=False  # Enable gzip compression if needed
)

# Save checkpoint (atomic write with temp file + rename)
checkpoint_id = await storage.save(state)

# Load checkpoint
state = await storage.load(checkpoint_id)

# List all checkpoints for agent
checkpoints = await storage.list_checkpoints(agent_id="agent_123")
for checkpoint in checkpoints:
    print(f"{checkpoint.checkpoint_id}: step {checkpoint.step_number}, {checkpoint.size_bytes} bytes")

# Delete old checkpoints
await storage.delete(checkpoint_id)
```
**File**: `src/kaizen/core/autonomy/state/storage.py:99-292`

#### Custom Storage Backend
```python
from kaizen.core.autonomy.state.storage import StorageBackend

class S3Storage(StorageBackend):
    """Store checkpoints in AWS S3"""

    async def save(self, state: AgentState) -> str:
        # Upload to S3
        return checkpoint_id

    async def load(self, checkpoint_id: str) -> AgentState:
        # Download from S3
        return state

    async def list_checkpoints(self, agent_id: str | None = None) -> list[CheckpointMetadata]:
        # List S3 objects
        return checkpoints

    async def delete(self, checkpoint_id: str) -> None:
        # Delete from S3
        pass

    async def exists(self, checkpoint_id: str) -> bool:
        # Check S3 object exists
        return True

# Use custom storage
state_manager = StateManager(storage=S3Storage(bucket="my-checkpoints"))
```
**File**: `src/kaizen/core/autonomy/state/storage.py:22-97`

### AgentState Schema

**Complete State Capture** (from `types.py:14-98`):
```python
@dataclass
class AgentState:
    # Identification
    checkpoint_id: str
    agent_id: str
    timestamp: datetime
    step_number: int

    # Conversation state
    conversation_history: list[dict[str, Any]]
    memory_contents: dict[str, Any]

    # Execution state
    pending_actions: list[dict[str, Any]]
    completed_actions: list[dict[str, Any]]

    # Permission state (TODO-160 integration)
    budget_spent_usd: float
    approval_history: list[dict[str, Any]]

    # Tool state
    tool_usage_counts: dict[str, int]
    tool_results_cache: dict[str, Any]

    # Specialist state (ADR-013 integration)
    active_specialists: list[str]
    specialist_invocations: list[dict[str, Any]]

    # Workflow state (Kailash SDK integration)
    workflow_run_id: str | None
    workflow_state: dict[str, Any]

    # Control protocol state (ADR-011 integration)
    control_protocol_state: dict[str, Any]

    # Hook contexts (ADR-014 integration)
    registered_hooks: list[dict[str, Any]]
    hook_event_history: list[dict[str, Any]]

    # Metadata
    parent_checkpoint_id: str | None  # For forking
    status: Literal["running", "completed", "failed", "interrupted"]
    metadata: dict[str, Any]
```

### State Snapshots

```python
# Create immutable snapshot for debugging
snapshot = state_manager.create_snapshot(
    state=current_state,
    reason="before_risky_operation"
)

# Get human-readable summary
summary = snapshot.get_summary()
print(f"Snapshot: {summary['step_number']} steps, {summary['conversation_turns']} turns")
```
**File**: `src/kaizen/core/autonomy/state/manager.py:276-298`

### Integration with BaseAgent

**TODO-168 Implementation Strategy**:
1. **Add state_manager to BaseAgent** - Instance variable with lazy initialization
2. **Auto-checkpoint in run()** - Call `should_checkpoint()` after each loop iteration
3. **Add checkpoint API** - `agent.save_checkpoint()`, `agent.resume_from_checkpoint()`
4. **Capture complete state** - Populate AgentState with conversation, memory, budget, etc.

**No new infrastructure needed** - extend existing StateManager

---

## 3. Interrupt Mechanism Patterns

### ✅ Existing Implementation

**Location**: `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/src/kaizen/core/autonomy/interrupts/`

**Components**:
- `manager.py` (295 lines) - InterruptManager with signal handling
- `types.py` (104 lines) - InterruptMode, InterruptSource, InterruptReason, InterruptStatus
- `handlers/budget.py` (126 lines) - BudgetInterruptHandler
- `handlers/timeout.py` - TimeoutInterruptHandler (TODO: verify implementation)

### Signal Handling Patterns

#### Pattern 1: POSIX Signal Handlers
```python
from kaizen.core.autonomy.interrupts.manager import InterruptManager

interrupt_manager = InterruptManager()

# Install signal handlers (SIGINT, SIGTERM, SIGUSR1)
interrupt_manager.install_signal_handlers()

# Handlers are thread-safe and non-blocking
# They set an anyio.Event that can be awaited

# Cleanup when done
interrupt_manager.uninstall_signal_handlers()
```
**File**: `src/kaizen/core/autonomy/interrupts/manager.py:34-81`

#### Pattern 2: Programmatic Interrupts
```python
from kaizen.core.autonomy.interrupts.types import InterruptMode, InterruptSource

# Request graceful interrupt
interrupt_manager.request_interrupt(
    mode=InterruptMode.GRACEFUL,  # Finish current step, then checkpoint
    source=InterruptSource.USER,   # User-initiated
    message="User requested shutdown",
    metadata={"user_id": "admin", "reason": "maintenance"}
)

# Request immediate interrupt
interrupt_manager.request_interrupt(
    mode=InterruptMode.IMMEDIATE,  # Stop now, checkpoint if possible
    source=InterruptSource.TIMEOUT,
    message="Execution timeout exceeded",
    metadata={"timeout_seconds": 300}
)
```
**File**: `src/kaizen/core/autonomy/interrupts/manager.py:105-142`

#### Pattern 3: Budget-Based Interrupts
```python
from kaizen.core.autonomy.interrupts.handlers.budget import BudgetInterruptHandler

budget_handler = BudgetInterruptHandler(
    interrupt_manager=interrupt_manager,
    budget_usd=10.0,          # $10 total budget
    warning_threshold=0.8      # Warn at 80% ($8)
)

# Track cost after each operation
budget_handler.track_cost(0.05)  # $0.05 for LLM call

# Automatically triggers interrupt when budget exceeded
if interrupt_manager.is_interrupted():
    reason = interrupt_manager.get_interrupt_reason()
    print(f"Interrupted: {reason.message}")
```
**File**: `src/kaizen/core/autonomy/interrupts/handlers/budget.py:16-125`

### Graceful Shutdown Patterns

#### Pattern 1: Shutdown Callbacks
```python
# Register shutdown callbacks (executed in order)
async def save_results():
    print("Saving results...")
    await save_to_db(results)

async def cleanup_temp_files():
    print("Cleaning up temporary files...")
    await cleanup()

interrupt_manager.register_shutdown_callback(save_results)
interrupt_manager.register_shutdown_callback(cleanup_temp_files)

# Callbacks execute automatically during shutdown
```
**File**: `src/kaizen/core/autonomy/interrupts/manager.py:177-209`

#### Pattern 2: Graceful Shutdown with Checkpoint
```python
# Execute graceful shutdown sequence:
# 1. Execute shutdown callbacks
# 2. Save checkpoint (if state_manager provided)
# 3. Return interrupt status

status = await interrupt_manager.execute_shutdown(
    state_manager=state_manager,
    agent_state=current_state
)

if status.can_resume():
    print(f"Checkpoint saved: {status.checkpoint_id}")
    print(f"Can resume from: {status.checkpoint_id}")
else:
    print("No checkpoint saved")

print(f"Interrupted by: {status.reason.source.value}")
print(f"Reason: {status.reason.message}")
```
**File**: `src/kaizen/core/autonomy/interrupts/manager.py:211-269`

### Interrupt Monitoring Patterns

#### Check Interrupt Status
```python
# Non-blocking check
if interrupt_manager.is_interrupted():
    print("Interrupt requested, finishing current operation...")

# Blocking wait with timeout
reason = await interrupt_manager.wait_for_interrupt(timeout=60.0)
if reason:
    print(f"Interrupted: {reason.message}")
else:
    print("No interrupt within timeout")
```
**File**: `src/kaizen/core/autonomy/interrupts/manager.py:144-175`

### Interrupt Types

**Interrupt Sources** (from `types.py:25-41`):
```python
class InterruptSource(Enum):
    SIGNAL = "signal"              # OS signal (SIGINT, SIGTERM, SIGUSR1)
    TIMEOUT = "timeout"            # Execution time limit exceeded
    BUDGET = "budget"              # Token/cost budget exceeded
    USER = "user"                  # User requested via control protocol
    PROGRAMMATIC = "programmatic"  # Code-initiated (hook, policy)
```

**Interrupt Modes** (from `types.py:14-23`):
```python
class InterruptMode(Enum):
    GRACEFUL = "graceful"   # Finish current step, then checkpoint and stop
    IMMEDIATE = "immediate" # Stop now, checkpoint if possible
```

### Integration with BaseAgent

**TODO-169 Implementation Strategy**:
1. **Add interrupt_manager to BaseAgent** - Instance variable with lazy initialization
2. **Install signal handlers** - Call `install_signal_handlers()` in `__init__`
3. **Check interrupts in run()** - Check `is_interrupted()` in agent loop
4. **Graceful shutdown** - Call `execute_shutdown()` with state_manager on interrupt
5. **Budget integration** - Use BudgetInterruptHandler with permission system

**No new infrastructure needed** - extend existing InterruptManager

---

## 4. Event System Patterns (Nexus)

### ✅ Existing Implementation

**Location**: Nexus framework (`sdk-users/apps/nexus/docs/reference/event-system-reference.md`)

**Note**: v1.0 events are **LOGGED** (not real-time broadcast). Real-time broadcasting planned for v1.1.

### Event System Architecture

**Components** (from `event-system-reference.md:57-251`):
```python
class EventType(Enum):
    # Workflow Events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_CANCELLED = "workflow.cancelled"

    # Node Events
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    NODE_RETRYING = "node.retrying"

    # System Events
    SYSTEM_STARTED = "system.started"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    HEALTH_CHECK = "system.health_check"

    # User Events
    USER_AUTHENTICATED = "user.authenticated"
    USER_SESSION_STARTED = "user.session_started"
    USER_SESSION_ENDED = "user.session_ended"
    USER_ACTION = "user.action"

    # Channel Events
    CHANNEL_CONNECTED = "channel.connected"
    CHANNEL_DISCONNECTED = "channel.disconnected"
    CHANNEL_MESSAGE = "channel.message"

    # Custom Events
    CUSTOM_EVENT = "custom.event"
```

### Event Bus Pattern

```python
class EventBus:
    def __init__(self, max_workers: int = 10):
        self.handlers: Dict[str, EventHandler] = {}
        self.subscribers: Dict[EventType, List[str]] = {}
        self.event_history: List[Event] = []

    def register_handler(self, handler: EventHandler) -> None:
        # Register handler for multiple event types
        pass

    def publish(self, event: Event) -> Dict[str, Any]:
        # Publish to all handlers synchronously
        pass

    async def publish_async(self, event: Event) -> Dict[str, Any]:
        # Publish to all handlers asynchronously
        pass
```
**File**: `sdk-users/apps/nexus/docs/reference/event-system-reference.md:252-446`

### Workflow Trigger Pattern

```python
class WorkflowTriggerManager:
    """Event-driven workflow triggers"""

    def register_trigger(self, trigger: WorkflowTrigger) -> None:
        # Register workflow to auto-execute on events
        pass

    async def process_event_for_triggers(self, event: Event) -> List[Dict[str, Any]]:
        # Check all triggers and execute matching workflows
        pass

# Example trigger
trigger = WorkflowTrigger(
    trigger_id="failure_response",
    workflow_name="failure-recovery-workflow",
    condition=TriggerCondition.EVENT_OCCURRED,
    event_types=[EventType.WORKFLOW_FAILED],
    filters={"priority": "high"},
    parameters={"recovery_mode": "automatic"}
)
```
**File**: `sdk-users/apps/nexus/docs/reference/event-system-reference.md:1142-1443`

### Integration Opportunity

**Hooks + Events Integration**:
- Use Kaizen hooks for **agent-level lifecycle events**
- Use Nexus events for **workflow-level orchestration events**
- **Bridge pattern**: Hooks trigger Nexus events for workflow orchestration

---

## 5. Core SDK Cycle State Persistence Patterns

### ✅ Existing Documentation

**Location**: `sdk-users/2-core-concepts/cheatsheet/030-cycle-state-persistence-patterns.md`

**Critical Insight**: Generic `{"output": "output"}` mapping **DOES NOT** preserve individual fields between cycle iterations.

### Correct Field Mapping Pattern

```python
# ✅ CORRECT: Specific field mapping (preserves state)
workflow = WorkflowBuilder()
workflow.add_node("PythonCodeNode", "counter", {
    "code": """
counter = input_data.get('counter', 0)
result = {'counter': counter + 1, 'done': counter >= 5}
"""
})

# 1. Build FIRST
built_workflow = workflow.build()

# 2. Create cycle
cycle = built_workflow.create_cycle("good_cycle")

# 3. CRITICAL: Use "result." prefix for PythonCodeNode + specific field mapping
cycle.connect("counter", "counter", mapping={"result.counter": "input_data"}) \
     .max_iterations(10) \
     .converge_when("done == True") \
     .build()
# Result: counter = 1, 2, 3... (increments correctly)
```
**File**: `sdk-users/2-core-concepts/cheatsheet/030-cycle-state-persistence-patterns.md:35-61`

### State Persistence Best Practices

**From Cycle State Persistence Patterns** (line 392-397):
1. **Always provide defaults** when accessing previous state
2. **Use iteration count** as backup for convergence logic
3. **Test both scenarios**: with and without state persistence
4. **Avoid complex state dependencies** in critical paths

---

## 6. Integration Opportunities

### Hooks + State + Interrupts Integration

**Complete Lifecycle Flow**:
```python
class BaseAgent:
    def __init__(self, config):
        # Initialize managers
        self.hook_manager = HookManager()
        self.state_manager = StateManager()
        self.interrupt_manager = InterruptManager()
        self.interrupt_manager.install_signal_handlers()

    async def run(self, **inputs):
        # PRE_AGENT_LOOP hook
        await self.hook_manager.trigger(
            HookEvent.PRE_AGENT_LOOP,
            agent_id=self.agent_id,
            data={"inputs": inputs}
        )

        step = 0
        while not converged:
            # Check for interrupts
            if self.interrupt_manager.is_interrupted():
                return await self._handle_interrupt()

            # Execute step
            result = await self._execute_step(inputs)
            step += 1

            # Auto-checkpoint if needed
            if self.state_manager.should_checkpoint(self.agent_id, step, time.time()):
                state = self._capture_state(step, result)
                await self.state_manager.save_checkpoint(state)

            # Check convergence
            converged = self._check_convergence(result)

        # POST_AGENT_LOOP hook
        await self.hook_manager.trigger(
            HookEvent.POST_AGENT_LOOP,
            agent_id=self.agent_id,
            data={"result": result, "steps": step}
        )

        return result

    async def _handle_interrupt(self):
        # Graceful shutdown with checkpoint
        state = self._capture_state(self.current_step, self.current_result)
        status = await self.interrupt_manager.execute_shutdown(
            state_manager=self.state_manager,
            agent_state=state
        )
        return {"interrupted": True, "checkpoint_id": status.checkpoint_id}
```

### Hooks + Nexus Events Bridge

**Pattern**: Agent hooks trigger Nexus workflow events
```python
# Register hook that publishes to Nexus event bus
class NexusEventHook(BaseHook):
    def __init__(self, nexus_event_bus):
        super().__init__(name="nexus_event_hook")
        self.event_bus = nexus_event_bus

    async def handle(self, context: HookContext) -> HookResult:
        # Convert hook event to Nexus event
        nexus_event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source=f"agent_{context.agent_id}",
            payload=context.data,
            metadata=context.metadata
        )

        # Publish to Nexus
        await self.event_bus.publish_async(nexus_event)

        return HookResult(success=True)
```

---

## 7. Recommendations for Phase 3 Implementation

### TODO-167: Hooks System

**REUSE EXISTING**:
- ✅ HookManager (`src/kaizen/core/autonomy/hooks/manager.py`)
- ✅ HookEvent types (`src/kaizen/core/autonomy/hooks/types.py`)
- ✅ Built-in hooks (`src/kaizen/core/autonomy/hooks/builtin/`)

**EXTEND WITH**:
1. Add `hook_manager` instance variable to BaseAgent
2. Add convenience methods: `agent.register_hook()`, `agent.discover_hooks()`
3. Trigger hooks in `run()` method (PRE/POST_AGENT_LOOP)
4. Integrate with tool execution (PRE/POST_TOOL_USE)
5. Document hook API in BaseAgent

**ESTIMATED EFFORT**: 2-3 hours (integration, not building from scratch)

### TODO-168: State Persistence

**REUSE EXISTING**:
- ✅ StateManager (`src/kaizen/core/autonomy/state/manager.py`)
- ✅ FilesystemStorage (JSONL format) (`src/kaizen/core/autonomy/state/storage.py`)
- ✅ AgentState schema (`src/kaizen/core/autonomy/state/types.py`)

**EXTEND WITH**:
1. Add `state_manager` instance variable to BaseAgent
2. Populate AgentState with conversation history, memory, budget, etc.
3. Auto-checkpoint in `run()` using `should_checkpoint()`
4. Add convenience methods: `agent.save_checkpoint()`, `agent.resume_from_checkpoint()`
5. Integrate with interrupt system (checkpoint on interrupt)

**ESTIMATED EFFORT**: 3-4 hours (state capture + integration)

### TODO-169: Interrupt Mechanism

**REUSE EXISTING**:
- ✅ InterruptManager (`src/kaizen/core/autonomy/interrupts/manager.py`)
- ✅ Signal handlers (SIGINT, SIGTERM, SIGUSR1)
- ✅ BudgetInterruptHandler (`src/kaizen/core/autonomy/interrupts/handlers/budget.py`)

**EXTEND WITH**:
1. Add `interrupt_manager` instance variable to BaseAgent
2. Install signal handlers in `__init__`
3. Check `is_interrupted()` in agent loop
4. Execute graceful shutdown with checkpoint on interrupt
5. Integrate BudgetInterruptHandler with permission system (TODO-160)

**ESTIMATED EFFORT**: 2-3 hours (integration + budget handler setup)

**TOTAL ESTIMATED EFFORT**: 7-10 hours (vs 40-60 hours from scratch)

---

## 8. Anti-Patterns to Avoid

### From Existing Codebase

1. **Generic State Mapping** (Cycle State Persistence):
   ```python
   # ❌ WRONG: Loses state between iterations
   cycle.connect("node", "node", mapping={"output": "input"})

   # ✅ CORRECT: Preserves state
   cycle.connect("node", "node", mapping={"result.counter": "input_data"})
   ```

2. **Synchronous Hooks in Async Context**:
   ```python
   # ❌ WRONG: Blocks async event loop
   def sync_hook(context):
       time.sleep(5)  # Blocks!

   # ✅ CORRECT: Use async hooks
   async def async_hook(context):
       await asyncio.sleep(5)  # Non-blocking
   ```

3. **Missing Error Isolation in Hooks**:
   ```python
   # ❌ WRONG: One hook failure stops all hooks
   for hook in hooks:
       await hook.handle(context)  # Raises, stops execution

   # ✅ CORRECT: Isolate hook failures (existing HookManager does this)
   for hook in hooks:
       try:
           await hook.handle(context)
       except Exception as e:
           logger.error(f"Hook failed: {e}")
           # Continue to next hook
   ```

4. **Not Checking Interrupt in Long-Running Loops**:
   ```python
   # ❌ WRONG: Can't be interrupted
   while not converged:
       result = expensive_operation()

   # ✅ CORRECT: Check interrupt regularly
   while not converged and not interrupt_manager.is_interrupted():
       result = expensive_operation()
   ```

5. **Relying on Complex State History in Cycles**:
   ```python
   # ❌ WRONG: Breaks when state doesn't persist
   all_results = input_data["results"]  # KeyError if state lost

   # ✅ CORRECT: Provide fallbacks
   all_results = input_data.get("results", [])
   ```

---

## 9. File References

### Hooks System
- `src/kaizen/core/autonomy/hooks/manager.py` - HookManager (426 lines)
- `src/kaizen/core/autonomy/hooks/types.py` - Core types (85 lines)
- `src/kaizen/core/autonomy/hooks/protocol.py` - BaseHook protocol (89 lines)
- `src/kaizen/core/autonomy/hooks/builtin/audit_hook.py` - Example hook (103 lines)
- `.claude/skills/03-nexus/nexus-event-system.md` - Nexus event system guide (473 lines)

### State Persistence
- `src/kaizen/core/autonomy/state/manager.py` - StateManager (305 lines)
- `src/kaizen/core/autonomy/state/storage.py` - Storage backends (299 lines)
- `src/kaizen/core/autonomy/state/types.py` - AgentState schema (171 lines)
- `sdk-users/2-core-concepts/cheatsheet/030-cycle-state-persistence-patterns.md` - Cycle patterns (442 lines)

### Interrupt Mechanism
- `src/kaizen/core/autonomy/interrupts/manager.py` - InterruptManager (295 lines)
- `src/kaizen/core/autonomy/interrupts/types.py` - Interrupt types (104 lines)
- `src/kaizen/core/autonomy/interrupts/handlers/budget.py` - Budget handler (126 lines)

### Event System (Nexus)
- `sdk-users/apps/nexus/docs/reference/event-system-reference.md` - Event system (1447 lines)
- `.claude/skills/03-nexus/nexus-event-system.md` - Quick reference (473 lines)

---

## 10. Next Steps

### Immediate Actions

1. **Review TODO files** for detailed implementation requirements:
   - `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/todos/active/TODO-167-hooks-system-implementation.md`
   - `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/todos/active/TODO-168-state-persistence-implementation.md`
   - `/Users/esperie/repos/dev/kailash_kaizen/apps/kailash-kaizen/todos/active/TODO-169-interrupt-mechanism-implementation.md`

2. **Update TODO files** with "REUSE EXISTING" strategy:
   - Change approach from "build from scratch" to "extend existing"
   - Update effort estimates (40-60h → 7-10h)
   - Add file references to existing implementations

3. **Create integration plan**:
   - Phase 3A: BaseAgent + HookManager integration (2-3h)
   - Phase 3B: BaseAgent + StateManager integration (3-4h)
   - Phase 3C: BaseAgent + InterruptManager integration (2-3h)

4. **Write integration tests**:
   - Test hook execution in BaseAgent.run()
   - Test auto-checkpointing during execution
   - Test graceful shutdown with checkpoint on interrupt

### Long-Term Opportunities

1. **Nexus + Kaizen Integration**:
   - Bridge Kaizen hooks with Nexus event system
   - Enable workflow triggers from agent events

2. **Custom Storage Backends**:
   - S3Storage for cloud checkpoints
   - DatabaseStorage (PostgreSQL/SQLite) for queryable checkpoints
   - RedisStorage for distributed checkpoints

3. **Advanced Hook Features**:
   - Hook composition (combine multiple hooks)
   - Conditional hooks (only trigger if condition met)
   - Async hook batching (batch multiple events for efficiency)

4. **Enhanced Interrupt Handlers**:
   - TimeoutInterruptHandler (with configurable timeouts)
   - MemoryInterruptHandler (interrupt on memory pressure)
   - CustomInterruptHandler (user-defined conditions)

---

## Conclusion

**Phase 3 infrastructure is 90% complete**. We have production-ready implementations for:
- ✅ Hooks system with priority-based execution
- ✅ State persistence with JSONL storage
- ✅ Interrupt handling with signal support

**Implementation strategy**: **EXTEND existing infrastructure** rather than build from scratch.

**Estimated effort**: 7-10 hours (vs 40-60 hours if built from scratch)

**Next action**: Update TODO-167, TODO-168, TODO-169 with REUSE/EXTEND approach and begin BaseAgent integration.
