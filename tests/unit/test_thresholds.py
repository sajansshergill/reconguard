from validation.expectations.thresholds import load_expectations


def test_expectations_load():
    cfg = load_expectations()
    assert cfg["freshness_days"] >= 0
    assert "hris" in cfg["required_columns"]