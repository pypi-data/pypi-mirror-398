"""CLI commands for dataframe transformations."""

import glob
from typing import Annotated, Literal

import pandas as pd
import typer

from pandas_term.cli.options import (
    FormatOption,
    InputFileArgument,
    OutputFileOption,
    OutputOptions,
    UseJsonOption,
    get_output_options,
)
from pandas_term.cli.validators import (
    get_columns,
    positive_int_list,
    valid_batch_pattern,
    valid_rename_mapping,
)
from pandas_term.core import io_operations, transforms

app = typer.Typer(add_completion=False)


@app.command()
def select(
    columns: Annotated[str, typer.Argument(help="Comma-separated list of columns to select")],
    input_file: InputFileArgument = "-",
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Select provided columns from the dataframe."""
    df = io_operations.read_dataframe(input_file)
    column_list = get_columns(df, columns)
    result = df[column_list]
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def drop(
    columns: Annotated[str, typer.Argument(help="Comma-separated list of columns to drop")],
    input_file: InputFileArgument = "-",
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Drop provided columns from the dataframe."""
    df = io_operations.read_dataframe(input_file)
    result = df.drop(columns=get_columns(df, columns))
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def sort(
    columns: Annotated[str, typer.Argument(help="Comma-separated list of columns to sort by")],
    input_file: InputFileArgument = "-",
    ascending: Annotated[bool, typer.Option("--ascending/--descending", help="Sort order")] = True,
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Sort dataframe by specified columns."""
    df = io_operations.read_dataframe(input_file)
    result = df.sort_values(by=get_columns(df, columns), ascending=ascending)
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def rename(
    mapping: Annotated[
        str,
        typer.Argument(help="Rename mapping as 'old:new,old2:new2'", callback=valid_rename_mapping),
    ],
    input_file: InputFileArgument = "-",
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Rename columns in the dataframe."""
    df = io_operations.read_dataframe(input_file)
    rename_map = {}
    for pair in mapping.split(","):
        old, new = pair.strip().split(":")
        rename_map[old.strip()] = new.strip()
    result = df.rename(columns=rename_map)
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def dedup(
    input_file: InputFileArgument = "-",
    subset: Annotated[
        str | None,
        typer.Option(
            "--subset", "-s", help="Comma-separated list of columns to consider for duplicates"
        ),
    ] = None,
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Remove duplicate rows from the dataframe."""
    df = io_operations.read_dataframe(input_file)
    result = df.drop_duplicates(subset=get_columns(df, subset))
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def merge(
    left_file: Annotated[str, typer.Argument(help="Left dataframe file path")],
    right_file: Annotated[str, typer.Argument(help="Right dataframe file path")],
    on: Annotated[
        str | None,
        typer.Option("--on", help="Comma-separated list of columns to merge on"),
    ] = None,
    how: Annotated[
        Literal["inner", "left", "right", "outer", "cross"],
        typer.Option("--how", help="Type of merge: inner, left, right, outer, cross"),
    ] = "inner",
    left_on: Annotated[
        str | None,
        typer.Option("--left-on", help="Comma-separated left dataframe columns to merge on"),
    ] = None,
    right_on: Annotated[
        str | None,
        typer.Option("--right-on", help="Comma-separated right dataframe columns to merge on"),
    ] = None,
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Merge two dataframes."""
    left_df = io_operations.read_dataframe(left_file)
    right_df = io_operations.read_dataframe(right_file)
    result = left_df.merge(
        right_df,
        on=get_columns(left_df, on),
        how=how,
        left_on=get_columns(left_df, left_on),
        right_on=get_columns(right_df, right_on),
    )
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def concat(
    files: Annotated[list[str], typer.Argument(help="Files or glob patterns to concatenate")],
    use_json: UseJsonOption = False,
    fmt: FormatOption = None,
    output: OutputFileOption = None,
) -> None:
    """Concatenate multiple dataframes vertically. Supports glob patterns like 'data_*.csv'."""
    matching_files = [
        file
        for pattern in files
        for file in sorted(glob.glob(pattern))  # noqa: PTH207
    ]

    dfs = [io_operations.read_dataframe(f) for f in matching_files]
    result = pd.concat(dfs, ignore_index=True)
    io_operations.write_dataframe(result, get_output_options(use_json, fmt, output))


@app.command()
def batch(
    input_file: InputFileArgument = "-",
    sizes: Annotated[
        str,
        typer.Option(
            "--sizes",
            "-s",
            help="Comma-separated batch sizes (last size repeats)",
            callback=positive_int_list,
        ),
    ] = "100",
    output_pattern: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output file pattern (e.g., 'batch_{}.csv')",
            callback=valid_batch_pattern,
        ),
    ] = "batch_{}.csv",
) -> None:
    """Split dataframe into batches and write to separate files."""
    df = io_operations.read_dataframe(input_file)
    size_list = [int(s.strip()) for s in sizes.split(",")]
    batches = transforms.batch_dataframe(df, size_list)

    for i, batch_df in enumerate(batches, start=1):
        output_file = output_pattern.format(i)
        io_operations.write_dataframe(batch_df, OutputOptions(file=output_file))
        typer.echo(f"Written batch {i} to {output_file} ({len(batch_df)} rows)")
