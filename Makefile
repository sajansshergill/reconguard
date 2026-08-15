.PHONY: setup generate test lint run dashboard-setup dashboard clean

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

dashboard-setup:
	pip install -r dashboard/requirements.txt

dashboard:
	streamlit run dashboard/app.py

clean:
	rm -rf data/ spark-warehouse/ metastore_db/ derby.log