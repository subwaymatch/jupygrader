#!/usr/bin/env python
import click
import os
import glob
from pathlib import Path
from typing import List, Union, Optional
import sys
import time
from datetime import datetime

from jupygrader import (
    grade_single_notebook,
    grade_notebooks,
    GradingItemConfig,
    __version__,
)


def print_version(ctx, param, value):
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"jupygrader version {__version__}")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version and exit.",
)
def cli():
    """
    jupygrader CLI tool for grading Jupyter notebooks.
    """
    pass


@cli.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(file_okay=False),
    help="Directory where graded results will be saved.",
)
@click.option(
    "-c",
    "--copy",
    "copy_files",
    multiple=True,
    help="Files to copy into the grading environment. Can be specified multiple times.",
)
@click.option(
    "--quiet", is_flag=True, help="Suppress progress and diagnostic information."
)
def grade(notebook_path, output_path, copy_files, quiet):
    """
    Grade a single Jupyter notebook.

    NOTEBOOK_PATH is the path to the Jupyter notebook to grade.
    """
    click.echo(f"Grading notebook: {notebook_path}")

    # If output path wasn't provided, use current directory
    if not output_path:
        output_path = os.getcwd()

    # Create the output directory if it doesn't exist
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Create GradingItemConfig object
    item_config = GradingItemConfig(
        notebook_path=notebook_path,
        output_path=output_path,
        copy_files=list(copy_files) if copy_files else None,
    )

    try:
        start_time = time.time()
        result = grade_notebook(
            notebook_path=item_config.notebook_path,
            output_path=item_config.output_path,
            copy_files=item_config.copy_files,
            verbose=not quiet,
        )
        elapsed = time.time() - start_time

        if not quiet:
            click.echo("=" * 60)
            click.echo(f"Grading complete in {elapsed:.2f} seconds")
            click.echo(
                f"Score: {result.learner_autograded_score}/{result.max_total_score}"
            )
            click.echo(
                f"Passed: {result.num_passed_cases}/{result.num_total_test_cases} tests"
            )
            click.echo(f"Results saved to: {output_path}")

            # Print paths to output files if they exist
            if result.graded_html_file:
                click.echo(f"HTML report: {result.graded_html_file}")
            if result.text_summary_file:
                click.echo(f"Text summary: {result.text_summary_file}")

        return result

    except Exception as e:
        click.echo(f"Error grading notebook: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("notebook_paths", type=click.Path(exists=True), nargs=-1)
@click.option(
    "-g",
    "--glob",
    "glob_pattern",
    help="Glob pattern to match notebook files, e.g. '*.ipynb' or 'submissions/*.ipynb'",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(file_okay=False),
    help="Directory where graded results will be saved.",
)
@click.option(
    "-c",
    "--copy",
    "copy_files",
    multiple=True,
    help="Files to copy into the grading environment. Can be specified multiple times.",
)
@click.option(
    "--export-csv",
    is_flag=True,
    default=True,
    help="Export results to CSV file (enabled by default).",
)
@click.option(
    "--no-export-csv",
    is_flag=True,
    default=False,
    help="Disable CSV export.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress progress and diagnostic information.",
)
def batch(
    notebook_paths,
    glob_pattern,
    output_path,
    copy_files,
    export_csv,
    no_export_csv,
    quiet,
):
    """
    Grade multiple Jupyter notebooks in batch.

    NOTEBOOK_PATHS are one or more paths to Jupyter notebooks to grade.
    If no paths are provided, you must specify a glob pattern with --glob.
    """
    # Resolve paths from arguments or glob pattern
    paths: List[Path] = []

    # Convert tuple of copy_files to a list if provided
    copy_files_list = list(copy_files) if copy_files else None

    if notebook_paths:
        paths = [Path(p) for p in notebook_paths]

    elif glob_pattern:
        paths = [Path(p) for p in glob.glob(glob_pattern, recursive=True)]

    else:
        click.echo("Error: No notebook paths or glob pattern provided.", err=True)
        sys.exit(1)

    if not paths:
        click.echo("No notebooks found matching the criteria.", err=True)
        sys.exit(1)

    # If output path wasn't provided, use current directory
    if not output_path:
        output_path = os.getcwd()

    # Create the output directory if it doesn't exist
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Override export_csv if no_export_csv is set
    if no_export_csv:
        export_csv = False

    # Create GradingItemConfig objects for each notebook
    grading_items = [
        GradingItemConfig(
            notebook_path=path, output_path=output_path, copy_files=copy_files_list
        )
        for path in paths
    ]

    try:
        if not quiet:
            click.echo(f"Starting batch grading of {len(paths)} notebooks...")

        start_time = time.time()

        results = grade_notebooks(
            grading_items=grading_items,
            verbose=not quiet,
            export_csv=export_csv,
            csv_output_path=output_path,
        )

        elapsed = time.time() - start_time

        if not quiet:
            click.echo("=" * 60)
            click.echo(f"Batch grading complete in {elapsed:.2f} seconds")

            # Calculate summary statistics
            total_points = sum(r.learner_autograded_score for r in results)
            total_max = sum(r.max_total_score for r in results)
            total_passed = sum(r.num_passed_cases for r in results)
            total_tests = sum(r.num_total_test_cases for r in results)

            click.echo(f"Total score: {total_points}/{total_max}")
            click.echo(f"Total passed: {total_passed}/{total_tests} tests")
            click.echo(f"Results saved to: {output_path}")

        return results

    except Exception as e:
        click.echo(f"Error in batch grading: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("notebook_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=True),
    help="Directory where extracted code will be saved.",
)
def extract(notebook_path, output_path):
    """
    Extract student code from a Jupyter notebook.

    NOTEBOOK_PATH is the path to the Jupyter notebook to extract code from.
    """
    import nbformat
    from jupygrader.notebook_operations import extract_user_code_from_notebook

    # If output path wasn't provided, use current directory
    if not output_path:
        output_path = os.getcwd()

    # Create the output directory if it doesn't exist
    Path(output_path).mkdir(parents=True, exist_ok=True)

    try:
        # Load the notebook
        notebook_path = Path(notebook_path)
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Extract code
        user_code = extract_user_code_from_notebook(nb)

        # Save extracted code
        output_file = Path(output_path) / f"{notebook_path.stem}_user_code.py"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(user_code)

        click.echo(f"Extracted code saved to {output_file}")

    except Exception as e:
        click.echo(f"Error extracting code: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
