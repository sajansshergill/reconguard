"""Emit a simple source->report lineage map."""


def build_lineage() -> dict:
    return {
        "gold_headcount_by_dept": {
            "silver_employees": {"bronze_hris": ["raw/hris.csv"]},
        },
        "gold_payroll_summary": {
            "silver_payroll": {"bronze_payroll": ["raw/payroll.csv"]},
        },
    }