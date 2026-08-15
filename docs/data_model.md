# Data model

Column definitions below follow `data_generator/schemas.py` and the
transformations in `pipelines/`. Types are given as the Spark types actually
used (`StructType` fields); in the local path these are OSS Delta tables
under `./data/<layer>/`, in the Azure path they're Unity Catalog managed
tables under `<catalog>.<schema>.<table>` (see `config/settings.yaml` for the
names, and [azure_service_mapping.md](azure_service_mapping.md) for the
local/Azure equivalence).

## Bronze

Raw extracts, schema-enforced on read, otherwise unmodified.

**`bronze.hris`** (from `ingest_hris.py` / `dlt_bronze.bronze_hris`)

| column         | type      | nullable | notes                                  |
|----------------|-----------|----------|-----------------------------------------|
| employee_id    | string    | no       | `E00001` style, primary key per record  |
| first_name     | string    | yes      |                                          |
| last_name      | string    | yes      |                                          |
| department     | string    | yes      | one of 5 fixed departments               |
| national_id    | string    | yes      | **PII** — excluded from gold             |
| base_salary    | double    | yes      | annual                                   |
| effective_date | date      | yes      | employee record is effective-dated       |
| is_current     | boolean   | yes      | most recent record per employee          |

**`bronze.payroll`** (from `ingest_payroll.py` / `dlt_bronze.bronze_payroll`)

| column       | type   | nullable | notes                          |
|--------------|--------|----------|----------------------------------|
| employee_id  | string | no       | foreign key to hris               |
| pay_period   | string | yes      | `"2026-07"` style                 |
| gross_pay    | double | yes      | for the pay period                |
| net_pay      | double | yes      | ≈ 72% of gross in generated data  |
| bank_account | string | yes      | **PII** — excluded from gold      |
| run_date     | date   | yes      | date payroll was run               |

Bronze is intentionally 1:1 with the source, including duplicate
`employee_id`s across effective-dated HRIS rows — resolving that is silver's
job, not bronze's.

## Silver

Cleaned, conformed, business-rule-enforced.

**`silver.employees`** (from `conform_employees.py` / `dlt_silver.silver_employees`)

Same columns as `bronze.hris`, filtered to one current row per
`employee_id` (highest `effective_date`), plus:

| column          | type   | notes                                    |
|-----------------|--------|-------------------------------------------|
| expected_gross  | double | `round(base_salary / 12, 2)` — the value the reconciliation engine compares payroll's `gross_pay` against |

**`silver.payroll`** (from `conform_payroll.py` / `dlt_silver.silver_payroll`)

Same columns as `bronze.payroll`, filtered to the pay period being processed
(from `config/reconciliation_rules.yaml: pay_period`) and de-duplicated on
`(employee_id, pay_period)`.

## Gold

Aggregated, report-ready, PII-free by construction (`national_id` and
`bank_account` never appear in a `select`; `validation/pii/mask_checks.py`
asserts this in CI).

**`gold.headcount_by_dept`** (from `headcount_by_dept.py`)

| column          | type   |
|-----------------|--------|
| department      | string |
| headcount       | long   |
| avg_base_salary | double |

**`gold.payroll_summary`** (from `payroll_summary.py`)

| column          | type   |
|-----------------|--------|
| pay_period      | string |
| employees_paid  | long   |
| total_gross     | double |
| total_net       | double |

(The DLT version, `dlt_gold.gold_payroll_summary`, computes `total_gross`
only — `total_net` is a local/gold-notebook-only column; see the source for
the exact field list DLT emits.)

## Audit tables

Written by `validation/reconciliation/audit_writer.write_audit()`, under
`<audit_path>/reconciliation_detail` and `<audit_path>/reconciliation_summary`
(append-only Delta).

**`audit.reconciliation_detail`** — every classified row, every run

| column     | type   | notes                                          |
|------------|--------|--------------------------------------------------|
| employee_id| string | the reconciliation key                            |
| left_value | double | payroll-side value (`gross_pay`)                  |
| right_value| double | hris-side value (`expected_gross`)                |
| break_type | string | one of `matched` / `value_mismatch` / `missing_left` / `missing_right` |
| run_id     | string | UUID, one per reconciliation run                  |
| run_ts     | string | UTC ISO timestamp of the run                      |
| pay_period | string | the pay period reconciled                          |

**`audit.reconciliation_summary`** — one row per run

| column         | type   | notes                             |
|----------------|--------|-------------------------------------|
| run_id         | string |                                     |
| run_ts         | string |                                     |
| pay_period     | string |                                     |
| matched        | long   | zero-filled count per break type   |
| value_mismatch | long   |                                     |
| missing_left   | long   |                                     |
| missing_right  | long   |                                     |

Both tables are append-only, so `reconciliation_summary` trends break counts
over time and `reconciliation_detail` lets you drill from a summary spike
back to the specific `employee_id`s that broke.
