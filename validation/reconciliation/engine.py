"""Core reconciliation engine. Framework code — domain-agnostic, config-driven."""
from pyspark.sql import functions as F
from validation.reconciliation.classifiers import break_type_expr

BREAK_TYPES = ["matched", "value_mismatch", "missing_left", "missing_right"]


def reconcile(left_df, right_df, key: str,
              left_value_col: str, right_value_col: str, tolerance: float):
    """Full-outer reconcile two datasets on `key`, classifying every row.

    left = payroll, right = hris (see classifiers for the convention).
    Returns a DataFrame with columns: key, left_value, right_value, break_type.
    """
    left = (left_df.select(F.col(key).alias("l_key"),
                           F.col(left_value_col).alias("left_value")))
    right = (right_df.select(F.col(key).alias("r_key"),
                             F.col(right_value_col).alias("right_value")))

    joined = left.join(right, left.l_key == right.r_key, how="full_outer")
    classified = joined.withColumn(
        "break_type",
        break_type_expr("l_key", "r_key", "left_value", "right_value", tolerance),
    )
    return classified.select(
        F.coalesce("l_key", "r_key").alias(key),
        "left_value", "right_value", "break_type",
    )


def summarize(result_df) -> dict:
    """Return a {break_type: count} dict, zero-filled for all categories."""
    counts = {r["break_type"]: r["count"]
              for r in result_df.groupBy("break_type").count().collect()}
    return {bt: counts.get(bt, 0) for bt in BREAK_TYPES}