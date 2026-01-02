"""
Fast version command for CLI - doesn't load FAISS
"""

import click
import sys
import os
import argparse
from typing import Optional

# Try to get version without importing arf
try:
    # Direct file read to avoid imports
    version_file = os.path.join(os.path.dirname(__file__), '__version__.py')
    with open(version_file, 'r') as f:
        for line in f:
            if '__version__' in line:
                version_str = line.split('=')[1].strip().strip("'\"")
                break
    VERSION = version_str
except Exception:
    VERSION = "unknown"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Agentic Reliability Framework CLI"
    )
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--doctor', action='store_true', help='Check installation')
    parser.add_argument('--serve', action='store_true', help='Start server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=7860, help='Port to bind to')
    parser.add_argument('--share', action='store_true', help='Create public share link')
    return parser.parse_args()


def show_help() -> None:
    """Show help information"""
    print("Agentic Reliability Framework CLI Help")
    print("Usage: arf [command] [options]")
    print("\nCommands:")
    print("  version      Show ARF version (fast - no FAISS load)")
    print("  doctor       Check ARF installation and dependencies")
    print("  serve        Start the ARF Gradio UI server")
    print("\nOptions:")
    print("  --host       Host to bind to (default: 0.0.0.0)")
    print("  --port       Port to bind to (default: 7860)")
    print("  --share      Create public Gradio share link")
    print("  --help       Show this help message")


def show_version() -> None:
    """Show version information"""
    print(f"Agentic Reliability Framework v{VERSION}")


@click.group()
@click.version_option(version=VERSION)
def main() -> None:
    """Agentic Reliability Framework - Multi-Agent AI for Production Reliability"""
    pass


@main.command()
def version() -> None:
    """Show ARF version (FAST - no FAISS load)"""
    click.echo(f"Agentic Reliability Framework v{VERSION}")


@main.command()
def doctor() -> None:
    """Check ARF installation and dependencies"""
    click.echo("Checking ARF installation...")
    
    # Check FAISS (but only when needed)
    try:
        import importlib.util
        faiss_spec = importlib.util.find_spec("faiss")
        if faiss_spec is not None:
            click.echo("✓ FAISS installed")
        else:
            click.echo("✗ FAISS not installed", err=True)
            sys.exit(1)
    except Exception:
        click.echo("✗ FAISS not installed", err=True)
        sys.exit(1)
    
    # Check other deps
    deps = [
        ("SentenceTransformers", "sentence_transformers"),
        ("Gradio", "gradio"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("Pydantic", "pydantic"),
        ("Requests", "requests"),
        ("CircuitBreaker", "circuitbreaker"),
        ("atomicwrites", "atomicwrites"),
        ("python-dotenv", "dotenv"),
        ("Click", "click"),
    ]
    
    all_ok = True
    for name, module in deps:
        try:
            __import__(module)
            click.echo(f"  ✓ {name}")
        except ImportError:
            click.echo(f"  ✗ {name}")
            all_ok = False
    
    if all_ok:
        click.echo("\n✅ All dependencies OK!")
    else:
        click.echo("\n❌ Some dependencies missing")
        sys.exit(1)


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=7860, type=int, help='Port to bind to')
@click.option('--share/--no-share', default=False, help='Create public Gradio share link')
def serve(host: str, port: int, share: bool) -> None:
    """Start the ARF Gradio UI server (loads FAISS)"""
    click.echo(f"🚀 Starting ARF v{VERSION} on {host}:{port}...")
    
    # NOW import agentic_reliability_framework as arf and load FAISS
    import agentic_reliability_framework as arf
    demo = arf.create_enhanced_ui()
    demo.launch(server_name=host, server_port=port, share=share)


def cli_main() -> None:
    """Main CLI entry point (compatibility with argparse version)"""
    args = parse_args()
    
    if args.version:
        show_version()
    elif args.doctor:
        # Use click version for consistency
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(doctor)
        print(result.output)
    elif args.serve:
        # Use click version for consistency
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(serve, ['--host', args.host, '--port', str(args.port)])
        if args.share:
            result = runner.invoke(serve, ['--host', args.host, '--port', str(args.port), '--share'])
        print(result.output)
    else:
        show_help()


if __name__ == "__main__":
    main()
