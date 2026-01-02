# =============================================================================
# DVT Profile Serve - Web UI for Profiling Results
# =============================================================================
# Serves a beautiful web interface to view profiling results stored in
# metadata_store.duckdb, similar to PipeRider's report viewer.
#
# Usage:
#   dvt profile serve              # Start server on http://localhost:8580
#   dvt profile serve --port 9000  # Custom port
#   dvt profile serve --no-browser # Don't auto-open browser
#
# Installation:
#   Copy this file to: core/dbt/task/profile_serve.py
#
# DVT v0.58.0: New web UI for profiling results
# =============================================================================

from __future__ import annotations

import json
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

# Try to import Rich for CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


class ProfileAPIHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the Profile Viewer API and static files."""

    def __init__(self, *args, metadata_store_path: Path = None, **kwargs):
        self.metadata_store_path = metadata_store_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # API endpoints
        if path == "/api/profiles":
            self._serve_profiles_list()
        elif path == "/api/profile":
            query = parse_qs(parsed.query)
            table_name = query.get("table", [None])[0]
            self._serve_profile_detail(table_name)
        elif path == "/api/summary":
            self._serve_summary()
        elif path == "/" or path == "/index.html":
            self._serve_html()
        else:
            # Serve static files
            super().do_GET()

    def _serve_json(self, data: Any, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _serve_html(self):
        """Serve the main HTML page."""
        html = self._generate_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _get_connection(self):
        """Get DuckDB connection to metadata store."""
        try:
            import duckdb
            return duckdb.connect(str(self.metadata_store_path), read_only=True)
        except Exception as e:
            return None

    def _serve_profiles_list(self):
        """Serve list of all profiled tables (from profile_results table)."""
        conn = self._get_connection()
        if not conn:
            self._serve_json({"error": "Could not connect to metadata store"}, 500)
            return

        try:
            # Query profile_results table (populated by dvt profile run)
            result = conn.execute("""
                SELECT
                    source_name,
                    table_name,
                    profile_mode,
                    COUNT(DISTINCT column_name) as column_count,
                    MAX(row_count) as row_count,
                    MAX(profiled_at) as last_profiled,
                    SUM(CASE WHEN alerts IS NOT NULL AND alerts != '[]' THEN 1 ELSE 0 END) as alert_count
                FROM profile_results
                GROUP BY source_name, table_name, profile_mode
                ORDER BY source_name, table_name
            """).fetchall()

            profiles = []
            for row in result:
                profiles.append({
                    "source_name": row[0],
                    "table_name": row[1],
                    "profile_mode": row[2],
                    "column_count": row[3],
                    "row_count": row[4],
                    "last_profiled": row[5],
                    "alert_count": row[6],
                    "type": "source" if not row[0].startswith("model:") else "model",
                })

            self._serve_json({"profiles": profiles})
        except Exception as e:
            self._serve_json({"profiles": [], "error": str(e)})
        finally:
            conn.close()

    def _serve_profile_detail(self, table_name: str):
        """Serve detailed profile for a specific table (from profile_results)."""
        if not table_name:
            self._serve_json({"error": "table parameter required"}, 400)
            return

        conn = self._get_connection()
        if not conn:
            self._serve_json({"error": "Could not connect to metadata store"}, 500)
            return

        try:
            import json as json_lib

            # Query profile_results for PipeRider-style metrics
            result = conn.execute("""
                SELECT
                    column_name,
                    profile_mode,
                    row_count,
                    null_count,
                    null_percent,
                    distinct_count,
                    distinct_percent,
                    min_value,
                    max_value,
                    mean_value,
                    median_value,
                    stddev_value,
                    p25,
                    p50,
                    p75,
                    min_length,
                    max_length,
                    avg_length,
                    histogram,
                    top_values,
                    alerts,
                    profiled_at,
                    duration_ms
                FROM profile_results
                WHERE table_name = ?
                ORDER BY column_name
            """, [table_name]).fetchall()

            columns = []
            row_count = None
            profile_mode = None
            profiled_at = None
            total_alerts = []

            for row in result:
                # Get table-level info from first row
                if row_count is None:
                    row_count = row[2]
                    profile_mode = row[1]
                    profiled_at = row[21]

                # Parse JSON fields
                histogram = None
                top_values = None
                alerts = []
                try:
                    if row[18]:
                        histogram = json_lib.loads(row[18]) if isinstance(row[18], str) else row[18]
                    if row[19]:
                        top_values = json_lib.loads(row[19]) if isinstance(row[19], str) else row[19]
                    if row[20]:
                        alerts = json_lib.loads(row[20]) if isinstance(row[20], str) else row[20]
                        total_alerts.extend(alerts)
                except:
                    pass

                columns.append({
                    "name": row[0],
                    "profile_mode": row[1],
                    "null_count": row[3],
                    "null_percent": row[4],
                    "distinct_count": row[5],
                    "distinct_percent": row[6],
                    "min_value": row[7],
                    "max_value": row[8],
                    "mean_value": row[9],
                    "median_value": row[10],
                    "stddev_value": row[11],
                    "p25": row[12],
                    "p50": row[13],
                    "p75": row[14],
                    "min_length": row[15],
                    "max_length": row[16],
                    "avg_length": row[17],
                    "histogram": histogram,
                    "top_values": top_values,
                    "alerts": alerts,
                    "duration_ms": row[22],
                })

            # Also try to get schema metadata from column_metadata
            schema_info = {}
            try:
                schema_result = conn.execute("""
                    SELECT column_name, adapter_type, spark_type, is_nullable, is_primary_key
                    FROM column_metadata
                    WHERE table_name = ?
                """, [table_name]).fetchall()
                for sr in schema_result:
                    schema_info[sr[0]] = {
                        "adapter_type": sr[1],
                        "spark_type": sr[2],
                        "is_nullable": sr[3],
                        "is_primary_key": sr[4],
                    }
            except:
                pass

            # Merge schema info into columns
            for col in columns:
                if col["name"] in schema_info:
                    col.update(schema_info[col["name"]])

            self._serve_json({
                "table_name": table_name,
                "profile_mode": profile_mode,
                "row_count": row_count,
                "column_count": len(columns),
                "profiled_at": profiled_at,
                "alert_count": len(total_alerts),
                "alerts": total_alerts,
                "columns": columns,
            })
        except Exception as e:
            self._serve_json({"error": str(e)}, 500)
        finally:
            conn.close()

    def _serve_summary(self):
        """Serve summary statistics (from profile_results)."""
        conn = self._get_connection()
        if not conn:
            self._serve_json({"error": "Could not connect to metadata store"}, 500)
            return

        try:
            # Get summary stats from profile_results
            tables = conn.execute("""
                SELECT COUNT(DISTINCT table_name) FROM profile_results
            """).fetchone()[0]

            columns = conn.execute("""
                SELECT COUNT(DISTINCT source_name || '.' || table_name || '.' || column_name)
                FROM profile_results
            """).fetchone()[0]

            sources = conn.execute("""
                SELECT COUNT(DISTINCT source_name) FROM profile_results
            """).fetchone()[0]

            # Count total rows across all tables
            total_rows = conn.execute("""
                SELECT COALESCE(SUM(row_count), 0) FROM (
                    SELECT DISTINCT source_name, table_name, MAX(row_count) as row_count
                    FROM profile_results
                    GROUP BY source_name, table_name
                )
            """).fetchone()[0]

            # Count alerts
            alert_count = 0
            try:
                import json as json_lib
                alerts_result = conn.execute("""
                    SELECT alerts FROM profile_results WHERE alerts IS NOT NULL AND alerts != '[]'
                """).fetchall()
                for row in alerts_result:
                    if row[0]:
                        try:
                            alerts = json_lib.loads(row[0]) if isinstance(row[0], str) else row[0]
                            alert_count += len(alerts) if alerts else 0
                        except:
                            pass
            except:
                pass

            # Get models count (tables with source_name starting with 'model:')
            models = conn.execute("""
                SELECT COUNT(DISTINCT table_name) FROM profile_results
                WHERE source_name LIKE 'model:%'
            """).fetchone()[0]

            self._serve_json({
                "total_tables": tables,
                "total_columns": columns,
                "sources": sources - models if sources > models else sources,
                "models": models,
                "total_rows": total_rows,
                "alert_count": alert_count,
            })
        except Exception as e:
            self._serve_json({"error": str(e)}, 500)
        finally:
            conn.close()

    def _generate_html(self) -> str:
        """Generate the HTML page for the profile viewer."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DVT Profile Viewer</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --bg: #0f172a;
            --bg-card: #1e293b;
            --text: #f1f5f9;
            --text-dim: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            padding: 2rem;
            text-align: center;
        }
        .header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .header p { color: rgba(255,255,255,0.8); }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
        }
        .stat-card h3 { color: var(--text-dim); font-size: 0.875rem; margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 2rem; font-weight: 700; color: var(--primary); }
        .stat-card .value.alert { color: var(--error); }
        .tables-section { margin-top: 2rem; }
        .tables-section h2 { margin-bottom: 1rem; }
        .table-list { display: grid; gap: 1rem; }
        .table-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.2s;
        }
        .table-card:hover { border-color: var(--primary); transform: translateY(-2px); }
        .table-card.selected { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3); }
        .table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .table-name { font-weight: 600; font-size: 1.1rem; }
        .table-badges { display: flex; gap: 0.5rem; }
        .table-type { font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 4px; background: var(--primary); }
        .table-type.source { background: var(--success); }
        .table-type.model { background: var(--warning); }
        .alert-badge { font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 4px; background: var(--error); }
        .table-meta { color: var(--text-dim); font-size: 0.875rem; }
        .table-stats { display: flex; gap: 1rem; margin-top: 0.5rem; color: var(--text-dim); font-size: 0.8rem; }
        .detail-panel {
            position: fixed; top: 0; right: -600px; width: 600px; height: 100vh;
            background: var(--bg-card); border-left: 1px solid var(--border);
            transition: right 0.3s; overflow-y: auto; z-index: 100;
        }
        .detail-panel.open { right: 0; }
        .detail-header { padding: 1.5rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .detail-header h2 { font-size: 1.25rem; }
        .close-btn { background: none; border: none; color: var(--text); font-size: 1.5rem; cursor: pointer; }
        .detail-content { padding: 1.5rem; }
        .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
        .summary-item { background: var(--bg); padding: 1rem; border-radius: 8px; text-align: center; }
        .summary-item .label { color: var(--text-dim); font-size: 0.75rem; margin-bottom: 0.25rem; }
        .summary-item .value { font-size: 1.25rem; font-weight: 600; }
        .alerts-section { background: rgba(239, 68, 68, 0.1); border: 1px solid var(--error); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
        .alerts-section h3 { color: var(--error); font-size: 0.9rem; margin-bottom: 0.5rem; }
        .alert-item { padding: 0.5rem; background: var(--bg); border-radius: 4px; margin-top: 0.5rem; font-size: 0.85rem; }
        .column-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .column-table th, .column-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
        .column-table th { color: var(--text-dim); font-weight: 500; font-size: 0.7rem; text-transform: uppercase; position: sticky; top: 0; background: var(--bg-card); }
        .type-badge { font-family: monospace; font-size: 0.75rem; background: rgba(99, 102, 241, 0.2); padding: 0.2rem 0.4rem; border-radius: 4px; }
        .metric { font-family: monospace; font-size: 0.8rem; }
        .metric.warning { color: var(--warning); }
        .metric.error { color: var(--error); }
        .progress-bar { width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
        .progress-bar .fill { height: 100%; background: var(--primary); }
        .progress-bar .fill.warning { background: var(--warning); }
        .progress-bar .fill.error { background: var(--error); }
        .loading { text-align: center; padding: 3rem; color: var(--text-dim); }
        .error { background: rgba(239, 68, 68, 0.2); border: 1px solid var(--error); padding: 1rem; border-radius: 8px; margin: 1rem 0; }
        @media (max-width: 768px) { .detail-panel { width: 100%; right: -100%; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>DVT Profile Viewer</h1>
        <p>PipeRider-style data profiling results</p>
    </div>

    <div class="container">
        <div class="stats-grid" id="stats">
            <div class="stat-card"><h3>Tables</h3><div class="value" id="stat-tables">-</div></div>
            <div class="stat-card"><h3>Columns</h3><div class="value" id="stat-columns">-</div></div>
            <div class="stat-card"><h3>Total Rows</h3><div class="value" id="stat-rows">-</div></div>
            <div class="stat-card"><h3>Sources</h3><div class="value" id="stat-sources">-</div></div>
            <div class="stat-card"><h3>Models</h3><div class="value" id="stat-models">-</div></div>
            <div class="stat-card"><h3>Alerts</h3><div class="value alert" id="stat-alerts">-</div></div>
        </div>

        <div class="tables-section">
            <h2>Profiled Tables</h2>
            <div class="table-list" id="table-list"><div class="loading">Loading profiles...</div></div>
        </div>
    </div>

    <div class="detail-panel" id="detail-panel">
        <div class="detail-header">
            <h2 id="detail-title">Table Details</h2>
            <button class="close-btn" onclick="closeDetail()">&times;</button>
        </div>
        <div class="detail-content" id="detail-content">
            <div class="loading">Select a table to view details</div>
        </div>
    </div>

    <script>
        function formatNumber(n) { return n != null ? n.toLocaleString() : '-'; }
        function formatPercent(n) { return n != null ? n.toFixed(1) + '%' : '-'; }

        async function loadSummary() {
            try {
                const resp = await fetch('/api/summary');
                const data = await resp.json();
                document.getElementById('stat-tables').textContent = formatNumber(data.total_tables);
                document.getElementById('stat-columns').textContent = formatNumber(data.total_columns);
                document.getElementById('stat-rows').textContent = formatNumber(data.total_rows);
                document.getElementById('stat-sources').textContent = formatNumber(data.sources);
                document.getElementById('stat-models').textContent = formatNumber(data.models);
                document.getElementById('stat-alerts').textContent = formatNumber(data.alert_count);
            } catch (e) { console.error('Failed to load summary:', e); }
        }

        async function loadProfiles() {
            const container = document.getElementById('table-list');
            try {
                const resp = await fetch('/api/profiles');
                const data = await resp.json();
                if (data.profiles.length === 0) {
                    container.innerHTML = '<div class="loading">No profiles found. Run "dvt profile run" first.</div>';
                    return;
                }
                container.innerHTML = data.profiles.map(p => `
                    <div class="table-card" onclick="showDetail('${p.table_name}')">
                        <div class="table-header">
                            <span class="table-name">${p.source_name ? p.source_name + '.' : ''}${p.table_name}</span>
                            <div class="table-badges">
                                ${p.alert_count > 0 ? `<span class="alert-badge">${p.alert_count} alerts</span>` : ''}
                                <span class="table-type ${p.type}">${p.type}</span>
                            </div>
                        </div>
                        <div class="table-stats">
                            <span>${formatNumber(p.row_count)} rows</span>
                            <span>${p.column_count} columns</span>
                            <span>Mode: ${p.profile_mode || 'minimal'}</span>
                        </div>
                        <div class="table-meta">Profiled: ${p.last_profiled ? new Date(p.last_profiled).toLocaleString() : '-'}</div>
                    </div>
                `).join('');
            } catch (e) { container.innerHTML = `<div class="error">Failed to load profiles: ${e.message}</div>`; }
        }

        async function showDetail(tableName) {
            const panel = document.getElementById('detail-panel');
            const title = document.getElementById('detail-title');
            const content = document.getElementById('detail-content');
            panel.classList.add('open');
            title.textContent = tableName;
            content.innerHTML = '<div class="loading">Loading...</div>';
            document.querySelectorAll('.table-card').forEach(c => c.classList.remove('selected'));
            if (event && event.currentTarget) event.currentTarget.classList.add('selected');

            try {
                const resp = await fetch(`/api/profile?table=${encodeURIComponent(tableName)}`);
                const data = await resp.json();
                if (data.error) { content.innerHTML = `<div class="error">${data.error}</div>`; return; }

                let html = `
                    <div class="summary-grid">
                        <div class="summary-item"><div class="label">Rows</div><div class="value">${formatNumber(data.row_count)}</div></div>
                        <div class="summary-item"><div class="label">Columns</div><div class="value">${data.column_count}</div></div>
                        <div class="summary-item"><div class="label">Alerts</div><div class="value" style="color:var(--error)">${data.alert_count}</div></div>
                    </div>`;

                if (data.alerts && data.alerts.length > 0) {
                    html += `<div class="alerts-section"><h3>Quality Alerts</h3>`;
                    data.alerts.forEach(a => {
                        html += `<div class="alert-item"><strong>${a.column_name || '-'}:</strong> ${a.message || a.type}</div>`;
                    });
                    html += `</div>`;
                }

                html += `<table class="column-table"><thead><tr>
                    <th>Column</th><th>Nulls</th><th>Distinct</th><th>Min</th><th>Max</th><th>Type</th>
                </tr></thead><tbody>`;

                data.columns.forEach(c => {
                    const nullClass = c.null_percent > 50 ? 'error' : c.null_percent > 10 ? 'warning' : '';
                    html += `<tr>
                        <td><strong>${c.name}</strong></td>
                        <td>
                            <div class="metric ${nullClass}">${formatPercent(c.null_percent)}</div>
                            <div class="progress-bar"><div class="fill ${nullClass}" style="width:${c.null_percent || 0}%"></div></div>
                        </td>
                        <td><span class="metric">${formatNumber(c.distinct_count)}</span></td>
                        <td><span class="metric">${c.min_value != null ? c.min_value : '-'}</span></td>
                        <td><span class="metric">${c.max_value != null ? c.max_value : '-'}</span></td>
                        <td><span class="type-badge">${c.adapter_type || '-'}</span></td>
                    </tr>`;
                });
                html += `</tbody></table>`;
                content.innerHTML = html;
            } catch (e) { content.innerHTML = `<div class="error">Failed to load details: ${e.message}</div>`; }
        }

        function closeDetail() {
            document.getElementById('detail-panel').classList.remove('open');
            document.querySelectorAll('.table-card').forEach(c => c.classList.remove('selected'));
        }

        loadSummary();
        loadProfiles();
    </script>
</body>
</html>'''

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def serve_profile_ui(
    project_dir: Path,
    port: int = 8580,
    host: str = "localhost",
    open_browser: bool = True,
):
    """
    Start the profile viewer web server.

    Args:
        project_dir: Path to the DVT project
        port: Port to serve on (default: 8580)
        host: Host to bind to (default: localhost)
        open_browser: Whether to open browser automatically
    """
    # Find metadata store
    metadata_store_path = project_dir / ".dvt" / "metadata_store.duckdb"

    if not metadata_store_path.exists():
        if HAS_RICH:
            console.print(Panel(
                "[yellow]No metadata store found.[/yellow]\n\n"
                "Run [bold cyan]dvt profile[/bold cyan] first to capture profiling data.",
                title="[bold red]Error[/bold red]",
                border_style="red",
            ))
        else:
            print("Error: No metadata store found.")
            print("Run 'dvt profile' first to capture profiling data.")
        return False

    # Create handler with metadata store path
    def handler(*args, **kwargs):
        return ProfileAPIHandler(*args, metadata_store_path=metadata_store_path, **kwargs)

    # Start server
    server = HTTPServer((host, port), handler)
    url = f"http://{host}:{port}"

    if HAS_RICH:
        console.print()
        console.print(Panel(
            f"[bold green]Profile Viewer running at:[/bold green]\n\n"
            f"  [bold cyan]{url}[/bold cyan]\n\n"
            f"[dim]Press Ctrl+C to stop[/dim]",
            title="[bold magenta]🔍 DVT Profile Viewer[/bold magenta]",
            border_style="magenta",
            box=box.DOUBLE,
        ))
        console.print()
    else:
        print(f"\nDVT Profile Viewer running at: {url}")
        print("Press Ctrl+C to stop\n")

    # Open browser
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[yellow]Server stopped.[/yellow]")
        else:
            print("\nServer stopped.")

    return True


if __name__ == "__main__":
    # For testing
    import sys
    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    serve_profile_ui(project_dir)
