# AutoSure

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Auto service management system for workshops — customers, vehicles, work orders, inventory, invoicing, and reports. Built with **Streamlit** and **PostgreSQL**, tuned for Indian garages (GST, ₹ pricing, Gujarat license plates).

---

## Features

| Module | What it does |
|--------|----------------|
| **Dashboard** | KPIs, charts, role-based quick actions |
| **Customers** | CRUD, search, customer types (regular / VIP / wholesale) |
| **Vehicles** | Linked to customers, VIN & Gujarat plate validation |
| **Service Orders** | Work orders, parts, labor, technician assignment |
| **Inventory** | Parts stock, low-stock alerts, SKU auto-generation |
| **Invoices** | Billing, payments, PDF export |
| **Reports** | Revenue, orders, inventory analytics (Plotly) |

**Roles:** Admin · Manager · Technician · Cashier — each sees only what they need.

---

## Prerequisites

Install these before you start:

1. **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
2. **PostgreSQL 14+** — [postgresql.org/download](https://www.postgresql.org/download/)
3. **Git** — [git-scm.com/downloads](https://git-scm.com/downloads)

Check versions:

```bash
python --version
psql --version
git --version
```

---

## Setup from scratch

### 1. Clone the repository

```bash
git clone https://github.com/tanvirshaikh2609/AutoSure.git
cd AutoSure
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Open **psql** or **pgAdmin** and run:

```sql
CREATE DATABASE car_service_db;
```

Or from the terminal (replace `postgres` with your superuser if different):

```bash
psql -U postgres -c "CREATE DATABASE car_service_db;"
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your real database password and business details:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=car_service_db
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

> **Never commit `.env`** — it is listed in `.gitignore`.

### 6. Initialize the database

Creates tables and loads demo users, customers, vehicles, services, and parts:

```bash
python database/init_db.py
```

Verify the connection:

```bash
python database/connection.py
```

Expected output: `Database connection successful!`

### 7. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Demo login credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@carservice.com | Admin@123 |
| Manager | manager@carservice.com | Manager@123 |
| Cashier | cashier@carservice.com | Cashier@123 |
| Technician | tech1@carservice.com … tech5@carservice.com | Tech@123 |

---

## How to use

1. **Sign in** with any demo account above.
2. Use the **sidebar** to switch pages (Dashboard, Customers, Vehicles, etc.).
3. Typical workflow:
   - Add or search a **Customer**
   - Register their **Vehicle**
   - Open a **Service Order** → assign technician → add services/parts → mark completed
   - Create an **Invoice** from the completed order → record payments
   - Check **Inventory** for low stock; **Reports** for charts and PDF export

Technicians see a limited view (their orders + read-only inventory). Cashiers focus on invoices and customer lookup.

---

## Project structure

```
AutoSure/
├── app.py                 # Entry point, login, home stats
├── config.py              # Settings from .env
├── requirements.txt
├── .env.example
├── database/
│   ├── connection.py      # SQLAlchemy engine & sessions
│   ├── models.py          # ORM models
│   └── init_db.py         # Schema + seed data
├── pages/                 # Streamlit multipage UI
│   ├── 1_Dashboard.py
│   ├── 2_Customers.py
│   ├── 3_Vehicles.py
│   ├── 4_Service_Orders.py
│   ├── 5_Inventory.py
│   ├── 7_Invoices.py
│   └── 8_Reports.py
├── services/              # Business logic layer
├── utils/                 # Auth, validators, terminology
├── static/styles.css
└── sql/schema.sql         # Reference SQL schema
```

---

## Configuration reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_*` | — | PostgreSQL connection |
| `TAX_RATE` | `0.18` | GST rate (18%) |
| `CURRENCY_SYMBOL` | `₹` | Display symbol |
| `DEFAULT_LABOR_RATE` | `500.00` | Default hourly labor (₹) |
| `COMPANY_*` | — | Name, address, phone on invoices |

See `.env.example` for the full list.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Database connection failed` | PostgreSQL running? `.env` credentials correct? DB created? |
| `ModuleNotFoundError` | Activate venv, run `pip install -r requirements.txt` |
| Login fails after init | Re-run `python database/init_db.py` |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |

---

## What I learned from building this

Building AutoSure taught me how a real business app is layered — not everything belongs in the UI.

- **Streamlit multipage apps** — `pages/` routing, session state for login, and keeping `app.py` as a thin shell instead of one giant script.
- **SQLAlchemy ORM** — models, relationships, and why `Decimal` matters for money (float rounding bites you on invoices).
- **Service layer pattern** — pages call `CustomerService`, `InvoiceService`, etc., so database logic stays out of Streamlit widgets.
- **Role-based access control** — decorators like `@require_permission('invoices')` and checking roles before showing delete buttons.
- **Password security** — bcrypt hashing via Passlib; never storing plain text passwords.
- **PostgreSQL in practice** — connection pooling, migrations via `create_all`, and seed scripts for repeatable demos.
- **Input validation** — regex for email, VIN, and Gujarat license plates (`GJ-XX-####-YY`) at the boundary where users type data.
- **Indian business context** — GST on invoices, ₹ formatting, and locale-specific sample data (Ahmedabad customers, GJ plates).
- **Reporting & PDFs** — Plotly charts in Streamlit and ReportLab for downloadable invoice/report PDFs.
- **Environment-based config** — `python-dotenv` so secrets and shop settings live in `.env`, not in code.

The biggest takeaway: **read the full flow before cutting code**. Fixing permissions in one page while leaving the shared helper broken would have been worse than a larger but correct change in `access_control.py`.

---

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for the full text. Attribution details are in [NOTICE](NOTICE).

Licensed under the [Apache License, Version 2.0](LICENSE).
