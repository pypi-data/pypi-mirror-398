"""Histogram command for temporal distribution analysis."""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

Granularity = Literal["hour", "day", "week", "month", "year"]

TRUNC_FORMAT = {
    "hour": "%Y-%m-%d %H:00",
    "day": "%Y-%m-%d",
    "week": "%Y-W%W",
    "month": "%Y-%m",
    "year": "%Y",
}

TEMPORAL_TYPES = {
    "date",
    "timestamp without time zone",
    "timestamp with time zone",
    "time without time zone",
    "time with time zone",
}


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool


def get_column_info(conn, schema: str, table: str, column: str) -> ColumnInfo | None:
    """Get column metadata from information_schema."""
    query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
          AND column_name = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (schema, table, column))
        row = cur.fetchone()

    if not row:
        return None

    return ColumnInfo(
        name=row[0],
        data_type=row[1],
        is_nullable=row[2] == "YES",
    )


def parse_last(value: str) -> date:
    """Parse relative date like '7d', '30d', '3m', '1y' into absolute date."""
    match = re.match(r"^(\d+)([dwmy])$", value.lower())
    if not match:
        raise ValueError(f"Invalid --last format: {value}. Use: 7d, 30d, 3m, 1y")

    amount, unit = int(match.group(1)), match.group(2)
    today = date.today()

    if unit == "d":
        return today - timedelta(days=amount)
    elif unit == "w":
        return today - timedelta(weeks=amount)
    elif unit == "m":
        # Approximate months as 30 days
        return today - timedelta(days=amount * 30)
    elif unit == "y":
        return today - timedelta(days=amount * 365)


def format_bucket(dt: datetime, granularity: Granularity) -> str:
    """Format datetime bucket for display."""
    return dt.strftime(TRUNC_FORMAT[granularity])


def render_bar(count: int, max_count: int, width: int = 30) -> str:
    """Render ASCII bar proportional to count."""
    if max_count == 0:
        return ""
    bar_len = int((count / max_count) * width)
    return "█" * bar_len


class HistogramError(Exception):
    """Raised when histogram cannot be computed."""

    pass


def run_histogram(
    conn,
    table: str,
    column: str,
    schema: str = "public",
    granularity: Granularity = "day",
    since: date | None = None,
    until: date | None = None,
    bars: bool = False,
    cumulative: bool = False,
    json_output: bool = False,
) -> None:
    """Execute histogram query and print results."""
    # Validate column exists and has correct type
    col_info = get_column_info(conn, schema, table, column)
    if not col_info:
        raise HistogramError(
            f"Column '{column}' not found in {schema}.{table}"
        )

    if col_info.data_type not in TEMPORAL_TYPES:
        raise HistogramError(
            f"Column '{column}' is {col_info.data_type}, expected date/timestamp"
        )

    # Build WHERE clause
    conditions = []
    params: list = []

    # Filter NULLs if column is nullable
    if col_info.is_nullable:
        conditions.append(f'"{column}" IS NOT NULL')

    if since:
        conditions.append(f'"{column}" >= %s')
        params.append(since)
    if until:
        conditions.append(f'"{column}" < %s')
        params.append(until)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            date_trunc(%s, "{column}") AS bucket,
            COUNT(*) AS count
        FROM "{schema}"."{table}"
        {where_clause}
        GROUP BY 1
        ORDER BY 1
    """

    with conn.cursor() as cur:
        cur.execute(query, [granularity] + params)
        rows = cur.fetchall()

    if not rows:
        return

    buckets = [{"bucket": format_bucket(r[0], granularity), "count": r[1]} for r in rows]

    if cumulative:
        total = sum(b["count"] for b in buckets)
        running = 0
        for b in buckets:
            running += b["count"]
            b["cumulative_pct"] = (running / total) * 100 if total > 0 else 0

    if json_output:
        print(json.dumps(buckets))
        return

    max_count = max(b["count"] for b in buckets)
    bucket_width = max(len(b["bucket"]) for b in buckets)
    count_width = max(len(f"{b['count']:,}") for b in buckets)

    for b in buckets:
        line = f"{b['bucket']:<{bucket_width}}  {b['count']:>{count_width},}"
        if cumulative:
            line += f"  {b['cumulative_pct']:>6.1f}%"
        if bars:
            if cumulative:
                line += f"  {render_bar(b['cumulative_pct'], 100)}"
            else:
                line += f"  {render_bar(b['count'], max_count)}"
        print(line)
