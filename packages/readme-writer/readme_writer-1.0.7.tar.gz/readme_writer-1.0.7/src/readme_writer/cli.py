"""Command-line interface for readme-writer."""

import os
import sys
from pathlib import Path
from typing import Optional, Set
import click
from rich.console import Console

from .core import DocumentationGenerator
from .config import Config

console = Console()


def validate_api_key(ctx, param, value):
    """Validate OpenAI API key."""
    if not value and not os.getenv("OPENAI_API_KEY"):
        raise click.BadParameter("OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --api-key option.")
    return value


def validate_repository_path(ctx, param, value):
    """Validate repository path."""
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"Repository path does not exist: {value}")
    if not path.is_dir():
        raise click.BadParameter(f"Repository path must be a directory: {value}")
    return path


def parse_skip_files(ctx, param, value):
    """Parse skip files option into a set of patterns."""
    if not value:
        return set()
    return {pattern.strip() for pattern in value.split(',') if pattern.strip()}


@click.command()
@click.argument("repository_path", callback=validate_repository_path)
@click.option("--model", "-m", default=os.getenv("OPENAI_MODEL", "gpt-4o"), 
              help="OpenAI model to use. Supported: gpt-5.2, gpt-5.1, gpt-5, gpt-5-mini, gpt-4.1, gpt-4o, gpt-4o-mini, o3, o4-mini (default: gpt-4o)")
@click.option("--output", "-o", default=os.getenv("OUTPUT_FILE", "README.md"), help="Output file name (default: README.md)")
@click.option("--api-key", callback=validate_api_key, help="OpenAI API key (or set OPENAI_API_KEY env var)")
@click.option("--temperature", "-t", default=float(os.getenv("OPENAI_TEMPERATURE", "0.3")), type=float, help="OpenAI temperature (default: 0.3)")
@click.option("--skip-files", callback=parse_skip_files, help="Additional file patterns to skip (comma-separated)")
@click.option("--max-tokens", default=int(os.getenv("OPENAI_MAX_TOKENS_PER_CHUNK", "6000")), type=int, help="Maximum tokens per chunk (default: 6000)")
@click.option("--no-diff", is_flag=True, help="Disable diff analysis for detecting changes")

@click.version_option(version=os.getenv("VERSION", "1.0.0"))
def main(repository_path: Path, model: str, output: str, api_key: Optional[str], 
         temperature: float, skip_files: Set[str], max_tokens: int, no_diff: bool):
    """Generate comprehensive README files using OpenAI API."""
    
    try:
        # Create configuration
        config = Config(
            model=model,
            output_file=output,
            temperature=temperature,
            max_tokens_per_chunk=max_tokens
        )
        
        # Create generator
        generator = DocumentationGenerator(config, api_key)
        
        # Disable diff analysis if requested
        if no_diff:
            generator.diff_analyzer = None
        
        # Generate documentation
        output_path = repository_path / output
        documentation = generator.generate_documentation(
            repository_path=repository_path,
            output_path=output_path,
            additional_skip_patterns=skip_files
        )
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 