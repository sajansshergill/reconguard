"""Clean + dedupe effective-dated employees: keep the current record per employee."""
from pyspark.sql import Window
from pyspark.sql import functions as F


def conform_employees(df):
    w = Window.partitionBy("employee_id").orderBy(F.col("effective_date").desc())
    ranked = df.withColumn("_rn", F.row_number().over(w))
    current = ranked.filter(F.col("_rn") == 1).drop("_rn")
    # expected monthly gross derived here for reconciliation
    return current.withColumn("expected_gross", F.round(F.col("base_salary") / 12, 2))