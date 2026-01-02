# arf_core/models/__init__.py - FIXED VERSION
"""
OSS Models Module
Apache 2.0 Licensed
"""

from .healing_intent import (
    HealingIntent,
    HealingIntentSerializer,
    HealingIntentError,
    SerializationError,
    ValidationError,
    IntentSource,
    IntentStatus,
    create_rollback_intent,
    create_restart_intent,
    create_scale_out_intent,
    create_oss_advisory_intent,
)

# Define EventSeverity enum
from enum import Enum

class EventSeverity(Enum):
    """Severity levels for reliability events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Define ReliabilityEvent dataclass
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ReliabilityEvent:
    """Reliability event for OSS analysis"""
    component: str
    severity: EventSeverity
    latency_p99: float = 100.0
    error_rate: float = 0.05
    throughput: float = 1000.0
    cpu_util: float = 0.5
    memory_util: float = 0.5
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Initialize timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

__all__ = [
    "HealingIntent",
    "HealingIntentSerializer",
    "HealingIntentError",
    "SerializationError",
    "ValidationError",
    "IntentSource",
    "IntentStatus",
    "create_rollback_intent",
    "create_restart_intent",
    "create_scale_out_intent",
    "create_oss_advisory_intent",
    "ReliabilityEvent",
    "EventSeverity",
]
