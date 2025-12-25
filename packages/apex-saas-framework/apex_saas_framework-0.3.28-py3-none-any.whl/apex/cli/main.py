"""
Typer CLI placeholder (FastAPI scaffolding removed for pure SDK mode).
"""

from __future__ import annotations

import typer

from apex import __version__

cli = typer.Typer(name="apexfastapi", help="(disabled) FastAPI scaffolding is removed")


@cli.command()
def version():
    """Show package version."""
    typer.echo(f"apex-saas-framework {__version__}")


@cli.command()
def init():
    """Disabled: FastAPI project scaffolding removed in SDK mode."""
    typer.echo("FastAPI project scaffolding is removed in pure SDK mode.")


@cli.command()
def create_superuser():
    """Disabled: FastAPI user bootstrap removed in SDK mode."""
    typer.echo("create_superuser is removed in pure SDK mode.")


def main():
    cli()


if __name__ == "__main__":
    main()













