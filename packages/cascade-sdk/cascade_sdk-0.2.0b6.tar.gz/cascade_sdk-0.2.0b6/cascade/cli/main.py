"""
Main CLI entry point for Cascade SDK
"""
import click


@click.group()
@click.version_option(version="0.2.0b6", prog_name="cascade")
def cli():
    """
    Cascade SDK - Agent Observability Platform
    
    Cloud-based observability for AI agent execution.
    
    Quick Start:
      1. Set CASCADE_API_KEY environment variable
      2. Use init_tracing() in your code to start tracing
      3. View traces at https://cascade-dashboard.vercel.app
    """
    pass


@cli.command()
def info():
    """Show Cascade SDK information and setup instructions."""
    click.echo("Cascade SDK - Agent Observability Platform")
    click.echo("=" * 50)
    click.echo("\n📦 Installation:")
    click.echo("   pip install cascade-sdk")
    click.echo("\n🔧 Setup:")
    click.echo("   1. Set your API key:")
    click.echo("      export CASCADE_API_KEY='your-api-key'")
    click.echo("\n   2. Use in your code:")
    click.echo("      from cascade import init_tracing, trace_run")
    click.echo("      init_tracing(project='my_project')")
    click.echo("\n📊 View Traces:")
    click.echo("   https://cascade-dashboard.vercel.app")
    click.echo("\n📚 Documentation:")
    click.echo("   https://github.com/yourusername/cascade_sdk")


if __name__ == "__main__":
    cli()

