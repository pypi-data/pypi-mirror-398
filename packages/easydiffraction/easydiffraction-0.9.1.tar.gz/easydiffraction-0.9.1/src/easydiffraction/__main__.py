# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import sys

# Ensure UTF-8 output on all platforms (e.g. Windows with cp1252)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import typer

import easydiffraction as ed

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(  # noqa: FBT003 - boolean option is intended
        False,
        '--version',
        '-V',
        help='Show easydiffraction version and exit.',
        is_eager=True,
    ),
):
    """EasyDiffraction command-line interface."""
    if version:
        ed.show_version()
        raise typer.Exit(code=0)
    # If no subcommand and no option provided, show help and exit 0.
    if ctx.invoked_subcommand is None:
        typer.echo(app.get_help(ctx))
        raise typer.Exit(code=0)
    # Otherwise, let the chosen subcommand execute.


@app.command('list-tutorials')
def list_tutorials():
    """List available tutorial notebooks."""
    ed.list_tutorials()


@app.command('download-tutorial')
def download_tutorial(
    id: int = typer.Argument(..., help='Tutorial ID to download.'),
    destination: str = typer.Option(
        'tutorials',
        '--destination',
        '-d',
        help='Directory to save the tutorial into.',
    ),
    overwrite: bool = typer.Option(
        False,  # noqa: FBT003 - boolean option is intended
        '--overwrite',
        '-o',
        help='Overwrite existing file if present.',
    ),
):
    """Download a specific tutorial notebook by ID."""
    ed.download_tutorial(id=id, destination=destination, overwrite=overwrite)


@app.command('download-all-tutorials')
def download_all_tutorials(
    destination: str = typer.Option(
        'tutorials',
        '--destination',
        '-d',
        help='Directory to save the tutorials into.',
    ),
    overwrite: bool = typer.Option(
        False,  # noqa: FBT003 - boolean option is intended
        '--overwrite',
        '-o',
        help='Overwrite existing files if present.',
    ),
):
    """Download all available tutorial notebooks."""
    ed.download_all_tutorials(destination=destination, overwrite=overwrite)


if __name__ == '__main__':
    app()
