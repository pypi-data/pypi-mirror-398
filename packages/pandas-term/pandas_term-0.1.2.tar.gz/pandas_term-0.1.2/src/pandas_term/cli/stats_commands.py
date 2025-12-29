"""CLI commands for dataframe statistics operations."""

from typing import Annotated

import typer

from pandas_term.cli.options import (
    FormatOption,
    InputFileArgument,
    OutputFileOption,
    UseJsonOption,
    get_output_options,
)
from pandas_term.cli.validators import validate_columns
from pandas_term.core import io_operations

app = typer.Typer(add_completion=False)


@app.command()
def describe(
    input_file: InputFileArgument = "-",
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Generate descriptive statistics for the dataframe."""
    df = io_operations.read_dataframe(input_file)
    result = df.describe()
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def unique(
    column: Annotated[str, typer.Argument(help="Column to get unique values from")],
    input_file: InputFileArgument = "-",
) -> None:
    """Display unique values in a column."""
    df = io_operations.read_dataframe(input_file)
    validate_columns(df, [column])
    for value in df[column].unique():
        typer.echo(value)


@app.command()
def shape(
    input_file: InputFileArgument = "-",
) -> None:
    """Display dimensions (rows, columns) of the dataframe."""
    df = io_operations.read_dataframe(input_file)
    rows, cols = df.shape
    typer.echo(f"{rows} rows x {cols} columns")


@app.command()
def columns(
    input_file: InputFileArgument = "-",
) -> None:
    """Display column names of the dataframe."""
    df = io_operations.read_dataframe(input_file)
    for col in df.columns:
        typer.echo(col)


@app.command()
def dtypes(
    input_file: InputFileArgument = "-",
) -> None:
    """Display column names and their data types."""
    df = io_operations.read_dataframe(input_file)
    for col, dtype in df.dtypes.items():
        typer.echo(f"{col}: {dtype}")
