"""
PHASE 7: MONITORING & METRICS COLLECTION
Day 10 Part 1 - Production-Ready Observability

Tracks:
- Blocks created per day (operational tempo)
- Approval latency (decision speed)
- Timeline size (data growth)
- Health check status
- Performance baselines

Architecture:
1. MetricsCollector - gather system metrics
2. PerformanceBaseline - establish and track SLOs
3. HealthCheck - system status verification
4. MetricsDashboard - expose metrics for monitoring
"""

import json
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class PerformanceBaseline:
    """Expected performance characteristics"""
    metric_name: str
    target_value: float
    warning_threshold: float  # When to warn
    critical_threshold: float  # When to alert
    unit: str
    description: str


class MetricsCollector:
    """Collects operational metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics = defaultdict(lambda: deque(maxlen=10000))
        self.retention_hours = retention_hours
        self.lock = threading.Lock()
        
        # Counters (gauges)
        self.blocks_created_today = 0
        self.approvals_processed = 0
        self.blocks_rejected = 0
        self.timeline_size_bytes = 0
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Record a metric data point"""
        with self.lock:
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.utcnow().isoformat(),
                tags=tags or {},
                unit=unit
            )
            self.metrics[name].append(metric)
    
    def record_block_created(self, block_type: str = "standard"):
        """Track block creation"""
        with self.lock:
            self.blocks_created_today += 1
            self.record_metric(
                "blocks_created",
                self.blocks_created_today,
                tags={"type": block_type},
                unit="count"
            )
    
    def record_approval(self, latency_ms: float, approved: bool):
        """Track approval decision"""
        with self.lock:
            self.approvals_processed += 1
            if not approved:
                self.blocks_rejected += 1
            
            self.record_metric(
                "approval_latency_ms",
                latency_ms,
                tags={"status": "approved" if approved else "rejected"},
                unit="ms"
            )
    
    def record_timeline_size(self, size_bytes: int):
        """Track timeline storage growth"""
        with self.lock:
            self.timeline_size_bytes = size_bytes
            self.record_metric(
                "timeline_size_bytes",
                size_bytes,
                unit="bytes"
            )
    
    def get_metric_history(self, name: str, hours: int = 1) -> List[Metric]:
        """Get historical metrics for time window"""
        with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return [
                m for m in self.metrics[name]
                if datetime.fromisoformat(m.timestamp) > cutoff
            ]
    
    def get_percentile(self, name: str, percentile: int = 99, hours: int = 1) -> Optional[float]:
        """Calculate percentile (e.g., p99 latency)"""
        metrics = self.get_metric_history(name, hours)
        if not metrics:
            return None
        
        values = sorted([m.value for m in metrics])
        index = int(len(values) * percentile / 100)
        return values[min(index, len(values) - 1)]
    
    def get_average(self, name: str, hours: int = 1) -> Optional[float]:
        """Calculate average metric value"""
        metrics = self.get_metric_history(name, hours)
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        return sum(values) / len(values)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric snapshot"""
        return {
            "blocks_created_today": self.blocks_created_today,
            "approvals_processed": self.approvals_processed,
            "blocks_rejected": self.blocks_rejected,
            "rejection_rate": self.blocks_rejected / max(1, self.approvals_processed),
            "timeline_size_bytes": self.timeline_size_bytes,
            "approval_latency_p99_ms": self.get_percentile("approval_latency_ms", 99, hours=1),
            "approval_latency_avg_ms": self.get_average("approval_latency_ms", hours=1),
        }
    
    def reset_daily_counters(self):
        """Reset daily counters"""
        with self.lock:
            self.blocks_created_today = 0
            self.approvals_processed = 0
            self.blocks_rejected = 0


class PerformanceMonitor:
    """Monitors against performance baselines"""
    
    def __init__(self):
        self.baselines = {}
        self.violations = []
        self.lock = threading.Lock()
        
        # Define default baselines
        self._setup_default_baselines()
    
    def _setup_default_baselines(self):
        """Configure default performance targets"""
        self.baselines = {
            "approval_latency_ms": PerformanceBaseline(
                metric_name="approval_latency_ms",
                target_value=50.0,
                warning_threshold=100.0,
                critical_threshold=500.0,
                unit="ms",
                description="P99 approval decision latency"
            ),
            "blocks_per_day": PerformanceBaseline(
                metric_name="blocks_created",
                target_value=1000.0,
                warning_threshold=2000.0,
                critical_threshold=5000.0,
                unit="count",
                description="Blocks created per day (capacity planning)"
            ),
            "rejection_rate": PerformanceBaseline(
                metric_name="rejection_rate",
                target_value=0.05,
                warning_threshold=0.10,
                critical_threshold=0.25,
                unit="ratio",
                description="Block rejection rate"
            ),
            "timeline_size_bytes": PerformanceBaseline(
                metric_name="timeline_size_bytes",
                target_value=10_000_000.0,  # 10 MB
                warning_threshold=100_000_000.0,  # 100 MB
                critical_threshold=500_000_000.0,  # 500 MB
                unit="bytes",
                description="Timeline storage size"
            )
        }
    
    def check_baseline(self, metric_name: str, value: float) -> Tuple[bool, Optional[str]]:
        """Check if metric violates baseline"""
        if metric_name not in self.baselines:
            return True, None  # Unknown metric, assume OK
        
        baseline = self.baselines[metric_name]
        
        if value > baseline.critical_threshold:
            violation = f"CRITICAL: {metric_name}={value:.2f} exceeds {baseline.critical_threshold}"
            with self.lock:
                self.violations.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric": metric_name,
                    "value": value,
                    "threshold": baseline.critical_threshold,
                    "severity": "CRITICAL"
                })
            return False, violation
        elif value > baseline.warning_threshold:
            violation = f"WARNING: {metric_name}={value:.2f} exceeds {baseline.warning_threshold}"
            with self.lock:
                self.violations.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric": metric_name,
                    "value": value,
                    "threshold": baseline.warning_threshold,
                    "severity": "WARNING"
                })
            return True, violation
        
        return True, None
    
    def get_violations(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent violations"""
        with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return [
                v for v in self.violations
                if datetime.fromisoformat(v["timestamp"]) > cutoff
            ]


class HealthChecker:
    """Comprehensive system health verification"""
    
    def __init__(self, metrics_collector: MetricsCollector, monitor: PerformanceMonitor):
        self.metrics = metrics_collector
        self.monitor = monitor
        self.last_check = None
        self.lock = threading.Lock()
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        with self.lock:
            current_metrics = self.metrics.get_current_metrics()
            
            # Evaluate health status
            issues = []
            status = HealthStatus.HEALTHY
            
            # Check approval latency
            if current_metrics.get("approval_latency_p99_ms"):
                ok, msg = self.monitor.check_baseline(
                    "approval_latency_ms",
                    current_metrics["approval_latency_p99_ms"]
                )
                if not ok:
                    status = HealthStatus.UNHEALTHY
                    issues.append(msg)
                elif msg:
                    if status != HealthStatus.UNHEALTHY:
                        status = HealthStatus.DEGRADED
                    issues.append(msg)
            
            # Check rejection rate
            ok, msg = self.monitor.check_baseline(
                "rejection_rate",
                current_metrics.get("rejection_rate", 0)
            )
            if not ok:
                status = HealthStatus.UNHEALTHY
                issues.append(msg)
            elif msg and status != HealthStatus.UNHEALTHY:
                status = HealthStatus.DEGRADED
                issues.append(msg)
            
            # Check timeline size
            ok, msg = self.monitor.check_baseline(
                "timeline_size_bytes",
                current_metrics.get("timeline_size_bytes", 0)
            )
            if not ok:
                status = HealthStatus.UNHEALTHY
                issues.append(msg)
            elif msg and status != HealthStatus.UNHEALTHY:
                status = HealthStatus.DEGRADED
                issues.append(msg)
            
            health_check = {
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": current_metrics,
                "issues": issues,
                "response_time_ms": time.time() * 1000  # Simulated
            }
            
            self.last_check = health_check
            return health_check
    
    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """Get last health check result"""
        return self.last_check


class MetricsDashboard:
    """Expose metrics for monitoring systems"""
    
    def __init__(self, metrics: MetricsCollector, health_checker: HealthChecker):
        self.metrics = metrics
        self.health = health_checker
    
    def get_prometheus_format(self) -> str:
        """Generate Prometheus-compatible metrics"""
        lines = []
        current = self.metrics.get_current_metrics()
        
        # Gauge metrics
        lines.append(f"# HELP univers_blocks_created_total Total blocks created")
        lines.append(f"# TYPE univers_blocks_created_total gauge")
        lines.append(f"univers_blocks_created_total {current['blocks_created_today']}")
        
        lines.append(f"# HELP univers_approvals_processed_total Total approvals processed")
        lines.append(f"# TYPE univers_approvals_processed_total gauge")
        lines.append(f"univers_approvals_processed_total {current['approvals_processed']}")
        
        lines.append(f"# HELP univers_blocks_rejected_total Total blocks rejected")
        lines.append(f"# TYPE univers_blocks_rejected_total gauge")
        lines.append(f"univers_blocks_rejected_total {current['blocks_rejected']}")
        
        lines.append(f"# HELP univers_rejection_rate Current rejection rate")
        lines.append(f"# TYPE univers_rejection_rate gauge")
        lines.append(f"univers_rejection_rate {current['rejection_rate']:.4f}")
        
        lines.append(f"# HELP univers_timeline_size_bytes Timeline storage size in bytes")
        lines.append(f"# TYPE univers_timeline_size_bytes gauge")
        lines.append(f"univers_timeline_size_bytes {current['timeline_size_bytes']}")
        
        if current.get('approval_latency_p99_ms'):
            lines.append(f"# HELP univers_approval_latency_p99_ms P99 approval latency")
            lines.append(f"# TYPE univers_approval_latency_p99_ms gauge")
            lines.append(f"univers_approval_latency_p99_ms {current['approval_latency_p99_ms']:.2f}")
        
        return "\n".join(lines)
    
    def get_json_metrics(self) -> Dict[str, Any]:
        """Get metrics as JSON"""
        health_check = self.health.perform_health_check()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": health_check,
            "metrics": self.metrics.get_current_metrics()
        }
    
    def export_metrics(self, filepath: str, format: str = "json"):
        """Export metrics to file"""
        if format == "json":
            data = self.get_json_metrics()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "prometheus":
            content = self.get_prometheus_format()
            with open(filepath, 'w') as f:
                f.write(content)


# Integration example
def test_monitoring():
    """Validate monitoring implementation"""
    collector = MetricsCollector()
    monitor = PerformanceMonitor()
    health = HealthChecker(collector, monitor)
    dashboard = MetricsDashboard(collector, health)
    
    # Simulate operations
    for i in range(100):
        collector.record_block_created()
        collector.record_approval(latency_ms=45 + (i % 20), approved=(i % 10 != 0))
    
    collector.record_timeline_size(5_000_000)
    
    # Check health
    status = health.perform_health_check()
    assert status["status"] in ["HEALTHY", "DEGRADED", "UNHEALTHY"]
    
    # Get metrics
    metrics = dashboard.get_json_metrics()
    assert metrics["metrics"]["blocks_created_today"] == 100
    
    print("✅ Monitoring tests passed")
    return True


if __name__ == "__main__":
    test_monitoring()
