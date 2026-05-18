"""
auth.py — JWT authentication + role-based access control.
"""
import os, hashlib, hmac, secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from database import Employee, get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hrdesk_dev_secret_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, stored = hashed.split(":", 1)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(computed.hex(), stored)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload["iat"] = datetime.utcnow()
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Employee:
    if not AUTH_REQUIRED:
        emp = db.query(Employee).filter(Employee.role == "ADMIN").first()
        if emp:
            return emp
        emp = db.query(Employee).first()
        if emp:
            return emp
        # Return a mock employee object if DB is empty
        mock = Employee()
        mock.id = 0
        mock.employee_id = "EMP-001"
        mock.first_name = "Admin"
        mock.last_name = "User"
        mock.email = "admin@hrdesk.com"
        mock.role = "ADMIN"
        mock.is_active = True
        return mock

    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(credentials.credentials)
    emp_id = payload.get("sub")
    emp = db.query(Employee).filter(
        Employee.employee_id == emp_id, Employee.is_active == True
    ).first()
    if not emp:
        raise HTTPException(status_code=401, detail="Employee not found")
    return emp


def require_roles(*roles):
    def checker(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {roles}")
        return current_user
    return checker


require_admin = require_roles("ADMIN")
require_hr = require_roles("ADMIN", "HR_MANAGER")
require_manager = require_roles("ADMIN", "HR_MANAGER", "MANAGER")
