"""Entry point: writes both raw source extracts as CSV under data/raw/."""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.hris_source import build_employees
from data_generator.payroll_source import build_payroll
from data_generator.break_injector import inject
from data_generator.schemas import HRIS_COLUMNS, PAYROLL_COLUMNS

RAW_DIR = os.environ.get("LOCAL_DATA_DIR", "./data") + "/raw"
# Override to vary the generated data across runs (e.g. to build up a
# demo-able history of distinct reconciliation runs). Leave unset for the
# default, reproducible dataset that the test suite is written against.
SEED = os.environ.get("LOCAL_DATA_SEED")


def _write_csv(path: str, columns: list[str], rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main(n_employees: int = 200) -> None:
    if SEED is not None:
        seed = int(SEED)
        employees = build_employees(n_employees, seed=seed)
        payroll = build_payroll(employees, seed=seed)
        hris_rows, payroll_rows = inject(employees, payroll, seed=seed)
    else:
        employees = build_employees(n_employees)
        payroll = build_payroll(employees)
        hris_rows, payroll_rows = inject(employees, payroll)

    _write_csv(f"{RAW_DIR}/hris.csv", HRIS_COLUMNS, hris_rows)
    _write_csv(f"{RAW_DIR}/payroll.csv", PAYROLL_COLUMNS, payroll_rows)
    print(f"Wrote {len(hris_rows)} HRIS rows and {len(payroll_rows)} payroll rows to {RAW_DIR}")


if __name__ == "__main__":
    main()
