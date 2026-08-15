"""Delta Live Tables bronze layer with ingestion expectations.
Runs inside a Databricks DLT pipeline, not locally."""
import dlt

RAW = "/Volumes/reconguard/landing/raw"


@dlt.table(name="bronze_hris", comment="Raw HRIS extract")
@dlt.expect_or_drop("valid_employee_id", "employee_id IS NOT NULL")
@dlt.expect("has_salary", "base_salary IS NOT NULL")
def bronze_hris():
    return spark.read.format("csv").option("header", True).load(f"{RAW}/hris.csv")


@dlt.table(name="bronze_payroll", comment="Raw payroll extract")
@dlt.expect_or_drop("valid_employee_id", "employee_id IS NOT NULL")
@dlt.expect("positive_gross", "gross_pay > 0")
def bronze_payroll():
    return spark.read.format("csv").option("header", True).load(f"{RAW}/payroll.csv")