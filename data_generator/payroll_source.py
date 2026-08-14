"""Generate a clean payroll run derived from the HRIS master."""
from datetime import date
from faker import Faker

fake = Faker()


def build_payroll(employees: list[dict], pay_period: str = "2026-07",
                  seed: int = 42) -> list[dict]:
    Faker.seed(seed)
    rows = []
    for emp in employees:
        gross = round(emp["base_salary"] / 12, 2)
        net = round(gross * 0.72, 2)
        rows.append({
            "employee_id": emp["employee_id"],
            "pay_period": pay_period,
            "gross_pay": gross,
            "net_pay": net,
            "bank_account": fake.iban(),
            "run_date": date(2026, 7, 28),
        })
    return rows