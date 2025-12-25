# ARF v3 – RAG Graph Schema

**Audience:** Senior Engineers, Architects, Platform Owners

**Purpose:** Define the concrete knowledge model that upgrades ARF from write-only vector storage to a learning, queryable incident memory.

---

## Design Goals

1. **Learning, not logging** – memory must influence future decisions
2. **Separation of concerns** – vectors ≠ truth, graph = truth
3. **Incremental adoption** – v2 compatibility preserved
4. **Auditability** – every recommendation traceable to evidence

---

## Conceptual Model

ARF v3 memory consists of **three layers**:

1. **FAISS Vector Index** – fast semantic recall
2. **Incident Graph** – structured incident knowledge
3. **Outcome Graph** – action effectiveness learning

```
Embedding → IncidentNode → OutcomeNode
        ↘ SIMILAR_TO ↗
```

---

## Incident Node

Represents a single detected reliability incident.

### Required Fields

```python
IncidentNode = {
  "incident_id": str,              # Stable fingerprint
  "component": str,                # payment-service, api-gateway
  "severity": str,                 # INFO | WARN | CRITICAL
  "timestamp": str,                # ISO-8601
  "metrics": {
    "latency_ms": float,
    "error_rate": float
  },
  "agent_analysis": dict,          # Detective + Diagnostician output
  "predictive_insights": dict,     # Forecasting agent output
  "embedding_id": int              # FAISS index reference
}
```

### Notes
- `incident_id` must be deterministic (hash of component + window)
- No free-form strings as primary fields
- Raw logs stay external; graph stores reasoning artifacts

---

## Outcome Node

Captures **what actually happened after intervention**.

```python
OutcomeNode = {
  "incident_id": str,
  "actions_taken": list[str],      # HealingAction enums
  "resolution_time_minutes": float,
  "success": bool,
  "blast_radius": str,             # single-service | multi-service
  "lessons_learned": str,
  "recorded_at": str
}
```

### Why Outcomes Are Separate

- One incident may have multiple attempts
- Enables A/B comparison of actions
- Allows postmortem replay

---

## Graph Edges

### Edge Types

| Edge | From → To | Meaning |
|---|---|---|
| SIMILAR_TO | Incident → Incident | Semantic similarity |
| CAUSED_BY | Incident → Incident | Dependency failure |
| ESCALATED_FROM | Incident → Incident | Progressive failure |
| RESOLVED_BY | Incident → Outcome | Action effectiveness |

### Edge Schema

```python
GraphEdge = {
  "source_id": str,
  "target_id": str,
  "type": str,
  "confidence": float,
  "created_at": str
}
```

---

## Retrieval Flow

1. New anomaly embedded
2. FAISS k-NN search (top-K)
3. IncidentNodes loaded by embedding_id
4. Graph expansion (edges + outcomes)
5. Context injected into Policy Engine

**Key Rule:** Policies never read FAISS directly – only the graph.

---

## Storage Strategy

| Layer | OSS | Enterprise |
|---|---|---|
| FAISS | In-process | Sharded / remote |
| Graph | In-memory / JSON | Graph DB / KV |
| Outcomes | Optional | Required |

---

## Migration from v2

- Existing FAISS vectors reused
- Flat text metadata replaced by IncidentNodes
- Retrieval introduced behind feature flag

---

## Non-Goals

- Full observability data warehousing
- Raw log storage
- Real-time graph mutation at millisecond scale

---

## Summary

The RAG Graph is ARF’s **institutional memory**.

It enables learning, explainability, and safer automation — without compromising performance or OSS integrity.

