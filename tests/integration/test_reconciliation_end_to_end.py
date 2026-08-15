from data_generator.hris_source import build_employees
from data_generator.payroll_source import build_payroll
from data_generator.break_injector import inject
from pipelines.silver.conform_employees import conform_employees
from pipelines.silver.conform_payroll import conform_payroll
from validation.reconciliation.engine import reconcile, summarize
from data_generator.schemas import HRIS_SCHEMA, PAYROLL_SCHEMA


def _rows_to_df(spark, rows, schema):
    return spark.createDataFrame([tuple(r[c.name] for c in schema.fields)
                                  for r in rows], schema)


def test_pipeline_detects_breaks(spark):
    emp = build_employees(100)
    pay = build_payroll(emp)
    hris_rows, pay_rows = inject(emp, pay)

    hris_df = conform_employees(_rows_to_df(spark, hris_rows, HRIS_SCHEMA))
    pay_df = conform_payroll(_rows_to_df(spark, pay_rows, PAYROLL_SCHEMA), "2026-07")

    s = summarize(reconcile(pay_df, hris_df, "employee_id",
                            "gross_pay", "expected_gross", 1.0))
    assert s["missing_left"] >= 2      # orphan payroll rows
    assert s["missing_right"] >= 1     # dropped payroll rows
    assert s["value_mismatch"] >= 1    # perturbed gross