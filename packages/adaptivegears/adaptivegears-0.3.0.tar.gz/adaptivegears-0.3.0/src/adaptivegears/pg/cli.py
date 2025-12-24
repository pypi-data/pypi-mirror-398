import json
import os
from datetime import date, datetime
from typing import Literal

import typer

from .histogram import Granularity, HistogramError, parse_last, run_histogram
from .schema import SchemaError, run_schema


def parse_date(value: str) -> date:
    """Parse YYYY-MM-DD string to date."""
    return datetime.strptime(value, "%Y-%m-%d").date()

SortColumn = Literal["name", "rows", "size", "avg"]
SORT_CONFIG: dict[str, tuple[str, bool]] = {
    "name": ("table", False),  # asc
    "rows": ("rows", True),  # desc
    "size": ("total_size", True),  # desc
    "avg": ("avg_row_size", True),  # desc
}

app = typer.Typer(help="PostgreSQL utilities")


def get_connection():
    try:
        import psycopg
    except ImportError:
        raise typer.Exit("psycopg not installed. Run: pip install adaptivegears")

    if not os.environ.get("PGDATABASE"):
        raise typer.Exit("PGDATABASE environment variable not set")

    return psycopg.connect()


def glob_to_sql_like(pattern: str) -> str:
    """Convert shell glob pattern to SQL LIKE pattern."""
    return pattern.replace("*", "%").replace("?", "_")


def format_size(bytes_val: int | None) -> str:
    """Human-readable size."""
    if bytes_val is None or bytes_val == 0:
        return "0 B"
    for unit in ("B", "kB", "MB", "GB", "TB"):
        if abs(bytes_val) < 1024:
            return (
                f"{bytes_val:.0f} {unit}" if unit == "B" else f"{bytes_val:.1f} {unit}"
            )
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


@app.command("ping")
def ping():
    """Check database connectivity."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    print("PONG")


@app.command("list")
def list_tables(
    pattern: str = typer.Argument(
        None, help="Table name pattern (glob: page_schema_*)"
    ),
    schema: str = typer.Option(
        "public", "--schema", "-s", help="Schema to list tables from"
    ),
    min_rows: int = typer.Option(
        None, "--min-rows", help="Only tables with at least N rows"
    ),
    max_rows: int = typer.Option(
        None, "--max-rows", help="Only tables with at most N rows"
    ),
    sort: SortColumn = typer.Option(
        None, "--sort", help="Sort by: name (asc), rows/size/avg (desc)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List tables with size statistics."""
    like_pattern = glob_to_sql_like(pattern) if pattern else "%"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.relname AS table,
                    c.reltuples::bigint AS rows,
                    pg_total_relation_size(c.oid) AS total_bytes
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = %s
                  AND c.relkind = 'r'
                  AND c.relname LIKE %s
                ORDER BY c.relname
                """,
                (schema, like_pattern),
            )
            rows = cur.fetchall()

    tables = []
    for table, row_count, total_bytes in rows:
        avg_bytes = total_bytes // row_count if row_count > 0 else 0
        tables.append(
            {
                "table": table,
                "rows": row_count,
                "total_size": total_bytes,
                "avg_row_size": avg_bytes,
            }
        )

    # Filter by row count
    if min_rows is not None:
        tables = [t for t in tables if t["rows"] >= min_rows]
    if max_rows is not None:
        tables = [t for t in tables if t["rows"] <= max_rows]

    # Sort
    if sort:
        key, reverse = SORT_CONFIG[sort]
        tables.sort(key=lambda t: t[key], reverse=reverse)

    if json_output:
        print(json.dumps(tables))
    else:
        if not tables:
            return
        name_width = max(len(t["table"]) for t in tables)
        rows_width = max(len(f"{t['rows']:,}") for t in tables)
        for t in tables:
            print(
                f"{t['table']:<{name_width}}  "
                f"{t['rows']:>{rows_width},}  "
                f"{format_size(t['total_size']):>10}  "
                f"{format_size(t['avg_row_size']):>10}"
            )


@app.command("histogram")
def histogram(
    table: str = typer.Argument(..., help="Table name"),
    column: str = typer.Argument(..., help="Date/timestamp column"),
    schema: str = typer.Option(
        "public", "--schema", "-s", help="Schema name"
    ),
    by: Granularity = typer.Option(
        "day", "--by", "-b", help="Bucket granularity: hour, day, week, month, year"
    ),
    since: str = typer.Option(
        None, "--since", help="Start date inclusive (YYYY-MM-DD)"
    ),
    until: str = typer.Option(
        None, "--until", help="End date exclusive (YYYY-MM-DD)"
    ),
    last: str = typer.Option(
        None, "--last", "-l", help="Relative range: 7d, 30d, 3m, 1y"
    ),
    bars: bool = typer.Option(False, "--bars", help="Show ASCII histogram bars"),
    cumulative: bool = typer.Option(False, "--cumulative", "-c", help="Show cumulative percentage"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show record count distribution over time."""
    since_date: date | None = None
    until_date: date | None = None

    # Handle --last as shortcut for --since
    if last:
        if since:
            raise typer.BadParameter("Cannot use both --since and --last")
        since_date = parse_last(last)
    elif since:
        since_date = parse_date(since)

    if until:
        until_date = parse_date(until)

    with get_connection() as conn:
        try:
            run_histogram(
                conn,
                table=table,
                column=column,
                schema=schema,
                granularity=by,
                since=since_date,
                until=until_date,
                bars=bars,
                cumulative=cumulative,
                json_output=json_output,
            )
        except HistogramError as e:
            raise typer.BadParameter(str(e))


@app.command("schema")
def schema(
    table: str = typer.Argument(..., help="Table name"),
    schema: str = typer.Option(
        "public", "--schema", "-s", help="Schema name"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show CREATE TABLE DDL with indexes."""
    with get_connection() as conn:
        try:
            run_schema(
                conn,
                table=table,
                schema=schema,
                json_output=json_output,
            )
        except SchemaError as e:
            raise typer.BadParameter(str(e))
