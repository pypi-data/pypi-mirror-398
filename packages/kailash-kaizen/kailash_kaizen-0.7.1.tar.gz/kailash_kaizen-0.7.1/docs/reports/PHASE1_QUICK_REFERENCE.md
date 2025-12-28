# Phase 1 Quick Reference: Agent Method Aliases

**Quick lookup table for implementing method aliases in Phase 1**

---

## Specialized Agents (11)

| Agent | Current Method | Alias To | Line # | Notes |
|-------|----------------|----------|--------|-------|
| **SimpleQAAgent** | `.ask(question, context, session_id)` | `.run()` | 217 | Add confidence threshold check |
| **ChainOfThoughtAgent** | `.solve_problem(problem, context)` | `.run()` | 238 | Add verification flag handling |
| **StreamingChatAgent** | `.chat(message)` | `.run()` | 267 | Keep `.stream()` separate (async iterator) |
| | `.chat_async(message)` | `.run_async()` | 285 | |
| **SelfReflectionAgent** | `.reflect(task)` | `.run()` | 253 | Reset reflection_history before call |
| | `.reflect_async(task)` | `.run_async()` | 290 | |
| **MemoryAgent** | `.chat(message, session_id)` | `.run()` | 279 | Handle memory store updates |
| **BatchProcessingAgent** | `.process_batch(batch)` | `.run_batch()` | 224 | **NEW** method, async |
| | `.process_single(prompt)` | `.run()` | 253 | |
| **CodeGenerationAgent** | `.generate_code(task_description, language)` | `.run()` | 326 | Add quality metrics post-processing |
| **HumanApprovalAgent** | `.decide(prompt)` | `.run_async()` | 220 | Handle approval_history |
| | `.decide_sync(prompt)` | `.run()` | 265 | |
| **RAGResearchAgent** | `.research(query, session_id)` | `.run()` | 390 | Add retrieval quality calculation |
| **ReActAgent** | `.solve_task(task, context)` | `.run()` | 370 | MultiCycleStrategy integration |
| **ResilientAgent** | `.query(query)` | `.run_async()` | 231 | FallbackStrategy integration |
| | `.query_sync(query)` | `.run()` | 252 | |

---

## Multi-Modal Agents (3)

| Agent | Current Method | Alias To | Line # | Notes |
|-------|----------------|----------|--------|-------|
| **VisionAgent** | `.analyze(image, question, store_in_memory)` | `.run()` | 132 | Vision provider integration |
| **TranscriptionAgent** | `.transcribe(audio, language, store_in_memory)` | `.run()` | 102 | Whisper integration |
| **MultiModalAgent** | `.analyze(**inputs, store_in_memory)` | `.run()` | 225 | Multi-modal adapter + cost tracking |

---

## Utility Methods (Keep As-Is)

**DO NOT alias these** - they provide distinct functionality:

### SimpleQAAgent
- None

### ChainOfThoughtAgent
- None

### StreamingChatAgent
- `.stream(message)` - Async iterator, different pattern

### SelfReflectionAgent
- `.get_reflection_history()` - Retrieves reflection history

### MemoryAgent
- `.clear_memory(session_id)` - Clears conversation memory
- `.get_conversation_count(session_id)` - Returns turn count

### BatchProcessingAgent
- None

### CodeGenerationAgent
- `.generate_tests(code, language)` - Test generation utility
- `.explain_code(code, language)` - Code explanation utility
- `.refactor_code(code, refactoring_goal, language)` - Refactoring utility

### HumanApprovalAgent
- `.get_approval_history()` - Retrieves approval history

### RAGResearchAgent
- `.add_document(doc_id, title, content)` - Document management
- `.get_document_count()` - Returns document count
- `.clear_documents()` - Clears vector store

### ReActAgent
- None

### ResilientAgent
- `.get_error_summary()` - Returns fallback error summary

### VisionAgent
- `.describe(image, detail)` - Image description
- `.extract_text(image)` - OCR utility
- `.batch_analyze(images, question)` - Batch processing
- `.extract_document(file_path, ...)` - Document extraction (opt-in)
- `.estimate_document_cost(file_path, provider)` - Cost estimation

### TranscriptionAgent
- `.transcribe_batch(audio_files, language)` - Batch transcription
- `.detect_language(audio)` - Language detection

### MultiModalAgent
- `.batch_analyze(images, audios, texts, questions, store_in_memory)` - Batch processing
- `.get_cost_summary()` - Cost tracking summary

---

## Implementation Pattern

```python
def domain_method(self, arg1, arg2, ...) -> ReturnType:
    """
    Domain-specific method description.

    This is an alias for .run() with domain-specific naming.
    Both .domain_method() and .run() are supported.

    Args:
        arg1: Description
        arg2: Description

    Returns:
        Return type description

    Example:
        >>> agent = Agent()
        >>> result = agent.domain_method(arg1, arg2)  # Domain-specific
        >>> result = agent.run(param1=arg1, param2=arg2)  # Generic
    """
    # 1. Input validation
    if not arg1:
        return {"error": "INVALID_INPUT", ...}

    # 2. Delegate to BaseAgent.run() with signature params
    result = self.run(
        param1=arg1,
        param2=arg2,
        ...
    )

    # 3. Domain-specific post-processing (optional)
    # e.g., add warnings, calculate metrics, update state

    return result
```

---

## Coordination Patterns (NO CHANGES)

These are composition patterns, NOT agents:
- ❌ SupervisorWorkerPattern
- ❌ ConsensusPattern
- ❌ DebatePattern
- ❌ SequentialPipeline
- ❌ HandoffPattern
- ❌ BasePattern

---

## Checklist Per Agent

- [ ] Read agent file
- [ ] Identify deprecated method(s)
- [ ] Add method alias(es) delegating to `.run()` or `.run_async()`
- [ ] Preserve input validation
- [ ] Preserve post-processing logic
- [ ] Update docstring with both usage patterns
- [ ] Add example showing both methods
- [ ] Verify utility methods remain unchanged
- [ ] Test both methods produce same output

---

## Priority Order

### Day 1 (High Priority - 8 agents)
1. SimpleQAAgent
2. ChainOfThoughtAgent
3. StreamingChatAgent
4. SelfReflectionAgent
5. MemoryAgent
6. CodeGenerationAgent
7. RAGResearchAgent
8. ReActAgent

### Day 1 (Medium Priority - 3 agents)
9. BatchProcessingAgent
10. HumanApprovalAgent
11. ResilientAgent

### Day 2 (Multi-Modal - 3 agents)
12. VisionAgent
13. TranscriptionAgent
14. MultiModalAgent

---

**Total Agents**: 14
**Total Aliases**: ~20 (some agents have both sync and async variants)
**Estimated Time**: 3-4 hours total
