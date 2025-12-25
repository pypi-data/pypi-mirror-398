from typing import Optional
import click
import pandas as pd
import logging
from .load import load as core_load
from .search import search as core_search
from .errors import KaggleEaseError

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """A minimal CLI mirror for KaggleEase."""
    pass

@cli.command()
@click.argument('dataset')
@click.option('--file', default=None, help='The specific file to load.')
@click.option('--timeout', default=300, help='Timeout in seconds for the operation.')
def load(dataset: str, file: Optional[str], timeout: int) -> None:
    """Loads a dataset and prints its head."""
    try:
        df = core_load(dataset, file=file, timeout=timeout)
        logger.info(f"Successfully loaded {dataset}.")
        print(df.head())
    except KaggleEaseError as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('dataset')
@click.option('--file', default=None, help='The specific file to preview.')
@click.option('--timeout', default=300, help='Timeout in seconds for the operation.')
@click.pass_context
def preview(ctx, dataset: str, file: Optional[str], timeout: int) -> None:
    """Previews a dataset by loading it and printing its head."""
    logger.info(f"Preview of {dataset}:")
    ctx.invoke(load, dataset=dataset, file=file, timeout=timeout)

@cli.command()
@click.argument('query')
@click.option('--timeout', default=30, help='Timeout in seconds for the search operation.')
@click.option('--top', default=5, help='Maximum number of results to return.')
def search(query: str, timeout: int, top: int) -> None:
    """Searches for datasets and prints the results."""
    results = core_search(query, top=top, timeout=timeout)
    if results:
        # Use pandas to create a nicely formatted table
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
    else:
        click.echo("No results found.")

if __name__ == '__main__':
    cli()
