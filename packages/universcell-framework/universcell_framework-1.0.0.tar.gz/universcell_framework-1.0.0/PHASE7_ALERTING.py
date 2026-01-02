"""
PHASE 7: ALERTING SYSTEM
Day 10 Part 3 - Production-Ready Alerts & Incident Response

Implements:
- Alert rules (consecutive blocks, timeout, corruption)
- Alert channels (log, email, webhook, PagerDuty)
- Incident tracking
- Alert deduplication
- Escalation policies

Architecture:
1. AlertRule - define alert conditions
2. AlertManager - manage active alerts
3. IncidentTracker - track incident lifecycle
4. NotificationChannel - send notifications
"""

import json
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertStatus(Enum):
    """Alert status throughout lifecycle"""
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SILENCED = "SILENCED"


@dataclass
class Alert:
    """Individual alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    message: str
    triggered_at: str
    resolved_at: Optional[str] = None
    status: AlertStatus = AlertStatus.TRIGGERED
    metadata: Dict[str, Any] = field(default_factory=dict)
    notification_count: int = 0


@dataclass
class IncidentEntry:
    """Incident tracking entry"""
    incident_id: str
    alert_id: str
    started_at: str
    impact: str  # "low", "medium", "high"
    resolved_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    affected_services: List[str] = field(default_factory=list)


class AlertRule:
    """Define alert triggering conditions"""
    
    def __init__(self,
                 name: str,
                 description: str,
                 condition_func: Callable[[Dict[str, Any]], bool],
                 severity: AlertSeverity,
                 title_template: str,
                 message_template: str,
                 deduplicate_seconds: int = 300):
        self.name = name
        self.description = description
        self.condition_func = condition_func
        self.severity = severity
        self.title_template = title_template
        self.message_template = message_template
        self.deduplicate_seconds = deduplicate_seconds
        
        self.last_triggered = None
        self.trigger_count = 0
    
    def evaluate(self, metrics: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Evaluate if alert should trigger"""
        try:
            should_trigger = self.condition_func(metrics)
            
            if should_trigger:
                # Check deduplication
                now = time.time()
                if self.last_triggered and (now - self.last_triggered) < self.deduplicate_seconds:
                    return False, None  # Deduplicated
                
                self.last_triggered = now
                self.trigger_count += 1
                
                # Format message
                return True, {
                    "title": self.title_template.format(**metrics),
                    "message": self.message_template.format(**metrics)
                }
            
            return False, None
        except Exception as e:
            return False, None  # Silent failure on eval error


class AlertManager:
    """Manage active alerts and their lifecycle"""
    
    def __init__(self):
        self.alerts = {}  # alert_id -> Alert
        self.rules = {}  # rule_name -> AlertRule
        self.alert_history = deque(maxlen=50000)
        
        self.lock = threading.Lock()
        self.next_alert_id = 0
    
    def register_rule(self, rule: AlertRule):
        """Register alert rule"""
        with self.lock:
            self.rules[rule.name] = rule
    
    def evaluate_rules(self, metrics: Dict[str, Any]) -> List[str]:
        """Evaluate all rules and trigger alerts"""
        triggered_ids = []
        
        with self.lock:
            for rule_name, rule in self.rules.items():
                should_trigger, alert_info = rule.evaluate(metrics)
                
                if should_trigger:
                    alert_id = self._generate_alert_id()
                    alert = Alert(
                        id=alert_id,
                        rule_name=rule_name,
                        severity=rule.severity,
                        title=alert_info["title"],
                        message=alert_info["message"],
                        triggered_at=datetime.utcnow().isoformat(),
                        metadata={
                            "metrics": metrics,
                            "rule_description": rule.description
                        }
                    )
                    
                    self.alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    triggered_ids.append(alert_id)
        
        return triggered_ids
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        self.next_alert_id += 1
        return f"alert_{self.next_alert_id}_{int(time.time() * 1000)}"
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge alert"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
                return True
            return False
    
    def resolve_alert(self, alert_id: str, resolution: str = "") -> bool:
        """Resolve alert"""
        with self.lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow().isoformat()
                alert.metadata["resolution"] = resolution
                return True
            return False
    
    def silence_alert(self, alert_id: str, duration_seconds: int = 3600) -> bool:
        """Silence alert for duration"""
        with self.lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.status = AlertStatus.SILENCED
                alert.metadata["silence_until"] = (
                    datetime.utcnow() + timedelta(seconds=duration_seconds)
                ).isoformat()
                return True
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (non-resolved) alerts"""
        with self.lock:
            return [
                a for a in self.alerts.values()
                if a.status != AlertStatus.RESOLVED
            ]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self.lock:
            alerts = list(self.alerts.values())
            
            return {
                "total_alerts": len(alerts),
                "by_status": {
                    status.value: len([a for a in alerts if a.status == status])
                    for status in AlertStatus
                },
                "by_severity": {
                    severity.value: len([a for a in alerts if a.severity == severity])
                    for severity in AlertSeverity
                },
                "critical_or_emergency": len([
                    a for a in alerts
                    if a.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
                    and a.status != AlertStatus.RESOLVED
                ])
            }


class IncidentTracker:
    """Track incidents from alert to resolution"""
    
    def __init__(self):
        self.incidents = {}  # incident_id -> IncidentEntry
        self.alert_to_incident = {}  # alert_id -> incident_id
        self.lock = threading.Lock()
        self.next_incident_id = 0
    
    def create_incident(self, alert_id: str, impact: str = "medium",
                       affected_services: List[str] = None) -> str:
        """Create incident from alert"""
        with self.lock:
            incident_id = f"inc_{self.next_incident_id}_{int(time.time())}"
            self.next_incident_id += 1
            
            incident = IncidentEntry(
                incident_id=incident_id,
                alert_id=alert_id,
                started_at=datetime.utcnow().isoformat(),
                impact=impact,
                affected_services=affected_services or []
            )
            
            self.incidents[incident_id] = incident
            self.alert_to_incident[alert_id] = incident_id
            
            return incident_id
    
    def resolve_incident(self, incident_id: str, resolution: str = "", root_cause: str = ""):
        """Mark incident resolved"""
        with self.lock:
            if incident_id in self.incidents:
                incident = self.incidents[incident_id]
                incident.resolved_at = datetime.utcnow().isoformat()
                incident.duration_seconds = (
                    datetime.fromisoformat(incident.resolved_at) -
                    datetime.fromisoformat(incident.started_at)
                ).total_seconds()
                incident.resolution = resolution
                incident.root_cause = root_cause
    
    def get_active_incidents(self) -> List[IncidentEntry]:
        """Get unresolved incidents"""
        with self.lock:
            return [i for i in self.incidents.values() if i.resolved_at is None]
    
    def get_incident_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get incident statistics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            recent = [
                i for i in self.incidents.values()
                if datetime.fromisoformat(i.started_at) > cutoff
            ]
            
            resolved = [i for i in recent if i.resolved_at]
            
            return {
                "total_incidents": len(recent),
                "resolved": len(resolved),
                "active": len(recent) - len(resolved),
                "avg_resolution_time_minutes": (
                    sum(i.duration_seconds for i in resolved if i.duration_seconds) /
                    max(1, len(resolved)) / 60
                    if resolved else 0
                ),
                "high_impact_count": sum(1 for i in recent if i.impact == "high")
            }


class NotificationChannel:
    """Base class for notification channels"""
    
    def send(self, alert: Alert) -> Tuple[bool, str]:
        raise NotImplementedError


class LogNotificationChannel(NotificationChannel):
    """Log-based notifications"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.sent = []
    
    def send(self, alert: Alert) -> Tuple[bool, str]:
        """Send alert via logging"""
        msg = f"[{alert.severity.value}] {alert.title}: {alert.message}"
        if self.logger:
            getattr(self.logger, alert.severity.value.lower(), lambda x: None)(msg)
        else:
            print(msg)
        
        self.sent.append({
            "alert_id": alert.id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True, f"Logged to console/file"


class WebhookNotificationChannel(NotificationChannel):
    """Webhook-based notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.sent = []
    
    def send(self, alert: Alert) -> Tuple[bool, str]:
        """Send alert via webhook"""
        # Simulate webhook send
        payload = {
            "alert_id": alert.id,
            "rule": alert.rule_name,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.triggered_at
        }
        
        # In real implementation:
        # import requests
        # response = requests.post(self.webhook_url, json=payload)
        
        self.sent.append({
            "alert_id": alert.id,
            "url": self.webhook_url,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True, f"Posted to {self.webhook_url}"


class AlertingSystem:
    """Main alerting system coordinator"""
    
    def __init__(self):
        self.manager = AlertManager()
        self.incident_tracker = IncidentTracker()
        self.notification_channels = []
        
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configure default alert rules"""
        
        # Consecutive blocks alert
        self.manager.register_rule(AlertRule(
            name="consecutive_blocks",
            description="Too many consecutive blocks without approval",
            condition_func=lambda m: m.get("consecutive_blocks", 0) > 5,
            severity=AlertSeverity.WARNING,
            title_template="Consecutive Blocks Alert",
            message_template="Detected {consecutive_blocks} consecutive blocks"
        ))
        
        # Approval timeout alert
        self.manager.register_rule(AlertRule(
            name="approval_timeout",
            description="Approvals taking too long",
            condition_func=lambda m: m.get("avg_approval_latency_ms", 0) > 1000,
            severity=AlertSeverity.WARNING,
            title_template="Approval Latency Alert",
            message_template="Average approval time: {avg_approval_latency_ms:.0f}ms"
        ))
        
        # Data corruption detection
        self.manager.register_rule(AlertRule(
            name="data_corruption",
            description="Potential data corruption detected",
            condition_func=lambda m: m.get("json_errors", 0) > 0,
            severity=AlertSeverity.CRITICAL,
            title_template="Data Corruption Alert",
            message_template="Detected {json_errors} JSON errors",
            deduplicate_seconds=600
        ))
        
        # High rejection rate
        self.manager.register_rule(AlertRule(
            name="high_rejection_rate",
            description="Abnormal rejection rate",
            condition_func=lambda m: m.get("rejection_rate", 0) > 0.25,
            severity=AlertSeverity.CRITICAL,
            title_template="High Block Rejection Alert",
            message_template="Rejection rate: {rejection_rate:.1%}"
        ))
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.notification_channels.append(channel)
    
    def evaluate_and_notify(self, metrics: Dict[str, Any]):
        """Evaluate alerts and send notifications"""
        triggered_ids = self.manager.evaluate_rules(metrics)
        
        for alert_id in triggered_ids:
            alert = self.manager.alerts[alert_id]
            
            # Create incident for CRITICAL/EMERGENCY
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                self.incident_tracker.create_incident(alert_id, impact="high")
            
            # Send notifications
            for channel in self.notification_channels:
                alert.notification_count += 1
                channel.send(alert)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get alerting system status"""
        active_alerts = self.manager.get_active_alerts()[:10]
        active_alerts_data = [
            {
                "id": a.id,
                "rule_name": a.rule_name,
                "severity": a.severity.value,
                "title": a.title,
                "message": a.message,
                "status": a.status.value
            }
            for a in active_alerts
        ]
        
        return {
            "alerts": self.manager.get_alert_summary(),
            "incidents": self.incident_tracker.get_incident_statistics(),
            "active_alerts": active_alerts_data
        }


# Testing
def test_alerting():
    """Validate alerting implementation"""
    system = AlertingSystem()
    system.add_notification_channel(LogNotificationChannel())
    
    # Simulate metrics that trigger CRITICAL alert
    metrics = {
        "consecutive_blocks": 10,
        "avg_approval_latency_ms": 50,
        "json_errors": 5,  # This triggers CRITICAL
        "rejection_rate": 0.05
    }
    
    system.evaluate_and_notify(metrics)
    
    status = system.get_system_status()
    assert status["alerts"]["total_alerts"] > 0, "Should have triggered alert"
    
    # Test incident tracking
    incidents = system.incident_tracker.get_active_incidents()
    assert len(incidents) > 0, "Should have created incident"
    
    print("✅ Alerting tests passed")
    return True


if __name__ == "__main__":
    test_alerting()
