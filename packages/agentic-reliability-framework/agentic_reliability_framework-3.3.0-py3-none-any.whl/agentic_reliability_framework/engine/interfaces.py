"""
Protocol interfaces and base classes for ARF v3
Designed to break circular dependencies and provide clear abstractions
"""

from typing import Protocol, Optional, Any, Dict, List, runtime_checkable
from ..models import ReliabilityEvent


@runtime_checkable
class ReliabilityEngineProtocol(Protocol):
    """Protocol for reliability engines to avoid circular imports"""

    async def process_event(self, event: ReliabilityEvent) -> Dict[str, Any]:
        """Process a reliability event"""
        ...

    async def process_event_enhanced(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Process event with enhanced features"""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        ...

    def get_engine_stats(self) -> Dict[str, Any]:
        """Alias for get_stats"""
        ...


@runtime_checkable
class MCPProtocol(Protocol):
    """Protocol for MCP servers"""

    async def execute_tool(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool"""
        ...

    def get_server_stats(self) -> Dict[str, Any]:
        """Get MCP server statistics"""
        ...


@runtime_checkable
class RAGProtocol(Protocol):
    """Protocol for RAG graph memory"""

    def find_similar(self, event: ReliabilityEvent, k: int = 5) -> List[Any]:
        """Find similar incidents"""
        ...

    def store_incident(self, event: ReliabilityEvent, analysis: Dict[str, Any]) -> str:
        """Store incident in graph"""
        ...

    def store_outcome(
        self,
        incident_id: str,
        actions_taken: List[str],
        success: bool,
        resolution_time_minutes: float,
        lessons_learned: Optional[List[str]] = None,
    ) -> str:
        """Store outcome for incident"""
        ...

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get RAG graph statistics"""
        ...

    def get_most_effective_actions(self, component: str, k: int = 3) -> List[Dict[str, Any]]:
        """Get most effective actions for a component"""
        ...


class BaseReliabilityEngine:
    """
    Base reliability engine with common functionality.
    Concrete engines should inherit from this.
    """
    
    def __init__(
        self,
        rag_graph: Optional[RAGProtocol] = None,
        mcp_server: Optional[MCPProtocol] = None
    ) -> None:
        """Initialize base engine with optional v3 dependencies"""
        self.rag = rag_graph
        self.mcp = mcp_server
        self._lock = None  # Should be initialized by subclass
        self._start_time = None  # Should be initialized by subclass
        self.metrics: Dict[str, Any] = {}
    
    async def process_event(self, event: ReliabilityEvent) -> Dict[str, Any]:
        """Process event - must be implemented by subclass"""
        raise NotImplementedError
    
    async def process_event_enhanced(self, event: ReliabilityEvent) -> Dict[str, Any]:
        """Enhanced processing - can be overridden by subclass"""
        return await self.process_event(event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics - must be implemented by subclass"""
        raise NotImplementedError
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Alias for get_stats"""
        return self.get_stats()
    
    def shutdown(self) -> None:
        """Graceful shutdown - can be overridden by subclass"""
        pass
