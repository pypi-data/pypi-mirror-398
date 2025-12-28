# Phase 1: Agent Method Standardization Audit

**Generated**: 2025-10-26
**Auditor**: kaizen-specialist
**Scope**: All 25 Kaizen agents across specialized/, autonomous/, multi_modal/, and coordination/

---

## Executive Summary

**Total Agents Audited**: 25 (11 specialized + 3 multi-modal + 6 coordination + 5 patterns/autonomous)

**Method Standardization Status**:
- ✅ **All agents inherit `.run()` from BaseAgent** - No implementation needed
- ⚠️ **11 specialized agents have deprecated domain methods** - Need aliasing to `.run()`
- ⚠️ **3 multi-modal agents have domain methods** - Need aliasing to `.run()`
- ✅ **6 coordination patterns are NOT agents** - No changes needed (composition patterns)

**Complexity Assessment**:
- **Simple (Day 1)**: 11 specialized agents - straightforward method aliasing
- **Moderate (Day 2)**: 3 multi-modal agents - method aliasing + optional features

---

## Detailed Audit by Category

### 1. Specialized Agents (11 total)

All inherit `.run()` from BaseAgent. Need to add aliases for domain-specific methods.

#### 1.1 SimpleQAAgent
- **File**: `src/kaizen/agents/specialized/simple_qa.py`
- **Current Methods**:
  - `.ask(question, context, session_id)` → Line 217-267
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.ask()` → `.run()`
  - Keep existing `.ask()` for backward compatibility
  - Document both in docstring
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.2 ChainOfThoughtAgent
- **File**: `src/kaizen/agents/specialized/chain_of_thought.py`
- **Current Methods**:
  - `.solve_problem(problem, context)` → Line 238-294
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.solve_problem()` → `.run()`
  - Keep existing `.solve_problem()` for backward compatibility
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.3 StreamingChatAgent
- **File**: `src/kaizen/agents/specialized/streaming_chat.py`
- **Current Methods**:
  - `.stream(message)` → Line 235-265 (async iterator)
  - `.chat(message)` → Line 267-283 (sync)
  - `.chat_async(message)` → Line 285-301 (async)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.chat()` → `.run()`
  - Add alias: `.chat_async()` → `.run_async()`
  - Keep `.stream()` as is (different pattern - async iterator)
- **Complexity**: Simple
- **Estimated Time**: 15 minutes

#### 1.4 SelfReflectionAgent
- **File**: `src/kaizen/agents/specialized/self_reflection.py`
- **Current Methods**:
  - `.reflect(task)` → Line 253-288
  - `.reflect_async(task)` → Line 290-325
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.reflect()` → `.run()`
  - Add alias: `.reflect_async()` → `.run_async()`
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.5 MemoryAgent
- **File**: `src/kaizen/agents/specialized/memory_agent.py`
- **Current Methods**:
  - `.chat(message, session_id)` → Line 279-325
  - `.clear_memory(session_id)` → Line 327-340 (utility)
  - `.get_conversation_count(session_id)` → Line 342-360 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.chat()` → `.run()`
  - Keep utility methods (`.clear_memory()`, `.get_conversation_count()`) as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.6 BatchProcessingAgent
- **File**: `src/kaizen/agents/specialized/batch_processing.py`
- **Current Methods**:
  - `.process_batch(batch)` → Line 224-251 (async)
  - `.process_single(prompt)` → Line 253-269 (sync)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.process_batch()` → `.run_batch()` (new method)
  - Add alias: `.process_single()` → `.run()`
- **Complexity**: Simple
- **Estimated Time**: 15 minutes

#### 1.7 CodeGenerationAgent
- **File**: `src/kaizen/agents/specialized/code_generation.py`
- **Current Methods**:
  - `.generate_code(task_description, language)` → Line 326-383
  - `.generate_tests(code, language)` → Line 385-422 (utility)
  - `.explain_code(code, language)` → Line 424-455 (utility)
  - `.refactor_code(code, refactoring_goal, language)` → Line 457-494 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.generate_code()` → `.run()`
  - Keep utility methods (`.generate_tests()`, `.explain_code()`, `.refactor_code()`) as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.8 HumanApprovalAgent
- **File**: `src/kaizen/agents/specialized/human_approval.py`
- **Current Methods**:
  - `.decide(prompt)` → Line 220-263 (async)
  - `.decide_sync(prompt)` → Line 265-282 (sync)
  - `.get_approval_history()` → Line 284-299 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.decide()` → `.run_async()`
  - Add alias: `.decide_sync()` → `.run()`
  - Keep `.get_approval_history()` as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.9 RAGResearchAgent
- **File**: `src/kaizen/agents/specialized/rag_research.py`
- **Current Methods**:
  - `.research(query, session_id)` → Line 390-479
  - `.add_document(doc_id, title, content)` → Line 481-502 (utility)
  - `.get_document_count()` → Line 504-517 (utility)
  - `.clear_documents()` → Line 519-531 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.research()` → `.run()`
  - Keep utility methods (`.add_document()`, `.get_document_count()`, `.clear_documents()`) as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.10 ReActAgent
- **File**: `src/kaizen/agents/specialized/react.py`
- **Current Methods**:
  - `.solve_task(task, context)` → Line 370-430
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.solve_task()` → `.run()`
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 1.11 ResilientAgent
- **File**: `src/kaizen/agents/specialized/resilient.py`
- **Current Methods**:
  - `.query(query)` → Line 231-250 (async)
  - `.query_sync(query)` → Line 252-269 (sync)
  - `.get_error_summary()` → Line 271-287 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.query()` → `.run_async()`
  - Add alias: `.query_sync()` → `.run()`
  - Keep `.get_error_summary()` as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

---

### 2. Multi-Modal Agents (3 total)

All inherit `.run()` from BaseAgent. Need to add aliases for domain methods.

#### 2.1 VisionAgent
- **File**: `src/kaizen/agents/multi_modal/vision_agent.py`
- **Current Methods**:
  - `.analyze(image, question, store_in_memory)` → Line 132-167
  - `.describe(image, detail)` → Line 169-182
  - `.extract_text(image)` → Line 184-194 (OCR)
  - `.batch_analyze(images, question)` → Line 196-215
  - `.extract_document(file_path, ...)` → Line 265-334 (NEW - document extraction)
  - `.estimate_document_cost(file_path, provider)` → Line 336-359
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.analyze()` → `.run()`
  - Keep utility methods (`.describe()`, `.extract_text()`, `.batch_analyze()`) as is
  - Keep document methods (`.extract_document()`, `.estimate_document_cost()`) as is
- **Complexity**: Moderate (has document extraction opt-in feature)
- **Estimated Time**: 15 minutes

#### 2.2 TranscriptionAgent
- **File**: `src/kaizen/agents/multi_modal/transcription_agent.py`
- **Current Methods**:
  - `.transcribe(audio, language, store_in_memory)` → Line 102-162
  - `.transcribe_batch(audio_files, language)` → Line 164-185
  - `.detect_language(audio)` → Line 187-198
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.transcribe()` → `.run()`
  - Keep utility methods (`.transcribe_batch()`, `.detect_language()`) as is
- **Complexity**: Simple
- **Estimated Time**: 10 minutes

#### 2.3 MultiModalAgent
- **File**: `src/kaizen/agents/multi_modal/multi_modal_agent.py`
- **Current Methods**:
  - `.analyze(**inputs, store_in_memory)` → Line 225-311
  - `.batch_analyze(images, audios, texts, questions, store_in_memory)` → Line 385-431
  - `.get_cost_summary()` → Line 433-455 (utility)
  - `.run()` (inherited from BaseAgent) ✅
- **Changes Needed**:
  - Add alias: `.analyze()` → `.run()`
  - Keep utility methods (`.batch_analyze()`, `.get_cost_summary()`) as is
- **Complexity**: Moderate (has document extraction + cost tracking opt-in)
- **Estimated Time**: 15 minutes

---

### 3. Coordination Patterns (6 total)

**CRITICAL**: These are NOT agents - they are composition patterns that orchestrate multiple agents.

#### 3.1 SupervisorWorkerPattern
- **File**: `src/kaizen/agents/coordination/supervisor_worker.py`
- **Type**: Coordination pattern (NOT an agent)
- **Methods**: `.run(task)`, `.run_parallel(task)`, `.run_with_routing(task)`
- **Changes Needed**: ❌ **NONE** - Not an agent, composition pattern only

#### 3.2 ConsensusPattern
- **File**: `src/kaizen/agents/coordination/consensus_pattern.py`
- **Type**: Coordination pattern (NOT an agent)
- **Methods**: `.run(decision)`, `.get_consensus_stats()`
- **Changes Needed**: ❌ **NONE** - Not an agent

#### 3.3 DebatePattern
- **File**: `src/kaizen/agents/coordination/debate_pattern.py`
- **Type**: Coordination pattern (NOT an agent)
- **Methods**: `.run(topic)`, `.get_debate_summary()`
- **Changes Needed**: ❌ **NONE** - Not an agent

#### 3.4 SequentialPipeline
- **File**: `src/kaizen/agents/coordination/sequential_pipeline.py`
- **Type**: Coordination pattern (NOT an agent)
- **Methods**: `.run(initial_input)`, `.add_stage(agent)`
- **Changes Needed**: ❌ **NONE** - Not an agent

#### 3.5 HandoffPattern
- **File**: `src/kaizen/agents/coordination/handoff_pattern.py`
- **Type**: Coordination pattern (NOT an agent)
- **Methods**: `.run(task)`, `.add_handler(agent)`
- **Changes Needed**: ❌ **NONE** - Not an agent

#### 3.6 BasePattern
- **File**: `src/kaizen/agents/coordination/base_pattern.py`
- **Type**: Base class for coordination patterns
- **Methods**: Abstract `.run()` method
- **Changes Needed**: ❌ **NONE** - Not an agent, base class only

---

## Implementation Plan

### Day 1: Specialized Agents (11 total)
**Duration**: 2-3 hours

| Agent | File | Time | Priority |
|-------|------|------|----------|
| SimpleQAAgent | `simple_qa.py` | 10 min | High |
| ChainOfThoughtAgent | `chain_of_thought.py` | 10 min | High |
| StreamingChatAgent | `streaming_chat.py` | 15 min | High |
| SelfReflectionAgent | `self_reflection.py` | 10 min | High |
| MemoryAgent | `memory_agent.py` | 10 min | High |
| BatchProcessingAgent | `batch_processing.py` | 15 min | Medium |
| CodeGenerationAgent | `code_generation.py` | 10 min | High |
| HumanApprovalAgent | `human_approval.py` | 10 min | Medium |
| RAGResearchAgent | `rag_research.py` | 10 min | High |
| ReActAgent | `react.py` | 10 min | High |
| ResilientAgent | `resilient.py` | 10 min | Medium |

**Total**: ~2 hours

### Day 2: Multi-Modal Agents (3 total)
**Duration**: 1 hour

| Agent | File | Time | Complexity |
|-------|------|------|------------|
| VisionAgent | `vision_agent.py` | 15 min | Moderate (document extraction) |
| TranscriptionAgent | `transcription_agent.py` | 10 min | Simple |
| MultiModalAgent | `multi_modal_agent.py` | 15 min | Moderate (cost tracking + docs) |

**Total**: ~1 hour

### Not Needed: Coordination Patterns (6 total)
These are composition patterns, NOT agents - no changes required.

---

## Method Aliasing Pattern (Template)

```python
class SimpleQAAgent(BaseAgent):
    """..."""

    def __init__(self, ...):
        super().__init__(...)

    # ========== PRIMARY EXECUTION METHOD (inherited) ==========
    # .run() is inherited from BaseAgent - always available

    # ========== DOMAIN-SPECIFIC ALIAS (backward compatibility) ==========
    def ask(
        self, question: str, context: str = "", session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask a question and get a structured answer.

        This is an alias for .run() with domain-specific naming.
        Both .ask() and .run() are supported for flexibility.

        Args:
            question: The question to answer
            context: Optional additional context
            session_id: Optional session ID for memory continuity

        Returns:
            Dictionary containing answer, confidence, reasoning

        Example:
            >>> agent = SimpleQAAgent()
            >>> result = agent.ask("What is AI?")  # Domain-specific
            >>> result = agent.run(question="What is AI?")  # Generic
        """
        # Input validation
        if not question or not question.strip():
            return {
                "answer": "Please provide a clear question for me to answer.",
                "confidence": 0.0,
                "reasoning": "Empty or invalid input received",
                "error": "INVALID_INPUT",
            }

        # Delegate to BaseAgent.run() with signature-based parameters
        result = self.run(
            question=question.strip(),
            context=context.strip() if context else "",
            session_id=session_id,
        )

        # Domain-specific post-processing
        confidence = result.get("confidence", 0)
        if confidence < self.qa_config.min_confidence_threshold:
            result["warning"] = (
                f"Low confidence ({confidence:.2f} < {self.qa_config.min_confidence_threshold})"
            )

        return result
```

---

## Validation Checklist

For each agent:
- [ ] Verify `.run()` is inherited from BaseAgent (should be present)
- [ ] Identify deprecated domain methods (`.ask()`, `.analyze()`, etc.)
- [ ] Add aliases that delegate to `.run()` or `.run_async()`
- [ ] Preserve backward compatibility (keep existing methods)
- [ ] Update docstrings to mention both methods
- [ ] Add examples showing both usage patterns
- [ ] Test both domain method and `.run()` produce same results
- [ ] Update tests to use `.run()` (prefer standardized method)

---

## Risk Assessment

### Low Risk
- All agents already inherit `.run()` from BaseAgent ✅
- No breaking changes required ✅
- Backward compatibility maintained ✅

### Medium Risk
- Need to update ~50+ tests to use `.run()` instead of domain methods
- Documentation updates required for all 14 agents

### Mitigation
- Phased rollout (Day 1: Specialized, Day 2: Multi-modal)
- Preserve all existing methods (aliases only)
- Comprehensive test coverage before and after

---

## Success Criteria

1. ✅ All 14 agents support `.run()` (inherited from BaseAgent)
2. ✅ All 14 agents have domain-specific aliases pointing to `.run()`
3. ✅ 100% backward compatibility (existing code still works)
4. ✅ Documentation updated with both usage patterns
5. ✅ Tests prefer `.run()` but domain methods still tested

---

## Next Steps

1. **Coordinate with tdd-implementer**: Create test plan for method aliasing
2. **Coordinate with pattern-expert**: Review coordination patterns (confirm no changes needed)
3. **Coordinate with intermediate-reviewer**: Review implementation after Day 1
4. **Coordinate with gold-standards-validator**: Validate compliance after Day 2

---

**End of Audit Report**
