"""Pure column-expression logic for classifying a reconciliation break.

Convention: left = payroll, right = hris.
  matched         -> both present, values within tolerance
  value_mismatch  -> both present, values differ beyond tolerance
  missing_left    -> present in payroll, absent from HRIS
  missing_right   -> present in HRIS, absent from payroll
"""
from pyspark.sql import functions as F
from pyspark.sql.column import Column


def break_type_expr(left_key: str, right_key: str,
                    left_val: str, right_val: str, tolerance: float) -> Column:
    both = F.col(left_key).isNotNull() & F.col(right_key).isNotNull()
    within = F.abs(F.col(left_val) - F.col(right_val)) <= F.lit(tolerance)
    return (
        F.when(both & within, F.lit("matched"))
         .when(both & ~within, F.lit("value_mismatch"))
         .when(F.col(left_key).isNotNull() & F.col(right_key).isNull(),
               F.lit("missing_left"))
         .otherwise(F.lit("missing_right"))
    )