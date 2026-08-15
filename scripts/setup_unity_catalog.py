"""Create the Unity Catalog objects + PII tags. Run once in the workspace."""
import yaml


def setup(spark):
    policy = yaml.safe_load(open("config/pii_policy.yaml"))
    spark.sql("CREATE CATALOG IF NOT EXISTS reconguard")
    for schema in ("bronze", "silver", "gold", "audit"):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS reconguard.{schema}")
    for entry in policy["sensitive_columns"]:
        col, tag = entry["column"], entry["tag"]
        # applied per table once tables exist:
        # ALTER TABLE reconguard.bronze.hris ALTER COLUMN <col> SET TAGS ('pii'='true')
        print(f"Tag intent: {col} -> {tag}")