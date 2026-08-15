"""Assert PII columns never reach gold in cleartext. Runs anywhere."""


def check_no_pii_in_gold(gold_df, excluded: list[str]) -> dict:
    leaked = [c for c in excluded if c in gold_df.columns]
    return {"check": "no_pii_in_gold", "passed": not leaked, "leaked": leaked}