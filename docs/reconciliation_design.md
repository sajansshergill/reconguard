# Reconciliation design

The reconciliation engine (`validation/reconciliation/engine.py` +
`classifiers.py`) is the centerpiece of the project: a parameterized,
domain-agnostic full-outer-join comparison that classifies every row into
exactly one break type. It's deliberately framework code — nothing in
`engine.py` or `classifiers.py` knows about payroll or HRIS; that knowledge
lives entirely in `config/reconciliation_rules.yaml` and in how
`scripts/run_local.py` calls `reconcile()`.

## Convention

Throughout the engine and classifiers, **left = payroll, right = hris**. This
is fixed by convention (not inferred), which is what lets `missing_left` /
`missing_right` mean the same thing on every run regardless of argument
order at the call site — `missing_left` always means "in payroll, absent
from HRIS" and `missing_right` always means "in HRIS, absent from payroll".

## Break taxonomy

| Break type       | Condition                                              | Meaning                                            |
|------------------|----------------------------------------------------------|-----------------------------------------------------|
| `matched`        | both sides present, `abs(left_value - right_value) <= tolerance` | present and equal (within tolerance) in both systems |
| `value_mismatch` | both sides present, difference exceeds tolerance          | present in both, disagreeing value (e.g. gross pay)   |
| `missing_left`   | present in payroll, key absent from HRIS                  | orphan payroll row — no employee record backs it      |
| `missing_right`  | present in HRIS, key absent from payroll                  | employee with no payroll row for the period            |

## How it works

1. `reconcile(left_df, right_df, key, left_value_col, right_value_col, tolerance)`
   selects `key` and the value column from each side, aliasing to
   `l_key`/`left_value` and `r_key`/`right_value` so both sides can carry
   independent nulls through the join.
2. A `full_outer` join on `l_key == r_key` means every row from both sides
   survives — a payroll-only row has a null `r_key`/`right_value`, an
   HRIS-only row has a null `l_key`/`left_value`, and a row present in both
   has neither.
3. `classifiers.break_type_expr()` is pure column-expression logic (a
   `pyspark.sql.Column`, not executed until the join is evaluated) that
   turns "which sides are null, and how far apart are the values" into one
   of the four break-type strings via a `CASE WHEN` chain (`F.when(...)`).
4. `reconcile()` returns one row per key with `left_value`, `right_value`,
   and `break_type` — the full detail, not just a count.
5. `summarize()` aggregates that into a `{break_type: count}` dict,
   zero-filled for every category in `BREAK_TYPES` so a run with zero
   mismatches still reports `value_mismatch: 0` rather than omitting the key
   (important for a caller that trends counts over time without having to
   handle a missing dict key).

## Configuration — `config/reconciliation_rules.yaml`

```yaml
key: employee_id
pay_period: "2026-07"
left_value_col: gross_pay          # actual, from payroll
right_value_col: expected_gross    # base_salary / 12, derived on hris side
tolerance: 1.00                    # absolute currency tolerance
```

`expected_gross` isn't a payroll or HRIS source column — it's derived in
`pipelines/silver/conform_employees.py` (`base_salary / 12`, rounded) so the
reconciliation is comparing "what payroll actually paid" against "what the
employee master says they should have been paid," which is the real-world
question this check exists to answer. Tolerance is an absolute currency
amount (not a percentage) because payroll rounding differences are small and
constant in magnitude, not proportional to salary.

## Output

`validation/reconciliation/report.py` turns a summary dict into a
human-readable block (total compared, a line per break type, and a total
break count), and `audit_writer.py` persists both the per-run summary and the
full per-row detail to Delta (see [data_model.md](data_model.md) for the
audit table schemas) so every run is queryable and trended, not just printed
to a CI log and discarded.

## Extending it

Because the engine takes `key`, `left_value_col`, `right_value_col`, and
`tolerance` as parameters rather than hardcoding `employee_id`/`gross_pay`,
reconciling a different pair of columns (or a different pair of datasets
entirely) is a config change, not a code change — point `reconcile()` at two
other DataFrames and two other column names. Multi-column reconciliation
(comparing more than one value column per key in a single pass) isn't
implemented; today each call to `reconcile()` compares exactly one value pair
per key.
