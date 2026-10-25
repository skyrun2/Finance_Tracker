# Finance Tracker — Personal Finance Tracker

> **Status:** ⚠️ **In Development (Not Live Yet)**  
> **Bank Statement Compatibility:** Currently only tested and operational with **OPay bank statements** in **CSV** or **XLSX** format.

---

## 📌 About the Project

**Finance Tracker** is a full-stack personal finance application built to streamline transaction tracking, budget monitoring, and financial health insights.

Tracking income and daily expenditures across multiple accounts is tedious and prone to manual entry errors. Finance Tracker automates this process through an intelligent **ETL (Extract, Transform, Load) import pipeline**:
1. You upload an exported bank statement (**OPay CSV or XLSX**).
2. The system validates the file structure and checks for duplicate uploads via file checksums.
3. Transactions are normalized, classified into expense/income categories using rule-based algorithms, and deduplicated against existing database entries.
4. Data is stored in a relational database and surfaced dynamically via an interactive dashboard, reports, and management interfaces.

---

## ✨ Features

- 🏦 **Bank Statement Imports:**
  - Automated statement ingestion for **OPay** accounts via CSV or XLSX.
  - Multi-stage ETL pipeline: validation ➔ normalization ➔ classification ➔ deduplication ➔ persistence.
  - Import history logs tracking processed rows, duplicates, and errors.
- 📊 **Dynamic Dashboard:**
  - Real-time balances for monthly income, expenses, net savings, and investments.
  - Interactive charts powered by Recharts (monthly breakdown and expenses by category).
  - Quick-glance recent transactions with value masking for privacy (`$ ••••`).
- 💳 **Account Management:**
  - Support for multiple account types: Checking Accounts, Savings, Credit Cards, and Investments.
  - Running balance tracking with automatic updates on transaction creations.
- 🏷️ **Categorization System:**
  - Default and custom categories for Income and Expenses.
  - Rule-based auto-assignment for incoming statement records.
- 🎯 **Financial Goals:**
  - Monthly and yearly target budgets by category or overall spending.
  - Real-time percentage progress indicators.
- 📈 **Investment Tracking:**
  - Value snapshot histories, profit/loss calculations, and percentage return metrics.
  - Monthly performance trend charts.
- 🔍 **Transactions Management:**
  - Full search and filtering by transaction type and category.
  - Pagination, manual transaction creation, and inline deletion.

---

## 🏗 Technical Architecture

```
┌─────────────────────────────────┐        ┌───────────────────────────────┐        ┌─────────────────────────┐
│        Next.js Frontend         │───────▶│       FastAPI REST API        │───────▶│   SQLite / PostgreSQL   │
│  (React 19, TypeScript, Tailwind)│        │   (SQLAlchemy 2, Pydantic v2) │        │   (Async Engine, aiosqlite)
└─────────────────────────────────┘        └───────────────────────────────┘        └─────────────────────────┘
```

### Tech Stack

#### **Backend**
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ORM / Database:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async engine) with [aiosqlite](https://github.com/omnilib/aiosqlite) (SQLite default) or [asyncpg](https://github.com/MagicStack/asyncpg) (PostgreSQL optional)
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings`
- **Data Ingestion & Parsing:** `pandas`, `openpyxl`, `python-dateutil`
- **Server:** `uvicorn`

#### **Frontend**
- **Framework:** [Next.js 16](https://nextjs.org/) (App Router, React 19)
- **Language:** TypeScript
- **Styling:** Tailwind CSS with CSS variables and Radix UI / Base UI primitives
- **Data Fetching:** [TanStack React Query v5](https://tanstack.com/query/latest)
- **Charts:** [Recharts](https://recharts.org/)
- **Icons & Alerts:** `lucide-react`, `sonner`

---

## 📁 Repository Structure

```
financa-main/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application entrypoint, CORS & startup seeders
│   │   ├── config.py            # Environment configurations (settings)
│   │   ├── database.py          # Async SQLAlchemy engine & session maker
│   │   ├── models.py            # Database tables (Accounts, Transactions, Imports...)
│   │   ├── schemas.py           # Pydantic models for request/response serialization
│   │   ├── routers/             # API endpoints (accounts, categories, transactions, imports...)
│   │   └── services/
│   │       ├── etl/             # ETL steps: validator, normalizer, classifier, persister
│   │       └── parsers/         # Bank statement parsers (CSV & XLSX)
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages (Dashboard, Accounts, Imports...)
│   │   ├── components/          # Reusable UI widgets, layout, sidebar, and chart cards
│   │   ├── hooks/               # Custom hooks (e.g., useVisibility)
│   │   ├── lib/                 # Utility constants, currency & date formatting
│   │   └── services/api.ts      # Fetch API wrapper
│   ├── package.json             # Node dependencies and scripts
│   └── tsconfig.json            # TypeScript configuration
└── README.md
```

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18.x or 20.x+** and **npm**

---

### 1. Backend Setup

1. **Navigate to the backend folder:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv venv or py -m venv venv
     source venv/Scripts/activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration (Optional):**
   Create a `.env` file inside `backend/` if you want to override defaults:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./financa.db
   MAX_UPLOAD_SIZE=52428800
   UPLOAD_DIR=./uploads
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - The API will be available at: `http://localhost:8000`
   - Interactive Swagger API Documentation: `http://localhost:8000/docs`

---

### 2. Frontend Setup

1. **Open a new terminal and navigate to the frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install node dependencies:**
   ```bash
   npm install
   ```

3. **Environment Configuration (Optional):**
   By default, the frontend requests `http://localhost:8000`. If you need to change this, create a `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open the application:**
   Visit [http://localhost:3000](http://localhost:3000) in your web browser.

---

## ⚠️ Notes & Current Limitations

- **Not Live in Production:** This software is currently under active development for local development and private testing only.
- **Bank Compatibility:** Currently, the CSV/XLSX statement ingestion has been tailored and validated specifically for **OPay bank account statements**. Uploading statements from unsupported financial institutions may fail during column mapping or validation. Support for other banks and credit institutions will be introduced in upcoming milestones.

---

## 📄 License

This project is licensed under the MIT License — see the repository files for details.
