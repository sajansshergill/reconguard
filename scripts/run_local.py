"""Run the full ReconGuard flow locally on OSS Delta + Spark."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

from data_generator.generate import main as generate_data
from pipelines.bronze.ingest_hris import ingest_hris
from pipelines.bronze.ingest_payroll import ingest_payroll
from pipelines.silver.conform_employees import conform_employees
from pipelines.silver.conform_payroll import conform_payroll
from pipelines.gold.payroll_summary import payroll_summary
from pipelines.gold.headcount_by_dept import headcount_by_dept
from validation.reconciliation.engine import reconcile, summarize
from validation.reconciliation.audit_writer import write_audit
from validation.reconciliation.report import format_summary
from validation.pii.mask_checks import check_no_pii_in_gold


def get_spark():
    builder = (SparkSession.builder.appName("reconguard-local")
               .config("spark.sql.extensions",
                       "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog",
                       "org.apache.spark.sql.delta.catalog.DeltaCatalog"))
    return configure_spark_with_delta_pip(builder).getOrCreate()


def main():
    cfg = yaml.safe_load(open("config/settings.yaml"))
    rules = yaml.safe_load(open("config/reconciliation_rules.yaml"))
    p = cfg["paths"]

    generate_data()
    spark = get_spark()

    ingest_hris(spark, f"{p['raw']}/hris.csv", f"{p['bronze']}/hris")
    ingest_payroll(spark, f"{p['raw']}/payroll.csv", f"{p['bronze']}/payroll")

    emp = conform_employees(spark.read.format("delta").load(f"{p['bronze']}/hris"))
    pay = conform_payroll(spark.read.format("delta").load(f"{p['bronze']}/payroll"),
                          rules["pay_period"])
    emp.write.format("delta").mode("overwrite").save(f"{p['silver']}/employees")
    pay.write.format("delta").mode("overwrite").save(f"{p['silver']}/payroll")

    result = reconcile(pay, emp, rules["key"],
                       rules["left_value_col"], rules["right_value_col"],
                       rules["tolerance"])
    summary = summarize(result)
    write_audit(spark, result, summary, rules["pay_period"], p["audit"])
    print(format_summary(summary, rules["pay_period"]))

    gold = payroll_summary(pay)
    headcount = headcount_by_dept(emp)
    gold.write.format("delta").mode("overwrite").save(f"{p['gold']}/payroll_summary")
    headcount.write.format("delta").mode("overwrite").save(f"{p['gold']}/headcount_by_dept")
    print(check_no_pii_in_gold(gold, ["bank_account", "national_id"]))
    spark.stop()


if __name__ == "__main__":
    main()