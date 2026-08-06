# SSGA HOLDINGS — Production Fintech Platform

A clean full-stack rebuild using React + TypeScript, FastAPI, SQLAlchemy and SQLite.

## Core systems
- Dual-ledger wallet with one customer-facing balance
- Staged MoMo deposit checkout and admin approval
- Earnings-only withdrawals (GHS 50 minimum, 16% fee)
- Five-question daily income gate with instant explanations
- Automatic package income credit after daily quiz completion
- Admin question bank CRUD designed for 500+ questions
- Packages, tasks, referrals, ads and rich notifications
- WebSocket admin alerts for withdrawal and deposit activity
- Responsive banking-style shell and distinct Task Center
- PWA manifest, service worker, premium SVG logo suite and favicon

## Local development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend && uvicorn app.main:app --reload

# separate terminal
cd frontend
npm install
npm run dev
```

Default admin (change immediately): `0200000000` / `admin123`.

## Render
Push the complete repository and create a **Blueprint**. `render.yaml` builds one Docker web service, compiling the UI and serving it from FastAPI. SQLite on Render Free is ephemeral. For production, attach a persistent disk and set `DATABASE_URL=sqlite:////var/data/ssga.db` and `UPLOAD_DIR=/var/data/uploads`, or use PostgreSQL.


## v3.1 recovery completion

The recovery release adds explicit `wallets`, `answers`, `referrals` and `income_credits` ledgers; separate frontend page modules; login/signup/404 routes; a root error boundary; privacy-aware realtime updates; duplicate request protection; strict withdrawal transitions; and SQLite foreign-key/WAL hardening. See `QA_REPORT.md` for the full audit.
