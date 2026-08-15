"""Reporting aggregate: payroll totals by period. No bank_account in gold."""
from pyspark.sql import functions as F


def payroll_summary(silver_payroll):
    return (silver_payroll
            .groupBy("pay_period")
            .agg(F.count("employee_id").alias("employees_paid"),
                 F.round(F.sum("gross_pay"), 2).alias("total_gross"),
                 F.round(F.sum("net_pay"), 2).alias("total_net")))