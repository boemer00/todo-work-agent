"""
Custom metrics tracking for agent performance.

Track important metrics like:
- Tool usage patterns
- Response latency
- Error rates
- User satisfaction signals

These metrics complement LangSmith's automatic tracing.
"""

from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict


class AgentMetrics:
    """
    Simple in-memory metrics tracker.

    In production, you'd send these to a metrics backend like:
    - Prometheus
    - Datadog
    - CloudWatch

    For learning, we'll keep them in memory and print summaries.
    """

    def __init__(self):
        self.tool_calls = defaultdict(int)
        self.errors = []
        self.response_times = []
        self.session_count = 0

    def track_tool_call(self, tool_name: str):
        """Track that a tool was called."""
        self.tool_calls[tool_name] += 1

    def track_error(self, error_type: str, error_msg: str, context: Dict[str, Any]):
        """Track an error occurrence."""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": error_msg,
            "context": context
        })

    def track_response_time(self, duration_ms: float):
        """Track response time in milliseconds."""
        self.response_times.append(duration_ms)

    def track_session_start(self):
        """Track a new session."""
        self.session_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Dictionary with metric summaries
        """
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

        return {
            "total_sessions": self.session_count,
            "tool_usage": dict(self.tool_calls),
            "total_errors": len(self.errors),
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": min(self.response_times) if self.response_times else 0,
            "max_response_time_ms": max(self.response_times) if self.response_times else 0,
        }

    def print_summary(self):
        """Print a human-readable metrics summary."""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("📊 AGENT METRICS SUMMARY")
        print("="*60)
        print(f"Total Sessions: {summary['total_sessions']}")
        print(f"\nTool Usage:")
        for tool, count in summary['tool_usage'].items():
            print(f"  • {tool}: {count} calls")
        print(f"\nPerformance:")
        print(f"  • Avg Response Time: {summary['avg_response_time_ms']}ms")
        print(f"  • Min Response Time: {summary['min_response_time_ms']}ms")
        print(f"  • Max Response Time: {summary['max_response_time_ms']}ms")
        print(f"\nErrors: {summary['total_errors']}")
        if self.errors:
            print("  Recent errors:")
            for error in self.errors[-3:]:  # Show last 3
                print(f"    • {error['error_type']}: {error['message']}")
        print("="*60 + "\n")


# Global metrics instance (singleton pattern)
_metrics_instance = None


def get_metrics() -> AgentMetrics:
    """
    Get the global metrics instance.

    Returns:
        The singleton AgentMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = AgentMetrics()
    return _metrics_instance


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    global _metrics_instance
    _metrics_instance = AgentMetrics()
