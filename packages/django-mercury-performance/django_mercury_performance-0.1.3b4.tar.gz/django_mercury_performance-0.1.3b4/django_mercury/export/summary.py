"""Multi-test summary HTML export functionality with charts and sortable tables."""

import json
import statistics
from datetime import datetime
from typing import TYPE_CHECKING, List, Tuple

from .utils import escape_html

if TYPE_CHECKING:
    from django_mercury.monitor import MonitorResult


SUMMARY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercury Performance Test Summary - {timestamp}</title>
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
            max-width: 1400px;
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
            font-size: 32px;
            margin-bottom: 12px;
        }}

        h2 {{
            color: #f0f6fc;
            font-size: 20px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #30363d;
        }}

        h3 {{
            color: #c9d1d9;
            font-size: 16px;
            margin: 16px 0 12px 0;
        }}

        .header {{
            background: #161b22;
            border: 1px solid #30363d;
            text-align: center;
        }}

        .timestamp {{
            color: #8b949e;
            font-size: 14px;
            margin-top: 8px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .stat {{
            background: #0d1117;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #30363d;
        }}

        .stat.pass {{
            border-color: #238636;
        }}

        .stat.fail {{
            border-color: #da3633;
        }}

        .stat-label {{
            color: #8b949e;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #f0f6fc;
        }}

        .stat-value.pass {{
            color: #3fb950;
        }}

        .stat-value.fail {{
            color: #f85149;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}

        .chart-container {{
            background: #0d1117;
            padding: 16px;
            border-radius: 6px;
            border: 1px solid #30363d;
        }}

        .chart-container canvas {{
            max-height: 300px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        table.sortable th {{
            cursor: pointer;
            user-select: none;
        }}

        th {{
            background: #0d1117;
            color: #f0f6fc;
            font-weight: 600;
            text-align: left;
            padding: 12px;
            border: 1px solid #30363d;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        th.sortable-header:hover {{
            background: #161b22;
        }}

        th.sort-active {{
            background: #161b22;
            color: #58a6ff;
        }}

        .sort-indicator {{
            float: right;
            color: #8b949e;
            font-size: 12px;
        }}

        td {{
            padding: 12px;
            border: 1px solid #30363d;
            font-size: 14px;
        }}

        tr:hover {{
            background: #0d1117;
        }}

        .status-pass {{
            color: #3fb950;
            font-weight: 600;
        }}

        .status-fail {{
            color: #f85149;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border: 1px solid;
        }}

        .badge.n1 {{
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            border-color: #da3633;
        }}

        .badge.slow {{
            background: rgba(210, 153, 34, 0.15);
            color: #d29922;
            border-color: #d29922;
        }}

        .pattern-summary {{
            background: rgba(248, 81, 73, 0.1);
            border-left: 3px solid #f85149;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 6px;
        }}

        .pattern-query {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 12px;
            color: #c9d1d9;
            background: #0d1117;
            padding: 10px;
            border-radius: 6px;
            margin: 8px 0;
            overflow-x: auto;
            border: 1px solid #30363d;
        }}

        .pattern-tests {{
            margin-top: 10px;
            font-size: 12px;
            color: #8b949e;
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

        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #30363d;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }}

        .progress-fill {{
            height: 100%;
            background: #238636;
            transition: width 0.3s ease;
        }}

        .progress-fill.fail {{
            background: #da3633;
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
        <!-- Header -->
        <div class="card header">
            <h1>Mercury Performance Test Summary</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>

        <!-- Dashboard Stats -->
        <div class="card">
            <h2>Test Run Statistics</h2>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-label">Total Tests</div>
                    <div class="stat-value">{total_tests}</div>
                </div>
                <div class="stat pass">
                    <div class="stat-label">Passed</div>
                    <div class="stat-value pass">{passed_tests}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pass_percent}%"></div>
                    </div>
                </div>
                <div class="stat fail">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value fail">{failed_tests}</div>
                    <div class="progress-bar">
                        <div class="progress-fill fail" style="width: {fail_percent}%"></div>
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Response Time</div>
                    <div class="stat-value">{avg_time:.1f}<small style="font-size: 16px;">ms</small></div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Query Count</div>
                    <div class="stat-value">{avg_queries:.1f}</div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="card">
            <h2>Performance Visualization</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <canvas id="responseTimeChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="queryDistChart"></canvas>
                </div>
            </div>
        </div>

        {slowest_section}

        {n_plus_one_section}

        {all_tests_section}

        <div class="footer">
            Generated by <a href="https://github.com/yourusername/django-mercury-performance" target="_blank">Django Mercury Performance Testing</a> v0.1.1
        </div>
    </div>

    <!-- Inline JavaScript with Chart.js -->
    <script>
        window.MERCURY_DATA = {mercury_data};
    </script>
    
    <script type="module">
        // Import Chart.js from CDN
        import Chart from 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/+esm';
        
        // ============================================================================
        // COMMON UTILITIES
        // ============================================================================
        
        function parseNumeric(str) {{
            const cleaned = str.replace(/[^0-9.-]/g, '');
            return parseFloat(cleaned) || 0;
        }}
        
        function detectDataType(value) {{
            if (/^-?\\d+(\\.\\d+)?(ms|μs|s|%)?$/.test(value.trim())) {{
                return 'number';
            }}
            if (/^\\d{{4}}-\\d{{2}}-\\d{{2}}/.test(value.trim())) {{
                return 'date';
            }}
            return 'string';
        }}
        
        // ============================================================================
        // TABLE SORTING
        // ============================================================================
        
        function initTables() {{
            const tables = document.querySelectorAll('table.sortable');
            tables.forEach(table => makeSortable(table));
        }}
        
        function makeSortable(table) {{
            const headers = table.querySelectorAll('th[data-sort]');
            
            headers.forEach((header, columnIndex) => {{
                header.classList.add('sortable-header');
                header.innerHTML += ' <span class="sort-indicator">↕</span>';
                
                let sortDirection = 'asc';
                
                header.addEventListener('click', () => {{
                    headers.forEach(h => h.classList.remove('sort-active'));
                    header.classList.add('sort-active');
                    
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                    
                    const indicator = header.querySelector('.sort-indicator');
                    indicator.textContent = sortDirection === 'asc' ? '↑' : '↓';
                    
                    sortTable(table, columnIndex, sortDirection);
                }});
            }});
        }}
        
        function sortTable(table, columnIndex, direction) {{
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            const firstCellValue = rows[0]?.cells[columnIndex]?.textContent.trim() || '';
            const dataType = detectDataType(firstCellValue);
            
            rows.sort((a, b) => {{
                const aValue = a.cells[columnIndex]?.textContent.trim() || '';
                const bValue = b.cells[columnIndex]?.textContent.trim() || '';
                
                let comparison = 0;
                
                if (dataType === 'number') {{
                    const aNum = parseNumeric(aValue);
                    const bNum = parseNumeric(bValue);
                    comparison = aNum - bNum;
                }} else if (dataType === 'date') {{
                    const aDate = new Date(aValue);
                    const bDate = new Date(bDate);
                    comparison = aDate - bDate;
                }} else {{
                    comparison = aValue.localeCompare(bValue);
                }}
                
                return direction === 'asc' ? comparison : -comparison;
            }});
            
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        // ============================================================================
        // CHART RENDERING
        // ============================================================================
        
        function getDarkThemeConfig() {{
            return {{
                color: '#c9d1d9',
                backgroundColor: '#161b22',
                borderColor: '#30363d',
                gridColor: '#30363d',
                colors: {{
                    success: '#238636',
                    failure: '#da3633',
                    warning: '#d29922',
                    accent: '#58a6ff',
                    secondary: '#8b949e'
                }}
            }};
        }}
        
        function renderResponseTimeChart(canvas, data) {{
            const theme = getDarkThemeConfig();
            const tests = data.tests || [];
            
            const labels = tests.map(t => t.name);
            const times = tests.map(t => t.response_time);
            const colors = tests.map(t => 
                t.status === 'fail' ? theme.colors.failure : theme.colors.success
            );
            
            new Chart(canvas, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Response Time (ms)',
                        data: times,
                        backgroundColor: colors,
                        borderColor: colors,
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: 'Response Time by Test',
                            color: theme.color,
                            font: {{
                                size: 14,
                                weight: 'normal'
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: '#161b22',
                            borderColor: '#30363d',
                            borderWidth: 1,
                            titleColor: theme.color,
                            bodyColor: theme.color,
                            callbacks: {{
                                label: function(context) {{
                                    return `${{context.parsed.y.toFixed(2)}}ms`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                color: theme.color,
                                callback: function(value) {{
                                    return value + 'ms';
                                }}
                            }},
                            grid: {{
                                color: theme.gridColor
                            }}
                        }},
                        x: {{
                            ticks: {{
                                color: theme.color,
                                display: false
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        function renderQueryDistributionChart(canvas, data) {{
            const theme = getDarkThemeConfig();
            const tests = data.tests || [];
            
            const buckets = {{}};
            const bucketSize = 5;
            
            tests.forEach(test => {{
                const bucket = Math.floor(test.query_count / bucketSize) * bucketSize;
                const bucketLabel = `${{bucket}}-${{bucket + bucketSize}}`;
                buckets[bucketLabel] = (buckets[bucketLabel] || 0) + 1;
            }});
            
            const sortedLabels = Object.keys(buckets).sort((a, b) => {{
                const aNum = parseInt(a.split('-')[0]);
                const bNum = parseInt(b.split('-')[0]);
                return aNum - bNum;
            }});
            
            const counts = sortedLabels.map(label => buckets[label]);
            
            new Chart(canvas, {{
                type: 'bar',
                data: {{
                    labels: sortedLabels,
                    datasets: [{{
                        label: 'Number of Tests',
                        data: counts,
                        backgroundColor: theme.colors.accent,
                        borderColor: theme.colors.accent,
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: 'Query Count Distribution',
                            color: theme.color,
                            font: {{
                                size: 14,
                                weight: 'normal'
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: '#161b22',
                            borderColor: '#30363d',
                            borderWidth: 1,
                            titleColor: theme.color,
                            bodyColor: theme.color,
                            callbacks: {{
                                title: function(context) {{
                                    return `${{context[0].label}} queries`;
                                }},
                                label: function(context) {{
                                    return `${{context.parsed.y}} test(s)`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                color: theme.color,
                                stepSize: 1
                            }},
                            grid: {{
                                color: theme.gridColor
                            }}
                        }},
                        x: {{
                            ticks: {{
                                color: theme.color
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // ============================================================================
        // INITIALIZATION
        // ============================================================================
        
        function init() {{
            console.log('Mercury Report: Initializing...');
            
            // Initialize sortable tables
            initTables();
            
            // Initialize charts
            if (window.MERCURY_DATA) {{
                const data = window.MERCURY_DATA;
                
                const responseTimeCanvas = document.getElementById('responseTimeChart');
                if (responseTimeCanvas) {{
                    renderResponseTimeChart(responseTimeCanvas, data);
                }}
                
                const queryDistCanvas = document.getElementById('queryDistChart');
                if (queryDistCanvas) {{
                    renderQueryDistributionChart(queryDistCanvas, data);
                }}
            }} else {{
                console.warn('MERCURY_DATA not found');
            }}
            
            console.log('Mercury Report: Ready');
        }}
        
        // Run when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', init);
        }} else {{
            init();
        }}
    </script>
</body>
</html>
"""


def export_summary_html(results: List[Tuple[str, "MonitorResult"]], filename: str) -> None:
    """Export summary of multiple test results to HTML.

    Args:
        results: List of (test_name, MonitorResult) tuples
        filename: Output HTML file path

    Example:
        from django_mercury.summary import MercurySummaryTracker
        tracker = MercurySummaryTracker.instance()
        # After running tests...
        export_summary_html(tracker.results, 'report.html')
    """
    if not results:
        # Create empty report
        html = SUMMARY_HTML_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            pass_percent=0,
            fail_percent=0,
            avg_time=0,
            avg_queries=0,
            slowest_section="",
            n_plus_one_section="",
            all_tests_section="<div class='card'><h2>No tests found</h2></div>",
            mercury_data=json.dumps({"tests": []}),
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        return

    # Calculate stats
    total = len(results)
    passed = sum(1 for _, r in results if not r.failures)
    failed = total - passed
    pass_percent = (passed / total * 100) if total > 0 else 0
    fail_percent = (failed / total * 100) if total > 0 else 0

    response_times = [r.response_time_ms for _, r in results]
    query_counts = [r.query_count for _, r in results]
    avg_time = statistics.mean(response_times)
    avg_queries = statistics.mean(query_counts)

    # Prepare data for JavaScript
    mercury_data = {
        "tests": [
            {
                "name": test_name,
                "response_time": result.response_time_ms,
                "query_count": result.query_count,
                "status": "pass" if not result.failures else "fail",
                "has_n1": bool(result.n_plus_one_patterns),
            }
            for test_name, result in results
        ],
        "stats": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "avg_time": avg_time,
            "avg_queries": avg_queries,
        },
    }

    # Generate sections
    slowest_section = _format_slowest_section(results)
    n_plus_one_section = _format_n_plus_one_summary(results)
    all_tests_section = _format_all_tests_section(results)

    # Generate HTML
    html = SUMMARY_HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        pass_percent=pass_percent,
        fail_percent=fail_percent,
        avg_time=avg_time,
        avg_queries=avg_queries,
        slowest_section=slowest_section,
        n_plus_one_section=n_plus_one_section,
        all_tests_section=all_tests_section,
        mercury_data=json.dumps(mercury_data),
    )

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def _format_slowest_section(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format slowest tests section with sortable table."""
    sorted_results = sorted(results, key=lambda x: x[1].response_time_ms, reverse=True)
    top_10 = sorted_results[:10]

    rows = []
    for test_name, result in top_10:
        status_class = "status-pass" if not result.failures else "status-fail"
        status_text = "PASS" if not result.failures else "FAIL"
        has_n1 = '<span class="badge n1">N+1</span>' if result.n_plus_one_patterns else ""

        rows.append(
            f"""
        <tr>
            <td>{escape_html(test_name)}</td>
            <td>{result.response_time_ms:.2f}ms</td>
            <td>{result.query_count}</td>
            <td>{has_n1}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
        """
        )

    return f"""
    <div class="card">
        <h2>Slowest Tests (Top 10)</h2>
        <table class="sortable">
            <thead>
                <tr>
                    <th data-sort="string">Test Name</th>
                    <th data-sort="number">Response Time</th>
                    <th data-sort="number">Query Count</th>
                    <th>N+1</th>
                    <th data-sort="string">Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """


def _format_n_plus_one_summary(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format N+1 patterns aggregated across all tests."""
    # Aggregate N+1 patterns
    pattern_map = {}  # normalized_query -> (count, [test_names])

    for test_name, result in results:
        for pattern in result.n_plus_one_patterns:
            key = pattern.normalized_query
            if key not in pattern_map:
                pattern_map[key] = (pattern.count, [test_name], pattern.sample_queries[:2])
            else:
                old_count, test_list, samples = pattern_map[key]
                pattern_map[key] = (old_count + pattern.count, test_list + [test_name], samples)

    if not pattern_map:
        return """
        <div class="card">
            <h2>N+1 Query Patterns</h2>
            <div class="no-patterns">No N+1 patterns detected across all tests</div>
        </div>
        """

    # Sort by total count
    sorted_patterns = sorted(pattern_map.items(), key=lambda x: x[1][0], reverse=True)

    items = []
    for query, (count, test_names, samples) in sorted_patterns[:15]:  # Top 15
        unique_tests = list(set(test_names))
        test_list = "<br>".join(f"• {escape_html(t)}" for t in unique_tests[:5])
        if len(unique_tests) > 5:
            test_list += f"<br>• ... and {len(unique_tests) - 5} more"

        sample_html = ""
        if samples:
            sample_html = "<br>".join(
                f'<div class="pattern-query">{escape_html(s)}</div>' for s in samples[:1]
            )

        items.append(
            f"""
        <div class="pattern-summary">
            <div style="font-weight: 600; color: #f85149; margin-bottom: 8px;">
                {count}x occurrences across {len(unique_tests)} test(s)
            </div>
            <div class="pattern-query">{escape_html(query[:150])}{'' if len(query) <= 150 else '...'}</div>
            {sample_html}
            <div class="pattern-tests">
                <strong>Affected tests:</strong><br>
                {test_list}
            </div>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>N+1 Query Patterns (Aggregated)</h2>
        <div style="margin-bottom: 16px; color: #f85149; font-size: 14px;">
            Found {len(pattern_map)} unique pattern(s) across all tests
        </div>
        {''.join(items)}
    </div>
    """


def _format_all_tests_section(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format all test results with sortable table."""
    rows = []

    for test_name, result in results:
        status_class = "status-pass" if not result.failures else "status-fail"
        status_text = "PASS" if not result.failures else "FAIL"
        has_n1 = '<span class="badge n1">N+1</span>' if result.n_plus_one_patterns else ""

        rows.append(
            f"""
        <tr>
            <td>{escape_html(test_name)}</td>
            <td>{result.response_time_ms:.2f}ms</td>
            <td>{result.query_count}</td>
            <td>{has_n1}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
        """
        )

    return f"""
    <div class="card">
        <h2>All Test Results ({len(results)} tests)</h2>
        <table class="sortable">
            <thead>
                <tr>
                    <th data-sort="string">Test Name</th>
                    <th data-sort="number">Response Time</th>
                    <th data-sort="number">Query Count</th>
                    <th>N+1</th>
                    <th data-sort="string">Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """
