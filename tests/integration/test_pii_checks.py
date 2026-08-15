from pipelines.gold.payroll_summary import payroll_summary
from validation.pii.mask_checks import check_no_pii_in_gold
from data_generator.schemas import PAYROLL_SCHEMA


def test_gold_has_no_pii(spark):
    rows = [("E1", "2026-07", 1000.0, 720.0, "GB00X", None)]
    df = spark.createDataFrame(
        [tuple(r) for r in rows],
        PAYROLL_SCHEMA)
    gold = payroll_summary(df)
    result = check_no_pii_in_gold(gold, ["bank_account", "national_id"])
    assert result["passed"], result