"""
DVT Docs Serve Task

v0.56.0: Enhanced with FastAPI backend and 3-tab web UI.

Serves documentation with:
- Traditional static HTML docs (backward compatible)
- REST API for catalog, profiling, lineage, and Spark status
- 3-tab web UI: Catalog, Profiling, Spark Monitor
"""

import os
import shutil
import webbrowser
from pathlib import Path
from typing import Optional

import click

from dbt.task.base import ConfiguredTask
from dbt.task.docs import DOCS_INDEX_FILE_PATH


class ServeTask(ConfiguredTask):
    """
    Serve documentation with optional enhanced API.

    When FastAPI is available, serves:
    - /api/catalog/* - Catalog nodes and search
    - /api/profile/* - Profile results and alerts
    - /api/lineage/* - Lineage graph and traversal
    - /api/spark/* - Spark status (local only)
    - /* - Static documentation files

    Falls back to simple HTTP server when FastAPI is not installed.
    """

    def run(self):
        port = self.args.port
        host = self.args.host
        project_root = Path(self.config.project_root)
        target_path = Path(self.config.project_target_path)

        # Check if FastAPI is available for enhanced serving
        if self._fastapi_available():
            self._run_fastapi_server(host, port, project_root, target_path)
        else:
            self._run_simple_server(host, port, target_path)

    def _fastapi_available(self) -> bool:
        """Check if FastAPI and uvicorn are installed."""
        try:
            import fastapi  # noqa: F401
            import uvicorn  # noqa: F401
            return True
        except ImportError:
            return False

    def _run_fastapi_server(
        self,
        host: str,
        port: int,
        project_root: Path,
        target_path: Path,
    ):
        """Run enhanced FastAPI server with REST API."""
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import RedirectResponse
        import uvicorn

        # Import API routers
        from dbt.task.docs.api import (
            catalog_router,
            profile_router,
            lineage_router,
            spark_router,
        )
        from dbt.task.docs.api import catalog, profile, lineage, spark

        # Initialize metadata store ONCE at startup
        try:
            from dbt.compute.metadata import ProjectMetadataStore
            store = ProjectMetadataStore(project_root)
            store.initialize()  # Only called once here
            click.echo(f"  Metadata store initialized: {project_root}/.dvt/metadata_store.duckdb")
        except Exception as e:
            click.echo(f"  Warning: Could not initialize metadata store: {e}")

        # Set project root for all API modules (store will skip re-initialization)
        catalog.set_project_root(project_root)
        profile.set_project_root(project_root)
        lineage.set_project_root(project_root)
        spark.set_project_root(project_root)

        # Create FastAPI app
        app = FastAPI(
            title="DVT Documentation",
            description="DVT catalog, profiling, and lineage API",
            version="0.56.0",
        )

        # Include API routers
        app.include_router(catalog_router)
        app.include_router(profile_router)
        app.include_router(lineage_router)
        app.include_router(spark_router)

        # Prepare static files directory
        os.chdir(target_path)
        shutil.copyfile(DOCS_INDEX_FILE_PATH, "index.html")

        # Root redirect to index.html
        @app.get("/")
        async def root():
            return RedirectResponse(url="/index.html")

        # Mount static files (must be last to not override API routes)
        app.mount("/", StaticFiles(directory=str(target_path), html=True), name="static")

        # Open browser if requested
        if self.args.browser:
            webbrowser.open_new_tab(f"http://localhost:{port}")

        # Print server info
        click.echo("")
        click.echo("╔════════════════════════════════════════════════════════════════╗")
        click.echo("║              DVT Documentation Server (Enhanced)               ║")
        click.echo("╠════════════════════════════════════════════════════════════════╣")
        click.echo(f"║  Serving at: http://{host}:{port}".ljust(66) + "║")
        click.echo("║                                                                ║")
        click.echo("║  Web UI:                                                       ║")
        click.echo(f"║    • Documentation: http://localhost:{port}/".ljust(66) + "║")
        click.echo(f"║    • API Docs: http://localhost:{port}/docs".ljust(66) + "║")
        click.echo("║                                                                ║")
        click.echo("║  API Endpoints:                                                ║")
        click.echo("║    • /api/catalog/*  - Catalog nodes and search               ║")
        click.echo("║    • /api/profile/*  - Profile results and alerts             ║")
        click.echo("║    • /api/lineage/*  - Lineage graph and traversal            ║")
        click.echo("║    • /api/spark/*    - Spark status (local only)              ║")
        click.echo("╠════════════════════════════════════════════════════════════════╣")
        click.echo("║  Press Ctrl+C to stop                                          ║")
        click.echo("╚════════════════════════════════════════════════════════════════╝")
        click.echo("")

        # Run server
        uvicorn.run(app, host=host, port=port, log_level="warning")

    def _run_simple_server(self, host: str, port: int, target_path: Path):
        """Run simple HTTP server (fallback when FastAPI not installed)."""
        import socketserver
        from http.server import SimpleHTTPRequestHandler

        os.chdir(target_path)
        shutil.copyfile(DOCS_INDEX_FILE_PATH, "index.html")

        if self.args.browser:
            webbrowser.open_new_tab(f"http://localhost:{port}")

        click.echo("")
        click.echo("╔════════════════════════════════════════════════════════════════╗")
        click.echo("║              DVT Documentation Server (Basic)                  ║")
        click.echo("╠════════════════════════════════════════════════════════════════╣")
        click.echo(f"║  Serving at: http://{host}:{port}".ljust(66) + "║")
        click.echo("║                                                                ║")
        click.echo("║  Note: Install fastapi and uvicorn for enhanced features:     ║")
        click.echo("║    pip install fastapi uvicorn                                 ║")
        click.echo("╠════════════════════════════════════════════════════════════════╣")
        click.echo("║  Press Ctrl+C to stop                                          ║")
        click.echo("╚════════════════════════════════════════════════════════════════╝")
        click.echo("")

        with socketserver.TCPServer((host, port), SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()
