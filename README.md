# ReconGuard

**An Azure-native data quality & validation platform for lakehouse pipelines.**

ReconGuard sits on top of a Databricks medallion pipeline and validates every hop —— ingestion, transformation, reconciliation, and the reporting layer —— with results gated in CI/CD. The pipeline itself is scaffolding. The validation layer is the product. 

Most data pipelines treat testing as few spot-check queries run by hand. ReconGuard treats data validation the way you'd treat application test coverage: reusable, parameterized, versioned, and enforced by a pipeline that refuses to promote data that fails.

## Why this exists
Enterprise data breaks silently. An HRIS export and a payroll export disagree on headcount, a transformation drops effective-dated rows, a masked column loses its mask after a refactor, and a Power BI report keeps rendering a number that no longer matches its source. None of these throw and error. They just quietly become wrong.

ReconGuard is built to catch each of those failure modes automatically, on every run, before the data reaches a dashboard. 
