"""Functions for reading and writing dataframes with various file types."""

import sys
from pathlib import Path

import pandas as pd

from pandas_term.cli.options import OutputOptions


def read_dataframe(file: str) -> pd.DataFrame:
    """Read a dataframe from a file path or stdin ('-')."""
    if file == "-":
        return pd.read_csv(sys.stdin)

    path = Path(file)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported file format: {suffix}")


def _write_to_stdout(df: pd.DataFrame, fmt: str) -> None:
    """Write dataframe to stdout in the specified format."""
    if fmt == "json":
        sys.stdout.write(df.to_json(orient="records", indent=2))
        sys.stdout.write("\n")
    elif fmt == "tsv":
        df.to_csv(sys.stdout, index=False, sep="\t", lineterminator="\n")
    elif fmt == "md":
        sys.stdout.write(df.to_markdown(index=False))
        sys.stdout.write("\n")
    elif fmt == "csv":
        df.to_csv(sys.stdout, index=False, lineterminator="\n")
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def write_dataframe(df: pd.DataFrame, output_opts: OutputOptions) -> None:
    """Write a dataframe to file if specified else stdout."""
    if output_opts.file is None:
        _write_to_stdout(df, output_opts.format)
        return

    path = Path(output_opts.file)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".tsv":
        df.to_csv(path, index=False, sep="\t")
    elif suffix in [".xlsx", ".xls"]:
        df.to_excel(path, index=False)
    elif suffix == ".json":
        df.to_json(path, orient="records", indent=2)
    elif suffix == ".parquet":
        df.to_parquet(path, index=False)
    elif suffix == ".md":
        path.write_text(df.to_markdown(index=False) + "\n", encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file extension: {suffix}")
