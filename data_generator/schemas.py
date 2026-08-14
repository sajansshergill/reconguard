"""Shared column names + Spark schemas for the two source systems."""
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType, DateType
)

HRIS_COLUMNS = [
    "employee_id", "first_name", "last_name", "department",
    "national_id", "base_salary", "effective_date", "is_current",
]

PAYROLL_COLUMNS = [
    "employee_id", "pay_period", "gross_pay", "net_pay",
    "bank_account", "run_date",
]

HRIS_SCHEMA = StructType([
    StructField("employee_id", StringType(), False),
    StructField("first_name", StringType(), True),
    StructField("last_name", StringType(), True),
    StructField("department", StringType(), True),
    StructField("national_id", StringType(), True),
    StructField("base_salary", DoubleType(), True),
    StructField("effective_date", DateType(), True),
    StructField("is_current", BooleanType(), True),
])

PAYROLL_SCHEMA = StructType([
    StructField("employee_id", StringType(), False),
    StructField("pay_period", StringType(), True),
    StructField("gross_pay", DoubleType(), True),
    StructField("net_pay", DoubleType(), True),
    StructField("bank_account", StringType(), True),
    StructField("run_date", DateType(), True),
])