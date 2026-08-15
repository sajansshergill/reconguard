# Architecture

## Data flow

```
        Source systems (simulated)
        ┌─────────────┐   ┌──────────────┐
        │ HRIS extract│   │ Payroll extr.│
        └──────┬──────┘   └──────┬───────┘
               │                 │
        ┌──────▼─────────────────▼───────┐
        │  Azure Data Factory (orchestr.) │
        └──────┬─────────────────────────┘
               │
   ┌───────────▼───────────────────────────────────┐
   │        Azure Databricks — Delta Lake           │
   │                                                 │
   │   Bronze ──▶ Silver ──▶ Gold                    │
   │     │          │          │                     │
   │  [ingest    [transform  [reporting              │
   │   checks]    checks]     checks]                │
   │                                                 │
   │        Unity Catalog (governance / lineage)     │
   └───────────┬─────────────────────────────────────┘
               │
        ┌──────▼──────┐        ┌───────────────────┐
        │  Power BI   │◀───────│ Report validation │
        └─────────────┘        └───────────────────┘

        Everything gated by ▶ Azure DevOps CI/CD
```

## Component walkthrough

### Source generation — `data_generator/`
`generate.py` is the entry point. It calls `hris_source.build_employees()` and
`payroll_source.build_payroll()` to produce a clean, internally-consistent
employee master and payroll run (both seeded, so runs are reproducible), then
`break_injector.inject()` deliberately corrupts the pair — dropping payroll
rows, adding orphan payroll rows, perturbing `gross_pay` beyond tolerance, and
duplicating HRIS employees with a stale effective-dated record. `schemas.py`
defines the column lists and Spark `StructType`s shared by the generator, the
bronze ingest jobs, and the tests, so the "contract" for each source lives in
one place.

### Bronze — `pipelines/bronze/`
`ingest_hris.py` / `ingest_payroll.py` read the raw CSVs against the explicit
schema from `schemas.py` and write them straight to Delta, unmodified — bronze
is a faithful, schema-enforced copy of the source. `dlt_bronze.py` is the
Databricks-native equivalent, expressed as Delta Live Tables with
`@dlt.expect` / `@dlt.expect_or_drop` decorators that enforce the same
contract declaratively (non-null `employee_id`, non-null `base_salary`,
positive `gross_pay`) and Databricks-emitted for free.

### Silver — `pipelines/silver/`
`conform_employees.py` resolves the effective-dated HRIS rows down to one
current record per employee (`ROW_NUMBER() OVER (PARTITION BY employee_id
ORDER BY effective_date DESC)`), and derives `expected_gross =
base_salary / 12`, which is what the reconciliation engine compares payroll
against. `conform_payroll.py` filters to the pay period being reconciled and
drops duplicate `(employee_id, pay_period)` rows. `dlt_silver.py` mirrors both
as DLT tables with `@dlt.expect_or_fail` / `@dlt.expect` business-rule
expectations.

### Gold — `pipelines/gold/`
`headcount_by_dept.py` and `payroll_summary.py` are the reporting aggregates
exposed downstream. Both are PII-free by construction — `national_id` and
`bank_account` never appear in a gold `select`, and `validation/pii/
mask_checks.py` asserts that in CI so a future refactor can't reintroduce
them silently. `dlt_gold.py` is the DLT-native equivalent, reading from the
DLT silver tables via `dlt.read(...)`.

### Validation layer — `validation/`
This is the actual subject of the project; the pipeline above exists to give
it something to validate. See [reconciliation_design.md](reconciliation_design.md)
for the reconciliation engine specifically. The other three checks:
- `expectations/` — schema/freshness/completeness gates on bronze
  (`ingestion_checks.py`), thresholds loaded from `config/expectations.yaml`
  (`thresholds.py`).
- `pii/` — `tag_checks.py` verifies sensitive columns carry the governance tag
  declared in `config/pii_policy.yaml` (against a manifest locally, against
  Unity Catalog's `information_schema.column_tags` on Databricks);
  `mask_checks.py` asserts PII columns never reach gold; `lineage.py` emits a
  source→report lineage map.
- `reporting/` — `report_reconcile.py` compares the gold Delta tables against
  the report layer (`xmla_client.py` queries Power BI over XMLA on Azure; the
  local path re-aggregates from silver as a stand-in for the report query, see
  [azure_service_mapping.md](azure_service_mapping.md)).

### Dashboard — `dashboard/`
A Streamlit UI over the Delta tables `scripts/run_local.py` writes — the
local stand-in for the Power BI report layer described above, not a
pipeline stage itself (nothing in `pipelines/` or `validation/` depends on
it). `data.py` reads the tables directly via `deltalake` (delta-rs) rather
than through Spark, so the app opens without paying Spark's session-startup
cost, and doesn't require PySpark to be installed at all just to view it;
`charts.py` builds the Plotly figures; `theme.py` holds the design tokens
(dark-mode palette, CSS); `app.py` wires it into KPI tiles, a break-trend
chart, a filterable break-detail table, the PII/governance panel, and
workforce/payroll charts.

Its sidebar can trigger a real pipeline run as a subprocess (`scripts/
run_local.py`) when PySpark *is* available — locally, or self-hosted.
When it isn't (a Streamlit Community Cloud deploy, whose free tier can't
reliably run a JVM-backed Spark session), `app.py` detects the missing
`pyspark` import, disables those buttons, and `data.py` falls back to a
static snapshot committed at `dashboard/sample_data/` — the same schema,
generated by the same code, just frozen — instead of the gitignored `data/`
a real run produces. See [gaps.md](gaps.md).

### Orchestration — `adf/`
`pipeline_reconguard.json` defines a two-activity ADF pipeline:
`IngestBronze` runs the `dlt_bronze` Databricks notebook, then
`RunValidationGate` runs after it succeeds. `daily_trigger.json` schedules it;
`linkedservices/` holds the Databricks and storage connections ADF needs.

### CI/CD — `.azure-pipelines/`
`ci.yml` runs on every commit to `main`: install deps, `ruff check .`, then
the shared `run-pytest.yml` template (pytest with JUnit output, published as
a test result). `validation-gate.yml` is the promotion gate: it runs
`scripts/run_local.py` — the full generate → bronze → silver → reconcile →
gold → PII-check flow — before running the same test template, so a failing
reconciliation or a leaked PII column fails the pipeline, not just a unit
test.

### Entry points — `scripts/`
`run_local.py` runs the entire flow against local OSS Delta + Spark: generate
data, ingest to bronze, conform to silver, reconcile, write the audit tables,
print the break summary, build the gold aggregate, and check it for PII. It's
what both a developer (`make run`) and the CI validation gate invoke.
`setup_unity_catalog.py` is Azure-only — run once against a real workspace to
create the catalog/schemas and print the column-tagging intent from
`config/pii_policy.yaml` (the actual `ALTER TABLE ... SET TAGS` statements are
applied per table once it exists, as noted in the script).
