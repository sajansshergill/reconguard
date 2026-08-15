"""Normalize payroll for a given pay period."""
from pyspark.sql import functions as F


def conform_payroll(df, pay_period: str):
    return (df.filter(F.col("pay_period") == pay_period)
              .dropDuplicates(["employee_id", "pay_period"]))