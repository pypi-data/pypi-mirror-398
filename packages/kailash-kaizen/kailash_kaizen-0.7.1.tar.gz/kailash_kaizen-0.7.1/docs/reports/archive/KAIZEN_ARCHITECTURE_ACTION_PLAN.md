# Kaizen Architecture - Action Plan

**Date**: 2025-10-03
**Status**: READY FOR IMPLEMENTATION
**Timeline**: 8 weeks (5 phases)

---

## Decision: Hybrid Architecture Model ✅

**Structure**:
```
kaizen/
├── src/kaizen/agents/     # Production-ready agents (IMPORTABLE)
│   ├── specialized/       # SimpleQAAgent, ReActAgent, etc.
│   ├── enterprise/        # ComplianceAgent, CustomerServiceAgent, etc.
│   ├── coordination/      # SupervisorAgent, DebateAgent, etc.
│   ├── rag/              # RAG variants
│   └── mcp/              # MCP-specific agents
│
└── examples/              # Learning & tutorials (EDUCATIONAL)
    ├── quickstart/        # 5-minute tutorials
    ├── tutorials/         # Step-by-step guides
    ├── recipes/           # Complete apps
    └── benchmarks/        # Performance tests
```

**Import Experience**:
```python
# NEW (Recommended)
from kaizen.agents import SimpleQAAgent, ReActAgent

# OLD (Deprecated, but works)
from kaizen.examples.simple_qa import SimpleQAAgent  # Warning
```

---

## Phase 1: Foundation (Week 1-2) - NO USER IMPACT

### Tasks
- [ ] Create `src/kaizen/agents/` directory structure
- [ ] Create subdirectories: `specialized/`, `enterprise/`, `coordination/`, `rag/`, `mcp/`
- [ ] Migrate 3 sample agents:
  - [ ] `SimpleQAAgent` → `agents/specialized/simple_qa.py`
  - [ ] `ReActAgent` → `agents/specialized/react.py`
  - [ ] `RAGAgent` → `agents/specialized/rag.py`
- [ ] Create `agents/__init__.py` with exports
- [ ] Add backward compatibility in `kaizen/__init__.py`
- [ ] Write unit tests for new import paths
- [ ] Verify 100% backward compatibility

### Success Criteria
- ✅ All existing imports still work
- ✅ New imports also work: `from kaizen.agents import SimpleQAAgent`
- ✅ No test failures
- ✅ No performance regression

### Code Template

**`src/kaizen/agents/__init__.py`**:
```python
"""Kaizen Production-Ready Agents.

This module provides ready-to-use agents for common patterns.
All agents are built on BaseAgent and support customization.
"""

# Specialized agents (single-agent patterns)
from .specialized.simple_qa import SimpleQAAgent
from .specialized.react import ReActAgent
from .specialized.chain_of_thought import ChainOfThoughtAgent
from .specialized.rag import RAGAgent
from .specialized.code_generation import CodeGenerationAgent

# Enterprise agents
from .enterprise.compliance import ComplianceMonitoringAgent
from .enterprise.customer_service import CustomerServiceAgent

# Coordination agents
from .coordination.supervisor import SupervisorAgent

__all__ = [
    # Specialized
    "SimpleQAAgent",
    "ReActAgent",
    "ChainOfThoughtAgent",
    "RAGAgent",
    "CodeGenerationAgent",
    # Enterprise
    "ComplianceMonitoringAgent",
    "CustomerServiceAgent",
    # Coordination
    "SupervisorAgent",
]

__version__ = "1.0.0"
```

**`kaizen/__init__.py` (backward compatibility)**:
```python
# Backward compatibility - forward old imports to new location
from kaizen.agents import (
    SimpleQAAgent,
    ReActAgent,
    ChainOfThoughtAgent,
    RAGAgent,
    # ... all agents
)

# This allows old imports to still work:
# from kaizen.examples.simple_qa import SimpleQAAgent
# → redirects to kaizen.agents.SimpleQAAgent
```

---

## Phase 2: Documentation (Week 3) - USER AWARENESS

### Tasks
- [ ] Update README.md with new import examples
- [ ] Create migration guide: `docs/migration/examples-to-agents.md`
- [ ] Update all tutorials to show new imports
- [ ] Update quickstart guide
- [ ] Add "New in v0.5.0" announcement
- [ ] Update examples/ README to reference agents/

### Success Criteria
- ✅ Documentation shows new patterns prominently
- ✅ Migration guide tested by 2 external reviewers
- ✅ All code examples updated
- ✅ SEO-friendly (search engines find new import paths)

### Migration Guide Template

**`docs/migration/examples-to-agents.md`**:
```markdown
# Migration Guide: examples/ → agents/

## TL;DR
**Old**: `from kaizen.examples.simple_qa import SimpleQAAgent`
**New**: `from kaizen.agents import SimpleQAAgent`

## Why?
Clear separation between production agents and learning examples.

## Timeline
- **v0.5.0** (Today): New imports available, old imports work
- **v0.6.0** (+1 month): Old imports work with loud warnings
- **v0.7.0** (+2 months): Old imports removed (breaking change)

## Migration Steps

### Step 1: Update Imports
```python
# Before
from kaizen.examples.simple_qa.workflow import SimpleQAAgent
from kaizen.examples.react_agent.workflow import ReActAgent

# After
from kaizen.agents import SimpleQAAgent, ReActAgent
```

### Step 2: Test
```bash
pytest tests/  # Should pass without warnings
```

### Step 3: Done!
No code changes needed beyond imports.

## Automated Migration
```bash
# Run migration script (optional)
python tools/migration/migrate_imports.py --path ./my_project/
```

## Need Help?
- Discord: #migration-help
- GitHub Issues: "Migration: examples → agents"
```

---

## Phase 3: Soft Warnings (Week 4) - GENTLE NUDGE

### Tasks
- [ ] Add deprecation warnings to old import paths
- [ ] Make warnings appear once per session (not spam)
- [ ] Update CI to test both old and new paths
- [ ] Monitor usage analytics (if available)
- [ ] Create FAQ for common migration issues

### Success Criteria
- ✅ Warnings are clear and actionable
- ✅ Warnings don't break tests
- ✅ Users report warnings are helpful (not annoying)
- ✅ 20%+ migration rate (if analytics available)

### Warning Implementation

```python
# kaizen/examples/simple_qa/__init__.py
import warnings
import functools

_warning_shown = False

def _show_deprecation_warning():
    global _warning_shown
    if not _warning_shown:
        warnings.warn(
            "\n"
            "┌─────────────────────────────────────────────────────────────┐\n"
            "│ DEPRECATION WARNING                                         │\n"
            "│                                                             │\n"
            "│ Importing from kaizen.examples is deprecated.               │\n"
            "│                                                             │\n"
            "│ Old: from kaizen.examples.simple_qa import SimpleQAAgent    │\n"
            "│ New: from kaizen.agents import SimpleQAAgent                │\n"
            "│                                                             │\n"
            "│ This import path will be removed in v0.7.0 (2 months).     │\n"
            "│ See: https://kaizen.docs/migration/examples-to-agents      │\n"
            "└─────────────────────────────────────────────────────────────┘\n",
            DeprecationWarning,
            stacklevel=3
        )
        _warning_shown = True

# Import and wrap
from kaizen.agents.specialized import SimpleQAAgent as _SimpleQAAgent

class SimpleQAAgent(_SimpleQAAgent):
    def __init__(self, *args, **kwargs):
        _show_deprecation_warning()
        super().__init__(*args, **kwargs)
```

---

## Phase 4: Hard Warnings (Release v0.6.0) - LOUD NOTICE

### Tasks
- [ ] Upgrade warnings to UserWarning (more visible)
- [ ] Add deprecation notice to release notes
- [ ] Email announcement to users (if mailing list exists)
- [ ] Create video tutorial on migration
- [ ] Monitor support channels for issues

### Success Criteria
- ✅ 80%+ of users migrated (via analytics or survey)
- ✅ No complaints about "surprise breaking changes"
- ✅ Clear timeline communicated
- ✅ Support resources available

---

## Phase 5: Removal (Release v0.7.0) - BREAKING CHANGE

### Tasks
- [ ] Remove backward compatibility imports
- [ ] Update version to v0.7.0 (major breaking change)
- [ ] Clear error messages for old imports
- [ ] Final migration announcement
- [ ] Update all public examples/tutorials

### Success Criteria
- ✅ Clean codebase (no legacy paths)
- ✅ Clear error messages guide users
- ✅ Minimal user disruption (<5% complaints)

### Error Message

```python
# kaizen/examples/simple_qa/__init__.py
raise ImportError(
    "\n"
    "╔═════════════════════════════════════════════════════════════╗\n"
    "║ IMPORT ERROR                                                ║\n"
    "║                                                             ║\n"
    "║ kaizen.examples.simple_qa is no longer available.           ║\n"
    "║                                                             ║\n"
    "║ Please update your imports:                                 ║\n"
    "║                                                             ║\n"
    "║   OLD: from kaizen.examples.simple_qa import SimpleQAAgent  ║\n"
    "║   NEW: from kaizen.agents import SimpleQAAgent              ║\n"
    "║                                                             ║\n"
    "║ See migration guide:                                        ║\n"
    "║ https://kaizen.docs/migration/examples-to-agents            ║\n"
    "╚═════════════════════════════════════════════════════════════╝\n"
)
```

---

## Implementation Priority

### Must-Have (v0.5.0)
1. ✅ Create `agents/` directory structure
2. ✅ Migrate 5 core agents (SimpleQA, ReAct, ChainOfThought, RAG, CodeGen)
3. ✅ Backward compatibility for all existing imports
4. ✅ Update documentation with new import patterns
5. ✅ Migration guide

### Should-Have (v0.6.0)
6. ✅ Migrate all remaining agents (enterprise, coordination, rag variants)
7. ✅ Factory pattern: `create_agent()`
8. ✅ Agent registry for discovery
9. ✅ Hard deprecation warnings
10. ✅ Examples/ refactored to tutorials/recipes

### Nice-to-Have (v0.7.0+)
11. ⚠️ Auto-migration tool
12. ⚠️ MCP-specific agents (MCPServerAgent, MCPClientAgent)
13. ⚠️ Plugin system for community agents
14. ⚠️ Agent marketplace/registry

---

## MCP Implementation Strategy

### Approach: MCP as Opt-In Enhancement

```python
# TIER 1: Core agents (NO MCP dependency)
from kaizen.agents import SimpleQAAgent
agent = SimpleQAAgent()  # Works without MCP

# TIER 2: MCP-enhanced agents (OPTIONAL)
from kaizen.agents import ReActAgent
agent = ReActAgent(config={
    "mcp_discovery_enabled": True  # Opt-in
})

# TIER 3: MCP-specific agents (ADVANCED)
from kaizen.agents.mcp import MCPServerAgent
server = MCPServerAgent(exposed_methods=["analyze"])
```

### MCP Implementation Phases

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| **Phase 0** | Week 1-2 | Core agents (no MCP) ✅ |
| **Phase 1** | Week 3-4 | ReActAgent with `mcp_enabled` flag |
| **Phase 2** | Week 5-6 | MCPServerAgent, MCPClientAgent |
| **Phase 3** | Week 7-8 | MCP tutorials in examples/recipes/ |

**Key Principle**: MCP enhances agents but is NOT required for basic functionality.

---

## Success Metrics & Targets

| Metric | Baseline | Target v0.5 | Target v0.6 | Target v0.7 |
|--------|----------|-------------|-------------|-------------|
| **TTFAX** (Time to First Agent Execution) | ~5 min | < 3 min | < 2 min | < 2 min |
| **Import Path Length** | 5 levels | 3 levels | 3 levels | 3 levels |
| **Lines of Code** (to use agent) | 15-20 | 10 | 5 | 5 |
| **Migration Rate** | 0% | 20% | 80% | 100% |
| **Documentation Search Time** | ~2 min | < 1 min | < 30s | < 30s |

### Measurement Tools

```python
# TTFAX Benchmark (run quarterly)
import time
start = time.time()

from kaizen.agents import SimpleQAAgent
agent = SimpleQAAgent()
result = agent.ask("What is AI?")

elapsed = time.time() - start
print(f"TTFAX: {elapsed:.1f}s (target: <120s)")
```

---

## Risk Mitigation

| Risk | Mitigation | Owner | Status |
|------|------------|-------|--------|
| **Backward compatibility breaks** | 5-phase migration, extensive testing | Core team | ⏳ In Progress |
| **User confusion (2 structures)** | Clear documentation, migration guide | Docs team | ⏳ In Progress |
| **Test maintenance burden** | 3-tier testing, mocked defaults | QA team | ⏳ In Progress |
| **MCP delays** | MCP is optional, not blocking | MCP team | ⏳ Planned |
| **Documentation drift** | Auto-generated API docs | Docs team | ⏳ Planned |

---

## Next Steps (This Week)

### Day 1-2: Prototype
- [ ] Create `src/kaizen/agents/` directory structure
- [ ] Implement `agents/__init__.py` with exports
- [ ] Migrate `SimpleQAAgent` as proof of concept

### Day 3-4: Validation
- [ ] Add backward compatibility layer
- [ ] Write tests for both import paths
- [ ] Run full test suite (should pass 100%)
- [ ] Document new structure in ADR-007

### Day 5: Review
- [ ] Team review of prototype
- [ ] External reviewer (early adopter)
- [ ] Finalize Phase 1 plan
- [ ] Commit Phase 1 code

**By end of Week 1**: Phase 1 prototype complete, backward compatible, tested

---

## Questions for Discussion

1. **Release Cadence**: Should we do monthly releases (v0.5, v0.6, v0.7) or quarterly?
2. **Migration Tool**: Do we need automated import rewriting, or is manual migration acceptable?
3. **MCP Priority**: Should we implement MCP-specific agents now, or defer to Phase 2?
4. **Factory Pattern**: Do we need `create_agent()` factory in v0.5.0, or can it wait?
5. **Community Input**: Should we survey users before finalizing the structure?

---

## Success Definition

**Phase 1 Success**:
- ✅ New imports work: `from kaizen.agents import SimpleQAAgent`
- ✅ Old imports work: `from kaizen.examples.simple_qa import SimpleQAAgent`
- ✅ 100% test pass rate
- ✅ Zero performance regression

**Overall Success (v0.7.0)**:
- ✅ TTFAX < 2 minutes
- ✅ 95%+ users migrated
- ✅ Clean codebase (no legacy paths)
- ✅ Positive community feedback

---

## Contact & Resources

- **Lead**: [Name]
- **Timeline**: 8 weeks (5 phases)
- **Status**: READY TO START
- **Documentation**: See `KAIZEN_ARCHITECTURE_ULTRATHINK_ANALYSIS.md` for full analysis

**Let's build the best developer experience in AI agent frameworks!** 🚀
