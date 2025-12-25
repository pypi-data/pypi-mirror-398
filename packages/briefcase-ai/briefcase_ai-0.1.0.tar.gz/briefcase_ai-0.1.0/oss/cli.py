#!/usr/bin/env python3
"""
briefcase-ai CLI - Main command-line interface
"""

import click
import sys
from pathlib import Path

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """briefcase-ai - Deterministic observability & replay for AI systems"""
    pass

@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host, port, reload):
    """Start the API server"""
    import uvicorn
    from briefcase.api.app import app

    click.echo(f"Starting briefcase-ai API server on {host}:{port}")
    uvicorn.run(
        "briefcase.api.app:app",
        host=host,
        port=port,
        reload=reload
    )

@cli.command()
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
def ui(api_url):
    """Start the Next.js UI in dev mode"""
    import subprocess
    import os

    ui_path = Path(__file__).parent / "ui"

    if not ui_path.exists():
        click.echo("UI directory not found. Please ensure oss/ui exists.")
        sys.exit(1)

    # Set API URL environment variable
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_URL"] = api_url

    click.echo(f"Starting briefcase-ai UI (API: {api_url})")

    # Install dependencies if needed
    node_modules = ui_path / "node_modules"
    if not node_modules.exists():
        click.echo("Installing UI dependencies...")
        subprocess.run(["npm", "install"], cwd=ui_path, check=True)

    # Start the UI
    subprocess.run(["npm", "run", "dev"], cwd=ui_path, env=env, check=True)

@cli.command()
def test():
    """Run the end-to-end test suite"""
    import subprocess

    click.echo("Running briefcase-ai test suite...")
    result = subprocess.run([sys.executable, "test_end_to_end.py"])
    sys.exit(result.returncode)

@cli.command()
def init_db():
    """Initialize the local SQLite database"""
    import os
    from oss.storage.database import init_database, configure_database, DatabaseConfig

    # Reset the database configuration if DATABASE_URL is set
    if "DATABASE_URL" in os.environ:
        config = DatabaseConfig(url=os.environ["DATABASE_URL"])
        configure_database(config)

    click.echo("Initializing briefcase-ai database...")
    init_database()
    click.echo("Database initialized successfully!")

@cli.command()
@click.option("--check", is_flag=True, help="Check formatting without changes")
def format(check):
    """Format the codebase with black"""
    import subprocess

    cmd = ["black", ".", "--exclude", "node_modules"]
    if check:
        cmd.append("--check")

    click.echo("Formatting Python code...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

@cli.command()
def lint():
    """Run linting with ruff"""
    import subprocess

    click.echo("Linting Python code...")
    result = subprocess.run(["ruff", "check", "."])
    sys.exit(result.returncode)

def main():
    """Main entry point"""
    cli()

if __name__ == "__main__":
    main()
