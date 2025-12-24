"""CloudWatch metrics fetching with pandas DataFrame output."""

from datetime import datetime
from typing import Literal

import boto3
import pandas as pd
from pydantic import BaseModel, field_validator

from adaptivegears.aws.units import (
    ByteScale,
    ByteRateScale,
    BYTE_FACTORS,
    BYTE_RATE_FACTORS,
)


Stat = Literal["avg", "max", "min", "sum", "count"]

STAT_MAP: dict[Stat, str] = {
    "avg": "Average",
    "max": "Maximum",
    "min": "Minimum",
    "sum": "Sum",
    "count": "SampleCount",
}


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case, handling acronyms."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Add underscore before uppercase if previous char is lowercase
            # or if next char is lowercase (end of acronym)
            prev_lower = name[i - 1].islower()
            next_lower = i + 1 < len(name) and name[i + 1].islower()
            if prev_lower or next_lower:
                result.append("_")
        result.append(char.lower())
    return "".join(result)


class Metric(BaseModel):
    """Specification for a CloudWatch metric to fetch."""

    name: str
    stats: list[Stat] = ["avg"]
    scale: ByteScale | ByteRateScale | None = None
    label: str | None = None

    def __init__(
        self,
        name: str | None = None,
        /,
        *,
        stats: list[Stat] | Stat | None = None,
        scale: ByteScale | ByteRateScale | None = None,
        label: str | None = None,
        **kwargs,
    ):
        # Allow positional name argument
        if name is not None:
            kwargs["name"] = name
        if stats is not None:
            kwargs["stats"] = stats
        if scale is not None:
            kwargs["scale"] = scale
        if label is not None:
            kwargs["label"] = label
        super().__init__(**kwargs)

    @field_validator("stats", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

    @property
    def column_label(self) -> str:
        """Return the label for DataFrame columns."""
        return self.label or _to_snake_case(self.name)

    def convert(self, value: float) -> float:
        """Apply unit conversion to a value."""
        if self.scale is None:
            return value
        if isinstance(self.scale, ByteScale):
            return value / BYTE_FACTORS[self.scale]
        if isinstance(self.scale, ByteRateScale):
            return value / BYTE_RATE_FACTORS[self.scale]
        return value


def fetch_metrics(
    namespace: str,
    dimensions: dict[str, str],
    metrics: list[Metric],
    start_time: datetime,
    end_time: datetime,
    period: int = 3600,
    region: str = "us-east-1",
) -> pd.DataFrame:
    """
    Fetch CloudWatch metrics and return as a pandas DataFrame.

    Args:
        namespace: CloudWatch namespace (e.g., "AWS/RDS", "AWS/EC2")
        dimensions: Metric dimensions as key-value pairs
        metrics: List of Metric defining what to fetch
        start_time: Start of time range (UTC)
        end_time: End of time range (UTC)
        period: Data point period in seconds (default 3600 = 1 hour)
        region: AWS region

    Returns:
        DataFrame with timestamp index and metric columns named {label}_{stat}
    """
    client = boto3.client("cloudwatch", region_name=region)

    # Build dimensions list
    dims = [{"Name": k, "Value": v} for k, v in dimensions.items()]

    # Build metric queries with counter-based IDs to avoid collisions
    metric_queries = []
    query_map: dict[str, tuple[Metric, Stat, str]] = {}  # id -> (metric, stat, col_name)

    for idx, spec in enumerate(metrics):
        for stat_idx, stat in enumerate(spec.stats):
            # Use counter-based ID to guarantee uniqueness
            query_id = f"q_{idx}_{stat_idx}"
            col_name = f"{spec.column_label}_{stat}"

            metric_queries.append({
                "Id": query_id,
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": spec.name,
                        "Dimensions": dims,
                    },
                    "Period": period,
                    "Stat": STAT_MAP[stat],
                },
            })
            query_map[query_id] = (spec, stat, col_name)

    # Fetch with pagination
    results: dict[str, list] = {q["Id"]: [] for q in metric_queries}
    timestamps: dict[str, list] = {q["Id"]: [] for q in metric_queries}

    # CloudWatch limits to 500 metrics per request
    chunk_size = 500
    paginator = client.get_paginator("get_metric_data")

    for i in range(0, len(metric_queries), chunk_size):
        chunk = metric_queries[i : i + chunk_size]

        for page in paginator.paginate(
            MetricDataQueries=chunk,
            StartTime=start_time,
            EndTime=end_time,
        ):
            for result in page["MetricDataResults"]:
                query_id = result["Id"]
                results[query_id].extend(result["Values"])
                timestamps[query_id].extend(result["Timestamps"])

    # Build DataFrame using concat to handle sparse data
    series = []
    for query_id, (spec, stat, col_name) in query_map.items():
        ts = timestamps[query_id]
        vals = results[query_id]

        if not ts:
            continue

        converted = [spec.convert(v) for v in vals]
        s = pd.Series(converted, index=ts, name=col_name)
        series.append(s)

    if not series:
        return pd.DataFrame()

    # Concat aligns on index, filling missing values with NaN
    df = pd.concat(series, axis=1)
    df.index.name = "timestamp"
    df = df.sort_index()

    return df
