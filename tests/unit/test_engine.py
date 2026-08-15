from validation.reconciliation.engine import reconcile, summarize, BREAK_TYPES


def test_summary_zero_filled(spark):
    payroll = spark.createDataFrame([("E1", 100.0)], ["employee_id", "gross_pay"])
    hris = spark.createDataFrame([("E1", 100.0)], ["employee_id", "expected_gross"])
    s = summarize(reconcile(payroll, hris, "employee_id",
                            "gross_pay", "expected_gross", 1.0))
    assert set(s.keys()) == set(BREAK_TYPES)
    assert s["matched"] == 1


def test_tolerance_boundary(spark):
    payroll = spark.createDataFrame([("E1", 100.5)], ["employee_id", "gross_pay"])
    hris = spark.createDataFrame([("E1", 100.0)], ["employee_id", "expected_gross"])
    s = summarize(reconcile(payroll, hris, "employee_id",
                            "gross_pay", "expected_gross", 1.0))
    assert s["matched"] == 1  # 0.5 diff within tolerance 1.0