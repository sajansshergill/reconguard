"""DLT gold serving tables (PII-free)."""
import dlt
from pyspark.sql import functions as F


@dlt.table(name="gold_headcount_by_dept")
def gold_headcount_by_dept():
    return (dlt.read("silver_employees")
            .groupBy("department")
            .agg(F.count("employee_id").alias("headcount"),
                 F.round(F.avg("base_salary"), 2).alias("avg_base_salary")))


@dlt.table(name="gold_payroll_summary")
def gold_payroll_summary():
    return (dlt.read("silver_payroll")
            .groupBy("pay_period")
            .agg(F.count("employee_id").alias("employees_paid"),
                 F.round(F.sum("gross_pay"), 2).alias("total_gross")))