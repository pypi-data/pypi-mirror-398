"""CLI commands for dataframe aggregation operations."""

from typing import Annotated

import typer

from pandas_term.cli.options import (
    FormatOption,
    InputFileArgument,
    OutputFileOption,
    UseJsonOption,
    get_output_options,
)
from pandas_term.cli.validators import get_columns
from pandas_term.core import io_operations

app = typer.Typer(add_completion=False)


@app.command()
def value_counts(
    columns: Annotated[str, typer.Argument(help="Comma-separated columns to count values in")],
    input_file: InputFileArgument = "-",
    normalize: Annotated[
        bool,
        typer.Option("--normalize", "-n", help="Return proportions instead of counts"),
    ] = False,
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Count unique value combinations in columns."""
    df = io_operations.read_dataframe(input_file)
    col_list = get_columns(df, columns)
    result = df.value_counts(subset=col_list, normalize=normalize).reset_index()
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def groupby(
    group_cols: Annotated[str, typer.Argument(help="Comma-separated list of columns to group by")],
    input_file: InputFileArgument = "-",
    *,
    col: Annotated[str, typer.Option("--col", "-c", help="Comma-separated columns to aggregate")],
    agg: Annotated[
        str,
        typer.Option("--agg", "-a", help="Aggregation function (sum, mean, count, etc.)"),
    ] = "sum",
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Group by columns and apply aggregation function."""
    df = io_operations.read_dataframe(input_file)
    group_col_list = get_columns(df, group_cols)
    agg_col_list = get_columns(df, col)
    result = df.groupby(group_col_list)[agg_col_list].agg(agg).reset_index()
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))
