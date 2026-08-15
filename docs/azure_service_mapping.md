# Azure service mapping

ReconGuard runs two ways: against a real Azure workspace (Option A in the
README — the visual proof) or fully locally on open-source Delta + Spark
(Option B — what CI actually runs). This table is the per-feature mapping
between the two, and which files implement each side.

| Feature                     | Azure (Option A)                                                          | Local (Option B)                                                                 |
|------------------------------|----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Compute                      | Azure Databricks cluster                                                    | Local Spark (`pyspark`, `local[2]`) — see `tests/conftest.py`, `scripts/run_local.py` |
| Storage                      | ADLS Gen2 / Databricks Volumes (`/Volumes/reconguard/landing/raw`, see `dlt_bronze.py`) | Local filesystem, paths from `config/settings.yaml: paths` (`./data/...`)          |
| Bronze/Silver/Gold pipelines | Delta Live Tables — `pipelines/*/dlt_*.py`, deployed as a DLT pipeline       | Plain PySpark functions — `pipelines/bronze/ingest_*.py`, `pipelines/silver/conform_*.py`, `pipelines/gold/*.py`, called directly from `scripts/run_local.py` |
| Ingestion/transform quality gates | `@dlt.expect` / `@dlt.expect_or_drop` / `@dlt.expect_or_fail` decorators, enforced by the DLT runtime | `validation/expectations/ingestion_checks.py`, called explicitly against the same DataFrames |
| Governance (tagging, masking) | Unity Catalog `information_schema.column_tags`, real masking policies — `tag_checks.check_tags_unity()` | A governance *manifest* — `{column: tag}` you intend to apply — checked by `tag_checks.check_tags_local()`. Proves the check logic; doesn't prove enforcement, since there's no real Unity Catalog locally |
| Catalog/schema creation       | `scripts/setup_unity_catalog.py`, run once against the workspace (`CREATE CATALOG` / `CREATE SCHEMA`, prints tagging intent) | N/A — local Delta tables are just paths on disk, no catalog layer |
| Orchestration                 | Azure Data Factory — `adf/pipeline_reconguard.json` runs `dlt_bronze` then a validation-gate notebook, triggered daily (`adf/triggers/daily_trigger.json`) | `scripts/run_local.py`, run directly or via `make run` / the CI validation gate |
| Report-layer validation       | `validation/reporting/xmla_client.py` queries the Power BI dataset over XMLA/DAX (`pyadomd`), compared against gold in `report_reconcile.py` | `report_reconcile.reconcile_report_local()` re-aggregates from silver as a stand-in for the report query — proves the comparison logic without a Power BI workspace |
| CI/CD enforcement              | Same Azure DevOps pipelines (`.azure-pipelines/`), pointed at the real workspace via pipeline variables | Same pipelines, running everything through `scripts/run_local.py` against local Delta — this is what actually executes today |

## Why both paths exist

The local path is what's testable without an Azure subscription, and it's
what CI runs on every commit — the reconciliation engine, the ingestion/
transform expectations, and the PII-in-gold check all exercise real logic
against real (generated) data, not mocks. The Azure path is what a reviewer
would spin up to see Unity Catalog tags, DLT pipeline graphs, and a Power BI
report actually running — see the README's "Getting started → Option A" for
the setup steps. Neither path is a fake stand-in for the other: the local
path validates the same assertions the Azure path would, just against OSS
Delta instead of Unity Catalog and a silver re-aggregation instead of a live
Power BI dataset. The two things that are *only* provable on Azure are:
Unity Catalog actually enforcing a masking policy at query time, and the
Power BI dataset actually agreeing (or disagreeing) with gold — both require
a live workspace to observe, not just a manifest or a re-aggregation.

## `config/settings.yaml: environment`

`settings.yaml` has an `environment: local | azure` flag with a parallel
`paths` block for local mode. Nothing in the codebase currently branches on
`environment` — it's a placeholder for wiring an Azure-mode path (Unity
Catalog table references instead of local FS paths) into the same
`scripts/run_local.py`-style entry point, rather than a second entry point
per environment. Today, running against Azure means running the DLT
pipeline in the workspace directly rather than switching this flag.
