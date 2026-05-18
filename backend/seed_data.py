"""
seed_data.py — populate DB with demo data.
Run: python seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta
import random
from database import (
    Base, engine, SessionLocal,
    Department, Employee, Attendance, LeaveRequest, PayrollRecord,
    BenefitPlan, EmployeeBenefit, Holiday, Announcement,
    QueryLog, EscalationTicket,
)
from auth import hash_password
from payroll_engine import process_payroll

db = SessionLocal()

def seed():
    print("Seeding database...")

    # Departments
    depts_data = [
        ("Engineering","ENG"), ("Human Resources","HR"), ("Finance","FIN"),
        ("Marketing","MKT"), ("Operations","OPS"), ("Sales","SAL"),
    ]
    depts = {}
    for name, code in depts_data:
        d = db.query(Department).filter(Department.code == code).first()
        if not d:
            d = Department(name=name, code=code)
            db.add(d); db.flush()
        depts[code] = d
    db.commit()
    print(f"  {len(depts)} departments")

    # Benefit Plans
    plans_data = [
        ("Group Health Insurance","HEALTH","Star Health",500,2000,True),
        ("Provident Fund","PF","EPFO",0,0,True),
        ("Employee State Insurance","ESI","ESIC",0,0,True),
        ("Group Life Insurance","LIFE","LIC",200,800,False),
        ("Gratuity","GRATUITY","Internal",0,0,True),
    ]
    for name, btype, provider, ec, erc, mandatory in plans_data:
        if not db.query(BenefitPlan).filter(BenefitPlan.name == name).first():
            db.add(BenefitPlan(name=name, type=btype, provider=provider,
                               employee_contribution=ec, employer_contribution=erc,
                               is_mandatory=mandatory))
    db.commit()

    # Employees
    emp_data = [
        ("EMP-001","Sravan","Kumar","sravan@hrdesk.com","ENG","Senior Software Engineer",120000,"ADMIN"),
        ("EMP-002","Priya","Sharma","priya@hrdesk.com","HR","HR Manager",95000,"HR_MANAGER"),
        ("EMP-003","Rahul","Verma","rahul@hrdesk.com","ENG","Software Engineer",85000,"EMPLOYEE"),
        ("EMP-004","Anita","Patel","anita@hrdesk.com","FIN","Finance Analyst",80000,"EMPLOYEE"),
        ("EMP-005","Vikram","Singh","vikram@hrdesk.com","MKT","Marketing Lead",90000,"MANAGER"),
        ("EMP-006","Deepa","Nair","deepa@hrdesk.com","OPS","Operations Manager",88000,"MANAGER"),
        ("EMP-007","Arjun","Mehta","arjun@hrdesk.com","ENG","DevOps Engineer",92000,"EMPLOYEE"),
        ("EMP-008","Kavya","Reddy","kavya@hrdesk.com","SAL","Sales Executive",65000,"EMPLOYEE"),
        ("EMP-009","Suresh","Iyer","suresh@hrdesk.com","FIN","Senior Accountant",78000,"EMPLOYEE"),
        ("EMP-010","Meera","Joshi","meera@hrdesk.com","HR","HR Executive",60000,"EMPLOYEE"),
    ]
    employees = {}
    for eid, fn, ln, email, dept, title, base, role in emp_data:
        e = db.query(Employee).filter(Employee.employee_id == eid).first()
        if not e:
            hra = round(base * 0.40, 2)
            da = round(base * 0.10, 2)
            ta = 3000.0
            special = max(0, round(base * 0.05, 2))
            e = Employee(
                employee_id=eid, first_name=fn, last_name=ln, email=email,
                phone=f"+91-9{random.randint(100000000,999999999)}",
                date_of_birth=date(1990+random.randint(0,8), random.randint(1,12), random.randint(1,28)),
                gender=random.choice(["Male","Female"]),
                department_id=depts[dept].id,
                job_title=title, date_of_joining=date(2020+random.randint(0,4), random.randint(1,12), 1),
                base_salary=base, hra=hra, da=da, ta=ta, special_allowance=special,
                gross_salary=base+hra+da+ta+special,
                pan_number=f"ABCDE{random.randint(1000,9999)}F",
                uan_number=f"10{random.randint(10000000000,99999999999)}",
                bank_account=f"{random.randint(10000000000,99999999999)}",
                bank_name=random.choice(["HDFC Bank","SBI","ICICI Bank","Axis Bank"]),
                ifsc_code=f"HDFC{random.randint(1000000,9999999)}",
                password_hash=hash_password("Password@123"),
                role=role,
            )
            db.add(e); db.flush()
        employees[eid] = e
    db.commit()
    print(f"  {len(employees)} employees")

    # Attendance (last 90 days)
    today = date.today()
    att_count = 0
    for emp in employees.values():
        for days_back in range(90):
            d = today - timedelta(days=days_back)
            if d.weekday() >= 5:
                continue
            if db.query(Attendance).filter(Attendance.employee_id == emp.id, Attendance.date == d).first():
                continue
            r = random.random()
            if r < 0.88:
                status = "PRESENT"
                ci = datetime.combine(d, datetime.min.time()).replace(hour=9, minute=random.randint(0,30))
                co = datetime.combine(d, datetime.min.time()).replace(hour=18, minute=random.randint(0,30))
                wh = round((co-ci).seconds/3600, 2)
                ot = max(0, wh-8)
            elif r < 0.94:
                status = "WORK_FROM_HOME"; ci = None; co = None; wh = 9.0; ot = 1.0
            elif r < 0.97:
                status = "ON_LEAVE"; ci = None; co = None; wh = 0.0; ot = 0.0
            else:
                status = "ABSENT"; ci = None; co = None; wh = 0.0; ot = 0.0
            db.add(Attendance(employee_id=emp.id, date=d, check_in=ci, check_out=co,
                              work_hours=wh, overtime_hours=ot, status=status))
            att_count += 1
    db.commit()
    print(f"  {att_count} attendance records")

    # Leave requests
    leave_count = 0
    for emp in list(employees.values())[:6]:
        if db.query(LeaveRequest).filter(LeaveRequest.employee_id == emp.id).first():
            continue
        start = today - timedelta(days=random.randint(5,30))
        end = start + timedelta(days=random.randint(1,3))
        db.add(LeaveRequest(
            employee_id=emp.id,
            leave_type=random.choice(["SICK","CASUAL","PAID"]),
            start_date=start, end_date=end,
            days_requested=float((end-start).days+1),
            reason="Personal reasons",
            status=random.choice(["APPROVED","PENDING","REJECTED"]),
        ))
        leave_count += 1
    db.commit()
    print(f"  {leave_count} leave requests")

    # Payroll (last 3 months)
    payroll_count = 0
    for emp in employees.values():
        for mb in range(1, 4):
            m = today.month - mb
            y = today.year
            if m <= 0:
                m += 12; y -= 1
            if not db.query(PayrollRecord).filter(
                PayrollRecord.employee_id == emp.id,
                PayrollRecord.pay_period == f"{y}-{m:02d}"
            ).first():
                try:
                    process_payroll(db, emp, m, y)
                    payroll_count += 1
                except Exception as ex:
                    print(f"    payroll error {emp.employee_id}: {ex}")
    print(f"  {payroll_count} payroll records")

    # Holidays
    hols = [
        ("Republic Day", date(today.year,1,26)),
        ("Holi", date(today.year,3,25)),
        ("Independence Day", date(today.year,8,15)),
        ("Gandhi Jayanti", date(today.year,10,2)),
        ("Diwali", date(today.year,10,20)),
        ("Christmas", date(today.year,12,25)),
    ]
    for name, hdate in hols:
        if not db.query(Holiday).filter(Holiday.date == hdate).first():
            db.add(Holiday(name=name, date=hdate))
    db.commit()

    # Announcements
    anns = [
        ("Q2 Appraisal Cycle Open","Performance appraisals for Q2 are now open. Complete self-assessment by end of month.","GENERAL"),
        ("Updated Leave Policy","Leave carry-forward limit is now 10 days per year.","POLICY"),
        ("May Payroll Processing","May 2025 payroll will be processed on May 28th.","PAYROLL"),
    ]
    for title, content, atype in anns:
        if not db.query(Announcement).filter(Announcement.title == title).first():
            db.add(Announcement(title=title, content=content, type=atype))
    db.commit()

    print("\nSeed complete!")
    print("Login: sravan@hrdesk.com / Password@123  (ADMIN)")
    print("Login: priya@hrdesk.com  / Password@123  (HR_MANAGER)")
    print("Login: rahul@hrdesk.com  / Password@123  (EMPLOYEE)")

if __name__ == "__main__":
    seed()
    db.close()
