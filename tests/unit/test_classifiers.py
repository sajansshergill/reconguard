from validation.reconciliation.engine import reconcile, summarize


def test_all_break_types(spark):
    payroll = spark.createDataFrame(
        [("E1", 1000.0), ("E2", 1200.0), ("E3", 900.0)],  # E3 orphan (missing_left)
        ["employee_id", "gross_pay"])
    hris = spark.createDataFrame(
        [("E1", 1000.0), ("E2", 1150.0), ("E4", 800.0)],  # E4 missing_left side absent
        ["employee_id", "expected_gross"])

    result = reconcile(payroll, hris, "employee_id",
                       "gross_pay", "expected_gross", tolerance=1.0)
    s = summarize(result)
    assert s["matched"] == 1          # E1
    assert s["value_mismatch"] == 1   # E2 (1000 vs 1150)
    assert s["missing_left"] == 1     # E3 in payroll only
    assert s["missing_right"] == 1    # E4 in hris only