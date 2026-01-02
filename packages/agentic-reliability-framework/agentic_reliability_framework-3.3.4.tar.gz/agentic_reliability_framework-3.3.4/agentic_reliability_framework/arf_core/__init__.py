"""
ARF Core Module - OSS Edition
Production-grade multi-agent AI for reliability monitoring
OSS Edition: Advisory mode only, Apache 2.0 Licensed

IMPORTANT: Direct imports only - no lazy loading to avoid circular dependencies
"""

# ============================================================================
# DIRECT IMPORTS - NO LAZY LOADING
# ============================================================================

# Import constants FIRST (they have no dependencies)
from .constants import (
    MAX_INCIDENT_HISTORY,
    MCP_MODES_ALLOWED,
    EXECUTION_ALLOWED,
    GRAPH_STORAGE,
    validate_oss_constants,
    get_oss_capabilities,
    OSSBoundaryError,
)

# Import models SECOND (they only depend on standard library)
from .models.healing_intent import (
    HealingIntent,
    HealingIntentSerializer,
    create_rollback_intent,
    create_restart_intent,
    create_scale_out_intent,
)

# Import config THIRD (depends on constants)
from .config.oss_config import (
    OSSConfig,
    load_oss_config_from_env,
)

# ============================================================================
# DYNAMIC IMPORTS FOR ENGINE MODULES
# ============================================================================

# We'll handle MCP clients dynamically to avoid circular imports
_oss_mcp_client_class = None

def _get_oss_mcp_client_class():
    """Dynamically import OSSMCPClient on first use"""
    global _oss_mcp_client_class
    if _oss_mcp_client_class is None:
        try:
            # Import when first accessed - breaks circular chain
            from .engine.simple_mcp_client import OSSMCPClient
            _oss_mcp_client_class = OSSMCPClient
        except ImportError as e:
            print(f"⚠️  Could not import OSSMCPClient: {e}")
            
            # Minimal fallback class
            class MinimalOSSMCPClient:
                def __init__(self, config=None):
                    self.mode = "advisory"
                    self.config = config or {}
                
                async def execute_tool(self, request_dict):
                    from datetime import datetime
                    
                    return {
                        "request_id": request_dict.get("request_id", "oss-request"),
                        "status": "advisory",
                        "message": f"Advisory analysis for {request_dict.get('tool', 'unknown')}",
                        "executed": False,
                        "result": {
                            "mode": "advisory",
                            "requires_enterprise": True,
                            "upgrade_url": "https://arf.dev/enterprise"
                        }
                    }
                
                def get_client_stats(self):
                    return {
                        "mode": "advisory",
                        "oss_edition": True,
                        "can_execute": False,
                        "can_advise": True,
                        "enterprise_upgrade_available": True
                    }
            
            _oss_mcp_client_class = MinimalOSSMCPClient
    
    return _oss_mcp_client_class

def create_mcp_client(config=None):
    """Factory function for OSSMCPClient"""
    OSSMCPClientClass = _get_oss_mcp_client_class()
    return OSSMCPClientClass(config=config)

# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # OSS Models
    "HealingIntent",
    "HealingIntentSerializer",
    "create_rollback_intent",
    "create_restart_intent",
    "create_scale_out_intent",
    
    # OSS Constants
    "MAX_INCIDENT_HISTORY",
    "MCP_MODES_ALLOWED",
    "EXECUTION_ALLOWED",
    "GRAPH_STORAGE",
    "validate_oss_constants",
    "get_oss_capabilities",
    "OSSBoundaryError",
    
    # OSS Config
    "OSSConfig",
    "load_oss_config_from_env",
    
    # OSS Engine (will be available as properties)
    "OSSMCPClient",
    "create_mcp_client",
]

# ============================================================================
# PROPERTY-BASED EXPORTS FOR DYNAMIC LOADING
# ============================================================================

import sys

class _ARFCoreModule(sys.modules[__name__].__class__):
    """Custom module class with property-based exports"""
    
    @property
    def OSSMCPClient(self):
        """Dynamically load OSSMCPClient class on access"""
        return _get_oss_mcp_client_class()

# Replace module class
if not isinstance(sys.modules[__name__], _ARFCoreModule):
    sys.modules[__name__].__class__ = _ARFCoreModule

# ============================================================================
# MODULE METADATA
# ============================================================================

OSS_EDITION = True
OSS_LICENSE = "Apache 2.0"
OSS_VERSION = "2.0.2"
ENTERPRISE_UPGRADE_URL = "https://arf.dev/enterprise"
