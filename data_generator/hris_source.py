"""Generate a clean HRIS employee master, effective-dated."""
import random
from datetime import date
from faker import Faker

fake = Faker()
DEPARTMENTS = ["Engineering", "Finance", "Sales", "Operations", "HR"]


def build_employees(n: int, seed: int = 42) -> list[dict]:
    random.seed(seed)
    Faker.seed(seed)
    employees = []
    for i in range(1, n + 1):
        emp_id = f"E{i:05d}"
        salary = round(random.uniform(48_000, 180_000), 2)
        employees.append({
            "employee_id": emp_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department": random.choice(DEPARTMENTS),
            "national_id": fake.ssn(),
            "base_salary": salary,
            "effective_date": date(2026, 1, 1),
            "is_current": True,
        })
    return employees