"""Reporting aggregate: headcount by department. PII columns excluded by design."""
from pyspark.sql import functions as F


def headcount_by_dept(silver_employees):
    return (silver_employees
            .groupBy("department")
            .agg(F.count("employee_id").alias("headcount"),
                 F.round(F.avg("base_salary"), 2).alias("avg_base_salary")))