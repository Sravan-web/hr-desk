"""
payroll_engine.py — Indian payroll: PF, ESI, PT, TDS, LOP, overtime.
"""
from datetime import date, datetime
from calendar import monthrange
from typing import Optional
from sqlalchemy.orm import Session
from database import Employee, PayrollRecord, Attendance

STANDARD_DEDUCTION = 50000
NEW_REGIME_SLABS = [
    (300000, 0.0), (600000, 0.05), (900000, 0.10),
    (1200000, 0.15), (1500000, 0.20), (float("inf"), 0.30),
]

def calculate_income_tax(annual_taxable: float, regime: str = "NEW") -> float:
    slabs = NEW_REGIME_SLABS if regime == "NEW" else [
        (250000, 0.0), (500000, 0.05), (1000000, 0.20), (float("inf"), 0.30)
    ]
    tax, prev = 0.0, 0.0
    for limit, rate in slabs:
        if annual_taxable <= prev:
            break
        tax += (min(annual_taxable, limit) - prev) * rate
        prev = limit
    if regime == "NEW" and annual_taxable <= 700000:
        tax = max(0, tax - 25000)
    return round(tax * 1.04, 2)

def get_professional_tax(monthly_gross: float) -> float:
    if monthly_gross <= 15000: return 0.0
    elif monthly_gross <= 20000: return 150.0
    return 200.0

def calculate_pf(basic: float) -> dict:
    base = min(basic, 15000)
    return {"employee": round(base * 0.12, 2), "employer": round(base * 0.12, 2)}

def calculate_esi(gross: float) -> dict:
    if gross > 21000: return {"employee": 0.0, "employer": 0.0}
    return {"employee": round(gross * 0.0075, 2), "employer": round(gross * 0.0325, 2)}

def get_attendance_summary(db: Session, employee_id: int, month: int, year: int) -> dict:
    _, total_days = monthrange(year, month)
    working_days = sum(1 for d in range(1, total_days + 1) if date(year, month, d).weekday() < 5)
    records = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date >= date(year, month, 1),
        Attendance.date <= date(year, month, total_days),
    ).all()
    present = sum(1 for r in records if r.status in ("PRESENT", "WORK_FROM_HOME"))
    half_day = sum(0.5 for r in records if r.status == "HALF_DAY")
    on_leave = sum(1 for r in records if r.status == "ON_LEAVE")
    overtime_hours = sum(r.overtime_hours or 0 for r in records)
    present_days = present + half_day
    absent_days = max(0, working_days - present_days - on_leave)
    return {"working_days": working_days, "present_days": present_days,
            "absent_days": absent_days, "leave_days": on_leave,
            "overtime_hours": overtime_hours, "lop_days": absent_days}

def process_payroll(db: Session, employee: Employee, month: int, year: int,
                    bonus: float = 0.0, incentives: float = 0.0,
                    loan_deduction: float = 0.0, other_deductions: float = 0.0,
                    overtime_rate: float = 1.5, processed_by_id: Optional[int] = None) -> PayrollRecord:
    pay_period = f"{year}-{month:02d}"
    existing = db.query(PayrollRecord).filter(
        PayrollRecord.employee_id == employee.id,
        PayrollRecord.pay_period == pay_period).first()
    att = get_attendance_summary(db, employee.id, month, year)
    working_days = att["working_days"]
    per_day = employee.base_salary / working_days if working_days > 0 else 0
    basic = round(employee.base_salary - (per_day * att["lop_days"]), 2)
    hourly = (employee.base_salary / working_days / 8) if working_days > 0 else 0
    overtime_pay = round(att["overtime_hours"] * hourly * overtime_rate, 2)
    gross = round(basic + (employee.hra or 0) + (employee.da or 0) +
                  (employee.ta or 0) + (employee.special_allowance or 0) +
                  overtime_pay + bonus + incentives, 2)
    pf = calculate_pf(basic)
    esi = calculate_esi(gross)
    pt = get_professional_tax(gross)
    annual_taxable = max(0, gross * 12 - STANDARD_DEDUCTION - pf["employee"] * 12)
    monthly_tds = round(calculate_income_tax(annual_taxable) / 12, 2)
    total_deductions = round(pf["employee"] + esi["employee"] + pt + monthly_tds + loan_deduction + other_deductions, 2)
    net_salary = round(gross - total_deductions, 2)
    rec = existing or PayrollRecord(employee_id=employee.id, month=month, year=year, pay_period=pay_period)
    rec.basic_salary = basic; rec.hra = employee.hra or 0; rec.da = employee.da or 0
    rec.ta = employee.ta or 0; rec.special_allowance = employee.special_allowance or 0
    rec.overtime_pay = overtime_pay; rec.bonus = bonus; rec.incentives = incentives
    rec.gross_earnings = gross; rec.pf_employee = pf["employee"]; rec.pf_employer = pf["employer"]
    rec.esi_employee = esi["employee"]; rec.esi_employer = esi["employer"]
    rec.professional_tax = pt; rec.income_tax_tds = monthly_tds
    rec.loan_deduction = loan_deduction; rec.other_deductions = other_deductions
    rec.total_deductions = total_deductions; rec.net_salary = net_salary
    rec.working_days = working_days; rec.present_days = att["present_days"]
    rec.absent_days = att["absent_days"]; rec.leave_days = att["leave_days"]
    rec.overtime_hours = att["overtime_hours"]; rec.lop_days = att["lop_days"]
    rec.status = "PROCESSED"; rec.processed_by = processed_by_id; rec.processed_at = datetime.utcnow()
    if not existing: db.add(rec)
    db.commit(); db.refresh(rec)
    return rec

def generate_payslip_data(record: PayrollRecord, employee: Employee) -> dict:
    dept = employee.department_rel
    return {
        "employee": {"id": employee.employee_id, "name": employee.full_name,
                     "designation": employee.job_title,
                     "department": dept.name if dept else "N/A",
                     "pan": employee.pan_number or "N/A",
                     "uan": employee.uan_number or "N/A",
                     "bank_account": employee.bank_account or "N/A",
                     "bank_name": employee.bank_name or "N/A"},
        "period": {"month": record.month, "year": record.year, "pay_period": record.pay_period,
                   "payment_date": record.payment_date.isoformat() if record.payment_date else None},
        "attendance": {"working_days": record.working_days, "present_days": record.present_days,
                       "absent_days": record.absent_days, "leave_days": record.leave_days,
                       "overtime_hours": record.overtime_hours, "lop_days": record.lop_days},
        "earnings": {"basic_salary": record.basic_salary, "hra": record.hra, "da": record.da,
                     "ta": record.ta, "special_allowance": record.special_allowance,
                     "overtime_pay": record.overtime_pay, "bonus": record.bonus,
                     "incentives": record.incentives, "gross_earnings": record.gross_earnings},
        "deductions": {"pf_employee": record.pf_employee, "pf_employer": record.pf_employer,
                       "esi_employee": record.esi_employee, "esi_employer": record.esi_employer,
                       "professional_tax": record.professional_tax,
                       "income_tax_tds": record.income_tax_tds,
                       "loan_deduction": record.loan_deduction,
                       "other_deductions": record.other_deductions,
                       "total_deductions": record.total_deductions},
        "net_salary": record.net_salary, "status": record.status,
    }
