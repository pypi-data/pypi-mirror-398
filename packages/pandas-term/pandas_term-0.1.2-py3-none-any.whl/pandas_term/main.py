import sys
from importlib.metadata import version as get_version
from typing import Annotated

import typer

from pandas_term.cli import aggregate_commands, filter_commands, stats_commands, transform_commands

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pd version: {get_version('pandas-term')}")
        raise typer.Exit


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    _version: Annotated[
        bool, typer.Option("-v", "--version", callback=version_callback, is_eager=True)
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.add_typer(transform_commands.app)
app.add_typer(filter_commands.app)
app.add_typer(stats_commands.app)
app.add_typer(aggregate_commands.app)


def cli() -> None:
    """Run cli with a catch all error display"""
    try:
        app()
    except Exception as e:
        typer.echo(typer.style(f"Internal Error: {e}", fg=typer.colors.RED), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
