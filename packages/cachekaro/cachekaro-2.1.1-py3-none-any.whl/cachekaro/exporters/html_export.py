"""
HTML exporter for CacheKaro.

Produces interactive HTML reports with charts and tables.
"""

from __future__ import annotations

import base64
import html
import json
from datetime import datetime

from cachekaro.exporters.base import Exporter, ExportFormat
from cachekaro.models.scan_result import ScanResult


# Build metadata - do not modify
def _d(x: str) -> str:
    return base64.b64decode(x).decode()


_attr = {
    "n": "TU9ISVQgQkFHUkk=",  # Name
    "u": "aHR0cHM6Ly9naXRodWIuY29tL01vaGl0LUJhZ3Jp",  # Profile URL
    "r": "aHR0cHM6Ly9naXRodWIuY29tL01vaGl0LUJhZ3JpL2NhY2hla2Fybw==",  # Repo URL
    "c": "SW5kaWE=",  # Country
}


class HtmlExporter(Exporter):
    """
    Exports scan results to HTML format.

    Produces a standalone HTML page with:
    - Interactive charts (using Chart.js)
    - Sortable/filterable tables
    - Responsive design
    - Clean minimalist purple theme
    """

    def __init__(self, title: str = "CacheKaro Report", dark_mode: bool = True):
        """
        Initialize the HTML exporter.

        Args:
            title: Page title
            dark_mode: Use dark color scheme (default True)
        """
        self.title = title
        self.dark_mode = dark_mode

    @property
    def format(self) -> ExportFormat:
        return ExportFormat.HTML

    @property
    def file_extension(self) -> str:
        return "html"

    def export(self, result: ScanResult) -> str:
        """Export scan result to HTML format."""
        # Prepare data for charts
        category_data = self._prepare_category_data(result)
        top_items_data = self._prepare_top_items_data(result)

        # Build HTML with minimalist purple theme
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {{
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --bg-card: #16162a;
            --bg-card-hover: #1e1e3a;
            --purple-primary: #7c3aed;
            --purple-light: #a78bfa;
            --purple-dark: #5b21b6;
            --purple-muted: #4c1d95;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #2d2d4a;
            --success: #22c55e;
            --warning: #eab308;
            --danger: #ef4444;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* Header */
        header {{
            text-align: center;
            margin-bottom: 48px;
            padding: 48px 24px;
            background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}

        header:hover {{
            border-color: var(--purple-primary);
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.15);
        }}

        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--purple-light);
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            transition: all 0.3s ease;
            animation: subtle-glow 3s ease-in-out infinite;
        }}

        .logo:hover {{
            text-shadow: 0 0 20px rgba(167, 139, 250, 0.5);
        }}

        @keyframes subtle-glow {{
            0%, 100% {{ text-shadow: 0 0 10px rgba(167, 139, 250, 0.2); }}
            50% {{ text-shadow: 0 0 20px rgba(167, 139, 250, 0.4); }}
        }}

        .tagline {{
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }}

        .timestamp {{
            margin-top: 16px;
            font-size: 0.875rem;
            color: var(--text-muted);
        }}

        /* Grid Layout */
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 24px;
        }}

        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Cards */
        .card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }}

        .card:hover {{
            border-color: var(--purple-primary);
            background: var(--bg-card-hover);
        }}

        .card-title {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }}

        /* Stats */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .stat {{
            text-align: center;
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: 8px;
            transition: all 0.3s ease;
        }}

        .stat:hover {{
            background: var(--bg-card-hover);
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.2);
        }}

        .stat:hover .stat-value {{
            text-shadow: 0 0 15px rgba(167, 139, 250, 0.6);
        }}

        .stat-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--purple-light);
            margin-bottom: 4px;
            transition: text-shadow 0.3s ease;
        }}

        .stat-value.highlight {{
            color: var(--success);
        }}

        .stat-value.warning {{
            color: var(--warning);
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Chart Container */
        .chart-container {{
            position: relative;
            height: 280px;
        }}

        /* Full width card */
        .card-full {{
            grid-column: 1 / -1;
        }}

        /* Table */
        .table-wrapper {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            cursor: pointer;
            user-select: none;
            transition: color 0.2s ease;
        }}

        th:hover {{
            color: var(--purple-light);
        }}

        tr:hover {{
            background: var(--bg-secondary);
        }}

        td {{
            font-size: 0.875rem;
        }}

        /* Size colors */
        .size-large {{
            color: var(--purple-light);
            font-weight: 600;
        }}

        .size-medium {{
            color: var(--warning);
        }}

        .size-small {{
            color: var(--text-secondary);
        }}

        /* Risk badges */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-safe {{
            background: rgba(34, 197, 94, 0.15);
            color: var(--success);
        }}

        .badge-moderate {{
            background: rgba(234, 179, 8, 0.15);
            color: var(--warning);
        }}

        .badge-caution {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
        }}

        /* Search box */
        .search-box {{
            width: 100%;
            padding: 12px 16px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 0.875rem;
            font-family: inherit;
            transition: all 0.2s ease;
        }}

        .search-box:focus {{
            outline: none;
            border-color: var(--purple-primary);
        }}

        .search-box::placeholder {{
            color: var(--text-muted);
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 48px;
            padding: 24px;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        footer a {{
            color: var(--purple-light);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: var(--bg-primary);
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--purple-primary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">CacheKaro</div>
            <p class="tagline">Storage & Cache Analysis Report</p>
            <p class="timestamp">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </header>

        <div class="grid">
            <div class="card">
                <h2 class="card-title">Disk Overview</h2>
                <div class="stats-grid">
                    <div class="stat">
                        <div class="stat-value">{result.formatted_disk_total}</div>
                        <div class="stat-label">Total Space</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value warning">{result.formatted_disk_used}</div>
                        <div class="stat-label">Used</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value highlight">{result.formatted_disk_free}</div>
                        <div class="stat-label">Free</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{result.disk_usage_percent:.1f}%</div>
                        <div class="stat-label">Usage</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">Cache Summary</h2>
                <div class="stats-grid">
                    <div class="stat">
                        <div class="stat-value">{result.formatted_total_size}</div>
                        <div class="stat-label">Total Cache</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value highlight">{result.formatted_cleanable_size}</div>
                        <div class="stat-label">Cleanable</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{result.total_files:,}</div>
                        <div class="stat-label">Files</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len(result.items)}</div>
                        <div class="stat-label">Locations</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">Space by Category</h2>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2 class="card-title">Top Consumers</h2>
                <div class="chart-container">
                    <canvas id="topItemsChart"></canvas>
                </div>
            </div>

            <div class="card card-full">
                <h2 class="card-title">All Cache Locations</h2>
                <input type="text" class="search-box" id="searchBox" placeholder="Search cache locations...">
                <div class="table-wrapper">
                    <table id="cacheTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable(0)">Name</th>
                                <th onclick="sortTable(1)">Category</th>
                                <th onclick="sortTable(2)">Size</th>
                                <th onclick="sortTable(3)">Files</th>
                                <th onclick="sortTable(4)">Age</th>
                                <th onclick="sortTable(5)">Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(result)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer>
            <p>Generated by <a href="{_d(_attr['r'])}"><strong>CacheKaro</strong></a> &middot; <em>Clean It Up!</em></p>
            <p style="margin-top: 12px;">Made in 🇮🇳 with ❤️ by <a href="{_d(_attr['u'])}">{_d(_attr['n'])}</a></p>
        </footer>
    </div>

    <script>
        // Color palette
        const colors = [
            '#7c3aed', '#a78bfa', '#c4b5fd', '#8b5cf6',
            '#6366f1', '#818cf8', '#60a5fa', '#38bdf8',
            '#22c55e', '#eab308'
        ];

        // Category Doughnut Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(category_data['labels'])},
                datasets: [{{
                    data: {json.dumps(category_data['values'])},
                    backgroundColor: colors,
                    borderColor: '#0f0f1a',
                    borderWidth: 2,
                    hoverBorderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            color: '#94a3b8',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 11
                            }},
                            padding: 12,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }}
                    }}
                }}
            }}
        }});

        // Top Items Bar Chart
        const topCtx = document.getElementById('topItemsChart').getContext('2d');
        new Chart(topCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_items_data['labels'])},
                datasets: [{{
                    data: {json.dumps(top_items_data['values'])},
                    backgroundColor: '#7c3aed',
                    borderRadius: 4,
                    borderSkipped: false
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{
                            color: '#2d2d4a',
                            drawBorder: false
                        }},
                        ticks: {{
                            color: '#64748b',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 11
                            }}
                        }}
                    }},
                    y: {{
                        grid: {{
                            display: false
                        }},
                        ticks: {{
                            color: '#94a3b8',
                            font: {{
                                family: "'Inter', sans-serif",
                                size: 11
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Table sorting
        let sortDirection = {{}};
        function sortTable(columnIndex) {{
            const table = document.getElementById('cacheTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const direction = sortDirection[columnIndex] ? 1 : -1;

            rows.sort((a, b) => {{
                let aValue = a.cells[columnIndex].textContent;
                let bValue = b.cells[columnIndex].textContent;

                if (columnIndex === 2 || columnIndex === 3 || columnIndex === 4) {{
                    aValue = parseFloat(aValue.replace(/[^0-9.-]/g, '')) || 0;
                    bValue = parseFloat(bValue.replace(/[^0-9.-]/g, '')) || 0;
                    return (aValue - bValue) * direction;
                }}

                return aValue.localeCompare(bValue) * direction;
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}

        // Search filtering
        document.getElementById('searchBox').addEventListener('input', function() {{
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#cacheTable tbody tr');

            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>"""

        return html_content

    def _prepare_category_data(self, result: ScanResult) -> dict:
        """Prepare data for category pie chart."""
        summaries = result.get_category_summaries()
        sorted_summaries = sorted(
            summaries.values(),
            key=lambda x: x.total_size,
            reverse=True
        )

        labels = []
        values = []
        for summary in sorted_summaries[:10]:  # Top 10 categories
            name = summary.category.value.replace("_", " ").title()
            labels.append(name)
            values.append(round(summary.total_size / (1024 * 1024), 2))  # MB

        return {"labels": labels, "values": values}

    def _prepare_top_items_data(self, result: ScanResult) -> dict:
        """Prepare data for top items bar chart."""
        top_items = result.get_top_items(8)

        labels = []
        values = []
        for item in top_items:
            labels.append(item.name[:25])  # Truncate long names
            values.append(round(item.size_bytes / (1024 * 1024), 2))  # MB

        return {"labels": labels, "values": values}

    def _generate_table_rows(self, result: ScanResult) -> str:
        """Generate HTML table rows for all items."""
        rows = []
        for item in sorted(result.items, key=lambda x: x.size_bytes, reverse=True):
            size_class = "size-large" if item.size_bytes > 100 * 1024 * 1024 else (
                "size-medium" if item.size_bytes > 10 * 1024 * 1024 else "size-small"
            )
            risk_class = f"badge-{item.risk_level.value}"

            rows.append(f"""
                <tr>
                    <td>{html.escape(item.name)}</td>
                    <td>{item.category.value.replace('_', ' ').title()}</td>
                    <td class="{size_class}">{item.formatted_size}</td>
                    <td>{item.file_count:,}</td>
                    <td>{item.age_days}d</td>
                    <td><span class="badge {risk_class}">{item.risk_level.value}</span></td>
                </tr>
            """)

        return "\n".join(rows)
