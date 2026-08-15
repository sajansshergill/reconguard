"""Reconcile the gold Delta tables against what the report layer returns.

Azure path: compare gold Delta vs the Power BI dataset (via XmlaClient).
Local path: compare gold Delta vs a re-aggregation from silver (a stand-in
for the report query), proving the concept without a Power BI workspace."""
from pyspark.sql import functions as F


def reconcile_report_local(gold_summary_df, silver_payroll_df) -> dict:
    report_total = (silver_payroll_df.agg(F.round(F.sum("gross_pay"), 2))
                    .collect()[0][0])
    gold_total = gold_summary_df.agg(F.round(F.sum("total_gross"), 2)).collect()[0][0]
    passed = abs((report_total or 0) - (gold_total or 0)) < 0.01
    return {"check": "report_vs_gold", "passed": passed,
            "gold_total": gold_total, "report_total": report_total}