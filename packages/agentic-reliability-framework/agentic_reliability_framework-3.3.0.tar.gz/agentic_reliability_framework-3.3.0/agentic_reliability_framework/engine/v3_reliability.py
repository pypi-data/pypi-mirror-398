"""
Enhanced V3 Reliability Engine with RAG Graph and MCP Server integration.
Extends the base V3ReliabilityEngine with full v3 features.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, cast, TYPE_CHECKING

import numpy as np

# Local imports with conditional typing
if TYPE_CHECKING:
    from ..memory.rag_graph import RAGGraphMemory
    from ..engine.mcp_server import MCPServer
    from ..models import ReliabilityEvent
else:
    # Runtime imports will be done lazily
    pass

from ..config import config
from .interfaces import ReliabilityEngineProtocol
from .reliability import V3ReliabilityEngine as BaseV3Engine, MCPResponse as BaseMCPResponse

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LEARNING_MIN_DATA_POINTS = 5


@dataclass
class MCPResponse(BaseMCPResponse):
    """Extended MCP response with v3 enhancements"""
    approval_id: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with v3 fields"""
        base_dict = super().to_dict()
        if self.approval_id:
            base_dict["approval_id"] = self.approval_id
        if self.tool_result:
            base_dict["tool_result"] = self.tool_result
        return base_dict


class V3ReliabilityEngine(BaseV3Engine):
    """
    Enhanced reliability engine with RAG Graph memory and MCP execution boundary.
    
    Extends the base V3ReliabilityEngine with:
    1. Semantic search of similar incidents via FAISS
    2. Historical context enhancement for policy decisions  
    3. MCP-governed execution of healing actions
    4. Outcome recording for continuous learning loop
    """
    
    def __init__(
        self,
        rag_graph: Optional[RAGGraphMemory] = None,
        mcp_server: Optional[MCPServer] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize enhanced V3 engine with RAG and MCP dependencies.
        
        Args:
            rag_graph: RAG graph for historical context
            mcp_server: MCP server for execution boundary
            *args: Additional args passed to base class
            **kwargs: Additional kwargs passed to base class
        """
        # Pass RAG and MCP to base class via kwargs
        kwargs['rag_graph'] = rag_graph
        kwargs['mcp_server'] = mcp_server
        super().__init__(*args, **kwargs)
        
        # V3-specific state
        self._v3_lock = threading.RLock()
        self.v3_metrics: Dict[str, Any] = {
            "v3_features_active": True,
            "rag_queries": 0,
            "rag_cache_hits": 0,
            "mcp_calls": 0,
            "mcp_successes": 0,
            "learning_updates": 0,
            "similar_incidents_found": 0,
            "historical_context_used": 0,
        }
        
        # Learning state
        self.learning_state: Dict[str, Any] = {
            "successful_predictions": 0,
            "failed_predictions": 0,
            "total_learned_patterns": 0,
            "last_learning_update": time.time(),
        }
        
        logger.info(
            f"Initialized Enhanced V3ReliabilityEngine with RAG and MCP "
            f"(RAG={rag_graph is not None}, MCP={mcp_server is not None})"
        )
    
    @property
    def v3_enabled(self) -> bool:
        """Check if v3 features should be used based on config"""
        # Check feature flags
        if not getattr(config, 'rag_enabled', False):
            return False
        
        if not getattr(config, 'mcp_enabled', False):
            return False
        
        # Check rollout percentage if configured
        rollout_percentage = getattr(config, 'rollout_percentage', 100)
        if rollout_percentage < 100:
            # Simple hash-based rollout
            import random
            random.seed(int(time.time()))
            return random.random() * 100 < rollout_percentage
        
        return True
    
    async def process_event_enhanced(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Enhanced event processing with RAG retrieval and MCP execution.
        
        Extends the base implementation with v3 features.
        """
        event = kwargs.get("event") or (args[0] if args else None)
        if not event or not isinstance(event, ReliabilityEvent):
            return {
                "status": "ERROR",
                "incident_id": "",
                "error": "Invalid event",
                "healing_actions": []
            }
        
        # Start timing
        start_time = time.time()
        
        try:
            # Step 1: Run base processing
            base_result = await super().process_event_enhanced(event)
            
            # If not an anomaly, return early
            if base_result.get("status") != "ANOMALY":
                return base_result
            
            # Step 2: RAG RETRIEVAL (v3 enhancement)
            rag_context: Dict[str, Any] = {}
            similar_incidents: List[Any] = []
            
            if self.v3_enabled and self.rag:
                try:
                    # Use RAG to find similar historical incidents
                    similar_incidents = self.rag.find_similar(event, k=3)
                    
                    with self._v3_lock:
                        self.v3_metrics["rag_queries"] += 1
                        self.v3_metrics["similar_incidents_found"] += len(similar_incidents)
                    
                    # Build RAG context
                    rag_context = self._build_rag_context(similar_incidents, event)
                    
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")
                    # Continue without RAG context
            
            # Step 3: ENHANCE POLICY DECISION with historical context
            enhanced_actions = []
            base_actions = base_result.get("healing_actions", [])
            
            if similar_incidents:
                # Enhance with historical context
                enhanced_actions = self._enhance_actions_with_context(
                    base_actions, similar_incidents, event, rag_context
                )
                
                with self._v3_lock:
                    self.v3_metrics["historical_context_used"] += 1
            else:
                enhanced_actions = base_actions
            
            # Step 4: MCP EXECUTION BOUNDARY (v3 enhancement)
            mcp_results: List[Dict[str, Any]] = []
            executed_actions: List[Dict[str, Any]] = []
            
            if self.v3_enabled and self.mcp and enhanced_actions:
                for action in enhanced_actions:
                    try:
                        # Create MCP request
                        mcp_request = self._create_mcp_request(
                            action, event, similar_incidents, rag_context
                        )
                        
                        # Execute via MCP
                        mcp_response_dict = await self.mcp.execute_tool(mcp_request)
                        
                        # Convert to MCPResponse object
                        mcp_response = MCPResponse(
                            executed=mcp_response_dict.get("executed", False),
                            status=mcp_response_dict.get("status", "unknown"),
                            result=mcp_response_dict.get("result", {}),
                            message=mcp_response_dict.get("message", ""),
                            approval_id=mcp_response_dict.get("approval_id"),
                            tool_result=mcp_response_dict.get("tool_result")
                        )
                        
                        with self._v3_lock:
                            self.v3_metrics["mcp_calls"] += 1
                            if mcp_response.executed or mcp_response.status == "completed":
                                self.v3_metrics["mcp_successes"] += 1
                        
                        mcp_results.append(mcp_response.to_dict())
                        
                        # If action was executed, record it
                        if mcp_response.executed or mcp_response.status == "completed":
                            executed_actions.append(action)
                            
                            # Step 5: OUTCOME RECORDING (v3 learning loop)
                            if self.rag:
                                outcome = await self._record_outcome(
                                    incident_id=base_result["incident_id"],
                                    action=action,
                                    mcp_response=mcp_response.to_dict(),  # Pass as dict
                                    event=event,
                                    similar_incidents=similar_incidents
                                )
                                
                                # Update learning state
                                success = outcome.get("success", False)
                                self._update_learning_state(success, {
                                    "incident_id": base_result["incident_id"],
                                    "action": action,
                                    "similar_incidents_count": len(similar_incidents),
                                    "rag_context": rag_context
                                })
                    
                    except Exception as e:
                        logger.error(f"MCP execution failed for action {action.get('action', 'unknown')}: {e}")
                        mcp_results.append({
                            "error": str(e),
                            "executed": False,
                            "status": "failed"
                        })
            
            # Step 6: Build comprehensive result
            result: Dict[str, Any] = {
                **base_result,
                "v3_processing": "enabled" if self.v3_enabled else "disabled",
                "v3_enhancements": {
                    "rag_enabled": bool(self.rag),
                    "mcp_enabled": bool(self.mcp),
                    "learning_enabled": getattr(config, 'learning_enabled', False),
                },
                "processing_time_ms": (time.time() - start_time) * 1000,
                "engine_version": "v3_enhanced",
            }
            
            # Add v3-specific data if available
            if similar_incidents:
                result["rag_context"] = {
                    "similar_incidents_count": len(similar_incidents),
                    "avg_similarity": rag_context.get("avg_similarity", 0.0),
                    "most_effective_action": rag_context.get("most_effective_action"),
                    "historical_success_rate": rag_context.get("success_rate", 0.0),
                }
            
            if mcp_results:
                result["mcp_execution"] = mcp_results
                result["executed_actions"] = executed_actions
            
            # Update metrics
            with self._lock:
                self.metrics["events_processed"] += 1
                if base_result.get("status") == "ANOMALY":
                    self.metrics["anomalies_detected"] += 1
                if mcp_results:
                    executed_count = len([r for r in mcp_results if r.get("executed")])
                    self.metrics["mcp_executions"] += executed_count
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in enhanced v3 event processing: {e}")
            
            # Fall back to base result on error
            try:
                base_result = await super().process_event_enhanced(event)
                base_result["v3_error"] = str(e)
                base_result["v3_processing"] = "failed"
                return base_result
            except Exception as base_error:
                return {
                    "status": "ERROR",
                    "incident_id": f"error_{int(time.time())}_{event.component if event else 'unknown'}",
                    "error": f"v3: {e}, base fallback: {base_error}",
                    "v3_processing": "failed",
                    "processing_time_ms": (time.time() - start_time) * 1000,
                }
    
    def _build_rag_context(
        self, 
        similar_incidents: List[Any], 
        current_event: ReliabilityEvent
    ) -> Dict[str, Any]:
        """Build RAG context from similar incidents"""
        if not similar_incidents:
            return {}
        
        context: Dict[str, Any] = {
            "similar_incidents_count": len(similar_incidents),
            "avg_similarity": self._calculate_avg_similarity(similar_incidents),
            "success_rate": self._calculate_success_rate(similar_incidents),
            "component_match": all(
                hasattr(incident, 'component') and incident.component == current_event.component 
                for incident in similar_incidents
            ),
        }
        
        # Get most effective action if RAG supports it
        if self.rag and hasattr(self.rag, 'get_most_effective_actions'):
            try:
                effective_actions = self.rag.get_most_effective_actions(
                    current_event.component, k=1
                )
                if effective_actions:
                    context["most_effective_action"] = effective_actions[0]
            except Exception as e:
                logger.debug(f"Error getting most effective actions: {e}")
        
        return context
    
    def _calculate_avg_similarity(self, similar_incidents: List[Any]) -> float:
        """Calculate average similarity score from similar incidents"""
        if not similar_incidents:
            return 0.0
        
        scores = []
        for incident in similar_incidents:
            if hasattr(incident, 'metadata'):
                score = incident.metadata.get("similarity_score")
                if score is not None:
                    scores.append(float(score))
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _calculate_success_rate(self, similar_incidents: List[Any]) -> float:
        """Calculate success rate from similar incidents"""
        if not similar_incidents:
            return 0.0
        
        successful_outcomes = 0
        total_outcomes = 0
        
        for incident in similar_incidents:
            if hasattr(incident, 'outcomes') and incident.outcomes:
                total_outcomes += len(incident.outcomes)
                successful_outcomes += sum(
                    1 for o in incident.outcomes 
                    if hasattr(o, 'success') and o.success
                )
        
        return float(successful_outcomes) / total_outcomes if total_outcomes > 0 else 0.0
    
    def _enhance_actions_with_context(
        self, 
        base_actions: List[Dict[str, Any]],
        similar_incidents: List[Any],
        event: ReliabilityEvent,
        rag_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance healing actions with historical context"""
        if not base_actions:
            return []
        
        enhanced_actions = []
        
        for action in base_actions:
            # Create enhanced action with historical context
            enhanced_action = {
                **action,
                "v3_enhanced": True,
                "historical_confidence": rag_context.get("avg_similarity", 0.0),
                "similar_incidents_count": len(similar_incidents),
                "context_source": "rag_graph",
            }
            
            # Add effectiveness score if available
            most_effective = rag_context.get("most_effective_action")
            if most_effective and action.get("action") == most_effective.get("action"):
                enhanced_action["historical_effectiveness"] = most_effective.get("success_rate", 0.0)
                enhanced_action["confidence_boost"] = True
            
            enhanced_actions.append(enhanced_action)
        
        # Sort by historical confidence (descending)
        enhanced_actions.sort(
            key=lambda x: float(x.get("historical_confidence", 0.0)), 
            reverse=True
        )
        
        return enhanced_actions
    
    def _create_mcp_request(
        self, 
        action: Dict[str, Any],
        event: ReliabilityEvent,
        historical_context: List[Any],
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create MCP request from enhanced action"""
        # Build justification with historical context
        justification_parts = [
            f"Event: {event.component} with {event.latency_p99:.0f}ms latency, {event.error_rate*100:.1f}% errors",
        ]
        
        if historical_context:
            justification_parts.append(
                f"Based on {len(historical_context)} similar historical incidents"
            )
        
        if rag_context and rag_context.get("most_effective_action"):
            effective = rag_context["most_effective_action"]
            justification_parts.append(
                f"Historically {effective.get('action')} has {effective.get('success_rate', 0)*100:.0f}% success rate"
            )
        
        justification = ". ".join(justification_parts)
        
        return {
            "tool": action.get("action", "unknown"),
            "component": event.component,
            "parameters": action.get("parameters", {}),
            "justification": justification,
            "metadata": {
                "event_fingerprint": getattr(event, 'fingerprint', ''),
                "event_severity": event.severity.value if hasattr(event.severity, 'value') else "unknown",
                "similar_incidents_count": len(historical_context),
                "historical_confidence": rag_context.get("avg_similarity", 0.0) if rag_context else 0.0,
                "rag_context": rag_context,
                **action.get("metadata", {})
            }
        }
    
    async def _record_outcome(
        self, 
        incident_id: str, 
        action: Dict[str, Any],
        mcp_response: Dict[str, Any],
        event: Optional[ReliabilityEvent] = None,
        similar_incidents: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Record outcome for learning loop"""
        if not self.rag:
            return {}
        
        try:
            # Determine success from mcp_response
            success = (
                mcp_response.get("status") == "completed" or 
                mcp_response.get("executed", False) or
                mcp_response.get("result", {}).get("success", False)
            )
            
            # Estimate resolution time (in production this would be actual time)
            resolution_time_minutes = 5.0  # Default estimate
            
            # Extract lessons learned
            lessons_learned = []
            if not success and mcp_response.get("message"):
                lessons_learned.append(f"Failed: {mcp_response['message']}")
            
            # Store outcome in RAG
            outcome_id = self.rag.store_outcome(
                incident_id=incident_id,
                actions_taken=[action.get("action", "unknown")],
                success=success,
                resolution_time_minutes=resolution_time_minutes,
                lessons_learned=lessons_learned
            )
            
            return {
                "outcome_id": outcome_id,
                "success": success,
                "resolution_time_minutes": resolution_time_minutes,
                "action": action.get("action", "unknown"),
            }
            
        except Exception as e:
            logger.error(f"Error recording outcome: {e}")
            return {}
    
    def _update_learning_state(
        self, 
        success: bool,
        context: Dict[str, Any]
    ) -> None:
        """Update learning state based on outcome"""
        if not getattr(config, 'learning_enabled', False):
            return
        
        with self._v3_lock:
            self.learning_state["last_learning_update"] = time.time()
            
            if success:
                self.learning_state["successful_predictions"] += 1
            else:
                self.learning_state["failed_predictions"] += 1
            
            # Check if we should extract new patterns
            total_predictions = (
                self.learning_state["successful_predictions"] + 
                self.learning_state["failed_predictions"]
            )
            
            learning_min_data_points = getattr(config, 'learning_min_data_points', DEFAULT_LEARNING_MIN_DATA_POINTS)
            if total_predictions % learning_min_data_points == 0:
                self._extract_learning_patterns(context)
                self.learning_state["total_learned_patterns"] += 1
                self.v3_metrics["learning_updates"] += 1
    
    def _extract_learning_patterns(self, context: Dict[str, Any]) -> None:
        """Extract learning patterns from context"""
        # Placeholder for pattern extraction logic
        logger.debug("Extracting learning patterns from context")
        
        # Example pattern extraction
        incident_id = context.get("incident_id")
        action = context.get("action", {})
        similar_count = context.get("similar_incidents_count", 0)
        
        if similar_count > 0 and action.get("historical_effectiveness", 0) > 0.7:
            logger.info(f"Learned pattern: Action {action.get('action')} effective with historical context")
    
# In v3_reliability.py, update the get_stats and shutdown methods:

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics including v3"""
        try:
            # Try to get base stats from superclass
            base_stats = super().get_stats()
        except AttributeError:
            # Fallback if base class doesn't have get_stats
            logger.warning("Base class doesn't have get_stats, using fallback")
            base_stats = {
                "events_processed": self.metrics.get("events_processed", 0),
                "anomalies_detected": self.metrics.get("anomalies_detected", 0),
                "rag_queries": self.metrics.get("rag_queries", 0),
                "mcp_executions": self.metrics.get("mcp_executions", 0),
                "successful_outcomes": self.metrics.get("successful_outcomes", 0),
                "failed_outcomes": self.metrics.get("failed_outcomes", 0),
                "uptime_seconds": time.time() - self._start_time,
                "engine_version": "v3_base_fallback",
            }
        
        # Add v3 metrics
        with self._v3_lock:
            v3_stats = self.v3_metrics.copy()
            
            # Calculate rates
            if v3_stats["rag_queries"] > 0:
                v3_stats["rag_cache_hit_rate"] = float(v3_stats["rag_cache_hits"]) / v3_stats["rag_queries"]
            
            if v3_stats["mcp_calls"] > 0:
                v3_stats["mcp_success_rate"] = float(v3_stats["mcp_successes"]) / v3_stats["mcp_calls"]
            
            # Add learning state
            v3_stats.update(self.learning_state)
            
            # Add feature status
            v3_stats["feature_status"] = {
                "rag_available": self.rag is not None,
                "mcp_available": self.mcp is not None,
                "rag_enabled": getattr(config, 'rag_enabled', False),
                "mcp_enabled": getattr(config, 'mcp_enabled', False),
                "learning_enabled": getattr(config, 'learning_enabled', False),
                "rollout_percentage": getattr(config, 'rollout_percentage', 0),
            }
        
        # Combine stats
        combined_stats: Dict[str, Any] = {
            **base_stats,
            "engine_version": "v3_enhanced",
            "v3_features": v3_stats["v3_features_active"],
            "v3_metrics": v3_stats,
            "rag_graph_stats": self.rag.get_graph_stats() if self.rag and hasattr(self.rag, 'get_graph_stats') else None,
            "mcp_server_stats": self.mcp.get_server_stats() if self.mcp and hasattr(self.mcp, 'get_server_stats') else None,
        }
        
        return combined_stats
    
    def shutdown(self) -> None:
        """Graceful shutdown of enhanced v3 engine"""
        logger.info("Shutting down Enhanced V3ReliabilityEngine...")
        
        # Save any pending learning data
        if getattr(config, 'learning_enabled', False):
            logger.info(f"Saved {self.learning_state['total_learned_patterns']} learning patterns")
        
        try:
            # Try to call super().shutdown() if it exists
            super().shutdown()
        except AttributeError:
            # Base class doesn't have shutdown, just log
            logger.debug("Base class doesn't have shutdown method")
        
        logger.info("Enhanced V3ReliabilityEngine shutdown complete")


# Factory function for backward compatibility
def create_v3_engine(
    rag_graph: Optional[RAGGraphMemory] = None,
    mcp_server: Optional[MCPServer] = None
) -> V3ReliabilityEngine:
    """
    Factory function to create enhanced V3 engine
    
    Args:
        rag_graph: Optional RAG graph memory
        mcp_server: Optional MCP server
        
    Returns:
        Configured V3ReliabilityEngine instance
    """
    try:
        return V3ReliabilityEngine(
            rag_graph=rag_graph, 
            mcp_server=mcp_server
        )
    except Exception as e:
        logger.exception(f"Error creating enhanced V3 engine: {e}")
        raise
