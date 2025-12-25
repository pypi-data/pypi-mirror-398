# Agentic Reliability Framework (ARF)
## Architecture v3: MCP + RAG Graph Memory

**Audience:** Engineering Leaders, Staff+ Engineers, CTOs, Buyers

**Purpose:** Describe how ARF evolves from a reactive anomaly system (v2) into a learning, decision-safe, agentic reliability platform (v3) using **Model Context Protocol (MCP)** and a **RAG Graph knowledge layer**.

---

## Executive Summary (Non-Technical)

ARF v2 already detects failures early and recommends actions. However, production buyers ask two hard questions:

1. *“Can the system learn from past incidents?”*
2. *“Can it act safely without breaking things?”*

ARF v3 answers both.

- **RAG Graph** turns past incidents into institutional memory.
- **MCP** enforces a hard execution boundary between *recommendation* and *action*.

Together, they transform ARF from **alerting intelligence** into **governed, learning automation**.

---

## v2 → v3 Evolution

| Capability | v2 (Today) | v3 (This Doc) |
|---|---|---|
| Anomaly Detection | ✅ | ✅ |
| Root Cause Analysis | ✅ | ✅ |
| Predictive Forecasting | ✅ | ✅ |
| Vector Memory | Write-only FAISS | FAISS + Retrieval |
| Learning Loop | ❌ | ✅ RAG Graph |
| Action Execution | Inline / implicit | Explicit MCP boundary |
| Safety & Governance | Best-effort | Enforced |

---

## Core Design Principles

1. **Memory must influence decisions** (otherwise it is useless)
2. **Execution must be explicitly governed** (never implicit)
3. **Learning must be explainable** (buyers demand this)
4. **Open core, paid execution** (sustainable OSS)

---

## High-Level Architecture

```
┌──────────────┐
│ Observability│
│  Signals     │
└──────┬───────┘
       ↓
┌──────────────────────────┐
│ Multi-Agent Reasoning    │
│ (Detective, Diagnostician│
│  Predictive)             │
└──────┬───────────────────┘
       ↓
┌──────────────────────────┐
│ RAG Graph Memory         │◄───────┐
│ (Incidents + Outcomes)  │        │
└──────┬───────────────────┘        │
       ↓                            │
┌──────────────────────────┐        │
│ Policy Engine             │        │
│ (Decide, Not Execute)     │        │
└──────┬───────────────────┘        │
       ↓                            │
┌──────────────────────────┐        │
│ MCP Server                │────────┘
│ (Governed Execution)      │
└──────────────────────────┘
```

---

## RAG Graph Memory (Learning Layer)

### Why FAISS Alone Is Not Enough

FAISS provides **recall**, not **reasoning**.

ARF v2 writes embeddings for anomalous events but never reads them. In v3, FAISS becomes a *retrieval primitive*, not the memory itself.

### RAG Graph Responsibilities

The RAG Graph stores **structured incident knowledge**:

- What happened
- Why it happened
- What was done
- Whether it worked

### Incident Node Schema (Conceptual)

```python
IncidentNode = {
  "incident_id": str,
  "component": str,
  "severity": str,
  "metrics": {"latency": float, "error_rate": float},
  "timestamp": str,
  "agent_analysis": dict,
  "predicted_impact": dict,
  "embedding_ref": int
}
```

### Outcome Node Schema

```python
OutcomeNode = {
  "incident_id": str,
  "actions_taken": list[str],
  "resolution_time_minutes": float,
  "success": bool,
  "lessons_learned": str
}
```

### Graph Edges

| Edge Type | Meaning |
|---|---|
| SIMILAR_TO | Semantic similarity |
| CAUSED_BY | Causal dependency |
| ESCALATED_FROM | Incident evolution |
| RESOLVED_BY | Action effectiveness |

---

## Retrieval Flow (RAG)

1. New anomaly detected
2. Event embedded and queried against FAISS
3. Top-K similar incidents retrieved
4. Graph expanded to include outcomes and actions
5. Context injected into policy reasoning

**Result:** ARF reasons with *history*, not just metrics.

---

## MCP Server (Execution Boundary)

### Why MCP Exists

In v2, policies imply actions.

In v3:
> **Policies never execute. MCP does.**

This creates a non-negotiable safety boundary.

### MCP Responsibilities

- Tool registration (restart, rollback, scale, throttle)
- Permission enforcement
- Simulation vs execution modes
- Audit logging

### MCP Tool Example

```json
{
  "tool": "ROLLBACK_DEPLOYMENT",
  "incident_id": "incident_2025_12_12_abc",
  "confidence": 0.82,
  "justification": [
    "Similar incident resolved by rollback",
    "No successful scale-based recovery"
  ]
}
```

---

## Execution Modes (Buyer-Relevant)

| Mode | Description |
|---|---|
| Advisory | Recommendations only (OSS default) |
| Approval | Human-in-the-loop |
| Automated | MCP executes with guardrails |

---

## OSS vs Paid Boundary

### Open Source (Core Intelligence)

- Agents
- Policy reasoning
- FAISS-based recall
- Basic similarity search

### Paid / Enterprise

- Persistent RAG Graph
- Outcome learning
- MCP execution server
- Human approval workflows
- Compliance & audit exports

This keeps ARF **credible as OSS** while monetizing **risk-bearing execution**.

---

## Why This Matters to Buyers

- Fewer repeated incidents
- Faster MTTR with evidence
- Safer automation
- Explainable decisions
- Clear blast-radius controls

ARF v3 behaves like a **senior SRE with perfect memory and zero ego**.

---

## Why This Matters to Engineers

- Clean separation of concerns
- No hidden side effects
- Deterministic execution paths
- Testable memory and policies
- Extensible graph schema

---

## Summary

ARF v3 introduces two critical primitives:

- **RAG Graph Memory** → learning and reasoning
- **MCP Execution Boundary** → safety and trust

Together, they elevate ARF from *monitoring intelligence* to **production-grade agentic reliability infrastructure**.

---

**Next Docs:**
- `architecture_v3_rag_schema.md`
- `architecture_v3_mcp_tools.md`
- `enterprise_execution_modes.md`

