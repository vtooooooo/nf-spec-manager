# 🔧 NF Spec Manager

A unified, automated, and governed solution for managing Network Function (NF) specifications across deployment environments — built as a portfolio project mirroring AT&T Labs' NF specification management challenge.

---

## 🚨 Problem Solved

Traditional NF spec management is fragmented across tools and teams, causing:
- ❌ Manual handoffs that introduce errors
- ❌ Configuration drift between dev, staging, and prod
- ❌ No audit trail — impossible to track who changed what
- ❌ Slow, inconsistent deployments across environments

This project replaces that with a unified, governed, automated platform.

---

## ✅ Solution Architecture

Git Repo (single source of truth)
        │
        ▼
GitHub Actions CI (validates all specs on every push)
        │
        ▼
NF Spec Manager
├── RBAC Layer        → Who can read/create/deploy/delete
├── Validator         → Pydantic schema enforcement
├── Deployment Engine → dev → staging → prod promotion
├── Audit Logger      → Append-only SQLite log
└── S3 Sync           → AWS S3 cloud backup and distribution
        │
        ▼
Streamlit Web UI (accessible to non-technical stakeholders)

---

## 🛠️ Tech Stack

Language          | Python 3.13
Schema Validation | Pydantic v2
Web UI            | Streamlit
Cloud Storage     | AWS S3 (boto3)
Audit Storage     | SQLite
CI/CD Pipeline    | GitHub Actions
Config Format     | YAML
Access Control    | Custom RBAC

---

## 🏗️ Project Structure

nf-spec-manager/
├── core/
│   ├── auth.py          # RBAC - roles and permissions
│   ├── validator.py     # Pydantic schema validation
│   ├── audit.py         # SQLite audit logging
│   ├── deployment.py    # Environment promotion engine
│   └── s3_sync.py       # AWS S3 integration
├── specs/
│   ├── dev/             # Development environment specs
│   ├── staging/         # Staging environment specs
│   └── prod/            # Production environment specs
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions CI pipeline
├── app.py               # Streamlit web UI
├── requirements.txt
└── .env                 # AWS credentials (never committed)

---

## 🔐 Role-Based Access Control (RBAC)

Role       | Read | Create | Update | Deploy | Delete
-----------|------|--------|--------|--------|-------
viewer     |  Yes |   No   |   No   |   No   |   No
editor     |  Yes |   Yes  |   Yes  |   No   |   No
deployer   |  Yes |   Yes  |   Yes  |   Yes  |   No
admin      |  Yes |   Yes  |   Yes  |   Yes  |  Yes

---

## 🔄 Deployment Pipeline

dev ──► staging ──► prod

- Every promotion triggers Pydantic schema validation
- Invalid specs are rejected before reaching the next environment
- Every action is logged to the audit trail
- Promoted specs are automatically synced to AWS S3

---

## ✅ NF Spec Schema

Every NF spec must conform to this structure:

name: upf-core              # lowercase, hyphens only
version: 1.0.0              # semantic versioning (MAJOR.MINOR.PATCH)
nf_type: CNF                # VNF | CNF | PNF
environment: dev            # dev | staging | prod
owner: network-team
description: User Plane Function
resources:
  cpu: "1000m"              # CPU request
  memory: "512Mi"           # Memory request
  replicas: 2               # 1-20 replicas
network:
  port: 8805                # 1-65535
  protocol: UDP             # TCP | UDP | HTTP | HTTPS | GRPC
  expose: false
tags:
  - 5g
  - core

---

## 🚀 Running Locally

# Clone the repo
git clone https://github.com/YOUR_USERNAME/nf-spec-manager.git
cd nf-spec-manager

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up AWS credentials
# Create .env file and fill in your AWS credentials

# Run the app
streamlit run app.py

Open: http://localhost:8501

---

## 👤 Demo Users

Username | Password | Role
---------|----------|----------
alice    | alice123 | deployer
bob      | bob123   | editor
carol    | carol123 | viewer
admin    | admin123 | admin

---

## 🔁 CI/CD Pipeline

Every git push to main or dev automatically:
1. Validates all YAML spec files against the Pydantic schema
2. Lints Python code with flake8
3. Fails the build if any spec is invalid — preventing bad configs from being merged

---

## 📜 Audit Log

Every action is recorded with:
- Timestamp    — when it happened
- User + Role  — who did it
- Action       — what was done (create/promote/delete)
- Spec name    — which spec was affected
- From/To env  — for promotions
- Status       — SUCCESS / FAILED / DENIED
- Message      — details or error reason

Audit logs are exportable as CSV from the UI.

---

## ☁️ AWS S3 Integration

- Specs are automatically uploaded to S3 after every promotion
- S3 bucket is organized by environment: specs/dev/, specs/staging/, specs/prod/
- Bulk sync available from the UI

---

## 💡 Key Design Decisions

Why YAML for specs?
Human-readable, version-controllable, and the industry standard for Kubernetes and cloud-native config.

Why Pydantic for validation?
Type-safe, self-documenting schema with clear error messages — rejects invalid specs before they reach any environment.

Why Git as source of truth?
Full change history, branching for safe experimentation, and PR-based approval workflows.

Why append-only audit log?
Compliance and traceability — you need to know exactly what happened, when, and who did it. Deleting log entries defeats the purpose.

---

## 👨‍💻 Author

Vittu Ramadasu Darshan
Master's in Data Science, University of New Haven (May 2026)
LinkedIn: YOUR_LINKEDIN_URL
Portfolio: YOUR_PORTFOLIO_URL
GitHub: https://github.com/YOUR_USERNAME
