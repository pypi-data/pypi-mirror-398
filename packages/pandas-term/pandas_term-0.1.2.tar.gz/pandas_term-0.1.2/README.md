# pandas-term

pandas-term is a CLI bringing [pandas](https://pandas.pydata.org/) operations to the command line.

![Demo](https://raw.githubusercontent.com/KatieLG/pandas-term/main/demo/demo.gif)

> **Note:** Still in early experimental development and may change

## Installation

```bash
pipx install pandas-term
```

or

```bash
uv tool install pandas-term
```

## Usage

All commands accept an input file path (or `-` for stdin) and support `-o/--output` for file output (default: stdout).

### Command Reference

| Command           | Pandas Equivalent      | Description                |
| ----------------- | ---------------------- | -------------------------- |
| `pd select`       | `df[columns]`          | Select columns             |
| `pd drop`         | `df.drop()`            | Drop columns               |
| `pd rename`       | `df.rename()`          | Rename columns             |
| `pd sort`         | `df.sort_values()`     | Sort by columns            |
| `pd dedup`        | `df.drop_duplicates()` | Remove duplicate rows      |
| `pd duplicated`   | `df.duplicated()`      | Identify duplicate rows    |
| `pd merge`        | `pd.merge()`           | Merge two dataframes       |
| `pd concat`       | `pd.concat()`          | Concatenate dataframes     |
| `pd batch`        | `df.iloc[]`            | Split into batches         |
| `pd query`        | `df.query()`           | Filter with query expr     |
| `pd head`         | `df.head()`            | First n rows               |
| `pd tail`         | `df.tail()`            | Last n rows                |
| `pd dropna`       | `df.dropna()`          | Drop rows with nulls       |
| `pd describe`     | `df.describe()`        | Descriptive statistics     |
| `pd unique`       | `df[col].unique()`     | Unique values in column    |
| `pd shape`        | `df.shape`             | Dimensions (rows, columns) |
| `pd columns`      | `df.columns`           | Column names               |
| `pd dtypes`       | `df.dtypes`            | Column data types          |
| `pd value-counts` | `df.value_counts()`    | Count unique values        |
| `pd groupby`      | `df.groupby().agg()`   | Group by and aggregate     |

### Transform

```bash
# Select columns
pd select name,price data.csv

# Drop, sort & rename
pd drop unwanted_column data.csv
pd sort price data.csv --descending
pd rename "price:cost,name:product_name" data.csv

# Remove duplicates
pd dedup data.csv
pd dedup --subset category,aisle data.csv

# Merge two dataframes
pd merge left.csv right.csv --on id --how inner

# Concatenate files (supports glob patterns)
pd concat file1.csv file2.json
pd concat "data_*.csv"
pd concat "*"

# Split into batches (last repeats)
pd batch data.csv --sizes 10,20,50 -o "batch_{}.csv"
```

### Filter

```bash
# Query expression
pd query "price > 4.5 and category == 'Fruit'" data.csv

# First/last N rows
pd head --n 100 data.csv
pd tail --n 50 data.csv

# Drop rows with nulls
pd dropna data.csv
pd dropna --subset "name,category" data.csv

# Identify duplicate rows
pd duplicated data.csv
pd duplicated --subset category data.csv
pd duplicated --keep last data.csv
```

### Stats

```bash
pd describe data.csv
pd unique country data.csv
pd shape data.csv
pd columns data.csv
pd dtypes data.csv
```

### Aggregate

```bash
# Count unique values
pd value-counts category data.csv
pd value-counts category,aisle data.csv --normalize

# Group by and aggregate
pd groupby category data.csv --col price --agg sum
pd groupby "category,ailse" data.csv --col price,stock --agg mean
```

### Piping

All commands support piping through stdin/stdout. When piping, you can omit the input file argument (it defaults to stdin):

```bash
cat data.csv | pd query "stock > 30" | pd select name,category

pd sort price data.csv --descending | pd head --n 10 | pd select name,category
```

### Output Formats

Use `-f`/`--format` for stdout format (default: csv):

```bash
pd head --n 10 data.csv -f json
pd head --n 10 data.csv -f tsv
pd head --n 10 data.csv -f md
```

`--json`/`-j` is shorthand for `-f json`.

File output format is determined by extension:

```bash
pd select name,category data.csv -o output.xlsx
pd query "stock > 30" data.json -o filtered.parquet
```

Supported: csv, tsv, json, xlsx, parquet, md

For other extensions, use redirection: `pd select name data.csv -f csv > output.txt`

## Dev setup

Requires [uv](https://docs.astral.sh/uv/)

Install dependencies:

```bash
uv sync
```

| Command          | Description                       |
| ---------------- | --------------------------------- |
| `make check`     | Format, lint, and test            |
| `make format`    | Format code                       |
| `make lint`      | Linting only                      |
| `make test`      | Run tests                         |
| `make snapshots` | Regenerate test snapshots         |
| `make coverage`  | Tests with coverage               |
| `make bump`      | Bump version number               |
| `make demo`      | Regnerate demo gif from tape file |
