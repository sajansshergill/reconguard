"""Schema, freshness and completeness checks for bronze tables."""
from datetime import timedelta

from pyspark.sql import functions as F

from validation.expectations.sim_clock import SIM_TODAY


def check_required_columns(df, required: list[str]) -> dict:
    missing = [c for c in required if c not in df.columns]
    return {"check": "required_columns", "passed": not missing, "missing": missing}


def check_freshness(df, run_date_col: str, max_age_days: int) -> dict:
    newest = df.agg(F.max(run_date_col)).collect()[0][0]
    cutoff = SIM_TODAY - timedelta(days=max_age_days)
    passed = newest is not None and newest >= cutoff
    return {"check": "freshness", "passed": passed, "newest": str(newest)}


def check_completeness(df, column: str, max_null_rate: float) -> dict:
    total = df.count()
    nulls = df.filter(F.col(column).isNull()).count()
    rate = (nulls / total) if total else 0.0
    return {"check": f"completeness[{column}]", "passed": rate <= max_null_rate,
            "null_rate": round(rate, 4)}