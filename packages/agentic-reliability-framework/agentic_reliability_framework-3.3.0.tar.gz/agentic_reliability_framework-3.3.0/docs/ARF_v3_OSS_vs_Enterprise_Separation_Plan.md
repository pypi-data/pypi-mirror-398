# ARF v3: Complete OSS vs Enterprise Separation & Implementation Plan

**Based on existing codebase**  
*Version: 3.3.0*  
*Author: Juan Petter AI Engineer*  
*December 19, 2025*

---

## Executive Summary

My current codebase **already has Enterprise features mixed with OSS code**. The MCP server supports all modes (advisory, approval, autonomous) and tools actually execute (or simulate execution). I need to **separate, not rewrite**, while maintaining functionality.

### Critical Findings:

1. **Current State**: Single repo with mixed OSS/Enterprise code
2. **MCP Server**: Full implementation with execution capability
3. **Configuration**: Runtime-based (`config.mcp_mode`), not build-time
4. **Tools**: Actually execute (or simulate) actions
5. **License**: Currently MIT, moving to Apache 2.0 (OSS) + Commercial (Enterprise)

---

## 1. Current Architecture Analysis

### 1.1 What I Have Working:

```python
# Already implemented and working:
✅ Full MCP server with 3 modes
✅ Tool implementations (rollback, restart, scale_out, etc.)
✅ RAG graph memory (FAISS-based)
✅ Reliability engine with learning
✅ Metrics Export API (Prometheus, JSON, CSV)
✅ Post-mortem benchmark suite
✅ Comprehensive models and validation
```
1.2 What Needs Separation:
```python
# Mixed concerns that need separation:
🚫 MCP execution modes all in same code
🚫 Tool execution not restricted
🚫 No build-time enforcement
🚫 No license validation
🚫 Same repo for OSS and Enterprise
```
## 2. Immediate Action Plan (5 Days)

### Day 1: Repository Restructuring & Build-Time Boundaries
1. Morning (4 hours):
2. Split repository into OSS and Enterprise components
3. Create OSS constants with hard limits
4. Implement build-time enforcement scripts

Afternoon (4 hours):
5. Create bridge interfaces for clear separation
6. Implement HealingIntent boundary pattern
7. Set up CI/CD with boundary checks

Key Files to Create Day 1:

```bash
# OSS Repository Structure
agentic-reliability-framework/          # Apache 2.0
├── arf-core/
│   ├── src/
│   │   ├── constants.py              # OSS_HARD_LIMITS
│   │   ├── boundaries.py             # Build-time validation
│   │   ├── models/healing_intent.py  # OSS→Enterprise bridge
│   │   └── security/oss_auth.py      # OSS-only security
│   └── tests/test_oss_boundaries.py
├── arf-mcp-client/                    # Advisory mode only
└── scripts/enforce_oss_constants.py

# Enterprise Repository
arf-enterprise/                        # Commercial
├── arf-mcp-server/                    # Your existing mcp_server.py
├── arf-graph-store/                   # Enhanced RAG
└── arf-learning/                      # Learning engine
```

### Day 2: MCP Server Separation & Mode Enforcement
1. Morning (4 hours):
2. Restrict OSS MCP client to advisory mode only
3. Create Enterprise MCP server with license validation
4. Implement HealingIntent serialization

Afternoon (4 hours):
5. Update tool implementations for separation
6. Create cross-layer integration tests
7. Implement secure handoff OSS→Enterprise

Key Changes to Existing Code:

```python
# Current mcp_server.py - NEEDS SPLITTING

# OSS Version (mcp_client.py):
class OSSMCPClient:
    """OSS: Advisory mode only, creates HealingIntent"""
    MODE = MCPMode.ADVISORY  # Hard-coded, immutable
    
    async def recommend_action(self, tool: str, params: dict) -> HealingIntent:
        # Analysis only, no execution
        return HealingIntent(...)

# Enterprise Version (mcp_server.py - enhanced):
class EnterpriseMCPServer(MCPServer):  # Your existing class
    def __init__(self, license_key: str):
        super().__init__()
        if not self._validate_enterprise_license(license_key):
            raise LicenseError("Enterprise license required")
        self.mode = config.mcp_mode  # Configurable
    
    async def execute_healing_intent(self, intent: HealingIntent) -> MCPResponse:
        """Enterprise-only: Execute OSS-generated intent"""
        # Your existing execution logic
        return await super().execute_tool(intent.to_mcp_request())
```

### Day 3: Security, Compliance & Data Separation
Morning (4 hours):
1. Implement tier-specific security modules
2. Create audit trail system (Enterprise only)
3. Set up data ownership boundaries

Afternoon (4 hours):
4. Implement compliance frameworks
5. Create backup systems per tier
6. Write security tests for boundaries

### Day 4: Testing Infrastructure & CI/CD
Morning (4 hours):
1. Create four-layer test suite
2. Implement API contract tests
3. Set up benchmark validation tests

Afternoon (4 hours):
4. Create integration test mocks
5. Set up test coverage reporting
6. Write cross-tier security tests

### Day 5: Deployment & Documentation
Morning (4 hours):
1. Create Docker configurations per tier
2. Implement Kubernetes manifests
3. Set up monitoring & alerting

Afternoon (4 hours):
4. Generate compliance readiness report
5. Create deployment documentation
6. Final validation and testing

## 3. Detailed Implementation Guide
### 3.1 Step 1: Create OSS Constants & Boundaries
```python
# arf-core/src/constants.py
"""
OSS HARD LIMITS - Build-time enforced
"""

from typing import Final
import sys

# === EXECUTION BOUNDARIES ===
MAX_INCIDENT_HISTORY: Final[int] = 1_000
MAX_RAG_LOOKBACK_DAYS: Final[int] = 7
MCP_MODES_ALLOWED: Final[tuple] = ("advisory",)  # ONLY advisory
EXECUTION_ALLOWED: Final[bool] = False
GRAPH_STORAGE: Final[str] = "in_memory"

# === VALIDATION AT IMPORT TIME ===
def _validate_oss_constants():
    """Runtime validation of OSS constants"""
    violations = []
    
    if MAX_INCIDENT_HISTORY > 1000:
        violations.append("MAX_INCIDENT_HISTORY > 1000")
    
    if set(MCP_MODES_ALLOWED) != {"advisory"}:
        violations.append("MCP_MODES_ALLOWED must be only ('advisory',)")
    
    if EXECUTION_ALLOWED:
        violations.append("EXECUTION_ALLOWED must be False")
    
    if GRAPH_STORAGE != "in_memory":
        violations.append("GRAPH_STORAGE must be 'in_memory'")
    
    if violations:
        raise RuntimeError(
            f"OSS constant violations: {violations}. "
            "These values are immutable in OSS version."
        )

_validate_oss_constants()
```

### 3.2 Step 2: Build-Time Enforcement Script
```python
# scripts/enforce_oss_constants.py
"""
Build-time validation of OSS boundaries
Runs in CI/CD to prevent Enterprise code in OSS
"""

import ast
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    # Execution patterns
    ("MCPMode.APPROVAL", "Approval mode requires Enterprise"),
    ("MCPMode.AUTONOMOUS", "Autonomous mode requires Enterprise"),
    ("await.*execute", "Async execution requires Enterprise"),
    
    # Storage patterns
    ("neo4j", "Neo4j persistence requires Enterprise"),
    ("postgres", "PostgreSQL requires Enterprise"),
    ("CREATE TABLE", "Database operations require Enterprise"),
    
    # Enterprise feature patterns
    ("license_key", "License validation requires Enterprise"),
    ("audit_trail", "Audit trails require Enterprise"),
    ("encryption_key", "Advanced encryption requires Enterprise"),
]

def scan_file(filepath: Path) -> list:
    """Scan Python file for forbidden patterns"""
    violations = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check for forbidden patterns
        for pattern, message in FORBIDDEN_PATTERNS:
            if pattern in content:
                # Find line number
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line:
                        violations.append(f"{filepath}:{i}: {message}")
                        break
                        
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
    
    return violations

def main():
    """Main validation routine"""
    oss_dirs = ["arf-core/src", "arf-mcp-client/src", "arf-rag/src"]
    
    all_violations = []
    for dir_path in oss_dirs:
        if Path(dir_path).exists():
            for py_file in Path(dir_path).rglob("*.py"):
                violations = scan_file(py_file)
                all_violations.extend(violations)
    
    if all_violations:
        print("❌ OSS BOUNDARY VIOLATIONS DETECTED:")
        for violation in all_violations:
            print(f"  {violation}")
        sys.exit(1)
    else:
        print("✅ All OSS files comply with boundaries")

if __name__ == "__main__":
    main()
```
### 3.3 Step 3: Healing Intent Boundary Pattern
```python
# arf-core/src/models/healing_intent.py
"""
Healing Intent - OSS creates, Enterprise executes
Clean boundary between intelligence and execution
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json


@dataclass(frozen=True)
class HealingIntent:
    """OSS-generated healing recommendation"""
    # Required fields
    action: str                          # e.g., "restart_container"
    parameters: Dict[str, Any]           # Action parameters
    justification: str                   # OSS reasoning chain
    confidence: float                    # 0.0 to 1.0
    
    # Context fields
    incident_id: str                     # Source incident
    component: str                       # Target component
    detected_at: datetime                # When OSS detected
    
    # OSS explainability (stays in OSS)
    reasoning_chain: Optional[List[Dict]] = None
    similar_incidents: Optional[List[Dict]] = None
    policy_applied: Optional[str] = None
    
    # Immutable identifier
    @property
    def intent_id(self) -> str:
        """Deterministic ID for idempotency"""
        data = {
            "action": self.action,
            "parameters": self.parameters,
            "incident_id": self.incident_id,
            "component": self.component,
            "detected_at": self.detected_at.isoformat(),
        }
        json_str = json.dumps(data, sort_keys=True)
        return f"intent_{hashlib.sha256(json_str.encode()).hexdigest()[:16]}"
    
    def to_enterprise_request(self) -> Dict[str, Any]:
        """Convert to Enterprise API request format"""
        # Only send necessary data to Enterprise
        return {
            "intent_id": self.intent_id,
            "action": self.action,
            "parameters": self.parameters,
            "justification": self.justification,
            "confidence": self.confidence,
            "incident_id": self.incident_id,
            "component": self.component,
            "detected_at": self.detected_at.isoformat(),
            # OSS metadata stays in OSS
            "requires_enterprise": True,
        }
    
    @classmethod
    def from_mcp_request(cls, request: Dict[str, Any]) -> "HealingIntent":
        """Create from existing MCP request (backward compatibility)"""
        return cls(
            action=request["tool"],
            parameters=request.get("parameters", {}),
            justification=request.get("justification", ""),
            confidence=0.85,  # Default for backward compat
            incident_id=request.get("metadata", {}).get("incident_id", "unknown"),
            component=request["component"],
            detected_at=datetime.fromisoformat(
                request.get("metadata", {}).get("detected_at", datetime.now().isoformat())
            ),
        )
```
### 3.4 Step 4: OSS MCP Client (Advisory Only)
```python
# arf-mcp-client/src/client.py
"""
OSS MCP Client - Advisory mode only
Cannot execute, only recommends
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from ..constants import MCP_MODES_ALLOWED
from ..models.healing_intent import HealingIntent


class MCPMode(Enum):
    """MCP execution modes"""
    ADVISORY = "advisory"      # OSS: Recommendations only
    APPROVAL = "approval"      # Enterprise: Human-in-loop
    AUTONOMOUS = "autonomous"  # Enterprise: Fully automated


class OSSMCPClient:
    """
    OSS MCP Client - Advisory mode only
    
    This is the OSS version of your existing MCPServer.
    It can analyze and recommend, but cannot execute.
    """
    
    def __init__(self):
        self.mode = MCPMode.ADVISORY  # Hard-coded for OSS
        self._analysis_engine = self._create_analysis_engine()
    
    async def analyze_and_recommend(
        self, 
        tool_name: str, 
        component: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> HealingIntent:
        """
        OSS: Analyze situation and create healing intent
        Returns intent that can be sent to Enterprise for execution
        """
        # Generate OSS reasoning
        justification = await self._generate_justification(
            tool_name, component, parameters, context
        )
        
        confidence = self._calculate_confidence(
            tool_name, component, parameters, context
        )
        
        # Create healing intent (OSS output)
        return HealingIntent(
            action=tool_name,
            parameters=parameters,
            justification=justification,
            confidence=confidence,
            incident_id=context.get("incident_id", "unknown") if context else "unknown",
            component=component,
            detected_at=datetime.now(),
            reasoning_chain=await self._generate_reasoning_chain(
                tool_name, component, parameters, context
            ),
            similar_incidents=await self._find_similar_incidents(
                component, parameters, context
            ),
        )
    
    async def _generate_justification(
        self, 
        tool: str, 
        component: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """OSS: Generate reasoning for action"""
        # This is where your existing analysis logic goes
        # But NO execution capability
        
        if context and context.get("similar_incidents"):
            similar_count = len(context["similar_incidents"])
            return (
                f"Based on {similar_count} similar historical incidents, "
                f"recommend {tool} for {component} with parameters {params}"
            )
        
        return (
            f"Based on anomaly analysis, recommend {tool} "
            f"for {component} with parameters {params}"
        )
    
    def _calculate_confidence(
        self,
        tool: str,
        component: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> float:
        """OSS: Calculate confidence without execution history"""
        # Pure reasoning - no outcome learning in OSS
        base_confidence = 0.85
        
        # Enhance with context if available
        if context:
            if context.get("severity") == "critical":
                base_confidence *= 1.1
            if context.get("similar_incidents"):
                base_confidence *= 1.05
        
        return min(base_confidence, 1.0)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OSS client capabilities"""
        return {
            "mode": self.mode.value,
            "can_execute": False,
            "can_advise": True,
            "max_incident_history": 1000,
            "enterprise_upgrade_available": True,
            "enterprise_features": [
                "autonomous_execution",
                "approval_workflows", 
                "persistent_storage",
                "learning_engine",
                "audit_trails",
                "compliance_reports"
            ]
        }


# Factory function for backward compatibility
def create_mcp_client() -> OSSMCPClient:
    """
    Factory function - returns OSS client in OSS build,
    would return Enterprise client in Enterprise build
    """
    return OSSMCPClient()
```
### 3.5 Step 5: Enterprise MCP Server (Enhanced)
```python
# arf-enterprise/arf-mcp-server/src/server.py
"""
Enterprise MCP Server - Enhanced version of your existing code
Adds license validation and OSS integration
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import from OSS package (dependency)
from arf_core.models.healing_intent import HealingIntent
from arf_core.constants import EXECUTION_ALLOWED

# Import your existing MCPServer
from ...agentic_reliability_framework.engine.mcp_server import (
    MCPServer, MCPRequest, MCPResponse, MCPMode
)


class EnterpriseMCPServer(MCPServer):
    """
    Enterprise MCP Server - Extends your existing implementation
    
    Key additions:
    1. License validation
    2. HealingIntent integration  
    3. Audit trails
    4. Learning integration
    """
    
    def __init__(self, license_key: Optional[str] = None):
        # Validate license
        if not self._validate_enterprise_license(license_key):
            raise LicenseError(
                "Enterprise license required. "
                "Get license at https://arf.dev/enterprise"
            )
        
        # Initialize your existing MCPServer
        super().__init__()
        
        # Enterprise enhancements
        self.license_key = license_key
        self.audit_log = []
        self.learning_engine = self._create_learning_engine()
        
        # Enable all modes for Enterprise
        self.mode = MCPMode(config.mcp_mode)  # Configurable
        
        print(f"✅ Enterprise MCPServer initialized with license: {license_key[:8]}...")
    
    def _validate_enterprise_license(self, license_key: Optional[str]) -> bool:
        """Validate Enterprise license"""
        if not license_key:
            return False
        
        # Basic format check
        if not license_key.startswith("ARF-ENT-"):
            return False
        
        # In production: validate against license server
        # For now, basic validation
        return len(license_key) > 20
    
    async def execute_healing_intent(
        self, 
        intent: HealingIntent,
        mode: Optional[MCPMode] = None
    ) -> MCPResponse:
        """
        Enterprise: Execute OSS-generated healing intent
        
        This is the clean handoff from OSS to Enterprise
        """
        # Log execution
        await self._audit_intent_execution(intent)
        
        # Convert HealingIntent to MCP request
        mcp_request = self._healing_intent_to_mcp_request(intent, mode)
        
        # Execute using your existing logic
        response = await super().execute_tool(mcp_request)
        
        # Record outcome for learning
        if response.executed or response.status == "completed":
            await self._record_outcome(intent, response)
        
        return response
    
    def _healing_intent_to_mcp_request(
        self, 
        intent: HealingIntent,
        mode: Optional[MCPMode] = None
    ) -> Dict[str, Any]:
        """Convert HealingIntent to MCP request format"""
        return {
            "tool": intent.action,
            "component": intent.component,
            "parameters": intent.parameters,
            "justification": intent.justification,
            "mode": (mode or self.mode).value,
            "metadata": {
                "intent_id": intent.intent_id,
                "oss_confidence": intent.confidence,
                "detected_at": intent.detected_at.isoformat(),
                "incident_id": intent.incident_id,
                "requires_enterprise": True,
            }
        }
    
    async def _audit_intent_execution(self, intent: HealingIntent):
        """Enterprise: Create audit entry"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "execute_healing_intent",
            "intent_id": intent.intent_id,
            "component": intent.component,
            "license_key": self.license_key[:8] + "..." if self.license_key else None,
            "mode": self.mode.value,
        }
        
        self.audit_log.append(audit_entry)
        
        # In production: persist to secure storage
        print(f"📝 Audit: Executing intent {intent.intent_id} for {intent.component}")
    
    async def _record_outcome(self, intent: HealingIntent, response: MCPResponse):
        """Enterprise: Record outcome for learning"""
        if self.learning_engine:
            outcome = {
                "intent_id": intent.intent_id,
                "action": intent.action,
                "success": response.executed or response.status == "completed",
                "response": response.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
            
            await self.learning_engine.record_outcome(outcome)
    
    def get_enterprise_stats(self) -> Dict[str, Any]:
        """Get Enterprise-specific statistics"""
        base_stats = super().get_server_stats()
        
        return {
            **base_stats,
            "enterprise_features": {
                "license_valid": True,
                "audit_entries": len(self.audit_log),
                "learning_enabled": self.learning_engine is not None,
                "modes_available": ["advisory", "approval", "autonomous"],
                "execution_allowed": True,
            },
            "compliance": {
                "audit_trail": len(self.audit_log) > 0,
                "license_check": True,
                "enterprise_only": True,
            }
        }


class LicenseError(Exception):
    """Enterprise license error"""
    pass
```
### 3.6 Step 6: CI/CD Pipeline Configuration
```yaml
# .github/workflows/oss-enforcement.yml
name: OSS Boundary Enforcement

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  enforce-oss-purity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install astunparse
          
      - name: Validate OSS Constants
        run: |
          python scripts/enforce_oss_constants.py
          
      - name: Check for Enterprise Patterns
        run: |
          # Scan OSS directories for forbidden code
          echo "Scanning for Enterprise code in OSS directories..."
          
          # Check for execution modes
          if grep -r "MCPMode.APPROVAL\|MCPMode.AUTONOMOUS" arf-core/ arf-mcp-client/; then
            echo "❌ Found Enterprise execution modes in OSS code"
            exit 1
          fi
          
          # Check for license validation
          if grep -r "license_key\|validate_license" arf-core/src/ arf-mcp-client/src/; then
            echo "❌ Found license validation in OSS code"
            exit 1
          fi
          
          # Check for audit trails
          if grep -r "audit_log\|audit_trail" arf-core/src/security/; then
            echo "❌ Found audit trails in OSS security"
            exit 1
          fi
          
          echo "✅ OSS code is pure"
          
      - name: Validate License Headers
        run: |
          python scripts/validate_headers.py --directory arf-core --license apache2
          python scripts/validate_headers.py --directory arf-mcp-client --license apache2
          
      - name: Run OSS Tests
        run: |
          pytest arf-core/tests/ -v
          pytest arf-mcp-client/tests/ -v
          
  build-enterprise:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'enterprise')
    steps:
      - uses: actions/checkout@v3
        
      - name: Build Enterprise Packages
        run: |
          # Build Enterprise Docker image
          docker build -f enterprise-docker/Dockerfile -t arf/enterprise:latest .
          
          # Build OSS Docker image (for reference)
          docker build -f Dockerfile -t arf/oss:latest .
          
      - name: Run Enterprise Tests
        run: |
          # Tests that require Enterprise features
          pytest tests/enterprise/ -v
```
### 3.7 Step 7: Configuration Separation
```python
# arf-core/src/config/oss_config.py
"""
OSS Configuration - Limited, immutable
"""

from pydantic import BaseModel, Field
from typing import Final


class OSSConfig(BaseModel):
    """OSS configuration with hard limits"""
    
    # These values are FINAL in OSS
    MAX_INCIDENT_HISTORY: Final[int] = Field(default=1000, frozen=True)
    MAX_RAG_LOOKBACK_DAYS: Final[int] = Field(default=7, frozen=True)
    MCP_MODE: Final[str] = Field(default="advisory", frozen=True)
    EXECUTION_ALLOWED: Final[bool] = Field(default=False, frozen=True)
    GRAPH_STORAGE: Final[str] = Field(default="in_memory", frozen=True)
    
    # Configurable but limited
    hf_api_key: str = ""
    hf_api_url: str = "https://router.huggingface.co/hf-inference/v1/completions"
    
    # Anomaly thresholds (configurable)
    latency_critical: float = 300.0
    latency_warning: float = 150.0
    error_rate_critical: float = 0.3
    
    @property
    def is_oss(self) -> bool:
        """Always True for OSS build"""
        return True
    
    def validate_oss_limits(self):
        """Validate OSS configuration doesn't exceed limits"""
        violations = []
        
        if self.MAX_INCIDENT_HISTORY > 1000:
            violations.append("MAX_INCIDENT_HISTORY > 1000")
        
        if self.MCP_MODE != "advisory":
            violations.append(f"MCP_MODE must be 'advisory', got '{self.MCP_MODE}'")
        
        if self.EXECUTION_ALLOWED:
            violations.append("EXECUTION_ALLOWED must be False")
        
        if violations:
            raise ValueError(f"OSS configuration violations: {violations}")


# Global OSS config
oss_config = OSSConfig()
oss_config.validate_oss_limits()
```
## 4. Migration Strategy for Existing Users
### 4.1 Backward Compatibility Layer
```python
# arf-core/src/compatibility.py
"""
Backward compatibility for existing users
"""

import warnings
from typing import Dict, Any
from .constants import MCP_MODES_ALLOWED, EXECUTION_ALLOWED


class CompatibilityLayer:
    """
    Provides backward compatibility while enforcing new boundaries
    """
    
    @staticmethod
    def create_mcp_client() -> Any:
        """
        Backward compatible factory function
        Returns OSS client, warns if trying to use Enterprise features
        """
        from .mcp_client import OSSMCPClient
        
        # Warn about mode limitations
        warnings.warn(
            "OSS version only supports advisory mode. "
            "Upgrade to Enterprise for approval/autonomous modes.",
            UserWarning,
            stacklevel=2
        )
        
        return OSSMCPClient()
    
    @staticmethod
    def check_enterprise_feature(feature_name: str, current_mode: str = "advisory"):
        """Check if feature requires Enterprise license"""
        enterprise_features = {
            "autonomous_execution": "autonomous",
            "approval_workflow": "approval",
            "persistent_storage": "autonomous",
            "learning_engine": "autonomous",
            "audit_trails": "approval",
        }
        
        required_mode = enterprise_features.get(feature_name)
        if required_mode and required_mode not in MCP_MODES_ALLOWED:
            raise FeatureRequiresEnterpriseError(feature_name, required_mode)


class FeatureRequiresEnterpriseError(Exception):
    """Error for features that require Enterprise license"""
    
    def __init__(self, feature_name: str, required_mode: str):
        super().__init__(
            f"Feature '{feature_name}' requires Enterprise license "
            f"(mode: {required_mode}). "
            f"Visit https://arf.dev/enterprise to upgrade."
        )
```
### 4.2 Upgrade Path Documentation
Create UPGRADE_TO_ENTERPRISE.md:

```markdown
# Upgrading from OSS to Enterprise

## Why Upgrade?

| Feature             | OSS                      | Enterprise                        |
|---------------------|--------------------------|-----------------------------------|
| **Execution Modes** | Advisory only            | Advisory, Approval, Autonomous    |
| **Storage**         | In-memory (1k incidents) | Persistent (unlimited)            |
| **Learning**        | None                     | Continuous learning from outcomes |
| **Compliance**      | Basic                    | SOC2, GDPR, HIPAA ready           |
| **Support**         | Community                | 24/7 Enterprise support           |

## Migration Steps

### 1. Export OSS Data
```bash
# Export your incidents
python -m arf_core.cli export incidents --format json > oss_backup.json

# Export configurations
python -m arf_core.cli export config > oss_config.json
2. Install Enterprise
bash
# Install Enterprise package
pip install arf-enterprise

# Set license key
export ARF_LICENSE_KEY="ARF-ENT-YOUR-LICENSE-KEY"
3. Import Data
bash
# Import to Enterprise
python -m arf_enterprise.cli import incidents oss_backup.json
python -m arf_enterprise.cli import config oss_config.json
4. Verify Migration
bash
# Check Enterprise features
python -m arf_enterprise.cli status

# Test execution modes
python -m arf_enterprise.cli test --mode=autonomous
API Changes
OSS API (stays the same):
python
from arf_core import create_mcp_client
client = create_mcp_client()  # Always advisory mode
Enterprise API (enhanced):
python
from arf_enterprise import create_enterprise_mcp_server
server = create_enterprise_mcp_server(license_key="...")
# All modes available
Support
Contact enterprise-support@arf.dev for migration assistance.

text
```
---

## 5. Testing Strategy

### 5.1 OSS Boundary Tests

```python
# tests/test_oss_boundaries.py
import pytest
from arf_core.constants import (
    MAX_INCIDENT_HISTORY,
    MCP_MODES_ALLOWED,
    EXECUTION_ALLOWED
)


def test_oss_constants_immutable():
    """Test OSS constants cannot be changed"""
    assert MAX_INCIDENT_HISTORY == 1000
    assert MCP_MODES_ALLOWED == ("advisory",)
    assert EXECUTION_ALLOWED is False
    
    # Try to change (should fail in actual implementation)
    with pytest.raises(Exception):
        import arf_core.constants as constants
        constants.MAX_INCIDENT_HISTORY = 2000


def test_oss_mcp_client_limits():
    """Test OSS MCP client only supports advisory mode"""
    from arf_mcp_client import OSSMCPClient
    
    client = OSSMCPClient()
    capabilities = client.get_capabilities()
    
    assert capabilities["mode"] == "advisory"
    assert capabilities["can_execute"] is False
    assert capabilities["can_advise"] is True
    
    # Should not have Enterprise features
    assert "license_key" not in capabilities
    assert "audit_trail" not in capabilities


def test_healing_intent_creation():
    """Test OSS can create healing intents"""
    from arf_core.models.healing_intent import HealingIntent
    from datetime import datetime
    
    intent = HealingIntent(
        action="restart_container",
        parameters={"service": "api"},
        justification="High latency detected",
        confidence=0.85,
        incident_id="inc_123",
        component="api-service",
        detected_at=datetime.now()
    )
    
    # OSS can create intent
    assert intent.action == "restart_container"
    assert intent.confidence == 0.85
    
    # Can convert to Enterprise request
    enterprise_request = intent.to_enterprise_request()
    assert enterprise_request["requires_enterprise"] is True
    assert "intent_id" in enterprise_request
```
### 5.2 Enterprise Integration Tests
```python
# tests/enterprise/test_enterprise_features.py
import pytest
import httpx


@pytest.mark.enterprise
class TestEnterpriseFeatures:
    """Tests that require Enterprise license"""
    
    @pytest.fixture
    def enterprise_client(self):
        """Enterprise API client with license"""
        return httpx.AsyncClient(
            base_url="http://localhost:8080",
            headers={
                "X-API-Key": "test-enterprise-key",
                "X-License-Key": "ARF-ENT-TEST-LICENSE"
            }
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_execution(self, enterprise_client):
        """Test autonomous execution (Enterprise only)"""
        response = await enterprise_client.post(
            "/api/v1/execute",
            json={
                "tool": "rollback",
                "component": "api-service",
                "parameters": {"revision": "previous"},
                "mode": "autonomous",
                "justification": "Critical outage detected"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["executed"] is True
        assert "audit_trail_id" in result
    
    @pytest.mark.asyncio 
    async def test_approval_workflow(self, enterprise_client):
        """Test approval workflow (Enterprise only)"""
        response = await enterprise_client.post(
            "/api/v1/execute",
            json={
                "tool": "scale_out",
                "component": "database",
                "parameters": {"factor": 2},
                "mode": "approval",
                "justification": "High load requires scaling"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "pending_approval"
        assert "approval_id" in result
    
    def test_license_validation(self):
        """Test Enterprise license validation"""
        from arf_enterprise.mcp_server import EnterpriseMCPServer
        
        # Valid license should work
        server = EnterpriseMCPServer(license_key="ARF-ENT-TEST-LICENSE-12345")
        assert server.license_key is not None
        
        # Invalid license should fail
        with pytest.raises(Exception, match="Enterprise license required"):
            EnterpriseMCPServer(license_key="invalid")
```
## 6. Deployment Configuration
### 6.1 OSS Dockerfile
```dockerfile
# Dockerfile (OSS)
FROM python:3.11-slim

WORKDIR /app

# Install OSS packages only
COPY arf-core/ ./arf-core/
COPY arf-mcp-client/ ./arf-mcp-client/
COPY arf-rag/ ./arf-rag/

# Install OSS dependencies
COPY requirements-oss.txt .
RUN pip install --no-cache-dir -r requirements-oss.txt
RUN pip install --no-cache-dir -e ./arf-core -e ./arf-mcp-client -e ./arf-rag

# OSS environment
ENV ARF_TIER=oss
ENV ARF_MCP_MODE=advisory
ENV ARF_MAX_INCIDENT_HISTORY=1000
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000
USER 1000:1000

CMD ["python", "-m", "arf_core.api"]
6.2 Enterprise Docker Compose
yaml
# docker-compose.enterprise.yml
version: '3.8'

services:
  arf-oss:
    image: arf/oss:latest
    environment:
      ARF_TIER: oss
      ARF_ENTERPRISE_URL: http://arf-enterprise:8080
    ports:
      - "8000:8000"
    networks:
      - arf-network

  arf-enterprise:
    image: arf/enterprise:latest
    environment:
      ARF_TIER: enterprise
      ARF_LICENSE_KEY: ${ARF_LICENSE_KEY}
      ARF_MCP_MODE: autonomous
      NEO4J_URI: bolt://neo4j:7687
    ports:
      - "8080:8080"
    volumes:
      - audit-data:/var/lib/arf/audit
      - backup-data:/var/lib/arf/backup
    networks:
      - arf-network
    depends_on:
      - neo4j

  neo4j:
    image: neo4j:5-enterprise
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_ACCEPT_LICENSE_AGREEMENT: yes
    volumes:
      - neo4j-data:/data
    networks:
      - arf-network

networks:
  arf-network:
    driver: bridge

volumes:
  neo4j-data:
  audit-data:
  backup-data:
```
## 7. Success Criteria & Validation
### 7.1 OSS Success (Day 1-2):
MAX_INCIDENT_HISTORY=1000 enforced at build time

MCP mode hard-coded to "advisory" in OSS

HealingIntent created but not executed

CI/CD passes OSS boundary checks

All existing tests pass

### 7.2 Enterprise Success (Day 3-4):
License validation working

All three MCP modes available

Audit trails implemented

Learning engine integrated

OSS→Enterprise handoff working

### 7.3 Business Success (Day 5):
Clear upgrade path documented

Pricing page with feature comparison

License key generation system

Support channels established

Migration documentation complete

### 8. Immediate Next Steps
Today/Tomorrow:
Create the OSS constants file (arf-core/src/constants.py)

Implement build-time enforcement script (scripts/enforce_oss_constants.py)

Create HealingIntent model (arf-core/src/models/healing_intent.py)

Set up CI/CD pipeline with boundary checks

Day 2:
Create OSS MCP client (advisory only)

Enhance Enterprise MCP server with license validation

Write boundary tests

Day 3-5:
Implement remaining components

Create documentation

Set up deployment configurations

9. Risk Mitigation
Risk	Impact	Mitigation
Breaking existing users	High	Backward compatibility layer
OSS contamination	High	Build-time enforcement in CI/CD
License bypass	Critical	Runtime validation + audit
Performance impact	Medium	Gradual rollout, feature flags
Migration complexity	Medium	Clear documentation, migration tools
