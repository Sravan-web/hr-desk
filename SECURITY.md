# 🛡️ HRBot Security Posture — Hackathon Documentation

> **Last Updated:** 2026-05-17  
> **Status:** MVP Security — Production-Ready Patterns  
> **Team:** HRBot Engineering

---

## Executive Summary

HRBot handles sensitive employee data (payroll, leave, harassment reports). Security is non-negotiable, but hackathon timelines demand speed. We adopted a **"Buy, Don't Build"** strategy: every security control uses vetted, managed services rather than custom implementations.

---

## 🏗️ Strategy 1: Never Build Auth from Scratch

| Decision | Details |
|----------|---------|
| **Approach** | Firebase Authentication (managed by Google) |
| **Implementation** | `middleware.py` → `verify_firebase_token()` dependency |
| **Token Format** | Firebase ID Tokens (JWT, RS256) |
| **Verification** | Server-side via `firebase-admin` SDK — no client-side trust |
| **Dev/Demo Mode** | `AUTH_REQUIRED=false` allows bypass with audit logging |
| **Production Mode** | `AUTH_REQUIRED=true` enforces JWT on every `/chat`, `/upload`, `/tickets` endpoint |

**Why Firebase?** Password hashing (bcrypt), session management, MFA support, and OIDC compliance — all out-of-the-box. Building this would have taken 10–15 hours and introduced vulnerabilities.

### Auth Flow
```
Frontend (Firebase JS SDK)
    │
    ├── User signs in (email/password, Google, SSO)
    │
    ├── Firebase returns ID Token (JWT)
    │
    └── Token sent via Authorization: Bearer <token>
            │
            └── Backend verifies via firebase-admin SDK
                    │
                    ├── ✅ Valid → Process request + audit log
                    └── ❌ Invalid → 401 Unauthorized + audit log
```

---

## 🌐 Strategy 2: Managed Cloud & Deployment

| Layer | Service | Security Benefit |
|-------|---------|-----------------|
| **Compute** | Google Cloud Run | Sandboxed containers, auto-scaling, TLS termination |
| **Container** | Multi-stage Dockerfile | Non-root user, minimal attack surface, health checks |
| **CI/CD** | Google Cloud Build | No SSH keys, IAM-scoped permissions |
| **Secrets** | Google Secret Manager | Encrypted at rest, versioned, audit-logged |
| **Frontend** | Vercel / Firebase Hosting | CDN with DDoS protection, automatic HTTPS |

### Container Hardening Checklist
- [x] Multi-stage build (build deps ≠ runtime image)
- [x] Non-root user (`hrbot:hrbot`)
- [x] Read-only application files (`chmod 555`)
- [x] Health check endpoint (`/health`)
- [x] No access logs in container stdout (prevents log injection)
- [x] Resource limits set in `cloudbuild.yaml` (512Mi RAM, 1 CPU, max 3 instances)

---

## 🔍 Strategy 3: Automated Vulnerability Scanning (CI/CD)

All scans run on every push to `main` and on every pull request, plus a weekly scheduled scan.

| Scanner | Target | What It Catches |
|---------|--------|-----------------|
| **CodeQL (SAST)** | Python + JavaScript source | SQL injection, XSS, path traversal, insecure deserialization |
| **pip-audit** | Python dependencies | Known CVEs in PyPI packages |
| **Safety** | Python dependencies | Alternative vulnerability database cross-check |
| **npm audit** | Node.js dependencies | Known CVEs in npm packages |
| **Gitleaks** | Git history | Accidentally committed secrets, API keys, passwords |
| **Trivy** | Docker image | OS-level CVEs, library vulnerabilities in the container |

### Pipeline Architecture
```
Push to main / PR
    │
    ├─► CodeQL Analysis ──────────► GitHub Security Tab
    │
    ├─► Python Dependency Audit ──► pip-audit + safety
    │
    ├─► Frontend Dependency Audit → npm audit + ESLint
    │
    ├─► Secret Leak Detection ───► Gitleaks (full history)
    │
    └─► Container Image Scan ────► Trivy → SARIF upload
```

**Config File:** `.github/workflows/security.yml`

---

## 🔐 Strategy 4: Secrets & Input Security

### 4a. Secrets Management

| Environment | Method | Tool |
|-------------|--------|------|
| **Local Dev** | `.env` file (git-ignored) | `python-dotenv` |
| **CI/CD** | GitHub Secrets | `${{ secrets.* }}` |
| **Production** | Google Secret Manager | `--set-secrets` in Cloud Build |

**Enforced via:**
- `.gitignore` blocks: `.env*`, `*-service-account.json`, `*.pem`, `*.p12`, `audit.log`
- `.env.example` provided as a schema reference (contains no real values)
- Gitleaks in CI catches any accidental commits

### 4b. Input Validation & Sanitization

| Protection | Implementation | File |
|------------|---------------|------|
| **XSS Prevention** | Regex stripping of `<script>`, `javascript:`, `on*=` handlers | `middleware.py` |
| **Query Length Limit** | Max 2000 characters per query | `middleware.py` + Pydantic validator |
| **Employee ID Format** | Alphanumeric + hyphens, max 50 chars | `main.py` Pydantic validator |
| **File Upload Limit** | Max 10MB, PDF/DOCX only | `main.py` upload endpoint |
| **Null Byte Injection** | Stripped from all inputs | `middleware.py` |

### 4c. HTTP Security Headers

Every response includes:

| Header | Value | Protection Against |
|--------|-------|--------------------|
| `X-Content-Type-Options` | `nosniff` | MIME sniffing attacks |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Reflected XSS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Feature abuse |

### 4d. CORS Lockdown

| Setting | Dev | Production |
|---------|-----|------------|
| `allow_origins` | `localhost:5173, localhost:3000` | `https://your-frontend.vercel.app` |
| `allow_methods` | `GET, POST` | `GET, POST` |
| `allow_headers` | `Authorization, Content-Type` | `Authorization, Content-Type` |

**Previous:** `allow_origins=["*"]` (wildcard — insecure)  
**Current:** Explicit allowlist loaded from `ALLOWED_ORIGINS` env var.

### 4e. Rate Limiting

| Parameter | Value |
|-----------|-------|
| Algorithm | Sliding window (in-memory) |
| Limit | 30 requests per 60 seconds per IP |
| Response | `429 Too Many Requests` |
| Production Upgrade | Redis-backed via Cloud Memorystore |

---

## 📋 Strategy 5: Security Testing Log & Timeline

This section tracks every security feature evaluated, tested, and deployed.

### Implementation Timeline

| Date | Phase | Action | Status |
|------|-------|--------|--------|
| Day 1 AM | Architecture | Decided against custom auth → Firebase Auth | ✅ Done |
| Day 1 AM | Architecture | Selected Cloud Run for sandboxed deployment | ✅ Done |
| Day 1 PM | Backend | Set up RAG pipeline with ChromaDB | ✅ Done |
| Day 1 PM | Backend | Configured `.env` + `.gitignore` for secrets | ✅ Done |
| Day 2 AM | CI/CD | Added CodeQL workflow for SAST scanning | ✅ Done |
| Day 2 AM | CI/CD | Added pip-audit + npm audit dependency scans | ✅ Done |
| Day 2 AM | CI/CD | Added Gitleaks secret scanning | ✅ Done |
| Day 2 AM | CI/CD | Added Trivy container image scanning | ✅ Done |
| Day 2 PM | Backend | Implemented rate limiting middleware | ✅ Done |
| Day 2 PM | Backend | Implemented input sanitization (XSS, injection) | ✅ Done |
| Day 2 PM | Backend | Added security headers middleware | ✅ Done |
| Day 2 PM | Backend | Locked down CORS from `*` to explicit allowlist | ✅ Done |
| Day 2 PM | Backend | Firebase JWT verification middleware | ✅ Done |
| Day 2 PM | Backend | File upload size validation (10MB limit) | ✅ Done |
| Day 2 PM | Backend | Pydantic request model validators | ✅ Done |
| Day 2 PM | Infra | Hardened Dockerfile (non-root, multi-stage) | ✅ Done |
| Day 2 PM | Infra | Cloud Build with Secret Manager integration | ✅ Done |
| Day 2 PM | Backend | Request audit logging (audit.log) | ✅ Done |
| Day 2 PM | Docs | Comprehensive security documentation | ✅ Done |

### Vulnerabilities Identified & Remediated

| # | Vulnerability | Severity | Found Via | Remediation | Status |
|---|--------------|----------|-----------|-------------|--------|
| 1 | CORS wildcard (`*`) | High | Manual review | Replaced with explicit origin allowlist | ✅ Fixed |
| 2 | No auth on API routes | High | Architecture review | Firebase JWT middleware on all endpoints | ✅ Fixed |
| 3 | No input sanitization | Medium | Manual review | XSS regex stripping + length limits | ✅ Fixed |
| 4 | Container runs as root | Medium | Dockerfile review | Added non-root `hrbot` user | ✅ Fixed |
| 5 | No rate limiting | Medium | Architecture review | Sliding-window rate limiter (30/min) | ✅ Fixed |
| 6 | API key in cloudbuild env | Medium | Manual review | Migrated to Google Secret Manager | ✅ Fixed |
| 7 | No file size validation | Low | Manual review | 10MB upload limit enforced | ✅ Fixed |
| 8 | No security headers | Low | OWASP checklist | 5 security headers on all responses | ✅ Fixed |
| 9 | Unrestricted API docs | Low | Manual review | Docs disabled in production via env var | ✅ Fixed |

---

## 🗂️ File Reference

| File | Purpose |
|------|---------|
| `backend/middleware.py` | Rate limiter, input sanitizer, Firebase auth, audit logger |
| `backend/main.py` | Hardened FastAPI app with security dependencies |
| `backend/Dockerfile` | Multi-stage, non-root container build |
| `.github/workflows/security.yml` | 5-job CI/CD security pipeline |
| `.env.example` | Environment variable schema (no real secrets) |
| `.gitignore` | Blocks secrets, logs, keys, service accounts |
| `cloudbuild.yaml` | Secure Cloud Run deployment with Secret Manager |
| `SECURITY.md` | This file — live security posture documentation |

---

## 🎯 Production Upgrade Path (Post-Hackathon)

These items are documented but deferred due to hackathon time constraints:

| Item | Current (MVP) | Production Target |
|------|--------------|-------------------|
| Rate Limiting | In-memory (single instance) | Redis via Cloud Memorystore |
| Session Storage | In-memory dict | Cloud SQL / Firestore |
| Auth Provider | Firebase Auth (email/password) | Firebase Auth + SAML SSO for enterprise |
| Audit Logs | Local `audit.log` file | Cloud Logging + BigQuery sink |
| Encryption | TLS in transit (Cloud Run) | + AES-256 at rest for ChromaDB |
| Penetration Testing | Automated scanners only | Professional pentest engagement |
| RBAC | Single employee role | Role-based (Employee, HR, Admin) |
