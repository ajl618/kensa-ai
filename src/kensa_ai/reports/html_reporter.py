"""
HTML report generator for Kensa-AI.
"""

from pathlib import Path
from typing import Any

from jinja2 import Template


class HTMLReporter:
    """
    Generate human-readable HTML reports.
    """

    HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kensa-AI Report - {{ run_id[:8] }}</title>
    <style>
        :root {
            --primary: #1a1a2e;
            --secondary: #16213e;
            --accent: #0f3460;
            --text: #eee;
            --success: #00d26a;
            --warning: #ffc107;
            --danger: #ff6b6b;
            --info: #00b8d9;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--primary);
            color: var(--text);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        header {
            background: var(--secondary);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }

        header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        header .meta {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            color: #aaa;
            font-size: 0.9rem;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .summary-card {
            background: var(--secondary);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }

        .summary-card .value {
            font-size: 2.5rem;
            font-weight: bold;
        }

        .summary-card .label {
            color: #888;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }

        .summary-card.passed .value { color: var(--success); }
        .summary-card.failed .value { color: var(--danger); }
        .summary-card.score .value { color: var(--info); }

        .section {
            background: var(--secondary);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        .section h2 {
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--accent);
        }

        .severity-chart {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .severity-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }

        .severity-critical { background: #dc3545; }
        .severity-high { background: #fd7e14; }
        .severity-medium { background: #ffc107; color: #000; }
        .severity-low { background: #17a2b8; }
        .severity-info { background: #6c757d; }

        .category-table {
            width: 100%;
            border-collapse: collapse;
        }

        .category-table th,
        .category-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--accent);
        }

        .category-table th {
            color: #888;
            text-transform: uppercase;
            font-size: 0.8rem;
        }

        .progress-bar {
            height: 8px;
            background: var(--accent);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-bar .fill {
            height: 100%;
            background: var(--success);
            transition: width 0.3s;
        }

        .results-list {
            max-height: 600px;
            overflow-y: auto;
        }

        .result-item {
            background: var(--accent);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        }

        .result-item.passed {
            border-left: 4px solid var(--success);
        }

        .result-item.failed {
            border-left: 4px solid var(--danger);
        }

        .result-item.error {
            border-left: 4px solid var(--warning);
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .result-name {
            font-weight: bold;
        }

        .result-status {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            text-transform: uppercase;
        }

        .result-status.passed { background: var(--success); color: #000; }
        .result-status.failed { background: var(--danger); }
        .result-status.error { background: var(--warning); color: #000; }

        .result-details {
            font-size: 0.9rem;
            color: #aaa;
        }

        .result-category {
            background: var(--secondary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
        }

        .collapsible {
            cursor: pointer;
        }

        .collapsible:after {
            content: ' ▼';
            font-size: 0.7rem;
        }

        .collapsed:after {
            content: ' ▶';
        }

        .evidence-info {
            background: var(--accent);
            padding: 1rem;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85rem;
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Kensa-AI Report</h1>
            <div class="meta">
                <span>Run ID: {{ run_id[:8] }}</span>
                <span>Target: {{ target.name }} ({{ target.model }})</span>
                <span>Generated: {{ timestamp }}</span>
                <span>Duration: {{ "%.1f"|format(duration_seconds) }}s</span>
            </div>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{{ summary.total_tests }}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="summary-card passed">
                <div class="value">{{ summary.passed }}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="value">{{ summary.failed }}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card score">
                <div class="value">{{ "%.0f"|format(summary.score * 100) }}%</div>
                <div class="label">Score</div>
            </div>
        </div>

        <div class="section">
            <h2>Severity Breakdown</h2>
            <div class="severity-chart">
                {% for severity, count in summary.by_severity.items() %}
                {% if count > 0 %}
                <span class="severity-badge severity-{{ severity }}">
                    {{ severity|upper }}: {{ count }}
                </span>
                {% endif %}
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>Results by Category</h2>
            <table class="category-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {% for category, stats in summary.by_category.items() %}
                    {% set total = stats.passed + stats.failed + stats.get('error', 0) %}
                    {% set rate = (stats.passed / total * 100) if total > 0 else 0 %}
                    <tr>
                        <td>{{ category }}</td>
                        <td>{{ stats.passed }}</td>
                        <td>{{ stats.failed }}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="fill" style="width: {{ rate }}%"></div>
                            </div>
                            {{ "%.0f"|format(rate) }}%
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Failed Tests ({{ summary.failed }})</h2>
            <div class="results-list">
                {% for result in results %}
                {% if result.status == 'failed' %}
                <div class="result-item failed">
                    <div class="result-header">
                        <span class="result-name">{{ result.test.name }}</span>
                        <span class="result-status failed">Failed</span>
                    </div>
                    <div class="result-details">
                        <span class="result-category">{{ result.test.category }}</span>
                        <span class="severity-badge severity-{{ result.test.severity }}">
                            {{ result.test.severity|upper }}
                        </span>
                        <p style="margin-top: 0.5rem;">{{ result.test.description }}</p>
                        {% if result.result.risk_indicators %}
                        <p style="margin-top: 0.5rem; color: #ff6b6b;">
                            Risk indicators: {{ result.result.risk_indicators|join(', ') }}
                        </p>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>All Test Results</h2>
            <div class="results-list">
                {% for result in results %}
                <div class="result-item {{ result.status }}">
                    <div class="result-header">
                        <span class="result-name">{{ result.test.name }}</span>
                        <span class="result-status {{ result.status }}">{{ result.status }}</span>
                    </div>
                    <div class="result-details">
                        <span class="result-category">{{ result.test.category }}</span>
                        <span class="severity-badge severity-{{ result.test.severity }}">
                            {{ result.test.severity|upper }}
                        </span>
                        {% if result.result %}
                        <span style="margin-left: 1rem;">
                            Confidence: {{ "%.0f"|format(result.result.confidence * 100) }}%
                        </span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        {% if evidence %}
        <div class="section">
            <h2>Evidence Information</h2>
            <div class="evidence-info">
                <p>Evidence Mode: {{ 'Enabled' if evidence.enabled else 'Disabled' }}</p>
                <p>Hash Algorithm: {{ evidence.hash_algorithm }}</p>
                <p>Report generated at: {{ timestamp }}</p>
            </div>
        </div>
        {% endif %}

        <footer>
            <p>Generated by Kensa-AI v0.1.0</p>
            <p>For ISO/IEC 42001 aligned AI security testing</p>
        </footer>
    </div>
</body>
</html>
'''

    def __init__(self):
        """Initialize the HTML reporter."""
        self.template = Template(self.HTML_TEMPLATE)

    def generate(self, results: dict[str, Any], output_path: Path) -> Path:
        """
        Generate HTML report from test results.

        Args:
            results: Test results dictionary
            output_path: Path to write the report

        Returns:
            Path to generated report
        """
        # Render HTML
        html = self.template.render(**results)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(html)

        return output_path

    def to_string(self, results: dict[str, Any]) -> str:
        """
        Generate HTML report as string.

        Args:
            results: Test results dictionary

        Returns:
            HTML string
        """
        return self.template.render(**results)
