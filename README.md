# ⚡ OptiShift: Intelligent Workforce Scheduling Engine

> An enterprise-grade workforce scheduling and constraint-solving engine designed to balance complex shift requirements, labor laws, cost, preferences, and fairness—with automated conflict resolution and explainable AI decisions.

---

## 🎯 The Problem
Workforce scheduling is an NP-hard combinatorial problem. Traditional spreadsheet methods and greedy algorithms break down when faced with overlapping constraints:
* **Hard Rules:** Legal working hours, mandatory skill certifications, and strict rest periods.
* **Soft Preferences:** Employee shift requests, department allocations, and cost optimization.
* **The Conflict Crisis:** When a sudden leave request or deadline change breaks a schedule, manual schedulers are left playing an endless game of whack-a-mole.

**OptiShift** automates this entire lifecycle, ensuring strict legal compliance, maximizing fairness, and explicitly isolating conflicts when a feasible schedule cannot be mathematically reached.

---

## 🏗️ System Architecture & Code Separation

To maintain strict modular isolation across team domains, the repository is split into clean, decoupled layers. This ensures backend, frontend, and solver development never collide.

## 🏗️ System Architecture & Code Separation

To maintain strict modular isolation across team domains, the repository is split into clean layers. This ensures backend, website frontend, and solver development never collide.

```text
scheduling-backend/
├── app/
│   ├── api/                 # 🌐 REST API Endpoints (Communicates with Website)
│   ├── models/              # 📋 JSON Contracts & Pydantic Schemas
│   ├── services/            # ⚙️ Business Logic & Solver Orchestration
│   │   ├── data_prep.py     # Data transformation for solver ingestion
│   │   └── solver_core.py   # 🧮 CP-SAT Optimization Kernel (Solver Team)
│   ├── core/                # 🔐 Config, Security, & Error Handling
│   └── main.py              # 🚀 API Server Entrypoint
├── tests/                   # Automated API & Unit Tests
├── requirements.txt         # Python Dependencies
└── README.md