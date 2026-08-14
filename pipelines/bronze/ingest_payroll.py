"""Raw payroll CSV -> bronze Delta table."""
from data_generator.schemas import PAYROLL_SCHEMA


def ingest_payroll(spark, raw_path: str, bronze_path: str):
    df = spark.read.csv(raw_path, header=True, schema=PAYROLL_SCHEMA)
    df.write.format("delta").mode("overwrite").save(bronze_path)
    return df
