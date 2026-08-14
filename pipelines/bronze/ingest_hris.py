"""Raw HRIS CSV -> bronze Delta table."""
from data_generator.schemas import HRIS_SCHEMA


def ingest_hris(spark, raw_path: str, bronze_path: str):
    df = spark.read.csv(raw_path, header=True, schema=HRIS_SCHEMA)
    df.write.format("delta").mode("overwrite").save(bronze_path)
    return df
