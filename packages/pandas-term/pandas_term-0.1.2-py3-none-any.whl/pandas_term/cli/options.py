"""Shared CLI options and helpers."""

from dataclasses import dataclass
from typing import Annotated

import typer

from pandas_term.cli.validators import OutputFormat, valid_input_file, valid_output_file


@dataclass
class OutputOptions:
    """Options for outputting dataframes."""

    file: str | None = None
    format: OutputFormat = "csv"


InputFileArgument = Annotated[
    str,
    typer.Argument(help="Input file path (default: stdin)", callback=valid_input_file),
]

UseJsonOption = Annotated[
    bool,
    typer.Option("--json", "-j", help="Output as JSON (shorthand for --format json)"),
]

FormatOption = Annotated[
    OutputFormat | None,
    typer.Option("--format", "-f", help="Output format: csv, json, tsv, md"),
]

OutputFileOption = Annotated[
    str | None,
    typer.Option(
        "--output", "-o", help="Output file path (default: stdout)", callback=valid_output_file
    ),
]


def get_output_options(
    use_json: bool = False,
    fmt: OutputFormat | None = None,
    output: str | None = None,
) -> OutputOptions:
    """Build OutputOptions from command arguments."""
    if use_json and fmt is not None:
        raise typer.BadParameter("Cannot specify both --json and --format")

    if use_json:
        resolved_format: OutputFormat = "json"
    elif fmt == "markdown":
        resolved_format = "md"
    elif fmt is not None:
        resolved_format = fmt
    else:
        resolved_format = "csv"

    return OutputOptions(file=output, format=resolved_format)
