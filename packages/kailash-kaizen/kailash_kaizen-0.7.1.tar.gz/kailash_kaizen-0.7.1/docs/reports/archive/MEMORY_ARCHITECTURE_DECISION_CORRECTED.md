# Memory Architecture Decision - CORRECTED

**Date**: 2025-10-02
**Status**: APPROVED
**Critical Correction**: DO NOT integrate LangChain directly - implement Kaizen's own memory patterns

---

## Executive Summary

**Original Error**: Proposed integrating LangChain's memory modules directly

**Critical Findings**:
1. ❌ **LangChain memory is DEPRECATED** (since 0.3.1, removal in 1.0.0)
2. ❌ **LangChain has NO global/shared memory** - only individual agent memory
3. ❌ **ReadOnlySharedMemory is NOT shared memory** - just a read-only wrapper
4. ✅ **Previous decision was correct**: Implement Kaizen's own versions, don't integrate DSPy/LangChain

**Corrected Approach**: Implement Kaizen's own memory patterns **INSPIRED BY** LangChain concepts, not using LangChain

---

## LangChain Memory Analysis (Source Code Review)

### What LangChain Provides

**File**: `/Users/esperie/repos/projects/langchain/libs/core/langchain_core/memory.py`

**Status**: **DEPRECATED** since 0.3.1, removal in 1.0.0
```python
@deprecated(
    since="0.3.3",
    removal="1.0.0",
    message=(
        "Please see the migration guide at: "
        "https://python.langchain.com/docs/versions/migrating_memory/"
    ),
)
class BaseMemory(Serializable, ABC):
    """Abstract base class for memory in Chains.

    DO NOT USE THIS ABSTRACTION FOR NEW CODE.
    """
```

**Architecture**:
```python
# Base hierarchy
BaseMemory
└── BaseChatMemory
    ├── ConversationBufferMemory (stores full conversation)
    ├── ConversationSummaryMemory (LLM-summarized history)
    ├── ConversationTokenBufferMemory (token-limited buffer)
    ├── ConversationEntityMemory (entity extraction)
    └── VectorStoreRetrieverMemory (semantic search)

# Storage backends (ChatMessageHistory)
BaseChatMessageHistory
├── InMemoryChatMessageHistory
├── RedisChatMessageHistory
├── MongoDBChatMessageHistory
├── PostgresChatMessageHistory
└── ... (15+ storage backends)
```

**Key Interface**:
```python
class BaseMemory(ABC):
    @abstractmethod
    def load_memory_variables(self, inputs: Dict) -> Dict:
        """Load relevant context from memory."""
        pass

    @abstractmethod
    def save_context(self, inputs: Dict, outputs: Dict) -> None:
        """Save conversation turn to memory."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear memory contents."""
        pass
```

### What LangChain Does NOT Provide

**ReadOnlySharedMemory** is NOT shared memory:
```python
# File: /Users/esperie/repos/projects/langchain/libs/langchain/langchain/memory/readonly.py
class ReadOnlySharedMemory(BaseMemory):
    """Memory wrapper that is read-only and cannot be changed."""

    memory: BaseMemory  # Wraps a SINGLE agent's memory

    def save_context(self, inputs, outputs) -> None:
        """Nothing should be saved or changed."""  # Just blocks writes
```

**Analysis**:
- ❌ NOT multi-agent shared memory
- ❌ NOT global memory pool
- ❌ Just a read-only wrapper around individual memory
- ❌ No agent-to-agent communication

**Conclusion**: LangChain has **ZERO shared/global memory capabilities**

---

## Corrected Memory Architecture for Kaizen

### Two Independent Memory Systems

Kaizen needs **TWO SEPARATE** memory systems (not either/or):

**1. Individual Agent Memory** (inspired by LangChain patterns)
- Purpose: Conversation context, history, facts
- Scope: Single agent
- Storage: In-memory, Redis, PostgreSQL, etc.
- Patterns: Buffer, Summary, Vector, Knowledge Graph

**2. Multi-Agent Shared Memory** (inspired by Core SDK's A2A)
- Purpose: Multi-agent collaboration, insight sharing
- Scope: Shared across agents
- Storage: Shared memory pool with attention filtering
- Patterns: Broadcast, filter by tags/importance/recency

### Implementation Strategy: Kaizen's Own Memory Patterns

**DO NOT**:
- ❌ `from langchain.memory import ConversationBufferMemory`
- ❌ Direct integration of LangChain modules
- ❌ Dependency on deprecated code

**DO**:
- ✅ Implement Kaizen's own memory classes
- ✅ Use LangChain's **concepts** as inspiration
- ✅ Adapt patterns to Kaizen's architecture
- ✅ Own the code for independent evolution

---

## Implementation Plan

### Phase 1: Individual Agent Memory (Week 1-2)

**Kaizen Memory Patterns** (inspired by LangChain):

```python
# src/kaizen/memory/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class KaizenMemory(ABC):
    """
    Base class for Kaizen's memory system.

    Inspired by LangChain's BaseMemory but:
    - Not deprecated
    - Adapted to Kaizen's agent architecture
    - Supports both sync and async
    - Integrated with BaseAgent
    """

    @abstractmethod
    def load_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant context from memory for agent execution."""
        pass

    @abstractmethod
    async def aload_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async load context from memory."""
        pass

    @abstractmethod
    def save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save a conversation turn to memory."""
        pass

    @abstractmethod
    async def asave_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Async save conversation turn."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all memory contents."""
        pass

    @abstractmethod
    async def aclear(self) -> None:
        """Async clear memory."""
        pass
```

**Memory Implementations**:

**1. BufferMemory** (inspired by ConversationBufferMemory):
```python
# src/kaizen/memory/buffer.py
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ConversationTurn:
    """Single conversation turn."""
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = None

class BufferMemory(KaizenMemory):
    """
    Stores full conversation history in memory.

    Inspired by LangChain's ConversationBufferMemory but:
    - Kaizen-native implementation
    - Structured conversation turns
    - Metadata support
    - Memory limits
    """

    def __init__(self, max_turns: int = 100):
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []

    def load_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load recent conversation history."""
        if not self.turns:
            return {"history": []}

        # Format conversation history
        history = []
        for turn in self.turns[-self.max_turns:]:
            history.append({
                "human": turn.inputs,
                "ai": turn.outputs,
                "timestamp": turn.timestamp.isoformat()
            })

        return {"history": history}

    async def aload_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async version."""
        return self.load_context(inputs)

    def save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation turn."""
        turn = ConversationTurn(
            inputs=inputs,
            outputs=outputs,
            timestamp=datetime.now()
        )
        self.turns.append(turn)

        # Limit memory size
        if len(self.turns) > self.max_turns * 2:
            self.turns = self.turns[-self.max_turns:]

    async def asave_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Async version."""
        self.save_turn(inputs, outputs)

    def clear(self) -> None:
        """Clear all turns."""
        self.turns.clear()

    async def aclear(self) -> None:
        """Async clear."""
        self.clear()
```

**2. SummaryMemory** (inspired by ConversationSummaryMemory):
```python
# src/kaizen/memory/summary.py
from kaizen.memory.base import KaizenMemory
from kaizen.core.base_agent import BaseAgent

class SummaryMemory(KaizenMemory):
    """
    Stores LLM-generated summaries of conversation history.

    Inspired by LangChain's ConversationSummaryMemory but:
    - Uses Kaizen agents for summarization
    - Adaptive summarization based on conversation length
    - Preserves recent turns verbatim
    """

    def __init__(
        self,
        summarizer_agent: BaseAgent,
        max_recent_turns: int = 5,
        summary_trigger: int = 10
    ):
        self.summarizer_agent = summarizer_agent
        self.max_recent_turns = max_recent_turns
        self.summary_trigger = summary_trigger

        self.summary: str = ""
        self.recent_turns: List[ConversationTurn] = []

    def load_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load summary + recent turns."""
        context = {
            "summary": self.summary,
            "recent_turns": [
                {"human": turn.inputs, "ai": turn.outputs}
                for turn in self.recent_turns
            ]
        }
        return context

    def save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save turn and trigger summarization if needed."""
        turn = ConversationTurn(
            inputs=inputs,
            outputs=outputs,
            timestamp=datetime.now()
        )
        self.recent_turns.append(turn)

        # Trigger summarization when threshold reached
        if len(self.recent_turns) >= self.summary_trigger:
            self._summarize_recent_turns()

    def _summarize_recent_turns(self) -> None:
        """Use LLM to summarize recent turns."""
        # Prepare turns for summarization
        turns_text = "\n".join([
            f"Human: {turn.inputs}\nAI: {turn.outputs}"
            for turn in self.recent_turns
        ])

        # Generate summary using Kaizen agent
        result = self.summarizer_agent.run(
            previous_summary=self.summary,
            new_turns=turns_text
        )

        # Update summary
        self.summary = result.get("updated_summary", "")

        # Keep only most recent turns
        self.recent_turns = self.recent_turns[-self.max_recent_turns:]
```

**3. VectorMemory** (inspired by VectorStoreRetrieverMemory):
```python
# src/kaizen/memory/vector.py
from kaizen.memory.base import KaizenMemory
from kaizen.retrieval.vector_store import SimpleVectorStore

class VectorMemory(KaizenMemory):
    """
    Stores conversation turns in vector store for semantic retrieval.

    Inspired by LangChain's VectorStoreRetrieverMemory but:
    - Uses Kaizen's SimpleVectorStore
    - Semantic search over conversation history
    - Retrieves most relevant past conversations
    """

    def __init__(
        self,
        vector_store: SimpleVectorStore = None,
        top_k: int = 3
    ):
        self.vector_store = vector_store or SimpleVectorStore()
        self.top_k = top_k

    def load_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load semantically similar past conversations."""
        # Extract query from inputs
        query = inputs.get("question") or inputs.get("message") or str(inputs)

        # Search vector store for similar conversations
        similar_turns = self.vector_store.search(query, top_k=self.top_k)

        # Format as context
        context = {
            "relevant_history": [
                {
                    "conversation": turn["text"],
                    "similarity": turn["score"]
                }
                for turn in similar_turns
            ]
        }
        return context

    def save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save turn to vector store."""
        # Format turn as text
        turn_text = f"Human: {inputs}\nAI: {outputs}"

        # Add to vector store
        self.vector_store.add_documents([{
            "text": turn_text,
            "metadata": {
                "inputs": inputs,
                "outputs": outputs,
                "timestamp": datetime.now().isoformat()
            }
        }])
```

**4. KnowledgeGraphMemory** (inspired by ConversationKGMemory):
```python
# src/kaizen/memory/knowledge_graph.py
from kaizen.memory.base import KaizenMemory
from typing import Dict, Any, Set, Tuple

class KnowledgeGraphMemory(KaizenMemory):
    """
    Extracts entities and relationships from conversations.

    Inspired by LangChain's ConversationKGMemory but:
    - Uses Kaizen agents for entity extraction
    - Graph structure for relationships
    - Semantic queries over knowledge
    """

    def __init__(self, entity_extractor_agent: BaseAgent):
        self.entity_extractor = entity_extractor_agent
        self.entities: Dict[str, Dict[str, Any]] = {}  # entity_id -> properties
        self.relationships: Set[Tuple[str, str, str]] = set()  # (entity1, relation, entity2)

    def load_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant entities and relationships."""
        # Extract entities mentioned in current input
        mentioned_entities = self._extract_entities(inputs)

        # Find related entities via relationships
        related_entities = set()
        for entity in mentioned_entities:
            related_entities.update(self._get_related_entities(entity))

        # Format as context
        context = {
            "known_entities": {
                entity_id: self.entities[entity_id]
                for entity_id in mentioned_entities | related_entities
                if entity_id in self.entities
            },
            "relationships": [
                {"from": e1, "relation": rel, "to": e2}
                for (e1, rel, e2) in self.relationships
                if e1 in (mentioned_entities | related_entities) or e2 in (mentioned_entities | related_entities)
            ]
        }
        return context

    def save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Extract and save entities/relationships."""
        # Use LLM to extract entities
        extraction_result = self.entity_extractor.run(
            text=f"{inputs}\n{outputs}"
        )

        # Update knowledge graph
        for entity in extraction_result.get("entities", []):
            self.entities[entity["id"]] = entity

        for relationship in extraction_result.get("relationships", []):
            self.relationships.add((
                relationship["from"],
                relationship["type"],
                relationship["to"]
            ))

    def _get_related_entities(self, entity_id: str) -> Set[str]:
        """Find entities related to given entity."""
        related = set()
        for (e1, rel, e2) in self.relationships:
            if e1 == entity_id:
                related.add(e2)
            elif e2 == entity_id:
                related.add(e1)
        return related
```

### Phase 2: Multi-Agent Shared Memory (Week 2-3)

**SharedMemoryPool** (inspired by Core SDK's A2A):

```python
# src/kaizen/memory/shared_memory.py
from typing import Dict, Any, List, Set
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class SharedInsight:
    """
    Insight shared between agents.

    Similar to Core SDK's A2A memory but adapted to Kaizen.
    """
    insight_id: str
    agent_id: str
    content: str
    tags: List[str]
    importance: float  # 0.0 to 1.0
    segment: str  # Topic/category
    timestamp: float
    metadata: Dict[str, Any] = None

class SharedMemoryPool:
    """
    Shared memory pool for multi-agent collaboration.

    Inspired by Core SDK's SharedMemoryPoolNode but:
    - Kaizen-native implementation
    - Integrated with BaseAgent
    - Attention-based filtering
    - Automatic insight decay
    """

    def __init__(self, max_insights: int = 1000, decay_hours: float = 24.0):
        self.max_insights = max_insights
        self.decay_hours = decay_hours

        self.insights: List[SharedInsight] = []
        self.tag_index: Dict[str, List[SharedInsight]] = {}
        self.segment_index: Dict[str, List[SharedInsight]] = {}

    def write_insight(
        self,
        agent_id: str,
        content: str,
        tags: List[str],
        importance: float = 0.5,
        segment: str = "general",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Agent writes insight to shared pool."""
        import uuid

        insight = SharedInsight(
            insight_id=str(uuid.uuid4()),
            agent_id=agent_id,
            content=content,
            tags=tags,
            importance=importance,
            segment=segment,
            timestamp=time.time(),
            metadata=metadata or {}
        )

        # Add to main list
        self.insights.append(insight)

        # Update indexes
        for tag in tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(insight)

        if segment not in self.segment_index:
            self.segment_index[segment] = []
        self.segment_index[segment].append(insight)

        # Cleanup old insights
        self._cleanup_insights()

        return insight.insight_id

    def read_relevant(
        self,
        agent_id: str,
        attention_filter: Dict[str, Any] = None
    ) -> List[SharedInsight]:
        """
        Agent reads relevant insights from pool.

        Attention filter options:
        - tags: List[str] - Filter by tags
        - importance_threshold: float - Minimum importance
        - segments: List[str] - Filter by segments
        - exclude_own: bool - Exclude own insights
        - max_age_hours: float - Maximum age
        - max_results: int - Limit results
        """
        filter_config = attention_filter or {}

        # Start with all insights
        candidates = self.insights.copy()

        # Filter by tags
        if "tags" in filter_config:
            required_tags = set(filter_config["tags"])
            candidates = [
                insight for insight in candidates
                if any(tag in required_tags for tag in insight.tags)
            ]

        # Filter by importance
        if "importance_threshold" in filter_config:
            threshold = filter_config["importance_threshold"]
            candidates = [
                insight for insight in candidates
                if insight.importance >= threshold
            ]

        # Filter by segments
        if "segments" in filter_config:
            segments = set(filter_config["segments"])
            candidates = [
                insight for insight in candidates
                if insight.segment in segments
            ]

        # Exclude own insights
        if filter_config.get("exclude_own", False):
            candidates = [
                insight for insight in candidates
                if insight.agent_id != agent_id
            ]

        # Filter by age
        if "max_age_hours" in filter_config:
            max_age_seconds = filter_config["max_age_hours"] * 3600
            cutoff_time = time.time() - max_age_seconds
            candidates = [
                insight for insight in candidates
                if insight.timestamp >= cutoff_time
            ]

        # Sort by importance (descending) and recency
        candidates.sort(
            key=lambda i: (i.importance, i.timestamp),
            reverse=True
        )

        # Limit results
        max_results = filter_config.get("max_results", 10)
        return candidates[:max_results]

    def _cleanup_insights(self) -> None:
        """Remove old/low-importance insights."""
        current_time = time.time()
        decay_seconds = self.decay_hours * 3600

        # Remove insights older than decay period
        self.insights = [
            insight for insight in self.insights
            if (current_time - insight.timestamp) < decay_seconds
        ]

        # If still over limit, remove lowest importance insights
        if len(self.insights) > self.max_insights:
            self.insights.sort(key=lambda i: i.importance, reverse=True)
            removed = self.insights[self.max_insights:]
            self.insights = self.insights[:self.max_insights]

            # Rebuild indexes
            self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """Rebuild tag and segment indexes."""
        self.tag_index.clear()
        self.segment_index.clear()

        for insight in self.insights:
            for tag in insight.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(insight)

            if insight.segment not in self.segment_index:
                self.segment_index[insight.segment] = []
            self.segment_index[insight.segment].append(insight)
```

### Phase 3: BaseAgent Integration (Week 3)

**Update BaseAgent to support both memory types**:

```python
# src/kaizen/core/base_agent.py (updated)
from kaizen.memory.base import KaizenMemory
from kaizen.memory.shared_memory import SharedMemoryPool

class BaseAgent(Node):
    def __init__(
        self,
        config: BaseAgentConfig,
        signature: Optional[Signature] = None,
        strategy: Optional[Any] = None,
        memory: Optional[KaizenMemory] = None,  # Individual memory
        shared_memory: Optional[SharedMemoryPool] = None,  # Multi-agent memory
        **kwargs
    ):
        # ... existing init ...

        # Memory systems
        self.memory = memory  # Individual agent memory
        self.shared_memory = shared_memory  # Multi-agent shared memory

    def run(self, **inputs) -> Dict[str, Any]:
        """Execute agent with memory integration."""
        try:
            # Pre-execution: Load memory context
            if self.memory:
                memory_context = self.memory.load_context(inputs)
                inputs = {**inputs, **memory_context}

            # Pre-execution: Load shared insights
            if self.shared_memory and self.config.attention_filter:
                shared_context = self.shared_memory.read_relevant(
                    agent_id=self.config.agent_id,
                    attention_filter=self.config.attention_filter
                )
                inputs["shared_insights"] = shared_context

            # Execute via strategy
            result = self.strategy.execute(self, inputs)

            # Post-execution: Save to memory
            if self.memory:
                self.memory.save_turn(inputs, result)

            # Post-execution: Share insights
            if self.shared_memory:
                insights = self._extract_insights(result)
                for insight in insights:
                    self.shared_memory.write_insight(
                        agent_id=self.config.agent_id,
                        content=insight["content"],
                        tags=insight.get("tags", []),
                        importance=insight.get("importance", 0.5),
                        segment=insight.get("segment", "general")
                    )

            return result

        except Exception as error:
            return self._handle_error(error, {'inputs': inputs})

    def _extract_insights(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract shareable insights from agent result."""
        # Simple heuristic for now - override in subclasses
        insights = []

        # Check if result has explicit insights
        if "insights" in result:
            return result["insights"]

        # Default: treat main output as single insight
        if "answer" in result or "response" in result:
            insights.append({
                "content": result.get("answer") or result.get("response"),
                "tags": [self.config.agent_id],
                "importance": 0.6,
                "segment": "general"
            })

        return insights
```

### Phase 4: Usage Examples (Week 4)

**Example 1: Individual Agent with Buffer Memory**:
```python
from kaizen.core.base_agent import BaseAgent
from kaizen.core.config import BaseAgentConfig
from kaizen.strategies import AsyncSingleShotStrategy
from kaizen.memory import BufferMemory

# Create agent with conversation memory
config = BaseAgentConfig(
    llm_provider="openai",
    model="gpt-4",
    temperature=0.1
)

agent = BaseAgent(
    config=config,
    signature=QASignature(),
    strategy=AsyncSingleShotStrategy(),
    memory=BufferMemory(max_turns=10)
)

# Conversation with memory
result1 = agent.run(question="My name is Alice")
# Agent: "Nice to meet you, Alice!"

result2 = agent.run(question="What's my name?")
# Agent: "Your name is Alice!" (retrieved from memory)
```

**Example 2: Multi-Agent with Shared Memory**:
```python
from kaizen.memory import SharedMemoryPool

# Create shared memory pool
shared_pool = SharedMemoryPool(max_insights=1000, decay_hours=24)

# Agent 1: Researcher
researcher = BaseAgent(
    config=BaseAgentConfig(
        agent_id="researcher_001",
        attention_filter={"tags": ["research", "data"]}
    ),
    strategy=AsyncSingleShotStrategy(),
    shared_memory=shared_pool
)

# Agent 2: Analyst
analyst = BaseAgent(
    config=BaseAgentConfig(
        agent_id="analyst_001",
        attention_filter={"tags": ["analysis", "data"], "importance_threshold": 0.7}
    ),
    strategy=AsyncSingleShotStrategy(),
    shared_memory=shared_pool
)

# Agent 1 performs research and shares insights
research_result = researcher.run(
    task="Research AI trends in 2025"
)
# Automatically writes insights to shared_pool

# Agent 2 reads shared insights and performs analysis
analysis_result = analyst.run(
    task="Analyze the research findings"
)
# Automatically reads relevant insights from shared_pool
```

**Example 3: Agent with Both Memory Types**:
```python
from kaizen.memory import VectorMemory, SharedMemoryPool

# Individual memory for conversation context
vector_memory = VectorMemory(top_k=5)

# Shared memory for team collaboration
team_memory = SharedMemoryPool()

# Create agent with both
agent = BaseAgent(
    config=config,
    strategy=AsyncSingleShotStrategy(),
    memory=vector_memory,  # Individual: semantic search over past conversations
    shared_memory=team_memory  # Multi-agent: collaborate with team
)

# Agent maintains individual conversation context
# AND participates in team knowledge sharing
result = agent.run(question="What did the team find about AI trends?")
# Uses both: vector_memory (own conversations) + team_memory (team insights)
```

---

## Summary

### What We're NOT Doing ❌

1. ❌ Integrating LangChain's memory modules
2. ❌ Using deprecated code
3. ❌ Depending on external memory abstractions
4. ❌ Using LangChain's "shared memory" (doesn't exist)

### What We're Doing ✅

1. ✅ Implementing Kaizen's own memory patterns
2. ✅ Using LangChain's **concepts** as inspiration
3. ✅ Full control and independent evolution
4. ✅ Two separate memory systems:
   - Individual agent memory (buffer, summary, vector, KG)
   - Multi-agent shared memory (A2A collaboration)

### Implementation Timeline

- **Week 1**: BufferMemory, SummaryMemory (individual memory)
- **Week 2**: VectorMemory, KnowledgeGraphMemory (advanced individual memory)
- **Week 2-3**: SharedMemoryPool (multi-agent collaboration)
- **Week 3**: BaseAgent integration
- **Week 4**: Examples and testing

### Code Ownership

**Kaizen owns ALL memory code**:
- `src/kaizen/memory/base.py` - Base memory interface
- `src/kaizen/memory/buffer.py` - Buffer memory
- `src/kaizen/memory/summary.py` - Summary memory
- `src/kaizen/memory/vector.py` - Vector memory
- `src/kaizen/memory/knowledge_graph.py` - KG memory
- `src/kaizen/memory/shared_memory.py` - Multi-agent shared memory

**No LangChain dependencies** ✅

---

## Approval Status

- ✅ **APPROVED**: Implement Kaizen's own memory patterns
- ✅ **REJECTED**: Direct LangChain integration
- ✅ **CONFIRMED**: Two independent memory systems needed
- ✅ **ALIGNED**: With previous decision to own implementations

**Next Steps**: Begin implementation of Phase 1 (BufferMemory + SummaryMemory)
