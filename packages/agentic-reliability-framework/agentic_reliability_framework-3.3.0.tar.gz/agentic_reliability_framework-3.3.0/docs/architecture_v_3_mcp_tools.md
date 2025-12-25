# ARF v3 – MCP Tool Architecture

**Audience:** Platform Engineers, Security Teams, Buyers

**Purpose:** Define how ARF safely crosses the boundary from *decision* to *action* using Model Context Protocol (MCP).

---

## Why MCP Exists in ARF

Reliability automation fails when systems:
- Act implicitly
- Skip approvals
- Lack audit trails

ARF v3 enforces a hard rule:

> **Agents reason. Policies decide. MCP executes.**

---

## Responsibility Split

| Layer | Responsibility |
|---|---|
| Agents | Analyze & predict |
| Policy Engine | Decide what *should* happen |
| MCP Server | Decide whether it *may* happen |

---

## MCP Server Role

The MCP server is a **governed execution plane**.

It provides:
- Explicit tool contracts
- Permission enforcement
- Execution modes
- Audit logs

It does **not**:
- Perform analysis
- Make policy decisions
- Learn from outcomes (delegated to RAG)

---

## Tool Taxonomy

Derived directly from `HealingAction`.

### Core Tool Categories

| Category | Examples |
|---|---|
| Traffic Control | RATE_LIMIT, CIRCUIT_BREAK |
| Compute | SCALE_UP, SCALE_DOWN |
| Deployment | ROLLBACK, RESTART |
| Isolation | DISABLE_FEATURE, FAILOVER |

---

## MCP Tool Schema (Canonical)

```json
{
  "tool": "ROLLBACK_DEPLOYMENT",
  "incident_id": "incident_2025_12_12_xyz",
  "confidence": 0.84,
  "risk_level": "MEDIUM",
  "justification": [
    "3 similar incidents resolved successfully",
    "Scaling attempts failed previously"
  ],
  "constraints": {
    "cooldown_minutes": 15,
    "max_executions": 1
  }
}
```

---

## Execution Modes

### 1. Advisory (OSS Default)

- MCP returns recommendations only
- No side effects
- Used for pilots and evaluation

### 2. Approval (Enterprise)

- Human approval required
- Slack / PagerDuty / UI
- Full audit trail

### 3. Autonomous (Enterprise)

- Pre-approved actions
- Guardrails enforced
- Continuous monitoring

---

## Safety Guardrails

MCP enforces:

- Rate limits
- Cooldowns
- Blast radius checks
- Environment restrictions

Example:
```python
if incident.severity != "CRITICAL":
    deny("Rollback not permitted")
```

---

## Audit & Compliance

Every MCP action records:

- Who approved
- Why it was executed
- What context was used
- What changed

This enables:
- SOC2 evidence
- Incident reviews
- Regulatory audits

---

## OSS vs Enterprise Boundary

### Open Source

- Tool schemas
- Simulation mode
- Policy → MCP handoff

### Enterprise

- Execution adapters (K8s, Cloud APIs)
- Approval workflows
- Audit exports
- RBAC

---

## Failure Modes & Design Responses

| Risk | Mitigation |
|---|---|
| Over-automation | Advisory default |
| Cascading actions | Cooldowns |
| Incorrect actions | Human approval |
| Black-box decisions | RAG justification |

---

## Summary

MCP is ARF’s **trust boundary**.

It allows ARF to automate *without* becoming dangerous — a prerequisite for real production adoption.

