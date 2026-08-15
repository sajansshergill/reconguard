"""Persist reconciliation results + run metadata to a Delta audit table."""
import uuid
from datetime import datetime
from pyspark.sql import functions as F


def write_audit(spark, result_df, summary: dict, pay_period: str,
                audit_path: str):
    run_id = str(uuid.uuid4())
    run_ts = datetime.utcnow().isoformat()

    # detail: every classified row, stamped with the run
    detail = (result_df
              .withColumn("run_id", F.lit(run_id))
              .withColumn("run_ts", F.lit(run_ts))
              .withColumn("pay_period", F.lit(pay_period)))
    detail.write.format("delta").mode("append").save(f"{audit_path}/reconciliation_detail")

    # summary: one row per run
    summary_row = [{
        "run_id": run_id, "run_ts": run_ts, "pay_period": pay_period, **summary,
    }]
    (spark.createDataFrame(summary_row)
        .write.format("delta").mode("append").save(f"{audit_path}/reconciliation_summary"))
    return run_id