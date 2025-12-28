# Kaizen - Quick Reference for Claude Code

## 🚀 What is Kaizen?

**Kaizen** is a signature-based AI agent framework built on Kailash Core SDK, providing production-ready agents with multi-modal processing, multi-agent coordination, and enterprise features.

## ⚡ Quick Start

### Basic Agent Usage

```python
from kaizen.agents import SimpleQAAgent
from dataclasses import dataclass

# Zero-config usage
agent = SimpleQAAgent(QAConfig())
result = agent.ask("What is AI?")
print(result["answer"])  # Direct answer access

# Progressive configuration
@dataclass
class CustomConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500

agent = SimpleQAAgent(CustomConfig())
```

### Multi-Modal Processing

```python
from kaizen.agents import VisionAgent, VisionAgentConfig

# Vision agent with Ollama
config = VisionAgentConfig(
    llm_provider="ollama",
    model="bakllava"  # or "llava"
)
agent = VisionAgent(config=config)

result = agent.analyze(
    image="/path/to/image.png",  # File path, NOT base64
    question="What is in this image?"  # 'question', NOT 'prompt'
)
print(result['answer'])  # Key is 'answer', NOT 'response'
```

### Multi-Agent Coordination

```python
from kaizen.agents.coordination.supervisor_worker import SupervisorWorkerPattern

# Semantic capability matching (NO hardcoded if/else!)
pattern = SupervisorWorkerPattern(supervisor, workers, coordinator, shared_pool)

# A2A automatically selects best worker
best_worker = pattern.supervisor.select_worker_for_task(
    task="Analyze sales data and create visualization",
    available_workers=[code_expert, data_expert, writing_expert],
    return_score=True
)
# Returns: {"worker": <DataAnalystAgent>, "score": 0.9}
```

## 🎯 Core API

### Available Specialized Agents

**Implemented and Production-Ready (v0.2.0):**
```python
from kaizen.agents import (
    # Single-Agent Patterns (8 agents)
    SimpleQAAgent,           # Question answering
    ChainOfThoughtAgent,     # Step-by-step reasoning
    ReActAgent,              # Reasoning + action cycles
    RAGResearchAgent,        # Research with retrieval
    CodeGenerationAgent,     # Code generation
    MemoryAgent,             # Memory-enhanced conversations

    # Multi-Modal Agents (2 agents)
    VisionAgent,             # Image analysis (Ollama + OpenAI GPT-4V)
    TranscriptionAgent,      # Audio transcription (Whisper)
)
```

### Tool Calling (NEW in v0.2.0)

**Autonomous tool execution with approval workflows via MCP:**
```python
from kaizen.core.base_agent import BaseAgent

# Tools auto-configured via MCP
agent = BaseAgent(
    config=config,
    signature=signature,
    tools="all"  # Enable 12 builtin tools via MCP
)

# OR configure custom MCP servers:
mcp_servers = [{
    "name": "kaizen_builtin",
    "command": "python",
    "args": ["-m", "kaizen.mcp.builtin_server"],
    "transport": "stdio"
}]
agent = BaseAgent(
    config=config,
    signature=signature,
    custom_mcp_servers=mcp_servers
)

# Discover tools
tools = await agent.discover_tools(category="file")

# Execute single tool
result = await agent.execute_tool("read_file", {"path": "data.txt"})

# Chain multiple tools
results = await agent.execute_tool_chain([
    {"tool_name": "read_file", "params": {"path": "input.txt"}},
    {"tool_name": "write_file", "params": {"path": "output.txt", "content": "..."}}
])
```

**12 Builtin Tools:**
- **File (5)**: read_file, write_file, delete_file, list_directory, file_exists
- **HTTP (4)**: http_get, http_post, http_put, http_delete
- **Bash (1)**: bash_command
- **Web (2)**: fetch_url, extract_links

### Control Protocol (NEW in v0.2.0)

**Bidirectional agent ↔ client communication:**
```python
from kaizen.core.autonomy.control import ControlProtocol
from kaizen.core.autonomy.control.transports import CLITransport

# Create bidirectional protocol
protocol = ControlProtocol(CLITransport())
await protocol.start()

# Agent asks questions during execution
answer = await agent.ask_user_question("Which option?", ["A", "B", "C"])

# Agent requests approval for dangerous operations
approved = await agent.request_approval("Delete files?", details)

# Agent reports progress
await agent.report_progress("Processing...", percentage=50)
```

**4 Transports:** CLI, HTTP/SSE, stdio, memory

### Agent Architecture Pattern

All agents follow the same BaseAgent pattern:

```python
from kaizen.core.base_agent import BaseAgent
from kaizen.signatures import Signature, InputField, OutputField
from dataclasses import dataclass

# 1. Define configuration
@dataclass
class MyConfig:
    llm_provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.7
    # BaseAgent auto-extracts: llm_provider, model, temperature, max_tokens, provider_config

# 2. Define signature (inputs/outputs)
class MySignature(Signature):
    question: str = InputField(desc="User input")
    answer: str = OutputField(desc="Agent output")

# 3. Extend BaseAgent
class MyAgent(BaseAgent):
    def __init__(self, config: MyConfig):
        super().__init__(config=config, signature=MySignature())

    def ask(self, question: str):
        return self.run(question=question)
```

### Structured Outputs (OpenAI API) 🆕

**Kaizen supports OpenAI's Structured Outputs API for 100% schema reliability.**

#### Why Use Structured Outputs?

**Problem**: Prompt-based schema enforcement is unreliable (~70-85% compliance)
- LLMs may return invalid enum values (e.g., "." instead of "continue")
- Missing required fields
- Wrong data types
- Requires retry logic and increases costs

**Solution**: OpenAI Structured Outputs API (`strict: true`)
- **100% schema compliance** guaranteed by OpenAI
- No retry logic needed
- Lower cost (single API call)
- Better developer experience

#### Quick Start

```python
from kaizen.core.base_agent import BaseAgent, BaseAgentConfig
from kaizen.signatures import Signature, InputField, OutputField
from kaizen.core.structured_output import create_structured_output_config

# 1. Define signature
class QASignature(Signature):
    question: str = InputField(desc="User question")
    answer: str = OutputField(desc="Answer")
    confidence: float = OutputField(desc="Confidence 0-1")

# 2. Create structured output config (strict mode = 100% reliability)
response_format = create_structured_output_config(
    QASignature(),
    strict=True,  # Enable OpenAI Structured Outputs
    name="qa_response"  # Optional schema name
)

# 3. Pass to BaseAgent via provider_config
config = BaseAgentConfig(
    llm_provider="openai",
    model="gpt-4o-2024-08-06",  # Required for strict mode
    provider_config={"response_format": response_format}
)

agent = BaseAgent(config=config, signature=QASignature())
result = agent.run(question="What is AI?")  # 100% schema compliance!
```

#### Supported Models

**Strict Mode (strict=True)** - 100% Reliability:
- `gpt-4o-2024-08-06` and later
- `gpt-4o-mini-2024-07-18` and later

**Legacy Mode (strict=False)** - Best Effort (~70-85%):
- All OpenAI models
- Older GPT-4 models
- GPT-3.5

#### Configuration Options

```python
# Strict mode (recommended for production)
response_format = create_structured_output_config(
    signature,
    strict=True,  # Enable strict mode
    name="response"  # Schema name (default: "response")
)
# Returns: {"type": "json_schema", "json_schema": {"name": "response", "strict": true, "schema": {...}}}

# Legacy mode (fallback for older models)
response_format = create_structured_output_config(
    signature,
    strict=False  # Prompt-based enforcement
)
# Returns: {"type": "json_object", "schema": {...}}
```

#### Advanced Usage

**With Enums** (Perfect for state machines):
```python
from enum import Enum

class NextAction(str, Enum):
    CONTINUE = "continue"
    VALIDATE = "validate"
    SUBMIT = "submit"
    ESCALATE = "escalate"

class ConversationSignature(Signature):
    message: str = InputField(desc="User message")
    response: str = OutputField(desc="Agent response")
    next_action: str = OutputField(desc="Next action (enum)")
    confidence: float = OutputField(desc="Confidence 0-1")

# With strict mode, next_action is GUARANTEED to be valid enum value
# No more invalid values like "." or "unknown"!
```

**With Complex Types**:
```python
class AnalysisSignature(Signature):
    text: str = InputField(desc="Input text")
    summary: str = OutputField(desc="Summary")
    keywords: list = OutputField(desc="Keywords")
    metadata: dict = OutputField(desc="Metadata")
    score: float = OutputField(desc="Quality score")
    is_valid: bool = OutputField(desc="Validation result")

# All types are strictly enforced:
# - list must be array
# - dict must be object
# - float must be number
# - bool must be boolean
```

#### Migration Guide

**Before (Unreliable)**:
```python
config = BaseAgentConfig(
    llm_provider="openai",
    model="gpt-4"
)
agent = BaseAgent(config=config, signature=signature)
# ~70-85% schema compliance, requires retry logic
```

**After (100% Reliable)**:
```python
from kaizen.core.structured_output import create_structured_output_config

response_format = create_structured_output_config(signature, strict=True)

config = BaseAgentConfig(
    llm_provider="openai",
    model="gpt-4o-2024-08-06",  # Update model
    provider_config={"response_format": response_format}  # Add this
)
agent = BaseAgent(config=config, signature=signature)
# 100% schema compliance guaranteed!
```

#### Troubleshooting

**Error: "Unsupported parameter: 'response_format'"**
- Solution: Update to `gpt-4o-2024-08-06` or later
- Or use `strict=False` for legacy mode

**Error: "Invalid schema"**
- Ensure all output fields have type annotations
- Check that enum values are strings
- Verify no circular references in schema

**Lower Reliability Than Expected**
- Check you're using `strict=True` (not `strict=False`)
- Verify model is `gpt-4o-2024-08-06` or later
- Confirm `response_format` is passed to `provider_config` (NOT as a top-level parameter)

**Warning: "Workflow parameters ['response_format'] not declared"**
- Use `provider_config={"response_format": ...}` instead of passing `response_format` directly
- Do NOT pass `response_format` as a top-level workflow parameter

## 📚 Documentation Structure

### Getting Started
- **[Installation](docs/getting-started/installation.md)** - Setup and dependencies
- **[Quickstart](docs/getting-started/quickstart.md)** - Your first Kaizen agent
- **[First Agent](docs/getting-started/first-agent.md)** - Detailed agent creation

### Core Guides
- **[Signature Programming](docs/guides/signature-programming.md)** - Type-safe I/O with Signatures
- **[BaseAgent Architecture](docs/guides/baseagent-architecture.md)** - Unified agent system
- **[Multi-Modal Processing](docs/guides/multi-modal.md)** - Vision and audio agents
- **[Multi-Agent Coordination](docs/guides/multi-agent.md)** - Google A2A protocol patterns

### Lifecycle & Observability
- **[Hooks System Guide](guides/hooks-system-guide.md)** - Event-driven extension points for zero-code-change observability
- **[State Persistence Guide](guides/state-persistence-guide.md)** - Checkpoint/resume/fork capabilities
- **[Interrupt Mechanism Guide](guides/interrupt-mechanism-guide.md)** - Graceful shutdown coordination
- **[Hooks System Reference](features/hooks-system.md)** - Lifecycle event hooks reference

### Reference
- **[API Reference](docs/reference/api-reference.md)** - Complete API documentation
- **[Configuration Guide](docs/reference/configuration.md)** - All config options
- **[Troubleshooting](docs/reference/troubleshooting.md)** - Common issues

### Examples
- **[Single-Agent Patterns](../examples/1-single-agent/)** - 10 basic patterns
- **[Multi-Agent Patterns](../examples/2-multi-agent/)** - 6 coordination patterns
- **[Enterprise Workflows](../examples/3-enterprise-workflows/)** - 5 production patterns
- **[Advanced RAG](../examples/4-advanced-rag/)** - 5 RAG techniques
- **[MCP Integration](../examples/5-mcp-integration/)** - 5 MCP patterns
- **[Multi-Modal](../examples/8-multi-modal/)** - Vision/audio examples
- **[Autonomy & Hooks](../examples/autonomy/hooks/)** - Observability examples (audit_trail, distributed_tracing, prometheus_metrics)

## 🔧 Common Patterns

### Basic Agent Pattern
```python
from kaizen.agents import SimpleQAAgent
from kaizen.agents.specialized.simple_qa import QAConfig

config = QAConfig(
    llm_provider="openai",
    model="gpt-4",
    temperature=0.7
)

agent = SimpleQAAgent(config)
result = agent.ask("What is quantum computing?")

# UX: One-line field extraction (built into BaseAgent)
answer = result.get("answer", "No answer")
confidence = result.get("confidence", 0.0)
```

### Memory-Enabled Agent
```python
# Enable memory with max_turns parameter
config = QAConfig(
    llm_provider="openai",
    model="gpt-4",
    max_turns=10  # Enable BufferMemory (None = disabled)
)

agent = SimpleQAAgent(config)

# Use session_id for memory continuity
result1 = agent.ask("My name is Alice", session_id="user123")
result2 = agent.ask("What's my name?", session_id="user123")
# Returns: "Your name is Alice"
```

### Vision Processing
```python
from kaizen.agents import VisionAgent, VisionAgentConfig

# Ollama vision (free, local)
config = VisionAgentConfig(
    llm_provider="ollama",
    model="bakllava"
)
agent = VisionAgent(config=config)

result = agent.analyze(
    image="/path/to/receipt.jpg",
    question="What is the total amount?"
)
```

### Multi-Agent Coordination
```python
from kaizen.agents.coordination.supervisor_worker import SupervisorWorkerPattern
from kaizen.agents import SimpleQAAgent, CodeGenerationAgent, RAGResearchAgent

# Create worker agents
qa_agent = SimpleQAAgent(config=QAConfig())
code_agent = CodeGenerationAgent(config=CodeConfig())
research_agent = RAGResearchAgent(config=RAGConfig())

# Create pattern with automatic A2A capability matching
pattern = SupervisorWorkerPattern(
    supervisor=supervisor_agent,
    workers=[qa_agent, code_agent, research_agent],
    coordinator=coordinator,
    shared_pool=shared_memory_pool
)

# Semantic task routing (no hardcoded logic!)
result = pattern.execute_task("Analyze this codebase and suggest improvements")
```

### Interrupt Mechanism (Graceful Shutdown)

**Graceful shutdown for autonomous agents:**

```python
from kaizen.agents.autonomous.base import BaseAutonomousAgent
from kaizen.agents.autonomous.config import AutonomousConfig
from kaizen.core.autonomy.interrupts.handlers import TimeoutInterruptHandler

# Enable interrupts in config
config = AutonomousConfig(
    llm_provider="ollama",
    model="llama3.2:1b",
    enable_interrupts=True,
    graceful_shutdown_timeout=5.0,
    checkpoint_on_interrupt=True
)

# Create agent with interrupt handlers
agent = BaseAutonomousAgent(config=config, signature=TaskSignature())
agent.interrupt_manager.add_handler(TimeoutInterruptHandler(timeout_seconds=30.0))

# Run agent - handles Ctrl+C, timeouts, budget limits
try:
    result = await agent.run_autonomous(task="Analyze dataset")
except InterruptedError as e:
    checkpoint_id = e.reason.metadata.get("checkpoint_id")
```

**Key Features:** USER/SYSTEM/PROGRAMMATIC interrupt sources, GRACEFUL/IMMEDIATE shutdown modes, automatic checkpoint preservation

**Handlers:** TimeoutInterruptHandler, BudgetInterruptHandler, ResourceInterruptHandler, custom via BaseInterruptHandler

**Examples:** `examples/autonomy/interrupts/` (ctrl_c, timeout, budget)

### Checkpoint System (State Persistence)

**Save/load/fork agent state with automatic checkpointing:**

```python
from kaizen.core.autonomy.state import StateManager, AgentState, FilesystemStorage

# Setup state manager
state_manager = StateManager(
    storage=FilesystemStorage("./checkpoints"),
    checkpoint_frequency=10,        # Every 10 steps
    retention_count=100             # Keep last 100
)

# Create state
agent_state = AgentState(
    agent_id="my_agent",
    step_number=0,
    conversation_history=[],
    memory_contents={},
    budget_spent_usd=0.0
)

# Save/load/fork operations
checkpoint_id = await state_manager.save_checkpoint(agent_state)
restored = await state_manager.load_checkpoint(checkpoint_id)
latest = await state_manager.resume_from_latest("my_agent")
forked = await state_manager.fork_from_checkpoint(checkpoint_id)
```

**Key Features:** Auto-checkpointing every N steps, resume from latest, fork independent branches, hook integration

**Location:** `kaizen.core.autonomy.state`

### 3-Tier Memory System (Hot/Warm/Cold)

**Hierarchical storage with automatic tier promotion/demotion:**

```python
from kaizen.memory.tiers import HotMemoryTier
from kaizen.memory.backends import DataFlowBackend
from dataflow import DataFlow

# Hot tier (in-memory, < 1ms)
hot_tier = HotMemoryTier(max_size=1000, eviction_policy="lru")
await hot_tier.put("key", value, ttl=300)
data = await hot_tier.get("key")

# Cold tier (DataFlow backend, < 100ms)
db = DataFlow(database_url="postgresql://...")

@db.model
class ConversationMessage:
    id: str
    conversation_id: str
    content: str

backend = DataFlowBackend(db, model_name="ConversationMessage")
backend.save_turn("session_123", {"user": "Hello", "agent": "Hi"})
turns = backend.load_turns("session_123", limit=10)
```

**Key Features:** Hot (<1ms), Warm (<10ms), Cold (<100ms) tiers, LRU/LFU/FIFO eviction, automatic promotion/demotion

**Location:** `kaizen.memory.tiers`, `kaizen.memory.backends`

### Planning Agents (Plan → Execute patterns)

**Agents with explicit planning phases:**

```python
from kaizen.agents import PlanningAgent, PEVAgent

# PlanningAgent: Plan → Validate → Execute
planning_agent = PlanningAgent(
    llm_provider="openai",
    model="gpt-4",
    max_plan_steps=10,
    validation_mode="strict"
)
result = planning_agent.run(task="Create research report")

# PEVAgent: Plan → Execute → Verify → Refine loop
pev_agent = PEVAgent(
    llm_provider="openai",
    model="gpt-4",
    max_iterations=10,
    verification_strictness="strict"
)
result = pev_agent.run(task="Generate and verify code")
```

**Key Features:** Explicit planning, validation, iterative refinement, error recovery

**Location:** `kaizen.agents.specialized.planning`, `kaizen.agents.specialized.pev`

### Meta-Controller Routing

**Intelligent agent routing via A2A capability matching:**

```python
from kaizen.orchestration.pipeline import Pipeline

# Semantic routing (best-fit selection)
pipeline = Pipeline.router(
    agents=[code_expert, data_expert, writing_expert],
    routing_strategy="semantic",  # or "round-robin", "random"
    error_handling="graceful"
)

# Auto-routes to best agent based on task
result = pipeline.run(
    task="Analyze sales data and create visualization"
)
# Automatically selects data_expert based on A2A capability match
```

**Key Features:** A2A capability matching, multiple routing strategies, graceful fallback

**Location:** `kaizen.orchestration.patterns.meta_controller`

### Hooks Security (Production)

**Production-ready security controls for hooks system:**

```python
from kaizen.core.autonomy.hooks.security import (
    AuthorizedHookManager,
    IsolatedHookManager,
    ResourceLimits,
    HookPrincipal,
    HookPermission,
)

# Authorization (RBAC)
admin_principal = HookPrincipal(
    identity="admin@company.com",
    permissions={HookPermission.REGISTER_HOOK, HookPermission.TRIGGER_HOOKS}
)

hook_manager = AuthorizedHookManager()
await hook_manager.register(
    event=HookEvent.POST_AGENT_LOOP,
    handler=my_hook,
    principal=admin_principal
)

# Process isolation with resource limits
limits = ResourceLimits(max_memory_mb=100, max_cpu_seconds=5)
isolated_manager = IsolatedHookManager(limits=limits, enable_isolation=True)

# Hooks execute in separate processes with memory/CPU constraints
# Prevents malicious hooks from crashing agent or exhausting resources
```

**Additional Security Features:**
- **Secure Loading**: Ed25519 signature verification for filesystem-discovered hooks
- **Metrics Auth**: API key authentication + IP whitelisting for metrics endpoints
- **Data Redaction**: Auto-redact API keys, passwords, PII from logs
- **Rate Limiting**: Prevent DoS via hook registration flooding
- **Input Validation**: Block code injection, XSS, path traversal attacks
- **Audit Trail**: Comprehensive logging for forensic analysis

**Compliance**: PCI DSS 4.0, HIPAA § 164.312, GDPR Article 32, SOC2

**Location**: `kaizen.core.autonomy.hooks.security`

## ⚠️ Common Mistakes to Avoid

### 1. Wrong Vision Agent Parameters
```python
# ❌ WRONG: Using 'prompt' instead of 'question'
result = agent.analyze(image=img, prompt="What is this?")

# ❌ WRONG: Using 'response' key
answer = result['response']

# ❌ WRONG: Passing base64 string
result = agent.analyze(image=base64_string, question="...")

# ✅ CORRECT: Use 'question' parameter and 'answer' key
result = agent.analyze(image="/path/to/image.png", question="What is this?")
answer = result['answer']
```

### 2. Missing API Keys
```python
# ❌ WRONG: Not loading .env
agent = SimpleQAAgent(QAConfig(llm_provider="openai"))

# ✅ CORRECT: Load .env first
from dotenv import load_dotenv
load_dotenv()  # Loads OPENAI_API_KEY from .env
agent = SimpleQAAgent(QAConfig(llm_provider="openai"))
```

### 3. Incorrect Configuration Pattern
```python
# ❌ WRONG: Using BaseAgentConfig directly
config = BaseAgentConfig(model="gpt-4")  # Don't do this!

# ✅ CORRECT: Use domain config (auto-converted to BaseAgentConfig)
config = QAConfig(model="gpt-4")
agent = SimpleQAAgent(config)  # Auto-extraction happens here
```

## 🏗️ Architecture

### Framework Position
```
┌─────────────────────────────────────────────────────────────┐
│                    Kaizen Framework                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  BaseAgent  │  │ Multi-Modal │  │  Multi-     │        │
│  │ Architecture│  │  Processing │  │  Agent      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          Kailash Core SDK                           │  │
│  │  WorkflowBuilder │ LocalRuntime │ 110+ Nodes       │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **BaseAgent** (`src/kaizen/core/base_agent.py`)
   - Unified agent system with lazy initialization
   - Auto-generates A2A capability cards (`to_a2a_card()`)
   - Strategy pattern execution (AsyncSingleShotStrategy default)
   - Production-ready with 100% test coverage

2. **Signature Programming** (`src/kaizen/signatures/`)
   - Type-safe I/O with InputField/OutputField
   - SignatureParser, SignatureCompiler, SignatureValidator
   - Enterprise extensions, Multi-modal support
   - 107 exported components

3. **Multi-Modal Processing** (`src/kaizen/agents/`)
   - Vision: Ollama (llava, bakllava) + OpenAI GPT-4V
   - Audio: Whisper transcription
   - Unified orchestration with MultiModalAgent
   - Real infrastructure testing (NO MOCKING)

4. **Multi-Agent Coordination** (`src/kaizen/agents/coordination/`)
   - Google A2A protocol integration (100% compliant)
   - SupervisorWorkerPattern with semantic matching (14/14 tests)
   - 4 additional patterns: Consensus, Debate, Sequential, Handoff
   - Automatic capability discovery, no hardcoded selection

## 🧪 Testing

### 3-Tier Testing Strategy
1. **Tier 1 (Unit)**: Fast, mocked LLM providers
2. **Tier 2 (Integration)**: Real Ollama inference (local, free)
3. **Tier 3 (E2E)**: Real OpenAI inference (paid API, budget-controlled)

**CRITICAL**: NO MOCKING in Tiers 2-3 (real infrastructure only)

### Test Execution
```bash
# Run all tests
pytest

# Run Tier 1 only (fast, mocked)
pytest tests/unit/

# Run Tier 2 (Ollama integration - requires Ollama running)
pytest tests/integration/test_ollama_validation.py

# Run Tier 3 (OpenAI - requires API key in .env)
pytest tests/integration/test_multi_modal_integration.py
```

## 🚦 Production Deployment

### Environment Configuration
```bash
# Required API Keys (.env)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional Configuration
KAIZEN_LOG_LEVEL=INFO
KAIZEN_PERFORMANCE_TRACKING=true
KAIZEN_ERROR_HANDLING=true
```

### Integration with DataFlow
```python
from dataflow import DataFlow
from kaizen.agents import SimpleQAAgent

# DataFlow for database operations
db = DataFlow()

@db.model
class QASession:
    question: str
    answer: str
    confidence: float

# Kaizen for AI processing
agent = SimpleQAAgent(QAConfig())
result = agent.ask("What is the capital of France?")

# Store in database via workflow
workflow = WorkflowBuilder()
workflow.add_node("QASessionCreateNode", "store", {
    "question": result["question"],
    "answer": result["answer"],
    "confidence": result["confidence"]
})
```

### Integration with Nexus
```python
from nexus import Nexus
from kaizen.agents import SimpleQAAgent

# Create Nexus platform
nexus = Nexus(
    title="AI Q&A Platform",
    enable_api=True,
    enable_cli=True,
    enable_mcp=True
)

# Deploy Kaizen agent
agent = SimpleQAAgent(QAConfig())
agent_workflow = agent.to_workflow()
nexus.register("qa_agent", agent_workflow.build())

# Available on all channels:
# - API: POST /workflows/qa_agent
# - CLI: nexus run qa_agent
# - MCP: qa_agent tool for AI assistants
```

## 💡 Tips

1. **API Keys in .env**: Always check `.env` file before asking user for API keys
2. **Use Actual Imports**: Import from `kaizen.agents`, not conceptual packages
3. **BaseAgent Pattern**: All custom agents should extend `BaseAgent`
4. **Config Auto-Extraction**: Use domain configs, BaseAgent auto-converts
5. **Multi-Modal API**: Use 'question' parameter and 'answer' key (not 'prompt'/'response')
6. **Memory Opt-In**: Set `max_turns` in config to enable BufferMemory
7. **Real Infrastructure**: Test with Ollama (Tier 2) before OpenAI (Tier 3)

## 🔗 Related Documentation

- **[Main Kaizen Docs](../CLAUDE.md)** - Complete framework documentation
- **[Kaizen Examples](../examples/)** - 40+ working implementations
- **[Hooks System Guide](guides/hooks-system-guide.md)** - Event-driven observability
- **[API Reference](reference/api-reference.md)** - Complete API documentation

---

**Framework**: Kaizen AI Framework built on Kailash Core SDK
