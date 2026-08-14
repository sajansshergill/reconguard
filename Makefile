.PHONY: setup generate test lint run clean

setup:
	pip install -r requirements.txt

generate:
	python -m data_generator.generate

test:
	pytest

lint:
	ruff check .

run:
	python scripts/run_local.py

clean:
	rm -rf data/ spark-warehouse/ metastore_db/ derby.log