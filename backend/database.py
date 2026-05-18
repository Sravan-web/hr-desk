"""
database.py — Full HR Management System models + session.
Covers: Employees, Departments, Attendance, Leave, Payroll, Tax, Benefits, Compliance.
"""
import os
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Date, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hrbot.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Departments ───────────────────────────────────────────────────────────────
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employees = relationship("Employee", back_populates="department_rel",
                             foreign_keys="Employee.department_id")


# ── Employees ─────────────────────────────────────────────────────────────────
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    job_title = Column(String(150), nullable=False)
    job_level = Column(String(50), nullable=True)
    employment_type = Column(String(50), default="FULL_TIME")
    status = Column(String(20), default="ACTIVE")
    date_of_joining = Column(Date, nullable=False, default=date.today)
    date_of_leaving = Column(Date, nullable=True)
    reporting_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    # Compensation
    base_salary = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    da = Column(Float, default=0.0)
    ta = Column(Float, default=0.0)
    special_allowance = Column(Float, default=0.0)
    gross_salary = Column(Float, default=0.0)
    # Statutory
    pan_number = Column(String(20), nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    uan_number = Column(String(20), nullable=True)
    bank_account = Column(String(30), nullable=True)
    bank_name = Column(String(100), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    # Leave balances
    sick_leave_balance = Column(Float, default=12.0)
    casual_leave_balance = Column(Float, default=12.0)
    paid_leave_balance = Column(Float, default=15.0)
    # Auth
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), default="EMPLOYEE")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department_rel = relationship("Department", back_populates="employees",
                                  foreign_keys=[department_id])
    attendance_records = relationship("Attendance", back_populates="employee",
                                      foreign_keys="Attendance.employee_id")
    leave_requests = relationship("LeaveRequest", back_populates="employee",
                                  foreign_keys="LeaveRequest.employee_id")
    payroll_records = relationship("PayrollRecord", back_populates="employee",
                                   foreign_keys="PayrollRecord.employee_id")
    benefits = relationship("EmployeeBenefit", back_populates="employee")
    documents = relationship("EmployeeDocument", back_populates="employee")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ── Attendance ────────────────────────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    work_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    status = Column(String(20), default="PRESENT")
    shift = Column(String(20), default="GENERAL")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="attendance_records",
                            foreign_keys=[employee_id])


# ── Leave ─────────────────────────────────────────────────────────────────────
class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING")
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="leave_requests",
                            foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approved_by])


class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False, unique=True)
    type = Column(String(30), default="NATIONAL")
    is_active = Column(Boolean, default=True)


# ── Payroll ───────────────────────────────────────────────────────────────────
class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    pay_period = Column(String(20), nullable=False)
    basic_salary = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    da = Column(Float, default=0.0)
    ta = Column(Float, default=0.0)
    special_allowance = Column(Float, default=0.0)
    overtime_pay = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    incentives = Column(Float, default=0.0)
    gross_earnings = Column(Float, default=0.0)
    pf_employee = Column(Float, default=0.0)
    pf_employer = Column(Float, default=0.0)
    esi_employee = Column(Float, default=0.0)
    esi_employer = Column(Float, default=0.0)
    professional_tax = Column(Float, default=0.0)
    income_tax_tds = Column(Float, default=0.0)
    loan_deduction = Column(Float, default=0.0)
    other_deductions = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    working_days = Column(Integer, default=0)
    present_days = Column(Float, default=0.0)
    absent_days = Column(Float, default=0.0)
    leave_days = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    lop_days = Column(Float, default=0.0)
    status = Column(String(20), default="DRAFT")
    processed_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    payment_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="payroll_records",
                            foreign_keys=[employee_id])


# ── Tax ───────────────────────────────────────────────────────────────────────
class TaxDeclaration(Base):
    __tablename__ = "tax_declarations"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    financial_year = Column(String(10), nullable=False)
    regime = Column(String(10), default="NEW")
    ppf = Column(Float, default=0.0)
    elss = Column(Float, default=0.0)
    life_insurance = Column(Float, default=0.0)
    nsc = Column(Float, default=0.0)
    home_loan_principal = Column(Float, default=0.0)
    tuition_fees = Column(Float, default=0.0)
    total_80c = Column(Float, default=0.0)
    medical_insurance_80d = Column(Float, default=0.0)
    home_loan_interest_24b = Column(Float, default=0.0)
    nps_80ccd = Column(Float, default=0.0)
    gross_income = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    taxable_income = Column(Float, default=0.0)
    estimated_tax = Column(Float, default=0.0)
    status = Column(String(20), default="DRAFT")
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship("Employee", foreign_keys=[employee_id])


# ── Benefits ──────────────────────────────────────────────────────────────────
class BenefitPlan(Base):
    __tablename__ = "benefit_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(100), nullable=True)
    employee_contribution = Column(Float, default=0.0)
    employer_contribution = Column(Float, default=0.0)
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class EmployeeBenefit(Base):
    __tablename__ = "employee_benefits"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    benefit_plan_id = Column(Integer, ForeignKey("benefit_plans.id"), nullable=False)
    enrollment_date = Column(Date, nullable=False, default=date.today)
    is_active = Column(Boolean, default=True)
    nominee_name = Column(String(100), nullable=True)
    policy_number = Column(String(50), nullable=True)
    employee = relationship("Employee", back_populates="benefits")
    plan = relationship("BenefitPlan")


# ── Documents ─────────────────────────────────────────────────────────────────
class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    document_name = Column(String(200), nullable=False)
    month = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    employee = relationship("Employee", back_populates="documents")


# ── Announcements ─────────────────────────────────────────────────────────────
class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(30), default="GENERAL")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Legacy (chat/tickets) ─────────────────────────────────────────────────────
class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    employee_id = Column(String, index=True, nullable=True)
    employee_name = Column(String, nullable=True)
    query = Column(Text)
    response = Column(Text)
    topic_category = Column(String, index=True)
    confidence_score = Column(Float)
    escalated = Column(Boolean, default=False)
    ticket_id = Column(String, nullable=True)
    sources_cited = Column(Text, nullable=True)


class EscalationTicket(Base):
    __tablename__ = "escalation_tickets"
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    employee_name = Column(String)
    employee_id = Column(String)
    department = Column(String, nullable=True)
    issue_summary = Column(Text)
    priority = Column(String)
    status = Column(String, default="OPEN")
    resolution_notes = Column(Text, nullable=True)


class PolicyGap(Base):
    __tablename__ = "policy_gaps"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(Text)
    topic_category = Column(String, nullable=True)
    frequency = Column(Integer, default=1)


# ── Init ──────────────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
