"""
briefcase-ai CLI module
"""

import click
import uvicorn
import os
import sys
from pathlib import Path

@click.group()
@click.version_option(version="0.1.0")
def main():
    """briefcase-ai - Deterministic observability & replay for AI systems"""
    pass

@main.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--dev', is_flag=True, help='Enable development mode with auto-reload')
def serve(host, port, dev):
    """Start the API server"""
    click.echo(f"Starting briefcase-ai API server on {host}:{port}")

    if dev:
        click.echo("Development mode enabled (auto-reload)")
        os.environ["BRIEFCASE_DEV"] = "true"

    # Import here to avoid circular imports
    from ..api.app import app

    uvicorn.run(
        "briefcase.api.app:app",
        host=host,
        port=port,
        reload=dev,
        log_level="info"
    )

@main.command()
@click.option('--host', default='127.0.0.1', help='API host')
@click.option('--port', default=8000, help='API port')
def ui(host, port):
    """Start the Next.js UI"""
    ui_path = Path(__file__).parent.parent / "ui"

    if not ui_path.exists():
        click.echo("UI directory not found. Please ensure the UI is built.", err=True)
        sys.exit(1)

    os.environ["BRIEFCASE_API_URL"] = f"http://{host}:{port}"

    click.echo(f"Starting briefcase-ai UI (connecting to API at {host}:{port})")
    click.echo(f"UI will be available at http://localhost:3000")

    # Change to UI directory and run npm dev
    os.chdir(ui_path)
    os.system("npm run dev")

@main.command()
def version():
    """Show version information"""
    click.echo("briefcase-ai v0.1.0")
    click.echo("Deterministic observability & replay for AI systems")

@main.command()
def status():
    """Check system status"""
    click.echo("briefcase-ai Status:")
    click.echo("- API: Not implemented yet")
    click.echo("- UI: Not implemented yet")
    click.echo("- Storage: Not implemented yet")
    click.echo("For full status, start the server and visit /health")

if __name__ == "__main__":
    main()
