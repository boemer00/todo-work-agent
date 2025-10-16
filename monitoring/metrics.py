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

    def calculate_percentiles(self) -> Dict[str, float]:
        """
        Calculate latency percentiles (P50, P95, P99).

        Returns:
            Dictionary with percentile values in milliseconds
        """
        if not self.response_times:
            return {"p50": 0, "p95": 0, "p99": 0}

        sorted_times = sorted(self.response_times)
        n = len(sorted_times)

        return {
            "p50": sorted_times[int(n * 0.50)],
            "p95": sorted_times[min(int(n * 0.95), n - 1)],
            "p99": sorted_times[min(int(n * 0.99), n - 1)]
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Dictionary with metric summaries including percentiles
        """
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

        percentiles = self.calculate_percentiles()

        return {
            "total_sessions": self.session_count,
            "total_requests": len(self.response_times),
            "tool_usage": dict(self.tool_calls),
            "total_errors": len(self.errors),
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": min(self.response_times) if self.response_times else 0,
            "max_response_time_ms": max(self.response_times) if self.response_times else 0,
            "p50_latency_ms": round(percentiles["p50"], 2),
            "p95_latency_ms": round(percentiles["p95"], 2),
            "p99_latency_ms": round(percentiles["p99"], 2),
        }

    def print_summary(self):
        """Print a human-readable metrics summary with percentiles."""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("📊 AGENT METRICS SUMMARY")
        print("="*60)
        print(f"Total Sessions: {summary['total_sessions']}")
        print(f"Total Requests: {summary['total_requests']}")

        if summary['tool_usage']:
            print(f"\nTool Usage:")
            total_calls = sum(summary['tool_usage'].values())
            for tool, count in sorted(summary['tool_usage'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_calls * 100) if total_calls > 0 else 0
                print(f"  • {tool}: {count} calls ({percentage:.1f}%)")

        print(f"\nLatency:")
        print(f"  • P50 (median): {summary['p50_latency_ms']:.0f}ms")
        print(f"  • P95: {summary['p95_latency_ms']:.0f}ms")
        print(f"  • P99: {summary['p99_latency_ms']:.0f}ms")
        print(f"  • Avg: {summary['avg_response_time_ms']:.0f}ms")
        print(f"  • Min: {summary['min_response_time_ms']:.0f}ms")
        print(f"  • Max: {summary['max_response_time_ms']:.0f}ms")

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
