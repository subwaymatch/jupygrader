#!/usr/bin/env python
import click
import os
import glob

from jupygrader import (
    __version__,
)

from jupygrader import grade_single_notebook, grade_notebooks

# Define the main CLI group
@click.group()
@click.version_option(__version__, '--version', '-v', message='jupygrader %(version)s')

def cli():
    """Jupygrader CLI"""
    pass

# Add hello command
@cli.command()
def hello():
    """Print Hello World"""
    click.echo("Hello World")

# Add bye command
@cli.command()
def bye():
    """Print Bye World"""
    click.echo("Bye World")

@cli.command()
@click.argument('notebook_path', nargs=-1, required=True)
@click.option('--verbose', is_flag=True, default=False, help='Enable verbose output.')
@click.option(
    '--export-csv/--no-export-csv',
    default=True,
    help='Export results to CSV (default: enabled).'
)
@click.option(
    '--csv-output-path',
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    default=None,
    help='Directory to write CSV output into (does not need to exist yet).'
)
@click.option('--regrade-existing', is_flag=True, default=False, help='Regrade even if results already exist.')
def grade(notebook_path, verbose, export_csv, csv_output_path, regrade_existing):
    """Grade one or more notebooks or patterns."""

    # Just resolve paths; don't require directory existence
    if csv_output_path is not None and os.path.isfile(csv_output_path):
        click.echo(f"Error: --csv-output-path must be a directory, not a file: {csv_output_path}", err=True)
        raise click.Abort() 

    notebook_paths = []
    for path in notebook_path:
        # If it's a file and ends with .ipynb
        if os.path.isfile(path) and path.endswith('.ipynb'):
            notebook_paths.append(os.path.abspath(path))
        # If it's a directory, convert to glob for all .ipynb recursively
        elif os.path.isdir(path):
            # Non-recursive: only look at top-level .ipynb files
            pattern = os.path.join(os.path.abspath(path), '*.ipynb')
            found = glob.glob(pattern)
            print(f"Found {len(found)} notebooks in directory {path}")
            print(found)
            notebook_paths.extend(found)
        # Otherwise, treat as glob pattern
        else:
            found = glob.glob(path, recursive=True)
            notebook_paths.extend([os.path.abspath(f) for f in found if f.endswith('.ipynb')])

    if not notebook_paths:
        click.echo("No notebooks found to grade.", err=True)
        raise click.Abort()

    # For now, just show what would happen (no grading yet)
    click.echo(f"Notebooks to grade: {notebook_paths}")
    click.echo(f"verbose={verbose}, export_csv={export_csv}, csv_output_path={csv_output_path}, regrade_existing={regrade_existing}")

    grade_notebooks(notebook_paths, verbose=verbose, export_csv=export_csv, csv_output_path=csv_output_path, regrade_existing=regrade_existing)


if __name__ == "__main__":
    cli()
