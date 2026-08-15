"""Verify sensitive columns carry the required governance tag.

On Databricks this queries Unity Catalog information_schema. Locally it
validates against a governance manifest (the tags you *intend* to apply)."""
import yaml


def load_policy(path: str = "config/pii_policy.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def check_tags_local(manifest: dict, policy: dict) -> list[dict]:
    """manifest = {column: tag}. Returns a result per sensitive column."""
    results = []
    for entry in policy["sensitive_columns"]:
        col, tag = entry["column"], entry["tag"]
        results.append({
            "column": col,
            "expected_tag": tag,
            "passed": manifest.get(col) == tag,
        })
    return results


def check_tags_unity(spark, catalog: str, policy: dict) -> list[dict]:
    """Databricks-only: read column tags from Unity Catalog."""
    tagged = spark.sql(
        f"SELECT column_name, tag_name FROM {catalog}.information_schema.column_tags"
    )
    have = {r["column_name"]: r["tag_name"] for r in tagged.collect()}
    return [{"column": e["column"], "passed": have.get(e["column"]) == e["tag"]}
            for e in policy["sensitive_columns"]]