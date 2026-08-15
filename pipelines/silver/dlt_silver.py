"""DLT silver transforms with business-rule expectations."""
import dlt
from pyspark.sql import Window
from pyspark.sql import functions as F


@dlt.table(name="silver_employees")
@dlt.expect_or_fail("unique_current", "is_current = true")
def silver_employees():
    df = dlt.read("bronze_hris")
    w = Window.partitionBy("employee_id").orderBy(F.col("effective_date").desc())
    return (df.withColumn("_rn", F.row_number().over(w))
              .filter("_rn = 1").drop("_rn")
              .withColumn("expected_gross", F.round(F.col("base_salary") / 12, 2)))


@dlt.table(name="silver_payroll")
@dlt.expect("no_negative_net", "net_pay >= 0")
def silver_payroll():
    return dlt.read("bronze_payroll").dropDuplicates(["employee_id", "pay_period"])