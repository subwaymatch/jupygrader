#!/usr/bin/env python
import click
import os
import nbformat
from jupygrader import __version__, grade_notebooks, strip_solution_codes_from_notebook
from jupygrader.utils import process_notebook_paths

notebook_path_argument = click.argument("notebook_paths", nargs=-1, required=True)


@click.group()
@click.version_option(__version__, "--version", "-v", message="jupygrader %(version)s")
def cli():
    """Jupygrader CLI"""
    pass


@cli.command()
@notebook_path_argument
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose output.")
@click.option(
    "--export-csv/--no-export-csv",
    default=True,
    help="Export results to CSV (default: enabled).",
)
@click.option(
    "--csv-output-path",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    default=None,
    help="Directory to write CSV output into (does not need to exist yet).",
)
@click.option(
    "--regrade-existing",
    is_flag=True,
    default=False,
    help="Regrade even if results already exist.",
)
@process_notebook_paths
def grade(notebook_paths, verbose, export_csv, csv_output_path, regrade_existing):
    """Grade one or more notebooks or patterns."""

    if csv_output_path is not None and os.path.isfile(csv_output_path):
        click.echo(
            f"Error: --csv-output-path must be a directory, not a file: {csv_output_path}",
            err=True,
        )
        raise click.Abort()

    click.echo(f"{len(notebook_paths)} notebook(s) to grade.")
    click.echo(
        f"verbose={verbose}, export_csv={export_csv}, csv_output_path={csv_output_path}, regrade_existing={regrade_existing}"
    )

    grade_notebooks(
        notebook_paths,
        verbose=verbose,
        export_csv=export_csv,
        csv_output_path=csv_output_path,
        regrade_existing=regrade_existing,
    )


@cli.command()
@click.argument(
    "notebook_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    required=True,
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    default=None,
    help="Path to save the stripped notebook. Defaults to '[input]-stripped.ipynb'.",
)
@click.option(
    "--clear-output/--no-clear-output",
    default=True,
    help="Also clear cell outputs and execution counts. Enabled by default.",
)
def strip(notebook_path, output_path, clear_output):
    """Strip solution code and optionally outputs from a Jupyter Notebook."""

    if not notebook_path.endswith(".ipynb"):
        click.echo(
            f"Error: The input file must be a Jupyter Notebook (.ipynb): {notebook_path}",
            err=True,
        )
        raise click.Abort()

    if output_path is None:
        base, ext = os.path.splitext(notebook_path)
        write_path = f"{base}-stripped{ext}"
    else:
        write_path = output_path
        if not write_path.endswith(".ipynb"):
            click.echo(
                f"Error: The output file must be a Jupyter Notebook (.ipynb): {write_path}",
                err=True,
            )
            raise click.Abort()

    click.echo(f"Stripping notebook: {os.path.basename(notebook_path)}")
    if not clear_output:
        click.echo("Preserving cell outputs.")

    try:
        nb = nbformat.read(notebook_path, as_version=4)
        nb_stripped = strip_solution_codes_from_notebook(nb, clear_output=clear_output)
        nbformat.write(nb_stripped, write_path)

        click.secho(
            f"Successfully created stripped notebook at: {os.path.basename(write_path)}",
            fg="green",
        )

    except Exception as e:
        click.echo(f"An error occurred while processing the notebook: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
