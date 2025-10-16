"""
Performance Dashboard - Terminal-based performance visualization.

Displays comprehensive performance metrics including:
- Latency percentiles (P50, P95, P99)
- Tool usage distribution
- Cost analysis
- Error tracking
- Request volume

Usage:
    from monitoring.performance_dashboard import display_dashboard
    display_dashboard()
"""

from typing import Dict, Any
from monitoring.metrics import get_metrics


def display_dashboard():
    """
    Display a comprehensive performance dashboard in the terminal.

    Shows all key metrics in an easy-to-read format.
    """
    metrics = get_metrics()
    summary = metrics.get_summary()

    print("\n" + "="*70)
    print("📊 PERFORMANCE DASHBOARD")
    print("="*70)

    # Session & Request Info
    print(f"\n{'SESSION OVERVIEW':<30}")
    print(f"  Total Sessions:          {summary['total_sessions']:>6}")
    print(f"  Total Requests:          {summary['total_requests']:>6}")

    # Latency Metrics
    if summary['total_requests'] > 0:
        print(f"\n{'LATENCY METRICS':<30}")
        print(f"  P50 (Median):            {summary['p50_latency_ms']:>6.0f} ms")
        print(f"  P95:                     {summary['p95_latency_ms']:>6.0f} ms")
        print(f"  P99:                     {summary['p99_latency_ms']:>6.0f} ms")
        print(f"  Average:                 {summary['avg_response_time_ms']:>6.0f} ms")
        print(f"  Min:                     {summary['min_response_time_ms']:>6.0f} ms")
        print(f"  Max:                     {summary['max_response_time_ms']:>6.0f} ms")

        # Performance Grade
        p50 = summary['p50_latency_ms']
        if p50 < 2000:
            grade = "A (Excellent)"
        elif p50 < 2500:
            grade = "B+ (Very Good)"
        elif p50 < 3000:
            grade = "B (Good)"
        elif p50 < 5000:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
        print(f"  Performance Grade:       {grade:>20}")

    # Tool Usage
    if summary['tool_usage']:
        print(f"\n{'TOOL USAGE':<30}")
        total_tool_calls = sum(summary['tool_usage'].values())
        sorted_tools = sorted(summary['tool_usage'].items(), key=lambda x: x[1], reverse=True)

        for tool, count in sorted_tools:
            percentage = (count / total_tool_calls * 100) if total_tool_calls > 0 else 0
            bar_length = int(percentage / 5)  # Scale to 20 chars max
            bar = "█" * bar_length
            print(f"  {tool:<20} {count:>3} calls ({percentage:>5.1f}%) {bar}")

    # Cost Analysis (based on gpt-4o-mini pricing)
    if summary['total_requests'] > 0:
        print(f"\n{'COST ANALYSIS (gpt-4o-mini)':<30}")
        # Rough estimates based on typical usage
        avg_cost_per_request = 0.003  # $0.003 per request (approximate)
        total_cost = summary['total_requests'] * avg_cost_per_request

        print(f"  Cost per Request:        ${avg_cost_per_request:>6.4f}")
        print(f"  Total Cost:              ${total_cost:>6.2f}")

        # Projections
        daily_projection = total_cost / (summary['total_sessions'] or 1) * 7  # Assume weekly sessions
        print(f"  Daily Projection:        ${daily_projection:>6.2f}")
        print(f"  Monthly Projection:      ${daily_projection * 30:>6.2f}")

    # Error Tracking
    print(f"\n{'ERROR TRACKING':<30}")
    print(f"  Total Errors:            {summary['total_errors']:>6}")

    if metrics.errors:
        error_rate = (summary['total_errors'] / summary['total_requests'] * 100) if summary['total_requests'] > 0 else 0
        print(f"  Error Rate:              {error_rate:>5.1f}%")

        # Show error breakdown
        error_types = {}
        for error in metrics.errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        print(f"\n  Error Types:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {error_type}: {count}")

        # Recent errors
        print(f"\n  Recent Errors (last 3):")
        for error in metrics.errors[-3:]:
            timestamp = error['timestamp'].split('T')[1].split('.')[0]  # Extract time
            print(f"    • [{timestamp}] {error['error_type']}: {error['message'][:50]}")
    else:
        print(f"  Error Rate:              {0:>5.1f}% ✅")

    # Performance Status
    print(f"\n{'SYSTEM STATUS':<30}")

    # Determine overall health
    issues = []
    if summary['total_requests'] > 0:
        if summary['p50_latency_ms'] > 5000:
            issues.append("High latency")
        if summary['total_errors'] / summary['total_requests'] > 0.05:
            issues.append("High error rate")

    if not issues:
        status = "✅ All systems healthy"
    else:
        status = f"⚠️  Issues detected: {', '.join(issues)}"

    print(f"  {status}")

    print("="*70)

    # Recommendations
    if summary['total_requests'] > 0:
        print("\n💡 RECOMMENDATIONS:")

        if summary['p50_latency_ms'] > 3000:
            print("  • Consider implementing streaming for better UX")
            print("  • Review OPTIMIZATION_PLAN.md for latency improvements")

        if summary['total_errors'] > 0:
            print("  • Review error logs in LangSmith")
            print("  • Check PERFORMANCE_ANALYSIS.md for debugging tips")

        if summary['total_requests'] < 10:
            print("  • Generate more test data for statistically significant metrics")

        print("\n📊 View detailed traces: https://eu.smith.langchain.com")
        print("📖 Documentation: docs/PERFORMANCE_ANALYSIS.md")

    print()


def export_metrics_json() -> Dict[str, Any]:
    """
    Export metrics as JSON for external tools.

    Returns:
        Dictionary with all metrics
    """
    metrics = get_metrics()
    return metrics.get_summary()


def print_quick_stats():
    """
    Print quick one-line performance stats.

    Useful for monitoring during development.
    """
    metrics = get_metrics()
    summary = metrics.get_summary()

    if summary['total_requests'] > 0:
        print(f"⚡ P50: {summary['p50_latency_ms']:.0f}ms | "
              f"P95: {summary['p95_latency_ms']:.0f}ms | "
              f"Requests: {summary['total_requests']} | "
              f"Errors: {summary['total_errors']}")
    else:
        print("⚡ No requests tracked yet")


# Example usage
if __name__ == "__main__":
    display_dashboard()
