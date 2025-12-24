"""
Performance monitoring and analytics dashboard for device fingerprinting.

This module provides a real-time analytics dashboard using Plotly for
visualization and Flask for serving. It offers insights into fingerprinting
performance, security events, and usage patterns.
"""

import time
import threading
import statistics
from typing import Dict, Any, List, Deque, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
import json

# Gracefully import optional dependencies
try:
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder
except ImportError:
    go = None
    PlotlyJSONEncoder = None


@dataclass
class PerformanceMetric:
    """Represents a single performance metric data point."""

    timestamp: float
    operation: str
    duration: float
    success: bool
    metadata: Dict[str, Any]


@dataclass
class SecurityEvent:
    """Represents a single security event."""

    timestamp: float
    event_type: str
    severity: str
    details: Dict[str, Any]


class AnalyticsDashboard:
    """
    A comprehensive analytics and monitoring dashboard.

    This class collects, processes, and visualizes performance and security data.
    It can generate JSON data suitable for a web dashboard.
    """

    def __init__(self, history_limit: int = 1000):
        self.metrics: Deque[PerformanceMetric] = deque(maxlen=history_limit)
        self.security_events: Deque[SecurityEvent] = deque(maxlen=history_limit)
        self.lock = threading.Lock()

    def record_operation(self, operation: str, duration: float, success: bool, **metadata: Any):
        """Records a performance metric for a given operation."""
        metric = PerformanceMetric(time.time(), operation, duration, success, metadata)
        with self.lock:
            self.metrics.append(metric)

    def record_security_event(self, event_type: str, severity: str, **details: Any):
        """Records a security-related event."""
        event = SecurityEvent(time.time(), event_type, severity, details)
        with self.lock:
            self.security_events.append(event)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Generates a dictionary of data for rendering a dashboard.

        This data includes summaries and figures for performance and security.
        """
        with self.lock:
            metrics = list(self.metrics)
            events = list(self.security_events)

        data = {
            "performance_summary": self._get_performance_summary(metrics),
            "security_summary": self._get_security_summary(events),
            "charts": {},
        }

        if go:
            data["charts"]["performance_timeseries"] = self._create_performance_timeseries(metrics)
            data["charts"]["security_events_timeline"] = self._create_security_events_timeline(
                events
            )

        return data

    def _get_performance_summary(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Creates a summary of performance metrics."""
        if not metrics:
            return {"total_operations": 0}

        ops = defaultdict(list)
        for m in metrics:
            ops[m.operation].append(m.duration)

        summary = {"total_operations": len(metrics), "operations": {}}
        for op, durations in ops.items():
            summary["operations"][op] = {
                "count": len(durations),
                "avg_duration": statistics.mean(durations),
                "p95_duration": (
                    statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else 0
                ),
            }
        return summary

    def _get_security_summary(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Creates a summary of security events."""
        if not events:
            return {"total_events": 0}

        return {
            "total_events": len(events),
            "by_severity": {
                sev: len([e for e in events if e.severity == sev])
                for sev in ["low", "medium", "high", "critical"]
            },
            "recent_events": [
                {"type": e.event_type, "severity": e.severity, "age_sec": time.time() - e.timestamp}
                for e in events
                if time.time() - e.timestamp < 3600
            ],
        }

    def _create_performance_timeseries(self, metrics: List[PerformanceMetric]) -> "go.Figure":
        """Creates a Plotly timeseries chart for performance."""
        fig = go.Figure()
        ops = defaultdict(lambda: {"x": [], "y": []})
        for m in metrics:
            ops[m.operation]["x"].append(datetime.fromtimestamp(m.timestamp))
            ops[m.operation]["y"].append(m.duration * 1000)  # ms

        for op, data in ops.items():
            fig.add_trace(go.Scatter(x=data["x"], y=data["y"], mode="lines+markers", name=op))

        fig.update_layout(title="Operation Duration Over Time", yaxis_title="Duration (ms)")
        return fig

    def _create_security_events_timeline(self, events: List[SecurityEvent]) -> "go.Figure":
        """Creates a Plotly timeline for security events."""
        fig = go.Figure()
        severities = ["low", "medium", "high", "critical"]
        colors = {"low": "green", "medium": "orange", "high": "red", "critical": "darkred"}

        for sev in severities:
            sev_events = [e for e in events if e.severity == sev]
            if sev_events:
                fig.add_trace(
                    go.Scatter(
                        x=[datetime.fromtimestamp(e.timestamp) for e in sev_events],
                        y=[sev] * len(sev_events),
                        mode="markers",
                        marker_color=colors[sev],
                        name=sev.capitalize(),
                    )
                )
        fig.update_layout(title="Security Events Timeline")
        return fig


# Global singleton instance
_dashboard_instance: Optional[AnalyticsDashboard] = None


def get_dashboard() -> AnalyticsDashboard:
    """Returns a singleton instance of the AnalyticsDashboard."""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = AnalyticsDashboard()
    return _dashboard_instance


def get_dashboard_json() -> str:
    """
    A convenience function to get the dashboard data as a JSON string.
    This can be used to feed a web frontend.
    """
    dashboard = get_dashboard()
    data = dashboard.get_dashboard_data()

    if PlotlyJSONEncoder:
        return json.dumps(data, cls=PlotlyJSONEncoder)
    else:
        # Fallback if Plotly is not installed
        # Charts will be empty, but summaries will be present
        data.pop("charts", None)
        return json.dumps(data)
