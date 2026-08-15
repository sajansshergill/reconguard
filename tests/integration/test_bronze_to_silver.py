from datetime import date
from pipelines.silver.conform_employees import conform_employees


def test_dedup_keeps_current(spark):
    rows = [
        ("E1", "Ada", "L", "Eng", "111", 120000.0, date(2026, 1, 1), True),
        ("E1", "Ada", "L", "Eng", "111", 100000.0, date(2025, 1, 1), False),
    ]
    cols = ["employee_id", "first_name", "last_name", "department",
            "national_id", "base_salary", "effective_date", "is_current"]
    df = spark.createDataFrame(rows, cols)
    out = conform_employees(df)
    assert out.count() == 1
    assert out.collect()[0]["base_salary"] == 120000.0