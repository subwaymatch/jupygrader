#!/usr/bin/env python
import click

from jupygrader import (
    __version__,
)

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

if __name__ == "__main__":
    cli()
