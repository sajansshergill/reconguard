"""The generated dataset's fixed "today" — it doesn't age, so freshness
checks anchor against this instead of date.today(). Deliberately dependency-
free (no pyspark) so both the Spark ingestion checks and the Spark-free
dashboard can import it without pulling in PySpark."""
from datetime import date

SIM_TODAY = date(2026, 7, 28)
