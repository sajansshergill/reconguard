from data_generator.hris_source import build_employees
from data_generator.payroll_source import build_payroll
from data_generator.break_injector import inject


def test_injector_creates_defects():
    emp = build_employees(50)
    pay = build_payroll(emp)
    hris_out, pay_out = inject(emp, pay)

    emp_ids = {e["employee_id"] for e in emp}
    orphans = [r for r in pay_out if r["employee_id"] not in emp_ids]
    dupes = len(hris_out) - len({e["employee_id"] for e in hris_out})

    assert orphans, "expected orphan payroll rows (missing_left)"
    assert dupes >= 1, "expected duplicated effective-dated HRIS rows"
    assert len(pay_out) != len(pay), "expected dropped/added payroll rows"