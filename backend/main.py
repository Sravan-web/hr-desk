"""
main.py — HR Desk Full API v2
Endpoints: Auth, Employees, Attendance, Leave, Payroll, Tax, Benefits, Reports, Chat
"""
import os, uuid
from datetime import datetime, date
from calendar import monthrange
from typing import Optional, List
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel
import httpx

from database import (
    get_db, Employee, Department, Attendance, LeaveRequest, PayrollRecord,
    TaxDeclaration, BenefitPlan, EmployeeBenefit, EmployeeDocument,
    Announcement, Holiday, QueryLog, EscalationTicket, PolicyGap,
)
import auth as auth_module
from auth import get_current_user, require_hr, require_admin, require_manager
import rag, agent
import payroll_engine

app = FastAPI(title="HR Desk API", version="2.0.0",
              docs_url="/docs" if os.getenv("ENABLE_DOCS","true")=="true" else None, redoc_url=None)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS","http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware,
                   allowed_hosts=os.getenv("ALLOWED_HOSTS","localhost,127.0.0.1,*").split(","))

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL","")

def notify_slack(ticket_id, name, priority, issue):
    if not SLACK_WEBHOOK: return
    try: httpx.post(SLACK_WEBHOOK, json={"text": f"*{ticket_id}* | {name} | {priority} | {issue}"}, timeout=5)
    except: pass

# ── Schemas ───────────────────────────────────────────────────────────────────
class LoginReq(BaseModel):
    email: str
    password: str

class EmpCreate(BaseModel):
    employee_id: str; first_name: str; last_name: str; email: str
    phone: Optional[str]=None; date_of_birth: Optional[date]=None; gender: Optional[str]=None
    department_id: Optional[int]=None; job_title: str; date_of_joining: date
    base_salary: float=0; hra: float=0; da: float=0; ta: float=3000; special_allowance: float=0
    pan_number: Optional[str]=None; uan_number: Optional[str]=None
    bank_account: Optional[str]=None; bank_name: Optional[str]=None; ifsc_code: Optional[str]=None
    role: str="EMPLOYEE"; password: str="Password@123"

class EmpUpdate(BaseModel):
    first_name: Optional[str]=None; last_name: Optional[str]=None; phone: Optional[str]=None
    department_id: Optional[int]=None; job_title: Optional[str]=None
    base_salary: Optional[float]=None; hra: Optional[float]=None; da: Optional[float]=None
    ta: Optional[float]=None; special_allowance: Optional[float]=None
    status: Optional[str]=None; role: Optional[str]=None
    pan_number: Optional[str]=None; bank_account: Optional[str]=None
    bank_name: Optional[str]=None; ifsc_code: Optional[str]=None

class AttCreate(BaseModel):
    employee_id: int; date: date
    check_in: Optional[datetime]=None; check_out: Optional[datetime]=None
    status: str="PRESENT"; shift: str="GENERAL"; notes: Optional[str]=None

class LeaveCreate(BaseModel):
    leave_type: str; start_date: date; end_date: date; reason: Optional[str]=None

class LeaveApproval(BaseModel):
    status: str; rejection_reason: Optional[str]=None

class PayrollRun(BaseModel):
    month: int; year: int
    employee_ids: Optional[List[int]]=None
    bonus_map: Optional[dict]={}; incentive_map: Optional[dict]={}

class TaxDeclCreate(BaseModel):
    financial_year: str; regime: str="NEW"
    ppf: float=0; elss: float=0; life_insurance: float=0; nsc: float=0
    home_loan_principal: float=0; tuition_fees: float=0
    medical_insurance_80d: float=0; home_loan_interest_24b: float=0; nps_80ccd: float=0

class DeptCreate(BaseModel):
    name: str; code: str; description: Optional[str]=None

class ChatReq(BaseModel):
    query: str; employee_name: str="Employee"
    employee_id: str="EMP-000"; department: str="General"

# ── Helpers ───────────────────────────────────────────────────────────────────
def ser_emp(e: Employee) -> dict:
    return {"id":e.id,"employee_id":e.employee_id,"name":e.full_name,
            "first_name":e.first_name,"last_name":e.last_name,"email":e.email,
            "phone":e.phone,"job_title":e.job_title,
            "department":e.department_rel.name if e.department_rel else None,
            "department_id":e.department_id,"status":e.status,"role":e.role,
            "date_of_joining":e.date_of_joining.isoformat() if e.date_of_joining else None,
            "base_salary":e.base_salary,"gross_salary":e.gross_salary,
            "sick_leave_balance":e.sick_leave_balance,
            "casual_leave_balance":e.casual_leave_balance,
            "paid_leave_balance":e.paid_leave_balance}

def ser_att(r: Attendance) -> dict:
    return {"id":r.id,"employee_id":r.employee_id,
            "date":r.date.isoformat(),
            "check_in":r.check_in.isoformat() if r.check_in else None,
            "check_out":r.check_out.isoformat() if r.check_out else None,
            "work_hours":r.work_hours,"overtime_hours":r.overtime_hours,
            "status":r.status,"shift":r.shift,"notes":r.notes}

def ser_leave(l: LeaveRequest) -> dict:
    return {"id":l.id,"employee_id":l.employee_id,
            "employee_name":l.employee.full_name if l.employee else None,
            "leave_type":l.leave_type,
            "start_date":l.start_date.isoformat(),"end_date":l.end_date.isoformat(),
            "days_requested":l.days_requested,"reason":l.reason,"status":l.status,
            "approved_by":l.approved_by,
            "approved_at":l.approved_at.isoformat() if l.approved_at else None,
            "rejection_reason":l.rejection_reason,
            "created_at":l.created_at.isoformat()}

def ser_pay(r: PayrollRecord) -> dict:
    return {"id":r.id,"employee_id":r.employee_id,
            "employee_name":r.employee.full_name if r.employee else None,
            "pay_period":r.pay_period,"month":r.month,"year":r.year,
            "basic_salary":r.basic_salary,"gross_earnings":r.gross_earnings,
            "total_deductions":r.total_deductions,"net_salary":r.net_salary,
            "pf_employee":r.pf_employee,"esi_employee":r.esi_employee,
            "professional_tax":r.professional_tax,"income_tax_tds":r.income_tax_tds,
            "bonus":r.bonus,"overtime_pay":r.overtime_pay,
            "working_days":r.working_days,"present_days":r.present_days,"lop_days":r.lop_days,
            "status":r.status,
            "payment_date":r.payment_date.isoformat() if r.payment_date else None}

# ── Health & Auth ─────────────────────────────────────────────────────────────
@app.get("/health")
def health(): return {"status":"healthy","version":"2.0.0","ts":datetime.utcnow().isoformat()}

@app.post("/auth/login")
def login(req: LoginReq, db: Session=Depends(get_db)):
    emp = db.query(Employee).filter(Employee.email==req.email, Employee.is_active==True).first()
    if not emp or not emp.password_hash or not auth_module.verify_password(req.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    emp.last_login = datetime.utcnow(); db.commit()
    token = auth_module.create_access_token({"sub":emp.employee_id,"role":emp.role})
    return {"access_token":token,"token_type":"bearer","employee_id":emp.employee_id,
            "name":emp.full_name,"role":emp.role,
            "department":emp.department_rel.name if emp.department_rel else None}

@app.get("/auth/me")
def me(u: Employee=Depends(get_current_user)):
    return ser_emp(u)

# ── Departments ───────────────────────────────────────────────────────────────
@app.get("/departments")
def list_depts(db: Session=Depends(get_db), _=Depends(get_current_user)):
    return [{"id":d.id,"name":d.name,"code":d.code,"description":d.description,
             "employee_count":len(d.employees)} for d in db.query(Department).filter(Department.is_active==True).all()]

@app.post("/departments", status_code=201)
def create_dept(data: DeptCreate, db: Session=Depends(get_db), _=Depends(require_hr)):
    if db.query(Department).filter(Department.code==data.code).first():
        raise HTTPException(400,"Department code exists")
    d = Department(name=data.name, code=data.code, description=data.description)
    db.add(d); db.commit(); db.refresh(d)
    return {"id":d.id,"name":d.name,"code":d.code}

# ── Employees ─────────────────────────────────────────────────────────────────
@app.get("/employees")
def list_emps(search: Optional[str]=None, department_id: Optional[int]=None,
              skip: int=0, limit: int=50,
              db: Session=Depends(get_db), _=Depends(require_hr)):
    q = db.query(Employee).filter(Employee.is_active==True)
    if department_id: q = q.filter(Employee.department_id==department_id)
    if search:
        q = q.filter((Employee.first_name.ilike(f"%{search}%")) |
                     (Employee.last_name.ilike(f"%{search}%")) |
                     (Employee.employee_id.ilike(f"%{search}%")) |
                     (Employee.email.ilike(f"%{search}%")))
    total = q.count()
    return {"total":total,"employees":[ser_emp(e) for e in q.offset(skip).limit(limit).all()]}

@app.get("/employees/me")
def my_profile(u: Employee=Depends(get_current_user)): return ser_emp(u)

@app.get("/employees/{eid}")
def get_emp(eid: int, db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    e = db.query(Employee).filter(Employee.id==eid).first()
    if not e: raise HTTPException(404,"Not found")
    if u.role=="EMPLOYEE" and u.id!=eid: raise HTTPException(403,"Access denied")
    return ser_emp(e)

@app.post("/employees", status_code=201)
def create_emp(data: EmpCreate, db: Session=Depends(get_db), _=Depends(require_hr)):
    if db.query(Employee).filter(Employee.email==data.email).first():
        raise HTTPException(400,"Email exists")
    if db.query(Employee).filter(Employee.employee_id==data.employee_id).first():
        raise HTTPException(400,"Employee ID exists")
    e = Employee(
        employee_id=data.employee_id, first_name=data.first_name, last_name=data.last_name,
        email=data.email, phone=data.phone, date_of_birth=data.date_of_birth, gender=data.gender,
        department_id=data.department_id, job_title=data.job_title, date_of_joining=data.date_of_joining,
        base_salary=data.base_salary, hra=data.hra, da=data.da, ta=data.ta,
        special_allowance=data.special_allowance,
        gross_salary=data.base_salary+data.hra+data.da+data.ta+data.special_allowance,
        pan_number=data.pan_number, uan_number=data.uan_number,
        bank_account=data.bank_account, bank_name=data.bank_name, ifsc_code=data.ifsc_code,
        password_hash=auth_module.hash_password(data.password), role=data.role,
    )
    db.add(e); db.commit(); db.refresh(e)
    return ser_emp(e)

@app.put("/employees/{eid}")
def update_emp(eid: int, data: EmpUpdate, db: Session=Depends(get_db), _=Depends(require_hr)):
    e = db.query(Employee).filter(Employee.id==eid).first()
    if not e: raise HTTPException(404,"Not found")
    for k,v in data.model_dump(exclude_none=True).items(): setattr(e,k,v)
    e.gross_salary = (e.base_salary or 0)+(e.hra or 0)+(e.da or 0)+(e.ta or 0)+(e.special_allowance or 0)
    e.updated_at = datetime.utcnow(); db.commit(); db.refresh(e)
    return ser_emp(e)

@app.delete("/employees/{eid}")
def deactivate_emp(eid: int, db: Session=Depends(get_db), _=Depends(require_admin)):
    e = db.query(Employee).filter(Employee.id==eid).first()
    if not e: raise HTTPException(404,"Not found")
    e.is_active=False; e.status="TERMINATED"; e.date_of_leaving=date.today()
    db.commit(); return {"message":f"{e.employee_id} deactivated"}

# ── Attendance ────────────────────────────────────────────────────────────────
@app.get("/attendance")
def get_att(employee_id: Optional[int]=None, month: Optional[int]=None, year: Optional[int]=None,
            db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    q = db.query(Attendance)
    if u.role=="EMPLOYEE": q = q.filter(Attendance.employee_id==u.id)
    elif employee_id: q = q.filter(Attendance.employee_id==employee_id)
    if month and year:
        _, ld = monthrange(year, month)
        q = q.filter(Attendance.date>=date(year,month,1), Attendance.date<=date(year,month,ld))
    return [ser_att(r) for r in q.order_by(Attendance.date.desc()).all()]

@app.post("/attendance", status_code=201)
def mark_att(data: AttCreate, db: Session=Depends(get_db), _=Depends(require_hr)):
    if db.query(Attendance).filter(Attendance.employee_id==data.employee_id, Attendance.date==data.date).first():
        raise HTTPException(400,"Already marked")
    wh = ot = 0.0
    if data.check_in and data.check_out:
        wh = round((data.check_out-data.check_in).seconds/3600,2); ot = max(0,wh-8)
    a = Attendance(employee_id=data.employee_id, date=data.date, check_in=data.check_in,
                   check_out=data.check_out, work_hours=wh, overtime_hours=ot,
                   status=data.status, shift=data.shift, notes=data.notes)
    db.add(a); db.commit(); db.refresh(a); return ser_att(a)

@app.post("/attendance/checkin")
def checkin(db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    today = date.today()
    existing = db.query(Attendance).filter(Attendance.employee_id==u.id, Attendance.date==today).first()
    if existing and existing.check_in: raise HTTPException(400,"Already checked in")
    now = datetime.utcnow()
    if existing: existing.check_in=now; existing.status="PRESENT"
    else: db.add(Attendance(employee_id=u.id, date=today, check_in=now, status="PRESENT"))
    db.commit(); return {"message":"Checked in","time":now.isoformat()}

@app.post("/attendance/checkout")
def checkout(db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    today = date.today()
    a = db.query(Attendance).filter(Attendance.employee_id==u.id, Attendance.date==today).first()
    if not a or not a.check_in: raise HTTPException(400,"No check-in found")
    if a.check_out: raise HTTPException(400,"Already checked out")
    now = datetime.utcnow()
    a.check_out=now; diff=(now-a.check_in).seconds/3600
    a.work_hours=round(diff,2); a.overtime_hours=round(max(0,diff-8),2)
    db.commit(); return {"message":"Checked out","work_hours":a.work_hours,"overtime":a.overtime_hours}

@app.get("/attendance/summary/{eid}")
def att_summary(eid: int, month: int=Query(...), year: int=Query(...),
                db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    if u.role=="EMPLOYEE" and u.id!=eid: raise HTTPException(403,"Access denied")
    return payroll_engine.get_attendance_summary(db, eid, month, year)

# ── Leave ─────────────────────────────────────────────────────────────────────
@app.get("/leaves")
def list_leaves(employee_id: Optional[int]=None, status: Optional[str]=None,
                db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    q = db.query(LeaveRequest)
    if u.role=="EMPLOYEE": q = q.filter(LeaveRequest.employee_id==u.id)
    elif employee_id: q = q.filter(LeaveRequest.employee_id==employee_id)
    if status: q = q.filter(LeaveRequest.status==status)
    return [ser_leave(l) for l in q.order_by(LeaveRequest.created_at.desc()).all()]

@app.post("/leaves", status_code=201)
def apply_leave(data: LeaveCreate, db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    if data.end_date < data.start_date: raise HTTPException(400,"End before start")
    days = float((data.end_date-data.start_date).days+1)
    bal = {"SICK":u.sick_leave_balance,"CASUAL":u.casual_leave_balance,"PAID":u.paid_leave_balance}
    if data.leave_type in bal and bal[data.leave_type] < days:
        raise HTTPException(400,f"Insufficient {data.leave_type} balance ({bal[data.leave_type]} days)")
    lr = LeaveRequest(employee_id=u.id, leave_type=data.leave_type,
                      start_date=data.start_date, end_date=data.end_date,
                      days_requested=days, reason=data.reason, status="PENDING")
    db.add(lr); db.commit(); db.refresh(lr); return ser_leave(lr)

@app.put("/leaves/{lid}/approve")
def approve_leave(lid: int, data: LeaveApproval, db: Session=Depends(get_db),
                  u: Employee=Depends(require_manager)):
    lr = db.query(LeaveRequest).filter(LeaveRequest.id==lid).first()
    if not lr: raise HTTPException(404,"Not found")
    if lr.status!="PENDING": raise HTTPException(400,"Already processed")
    lr.status=data.status; lr.approved_by=u.id; lr.approved_at=datetime.utcnow()
    lr.rejection_reason=data.rejection_reason
    if data.status=="APPROVED":
        emp = db.query(Employee).filter(Employee.id==lr.employee_id).first()
        if emp:
            if lr.leave_type=="SICK": emp.sick_leave_balance=max(0,emp.sick_leave_balance-lr.days_requested)
            elif lr.leave_type=="CASUAL": emp.casual_leave_balance=max(0,emp.casual_leave_balance-lr.days_requested)
            elif lr.leave_type=="PAID": emp.paid_leave_balance=max(0,emp.paid_leave_balance-lr.days_requested)
    db.commit(); return ser_leave(lr)

@app.get("/holidays")
def list_holidays(year: Optional[int]=None, db: Session=Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Holiday).filter(Holiday.is_active==True)
    if year: q = q.filter(extract("year",Holiday.date)==year)
    return [{"id":h.id,"name":h.name,"date":h.date.isoformat(),"type":h.type} for h in q.all()]

# ── Payroll ───────────────────────────────────────────────────────────────────
@app.post("/payroll/process")
def run_payroll(data: PayrollRun, db: Session=Depends(get_db), u: Employee=Depends(require_hr)):
    emps = db.query(Employee).filter(Employee.is_active==True)
    if data.employee_ids: emps = emps.filter(Employee.id.in_(data.employee_ids))
    results, errors = [], []
    for emp in emps.all():
        try:
            rec = payroll_engine.process_payroll(
                db, emp, data.month, data.year,
                bonus=(data.bonus_map or {}).get(str(emp.id),0),
                incentives=(data.incentive_map or {}).get(str(emp.id),0),
                processed_by_id=u.id)
            results.append({"employee_id":emp.employee_id,"name":emp.full_name,
                            "gross":rec.gross_earnings,"net":rec.net_salary})
        except Exception as ex:
            errors.append({"employee_id":emp.employee_id,"error":str(ex)})
    return {"processed":len(results),"errors":len(errors),
            "period":f"{data.year}-{data.month:02d}","results":results,"error_details":errors}

@app.get("/payroll")
def list_payroll(employee_id: Optional[int]=None, month: Optional[int]=None,
                 year: Optional[int]=None, db: Session=Depends(get_db),
                 u: Employee=Depends(get_current_user)):
    q = db.query(PayrollRecord)
    if u.role=="EMPLOYEE": q = q.filter(PayrollRecord.employee_id==u.id)
    elif employee_id: q = q.filter(PayrollRecord.employee_id==employee_id)
    if month: q = q.filter(PayrollRecord.month==month)
    if year: q = q.filter(PayrollRecord.year==year)
    return [ser_pay(r) for r in q.order_by(PayrollRecord.year.desc(),PayrollRecord.month.desc()).all()]

@app.get("/payroll/{rid}/payslip")
def get_payslip(rid: int, db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    rec = db.query(PayrollRecord).filter(PayrollRecord.id==rid).first()
    if not rec: raise HTTPException(404,"Not found")
    if u.role=="EMPLOYEE" and u.id!=rec.employee_id: raise HTTPException(403,"Access denied")
    emp = db.query(Employee).filter(Employee.id==rec.employee_id).first()
    return payroll_engine.generate_payslip_data(rec, emp)

@app.put("/payroll/{rid}/mark-paid")
def mark_paid(rid: int, payment_date: Optional[date]=None,
              db: Session=Depends(get_db), _=Depends(require_hr)):
    rec = db.query(PayrollRecord).filter(PayrollRecord.id==rid).first()
    if not rec: raise HTTPException(404,"Not found")
    rec.status="PAID"; rec.payment_date=payment_date or date.today()
    db.commit(); return {"message":"Marked paid","payment_date":rec.payment_date.isoformat()}

# ── Tax ───────────────────────────────────────────────────────────────────────
@app.get("/tax/declarations")
def list_tax(db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    q = db.query(TaxDeclaration)
    if u.role=="EMPLOYEE": q = q.filter(TaxDeclaration.employee_id==u.id)
    return q.order_by(TaxDeclaration.financial_year.desc()).all()

@app.post("/tax/declarations", status_code=201)
def submit_tax(data: TaxDeclCreate, db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    if db.query(TaxDeclaration).filter(TaxDeclaration.employee_id==u.id,
                                        TaxDeclaration.financial_year==data.financial_year).first():
        raise HTTPException(400,"Already submitted for this FY")
    total_80c = min(150000, data.ppf+data.elss+data.life_insurance+data.nsc+data.home_loan_principal+data.tuition_fees)
    annual_gross = (u.gross_salary or 0)*12
    total_ded = total_80c+data.medical_insurance_80d+data.home_loan_interest_24b+data.nps_80ccd+50000
    taxable = max(0, annual_gross-total_ded)
    tax = payroll_engine.calculate_income_tax(taxable, data.regime)
    d = TaxDeclaration(employee_id=u.id, financial_year=data.financial_year, regime=data.regime,
                       ppf=data.ppf, elss=data.elss, life_insurance=data.life_insurance,
                       nsc=data.nsc, home_loan_principal=data.home_loan_principal,
                       tuition_fees=data.tuition_fees, total_80c=total_80c,
                       medical_insurance_80d=data.medical_insurance_80d,
                       home_loan_interest_24b=data.home_loan_interest_24b, nps_80ccd=data.nps_80ccd,
                       gross_income=annual_gross, total_deductions=total_ded,
                       taxable_income=taxable, estimated_tax=tax,
                       status="SUBMITTED", submitted_at=datetime.utcnow())
    db.add(d); db.commit(); db.refresh(d)
    return {"id":d.id,"financial_year":d.financial_year,"regime":d.regime,
            "gross_income":d.gross_income,"taxable_income":d.taxable_income,
            "estimated_tax":d.estimated_tax,"status":d.status}

@app.get("/tax/calculator")
def tax_calc(annual_income: float=Query(...), regime: str=Query("NEW"),
             pf_annual: float=Query(0), deductions_80c: float=Query(0),
             _=Depends(get_current_user)):
    taxable = max(0, annual_income-50000-pf_annual-min(150000,deductions_80c))
    tax = payroll_engine.calculate_income_tax(taxable, regime)
    return {"annual_income":annual_income,"regime":regime,"standard_deduction":50000,
            "pf_deduction":pf_annual,"section_80c":min(150000,deductions_80c),
            "taxable_income":taxable,"annual_tax":tax,"monthly_tds":round(tax/12,2),
            "effective_rate":round(tax/annual_income*100,2) if annual_income>0 else 0}

# ── Benefits ──────────────────────────────────────────────────────────────────
@app.get("/benefits/plans")
def benefit_plans(db: Session=Depends(get_db), _=Depends(get_current_user)):
    return [{"id":p.id,"name":p.name,"type":p.type,"provider":p.provider,
             "employee_contribution":p.employee_contribution,
             "employer_contribution":p.employer_contribution,
             "is_mandatory":p.is_mandatory}
            for p in db.query(BenefitPlan).filter(BenefitPlan.is_active==True).all()]

@app.get("/benefits/my")
def my_benefits(db: Session=Depends(get_db), u: Employee=Depends(get_current_user)):
    return [{"id":b.id,"plan_name":b.plan.name if b.plan else None,
             "plan_type":b.plan.type if b.plan else None,
             "provider":b.plan.provider if b.plan else None,
             "enrollment_date":b.enrollment_date.isoformat(),
             "policy_number":b.policy_number,"nominee_name":b.nominee_name}
            for b in db.query(EmployeeBenefit).filter(
                EmployeeBenefit.employee_id==u.id, EmployeeBenefit.is_active==True).all()]

# ── Reports ───────────────────────────────────────────────────────────────────
@app.get("/reports/dashboard")
def dashboard(db: Session=Depends(get_db), _=Depends(require_hr)):
    today = date.today()
    total_emp = db.query(Employee).filter(Employee.is_active==True).count()
    active_emp = db.query(Employee).filter(Employee.status=="ACTIVE",Employee.is_active==True).count()
    on_leave = db.query(LeaveRequest).filter(LeaveRequest.status=="APPROVED",
        LeaveRequest.start_date<=today, LeaveRequest.end_date>=today).count()
    pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status=="PENDING").count()
    present_today = db.query(Attendance).filter(Attendance.date==today,
        Attendance.status.in_(["PRESENT","WORK_FROM_HOME"])).count()
    month_payroll = db.query(func.sum(PayrollRecord.net_salary)).filter(
        PayrollRecord.month==today.month, PayrollRecord.year==today.year).scalar() or 0
    dept_counts = db.query(Department.name, func.count(Employee.id)).join(
        Employee, Employee.department_id==Department.id).filter(Employee.is_active==True).group_by(Department.name).all()
    trend = []
    for i in range(5,-1,-1):
        m=today.month-i; y=today.year
        if m<=0: m+=12; y-=1
        total = db.query(func.sum(PayrollRecord.net_salary)).filter(
            PayrollRecord.month==m, PayrollRecord.year==y).scalar() or 0
        trend.append({"period":f"{y}-{m:02d}","total":round(total,2)})
    return {"total_employees":total_emp,"active_employees":active_emp,
            "on_leave_today":on_leave,"pending_leaves":pending_leaves,
            "present_today":present_today,"current_month_payroll":round(month_payroll,2),
            "department_headcount":[{"dept":d,"count":c} for d,c in dept_counts],
            "payroll_trend":trend}

@app.get("/reports/payroll-summary")
def payroll_summary(month: int=Query(...), year: int=Query(...),
                    db: Session=Depends(get_db), _=Depends(require_hr)):
    recs = db.query(PayrollRecord).filter(PayrollRecord.month==month,PayrollRecord.year==year).all()
    return {"period":f"{year}-{month:02d}","employee_count":len(recs),
            "total_gross":round(sum(r.gross_earnings for r in recs),2),
            "total_net":round(sum(r.net_salary for r in recs),2),
            "total_pf":round(sum(r.pf_employee+(r.pf_employer or 0) for r in recs),2),
            "total_tds":round(sum(r.income_tax_tds for r in recs),2),
            "records":[ser_pay(r) for r in recs]}

@app.get("/reports/headcount")
def headcount(db: Session=Depends(get_db), _=Depends(require_hr)):
    by_dept = db.query(Department.name, func.count(Employee.id)).join(
        Employee, Employee.department_id==Department.id).filter(Employee.is_active==True).group_by(Department.name).all()
    by_status = db.query(Employee.status, func.count(Employee.id)).filter(
        Employee.is_active==True).group_by(Employee.status).all()
    return {"total":db.query(Employee).filter(Employee.is_active==True).count(),
            "by_department":[{"department":d,"count":c} for d,c in by_dept],
            "by_status":[{"status":s,"count":c} for s,c in by_status]}

@app.get("/reports/attendance-summary")
def att_report(month: int=Query(...), year: int=Query(...),
               department_id: Optional[int]=None,
               db: Session=Depends(get_db), _=Depends(require_hr)):
    q = db.query(Employee).filter(Employee.is_active==True)
    if department_id: q = q.filter(Employee.department_id==department_id)
    summaries = []
    for emp in q.all():
        s = payroll_engine.get_attendance_summary(db, emp.id, month, year)
        summaries.append({"employee_id":emp.employee_id,"name":emp.full_name,
                          "department":emp.department_rel.name if emp.department_rel else None,**s})
    return {"period":f"{year}-{month:02d}","summaries":summaries}

# ── Announcements ─────────────────────────────────────────────────────────────
@app.get("/announcements")
def announcements(db: Session=Depends(get_db), _=Depends(get_current_user)):
    return [{"id":a.id,"title":a.title,"content":a.content,"type":a.type,
             "created_at":a.created_at.isoformat()}
            for a in db.query(Announcement).filter(Announcement.is_active==True)
                       .order_by(Announcement.created_at.desc()).limit(20).all()]

# ── Chat (AI assistant, preserved) ───────────────────────────────────────────
@app.post("/chat")
def chat(req: ChatReq, bg: BackgroundTasks, db: Session=Depends(get_db)):
    results = rag.search_policies(req.query)
    ctx = "\n\n".join([f"Source: {r['source']} ({r['section']})\n{r['text']}" for r in results])
    sources = [f"{r['source']} ({r['section']})" for r in results]
    ai = agent.generate_response(req.query, req.employee_name, ctx)
    ticket_id = None; reply = ai.answer
    if ai.escalate:
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
        reply = f"{ai.answer}\n\n---\nTicket **{ticket_id}** created. HR will respond within 24 hours."
        priority = "HIGH" if ai.topic in ["PAYROLL","POLICY"] else "MEDIUM"
        db.add(EscalationTicket(id=ticket_id, employee_name=req.employee_name,
                                employee_id=req.employee_id, department=req.department,
                                issue_summary=req.query, priority=priority))
        bg.add_task(notify_slack, ticket_id, req.employee_name, priority, req.query)
    if not results or ai.confidence < 0.4:
        gap = db.query(PolicyGap).filter(PolicyGap.query==req.query).first()
        if gap: gap.frequency+=1
        else: db.add(PolicyGap(query=req.query, topic_category=ai.topic))
    db.add(QueryLog(employee_id=req.employee_id, employee_name=req.employee_name,
                    query=req.query, response=reply, topic_category=ai.topic,
                    confidence_score=ai.confidence, escalated=ai.escalate, ticket_id=ticket_id,
                    sources_cited=", ".join(ai.sources) if ai.sources else None))
    db.commit()
    return {"response":reply,"topic":ai.topic,"confidence":ai.confidence,
            "escalated":ai.escalate,"ticket_id":ticket_id,"sources":ai.sources or sources[:3]}

@app.post("/upload_policy")
async def upload_policy(file: UploadFile=File(...)):
    if not file.filename: raise HTTPException(400,"No file")
    if not file.filename.lower().endswith((".pdf",".txt",".md")):
        raise HTTPException(400,"Only PDF/TXT/MD allowed")
    content = await file.read()
    ok, msg = rag.process_and_store_document(content, file.filename)
    if not ok: raise HTTPException(400, msg)
    return {"message":msg,"filename":file.filename}

@app.get("/tickets")
def get_tickets(db: Session=Depends(get_db)):
    return db.query(EscalationTicket).order_by(EscalationTicket.timestamp.desc()).all()

@app.get("/stats")
def stats(db: Session=Depends(get_db)):
    logs = db.query(QueryLog).all()
    topic_counts = {}
    for l in logs: topic_counts[l.topic_category] = topic_counts.get(l.topic_category,0)+1
    gaps = db.query(PolicyGap).order_by(PolicyGap.frequency.desc()).limit(10).all()
    return {"total_queries":len(logs),
            "total_escalations":db.query(EscalationTicket).count(),
            "policy_chunks_stored":rag.get_collection_count(),
            "topic_breakdown":topic_counts,
            "policy_gaps":[{"query":g.query,"topic":g.topic_category,"frequency":g.frequency} for g in gaps]}
