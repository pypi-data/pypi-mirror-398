"""Single test HTML export functionality."""

from typing import TYPE_CHECKING

from .utils import escape_html

if TYPE_CHECKING:
    from django_mercury.monitor import MonitorResult


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercury Performance Report - {test_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 16px;
        }}

        h1 {{
            color: #f0f6fc;
            font-size: 28px;
            margin-bottom: 16px;
        }}

        h2 {{
            color: #f0f6fc;
            font-size: 20px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #30363d;
        }}

        .header {{
            background: #161b22;
            border: 1px solid #30363d;
        }}

        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status.pass {{
            background: rgba(35, 134, 54, 0.15);
            color: #3fb950;
            border: 1px solid #238636;
        }}

        .status.fail {{
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            border: 1px solid #da3633;
        }}

        .meta {{
            color: #8b949e;
            font-size: 14px;
            margin-top: 12px;
        }}

        .meta code {{
            background: #0d1117;
            padding: 3px 6px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            color: #58a6ff;
            border: 1px solid #30363d;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .metric {{
            background: #0d1117;
            padding: 16px;
            border-radius: 6px;
            border: 1px solid #30363d;
        }}

        .metric.pass {{
            border-color: #238636;
        }}

        .metric.fail {{
            border-color: #da3633;
        }}

        .metric-label {{
            color: #8b949e;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 24px;
            font-weight: 700;
            color: #f0f6fc;
        }}

        .metric-value.pass {{
            color: #3fb950;
        }}

        .metric-value.fail {{
            color: #f85149;
        }}

        .metric-threshold {{
            color: #6e7681;
            font-size: 12px;
            margin-top: 4px;
        }}

        .pattern {{
            background: rgba(248, 81, 73, 0.1);
            border-left: 3px solid #f85149;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 6px;
        }}

        .pattern-header {{
            font-weight: 600;
            color: #f85149;
            margin-bottom: 8px;
        }}

        .pattern-count {{
            display: inline-block;
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid #da3633;
        }}

        .pattern-sql {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 12px;
            color: #c9d1d9;
            background: #0d1117;
            padding: 12px;
            border-radius: 6px;
            margin-top: 8px;
            overflow-x: auto;
            line-height: 1.5;
            border: 1px solid #30363d;
        }}

        .sample-queries {{
            margin-top: 12px;
        }}

        .sample-label {{
            font-size: 12px;
            color: #8b949e;
            font-weight: 600;
            margin-bottom: 6px;
        }}

        .sample {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 11px;
            color: #8b949e;
            background: #0d1117;
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 6px;
            overflow-x: auto;
            border: 1px solid #30363d;
        }}

        .warning {{
            background: rgba(210, 153, 34, 0.1);
            border-left: 3px solid #d29922;
            padding: 12px 16px;
            margin-bottom: 12px;
            border-radius: 6px;
        }}

        .warning-text {{
            color: #d29922;
            font-size: 14px;
        }}

        .failure {{
            background: rgba(248, 81, 73, 0.1);
            border-left: 3px solid #f85149;
            padding: 12px 16px;
            margin-bottom: 12px;
            border-radius: 6px;
        }}

        .failure-text {{
            color: #f85149;
            font-size: 14px;
        }}

        .footer {{
            text-align: center;
            color: #8b949e;
            font-size: 12px;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #30363d;
        }}

        .footer a {{
            color: #58a6ff;
            text-decoration: none;
        }}

        .footer a:hover {{
            text-decoration: underline;
        }}

        .no-patterns {{
            color: #3fb950;
            font-size: 14px;
            padding: 16px;
            text-align: center;
            background: rgba(35, 134, 54, 0.1);
            border-radius: 6px;
            border: 1px solid #238636;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Card -->
        <div class="card header">
            <h1>Mercury Performance Report</h1>
            <div class="meta">
                <div><strong>Test:</strong> {test_name}</div>
                <div><strong>Location:</strong> <code>{test_location}</code></div>
                <div style="margin-top: 12px;">
                    <span class="status {status_class}">{status}</span>
                </div>
            </div>
        </div>

        <!-- Metrics Card -->
        <div class="card">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric {time_class}">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value {time_class}">{response_time}ms</div>
                    <div class="metric-threshold">Threshold: {time_threshold}ms</div>
                </div>
                <div class="metric {query_class}">
                    <div class="metric-label">Query Count</div>
                    <div class="metric-value {query_class}">{query_count}</div>
                    <div class="metric-threshold">Threshold: {query_threshold}</div>
                </div>
            </div>
        </div>

        {n_plus_one_section}

        {warnings_section}

        {failures_section}

        <div class="footer">
            Generated by <a href="https://github.com/yourusername/django-mercury-performance" target="_blank">Django Mercury Performance Testing</a> v0.1.1
        </div>
    </div>
</body>
</html>
"""


def export_html(result: "MonitorResult", filename: str) -> None:
    """Export MonitorResult to standalone HTML file.

    Args:
        result: MonitorResult instance with test metrics
        filename: Path to output HTML file

    Example:
        with monitor() as result:
            response = self.client.get('/api/users/')

        result.to_html('performance_report.html')
    """
    # Determine status
    status = "PASSED" if not result.failures else "FAILED"
    status_class = "pass" if not result.failures else "fail"

    # Color-code metrics
    time_class = (
        "pass" if result.response_time_ms <= result.thresholds["response_time_ms"] else "fail"
    )
    query_class = "pass" if result.query_count <= result.thresholds["query_count"] else "fail"

    # Format N+1 section
    n_plus_one_section = _format_n_plus_one_html(result)

    # Format warnings section
    warnings_section = _format_warnings_html(result.warnings) if result.warnings else ""

    # Format failures section
    failures_section = _format_failures_html(result.failures) if result.failures else ""

    # Generate HTML
    html = HTML_TEMPLATE.format(
        test_name=escape_html(result.test_name or "Unknown Test"),
        test_location=escape_html(result.test_location or "Unknown Location"),
        status=status,
        status_class=status_class,
        response_time=f"{result.response_time_ms:.2f}",
        time_threshold=result.thresholds["response_time_ms"],
        time_class=time_class,
        query_count=result.query_count,
        query_threshold=result.thresholds["query_count"],
        query_class=query_class,
        n_plus_one_section=n_plus_one_section,
        warnings_section=warnings_section,
        failures_section=failures_section,
    )

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def _format_n_plus_one_html(result: "MonitorResult") -> str:
    """Format N+1 patterns section as HTML."""
    if not result.n_plus_one_patterns:
        return """
        <div class="card">
            <h2>N+1 Query Patterns</h2>
            <div class="no-patterns">No N+1 patterns detected</div>
        </div>
        """

    patterns_html = []
    for pattern in result.n_plus_one_patterns:
        # Determine severity
        threshold = result.thresholds["n_plus_one_threshold"]
        if pattern.count >= threshold:
            severity = "FAILURE"
        elif pattern.count >= int(threshold * 0.8):
            severity = "WARNING"
        else:
            severity = "NOTICE"

        # Format sample queries
        samples_html = ""
        if pattern.sample_queries:
            samples = []
            for query in pattern.sample_queries[:3]:
                samples.append(f'<div class="sample">{escape_html(query)}</div>')
            samples_html = f"""
            <div class="sample-queries">
                <div class="sample-label">Sample Queries:</div>
                {''.join(samples)}
            </div>
            """

        pattern_html = f"""
        <div class="pattern">
            <div class="pattern-header">
                {severity}: <span class="pattern-count">{pattern.count}x</span>
            </div>
            <div class="pattern-sql">{escape_html(pattern.normalized_query)}</div>
            {samples_html}
        </div>
        """
        patterns_html.append(pattern_html)

    return f"""
    <div class="card">
        <h2>N+1 Query Patterns Detected</h2>
        {''.join(patterns_html)}
    </div>
    """


def _format_warnings_html(warnings: list) -> str:
    """Format warnings section as HTML."""
    if not warnings:
        return ""

    warnings_html = []
    for warning in warnings:
        warnings_html.append(
            f"""
        <div class="warning">
            <span class="warning-text">{escape_html(warning)}</span>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>Warnings</h2>
        {''.join(warnings_html)}
    </div>
    """


def _format_failures_html(failures: list) -> str:
    """Format failures section as HTML."""
    if not failures:
        return ""

    failures_html = []
    for failure in failures:
        # Handle multi-line failures (preserve formatting)
        failure_text = escape_html(failure).replace("\n", "<br>")
        failures_html.append(
            f"""
        <div class="failure">
            <span class="failure-text">{failure_text}</span>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>Failures</h2>
        {''.join(failures_html)}
    </div>
    """
