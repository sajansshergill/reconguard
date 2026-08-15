import pytest
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    builder = (SparkSession.builder.appName("reconguard-tests").master("local[2]")
               .config("spark.sql.extensions",
                       "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog",
                       "org.apache.spark.sql.delta.catalog.DeltaCatalog")
               .config("spark.sql.shuffle.partitions", "2"))
    s = configure_spark_with_delta_pip(builder).getOrCreate()
    yield s
    s.stop()