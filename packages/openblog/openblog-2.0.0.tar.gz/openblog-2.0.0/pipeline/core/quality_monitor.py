"""
Quality Monitor - Tracks and alerts on quality metrics.

Monitors:
- AEO scores over time
- Quality degradation trends
- Critical issues frequency
- Regeneration rates

Alerts:
- Low quality articles (AEO < 70)
- Quality degradation trends
- High critical issue rates
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class QualityAlert:
    """Quality alert record."""
    job_id: str
    alert_type: str  # "low_aeo", "degradation", "high_critical_issues"
    severity: str  # "warning", "critical"
    message: str
    aeo_score: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)


class QualityMonitor:
    """
    Monitors quality metrics and generates alerts.
    
    Tracks:
    - Recent AEO scores (rolling window)
    - Quality trends
    - Critical issues frequency
    """
    
    # Alert thresholds
    LOW_AEO_THRESHOLD = 70  # Alert if AEO < 70
    CRITICAL_AEO_THRESHOLD = 50  # Critical alert if AEO < 50
    DEGRADATION_THRESHOLD = 10  # Alert if average drops by 10+ points
    HIGH_CRITICAL_ISSUES_THRESHOLD = 3  # Alert if >3 critical issues
    
    def __init__(self, window_size: int = 100):
        """
        Initialize quality monitor.
        
        Args:
            window_size: Number of recent articles to track (default: 100)
        """
        self.window_size = window_size
        self.recent_scores: deque = deque(maxlen=window_size)
        self.recent_timestamps: deque = deque(maxlen=window_size)
        self.alerts: List[QualityAlert] = []
        self.max_alerts = 1000
        
        # Statistics
        self.total_articles = 0
        self.low_quality_count = 0
        self.critical_quality_count = 0
        
    def record_quality(self, job_id: str, quality_report: Dict[str, Any]) -> Optional[QualityAlert]:
        """
        Record quality metrics and check for alerts.
        
        Args:
            job_id: Job identifier
            quality_report: Quality report from Stage 10
            
        Returns:
            QualityAlert if threshold exceeded, None otherwise
        """
        self.total_articles += 1
        
        metrics = quality_report.get("metrics", {})
        aeo_score = metrics.get("aeo_score", 0)
        critical_issues = quality_report.get("critical_issues", [])
        
        # Record score
        self.recent_scores.append(aeo_score)
        self.recent_timestamps.append(datetime.now())
        
        # Check for alerts
        alert = None
        
        # 1. Low AEO score alert
        if aeo_score < self.CRITICAL_AEO_THRESHOLD:
            self.critical_quality_count += 1
            alert = QualityAlert(
                job_id=job_id,
                alert_type="critical_low_aeo",
                severity="critical",
                message=f"Critical: AEO score {aeo_score}/100 is below critical threshold ({self.CRITICAL_AEO_THRESHOLD})",
                aeo_score=aeo_score,
                context={
                    "critical_issues": len(critical_issues),
                    "suggestions": len(quality_report.get("suggestions", []))
                }
            )
        elif aeo_score < self.LOW_AEO_THRESHOLD:
            self.low_quality_count += 1
            alert = QualityAlert(
                job_id=job_id,
                alert_type="low_aeo",
                severity="warning",
                message=f"Warning: AEO score {aeo_score}/100 is below target threshold ({self.LOW_AEO_THRESHOLD})",
                aeo_score=aeo_score,
                context={
                    "critical_issues": len(critical_issues),
                    "suggestions": len(quality_report.get("suggestions", []))
                }
            )
        
        # 2. High critical issues alert
        if len(critical_issues) >= self.HIGH_CRITICAL_ISSUES_THRESHOLD:
            if alert is None:
                alert = QualityAlert(
                    job_id=job_id,
                    alert_type="high_critical_issues",
                    severity="warning",
                    message=f"Warning: {len(critical_issues)} critical issues detected",
                    aeo_score=aeo_score,
                    context={
                        "critical_issues_count": len(critical_issues),
                        "critical_issues": critical_issues[:5]  # First 5
                    }
                )
            else:
                # Add to existing alert
                alert.context["critical_issues_count"] = len(critical_issues)
                alert.context["critical_issues"] = critical_issues[:5]
        
        # 3. Quality degradation alert (if we have enough data)
        if len(self.recent_scores) >= 20:
            degradation_alert = self._check_degradation(job_id, aeo_score)
            if degradation_alert:
                # Combine with existing alert if present
                if alert:
                    alert.message += f" | {degradation_alert.message}"
                    alert.context.update(degradation_alert.context)
                else:
                    alert = degradation_alert
        
        # Store alert
        if alert:
            self.alerts.append(alert)
            if len(self.alerts) > self.max_alerts:
                self.alerts.pop(0)
            
            # Log alert
            self._log_alert(alert)
        
        return alert
    
    def _check_degradation(self, job_id: str, current_score: float) -> Optional[QualityAlert]:
        """
        Check for quality degradation trend.
        
        Compares recent average to older average to detect degradation.
        """
        if len(self.recent_scores) < 20:
            return None
        
        # Split into two halves
        midpoint = len(self.recent_scores) // 2
        older_scores = list(self.recent_scores)[:midpoint]
        recent_scores = list(self.recent_scores)[midpoint:]
        
        older_avg = sum(older_scores) / len(older_scores) if older_scores else 0
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        degradation = older_avg - recent_avg
        
        if degradation >= self.DEGRADATION_THRESHOLD:
            return QualityAlert(
                job_id=job_id,
                alert_type="quality_degradation",
                severity="warning",
                message=f"Quality degradation detected: Average dropped from {older_avg:.1f} to {recent_avg:.1f} ({degradation:.1f} points)",
                aeo_score=current_score,
                context={
                    "older_average": older_avg,
                    "recent_average": recent_avg,
                    "degradation": degradation,
                    "sample_size": len(self.recent_scores)
                }
            )
        
        return None
    
    def _log_alert(self, alert: QualityAlert) -> None:
        """Log quality alert."""
        if alert.severity == "critical":
            logger.critical(
                f"🚨 QUALITY ALERT [{alert.alert_type}]: {alert.message} "
                f"(Job: {alert.job_id}, AEO: {alert.aeo_score})"
            )
        else:
            logger.warning(
                f"⚠️  QUALITY WARNING [{alert.alert_type}]: {alert.message} "
                f"(Job: {alert.job_id}, AEO: {alert.aeo_score})"
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get quality monitoring statistics."""
        if not self.recent_scores:
            return {
                "total_articles": self.total_articles,
                "average_aeo": 0,
                "low_quality_rate": 0,
                "critical_quality_rate": 0,
                "recent_alerts": len(self.alerts)
            }
        
        recent_avg = sum(self.recent_scores) / len(self.recent_scores)
        low_quality_rate = (self.low_quality_count / max(self.total_articles, 1)) * 100
        critical_quality_rate = (self.critical_quality_count / max(self.total_articles, 1)) * 100
        
        return {
            "total_articles": self.total_articles,
            "recent_articles": len(self.recent_scores),
            "average_aeo": recent_avg,
            "min_aeo": min(self.recent_scores),
            "max_aeo": max(self.recent_scores),
            "low_quality_count": self.low_quality_count,
            "critical_quality_count": self.critical_quality_count,
            "low_quality_rate": low_quality_rate,
            "critical_quality_rate": critical_quality_rate,
            "recent_alerts": len([a for a in self.alerts if self._is_recent(a, hours=24)]),
            "total_alerts": len(self.alerts)
        }
    
    def _is_recent(self, alert: QualityAlert, hours: int = 24) -> bool:
        """Check if alert is within recent time window."""
        try:
            alert_time = datetime.fromisoformat(alert.timestamp)
            return (datetime.now() - alert_time) < timedelta(hours=hours)
        except:
            return False
    
    def get_recent_alerts(self, hours: int = 24) -> List[QualityAlert]:
        """Get alerts from recent time window."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert.timestamp) >= cutoff
        ]


# Global monitor instance
_quality_monitor: Optional[QualityMonitor] = None


def get_quality_monitor() -> QualityMonitor:
    """Get global quality monitor instance."""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = QualityMonitor()
    return _quality_monitor


def reset_quality_monitor():
    """Reset global quality monitor (for testing)."""
    global _quality_monitor
    _quality_monitor = None

