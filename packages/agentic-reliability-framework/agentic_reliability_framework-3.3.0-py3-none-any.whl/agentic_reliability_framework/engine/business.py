"""
Business Impact Calculation and Metrics Tracking
Extracted from app.py for modularity
"""

import threading
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, cast
from collections import deque
from dataclasses import dataclass

from ..models import ReliabilityEvent
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class BusinessImpactResult:
    """Business impact calculation result"""
    revenue_loss_estimate: float
    affected_users_estimate: int
    severity_level: str
    throughput_reduction_pct: float


class BusinessImpactCalculator:
    """Calculate business impact of anomalies"""
    
    def __init__(self, revenue_per_request: float = 0.01):
        self.revenue_per_request = revenue_per_request
        logger.info("Initialized BusinessImpactCalculator")
    
    def calculate_impact(
        self,
        event: ReliabilityEvent,
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """Calculate business impact for a reliability event"""
        try:
            base_revenue_per_minute = config.base_revenue_per_minute
            
            impact_multiplier = 1.0
            
            # Impact factors
            if event.latency_p99 > config.latency_critical:
                impact_multiplier += 0.5
            if event.error_rate > 0.1:
                impact_multiplier += 0.8
            if event.cpu_util and event.cpu_util > config.cpu_critical:
                impact_multiplier += 0.3
            
            revenue_loss = base_revenue_per_minute * impact_multiplier * (duration_minutes / 60)
            
            base_users_affected = config.base_users
            user_impact_multiplier = (event.error_rate * 10) + \
                (max(0, event.latency_p99 - 100) / 500)
            affected_users = int(base_users_affected * user_impact_multiplier)
            
            # Severity classification
            if revenue_loss > 500 or affected_users > 5000:
                severity = "CRITICAL"
            elif revenue_loss > 100 or affected_users > 1000:
                severity = "HIGH"
            elif revenue_loss > 50 or affected_users > 500:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            logger.info(
                f"Business impact: {revenue_loss:.2f} revenue loss, "
                f"{affected_users} users, {severity} severity"
            )
            
            return {
                'revenue_loss_estimate': round(revenue_loss, 2),
                'affected_users_estimate': affected_users,
                'severity_level': severity,
                'throughput_reduction_pct': round(min(100, user_impact_multiplier * 100), 1)
            }
        
        except Exception as e:
            logger.error(f"Error calculating business impact: {e}")
            return {
                'revenue_loss_estimate': 0.0,
                'affected_users_estimate': 0,
                'severity_level': "LOW",
                'throughput_reduction_pct': 0.0
            }
    
    def calculate_impact_detailed(
        self,
        event: ReliabilityEvent,
        duration_minutes: int = 5
    ) -> BusinessImpactResult:
        """Calculate business impact with detailed result"""
        impact_dict = self.calculate_impact(event, duration_minutes)
        
        return BusinessImpactResult(
            revenue_loss_estimate=float(impact_dict['revenue_loss_estimate']),
            affected_users_estimate=int(impact_dict['affected_users_estimate']),
            severity_level=str(impact_dict['severity_level']),
            throughput_reduction_pct=float(impact_dict['throughput_reduction_pct'])
        )


class BusinessMetricsTracker:
    """Track cumulative business metrics for ROI dashboard"""
    
    def __init__(self) -> None:
        self.total_incidents: int = 0
        self.incidents_auto_healed: int = 0
        self.total_revenue_saved: float = 0.0
        self.total_revenue_at_risk: float = 0.0
        self.detection_times: List[float] = []
        self._lock = threading.RLock()
        logger.info("Initialized BusinessMetricsTracker")
    
    def record_incident(
        self,
        severity: str,
        auto_healed: bool,
        revenue_loss: float,
        detection_time_seconds: float = 120.0  # 2 minutes default
    ) -> None:
        """Record an incident and update metrics"""
        with self._lock:
            self.total_incidents += 1
            
            if auto_healed:
                self.incidents_auto_healed += 1
            
            # Calculate what revenue would have been lost (industry average: 14 min response)
            # vs what we actually lost (ARF average: 2 min response)
            industry_avg_response_minutes = 14
            arf_response_minutes = detection_time_seconds / 60
            
            # Revenue at risk if using traditional monitoring
            revenue_per_minute = revenue_loss / max(1, arf_response_minutes)
            traditional_loss = revenue_per_minute * industry_avg_response_minutes
            
            self.total_revenue_at_risk += traditional_loss
            self.total_revenue_saved += (traditional_loss - revenue_loss)
            
            self.detection_times.append(detection_time_seconds)
            
            logger.info(
                f"Recorded incident: auto_healed={auto_healed}, "
                f"saved=${traditional_loss - revenue_loss:.2f}"
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current cumulative metrics"""
        with self._lock:
            auto_heal_rate = (
                (self.incidents_auto_healed / self.total_incidents * 100)
                if self.total_incidents > 0 else 0
            )
            
            avg_detection_time = (
                sum(self.detection_times) / len(self.detection_times)
                if self.detection_times else 120.0
            )
            
            # Ensure all values are properly typed
            return {
                "total_incidents": self.total_incidents,
                "incidents_auto_healed": self.incidents_auto_healed,
                "auto_heal_rate": float(auto_heal_rate),
                "total_revenue_saved": float(self.total_revenue_saved),
                "total_revenue_at_risk": float(self.total_revenue_at_risk),
                "avg_detection_time_seconds": float(avg_detection_time),
                "avg_detection_time_minutes": float(avg_detection_time / 60),
                "time_improvement": float(
                    (14 - (avg_detection_time / 60)) / 14 * 100
                )  # vs industry 14 min
            }
    
    def reset(self) -> None:
        """Reset all metrics (for demo purposes)"""
        with self._lock:
            self.total_incidents = 0
            self.incidents_auto_healed = 0
            self.total_revenue_saved = 0.0
            self.total_revenue_at_risk = 0.0
            self.detection_times = []
            logger.info("Reset BusinessMetricsTracker")
    
    def export_for_dashboard(self) -> Dict[str, Any]:
        """Export metrics formatted for dashboard display"""
        metrics = self.get_metrics()
        
        return {
            "incidents": {
                "total": metrics["total_incidents"],
                "auto_healed": metrics["incidents_auto_healed"],
                "auto_heal_rate": f"{metrics['auto_heal_rate']:.1f}%"
            },
            "financial": {
                "revenue_saved": f"${metrics['total_revenue_saved']:,.2f}",
                "revenue_at_risk": f"${metrics['total_revenue_at_risk']:,.2f}",
                "roi_percentage": self._calculate_roi()
            },
            "performance": {
                "avg_response_time": f"{metrics['avg_detection_time_minutes']:.1f} min",
                "time_improvement": f"{metrics['time_improvement']:.1f}%",
                "vs_industry_standard": "14 min"
            }
        }
    
    def _calculate_roi(self) -> float:
        """Calculate ROI percentage"""
        # Simplified ROI calculation
        if self.total_revenue_at_risk > 0:
            roi = (self.total_revenue_saved / self.total_revenue_at_risk) * 100
            return float(roi)
        return 0.0
