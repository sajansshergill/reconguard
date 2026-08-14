"""Inject deliberate breaks so the reconciliation engine has something to catch."""
import random
import copy
from datetime import date


def inject(employees: list[dict], payroll: list[dict], seed: int = 7):
    """Returns (hris_rows, payroll_rows) with injected defects.

    Defects:
      - drop payroll rows      -> missing_right (in HRIS, not in payroll)
      - orphan payroll rows    -> missing_left  (in payroll, not in HRIS)
      - perturbed gross_pay    -> value_mismatch
      - duplicate HRIS rows    -> exercises silver dedup logic
    """
    random.seed(seed)
    hris = copy.deepcopy(employees)
    pay = copy.deepcopy(payroll)

    # 1. drop 3 payroll rows
    for _ in range(3):
        if pay:
            pay.pop(random.randrange(len(pay)))

    # 2. add 2 orphan payroll rows (no matching employee)
    for k in range(2):
        pay.append({
            "employee_id": f"E9{k:04d}",
            "pay_period": "2026-07",
            "gross_pay": 5000.0,
            "net_pay": 3600.0,
            "bank_account": "GB00ORPHAN0000000000",
            "run_date": date(2026, 7, 28),
        })

    # 3. perturb gross_pay on 4 rows beyond tolerance
    for row in random.sample(pay, min(4, len(pay))):
        row["gross_pay"] = round(row["gross_pay"] + random.uniform(50, 500), 2)

    # 4. duplicate 2 HRIS employees with a stale (superseded) record
    for emp in random.sample(hris, min(2, len(hris))):
        stale = copy.deepcopy(emp)
        stale["effective_date"] = date(2025, 1, 1)
        stale["is_current"] = False
        hris.append(stale)

    return hris, pay