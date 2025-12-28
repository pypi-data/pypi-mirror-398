"""CLI entry point for Rainfall."""

import click
import sys
from pathlib import Path

from rainfall.config import RainfallConfig
from rainfall.core import execute_with_rainfall


@click.command()
@click.argument("script", type=click.Path(exists=True, path_type=Path))
@click.option("--api-key", envvar="GEMINI_API_KEY", help="Gemini API key")
@click.option("--model", default="gemini-3-flash-preview", help="Model to use")
@click.option("--verbose", "-v", is_flag=True, help="Show LLM prompts and responses")
@click.option("--dry-run", is_flag=True, help="Show stub functions without executing")
@click.option("--temperature", default=0.2, type=float, help="LLM temperature (0-1)")
def main(
    script: Path,
    api_key: str | None,
    model: str,
    verbose: bool,
    dry_run: bool,
    temperature: float,
):
    """
    Run a Python script with AI-powered stub functions.
    
    Functions with `...` or `pass` as their body will be executed by an LLM
    based on their name, signature, and docstring.
    
    Example:
    
        rainfall my_script.py --api-key=YOUR_KEY
    """
    config = RainfallConfig(
        api_key=api_key,
        model=model,
        verbose=verbose,
        dry_run=dry_run,
        temperature=temperature,
    )
    
    try:
        config.validate()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    
    try:
        execute_with_rainfall(script, config)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
