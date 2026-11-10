# PrepPilot: AI Interview Preparation Platform

Final-year B.Tech CSE (Data Science) capstone. One workspace where students prepare for campus placements with AI feedback, and the Training & Placement Office (TPO) sees which students need help.

**Stack:** React 19 + TypeScript + Vite + Tailwind · Flask + SQLAlchemy + Alembic · PostgreSQL · scikit-learn · Gemini / OpenAI / Anthropic (pluggable) · Judge0

The technical design is in [docs/architecture.md](docs/architecture.md).

## Features

**Students**
- Register with college email, branch and roll number. JWT access tokens, rotating refresh tokens, bcrypt password hashes, password reset.
- **Resume analyzer:** upload a PDF or DOCX, check it against a target role and job description, get an ATS-style score, skill match, missing skills and formatting issues, and download a PDF report.
- **Mock interviews:** multi-turn HR and technical interviews (typed answers or browser voice input), scored per dimension with strengths and improvements.
- **Coding practice:** 36 problems in Python, Java and C++, visible and hidden tests, and an AI code review of correctness and complexity.
- **Company prep:** 9 company profiles with curated and AI-generated HR, technical and coding questions.
- **Dashboard:** score history, category charts, strong and weak areas.
- **Placement readiness:** a Random Forest estimate with a what-if simulator (proof of concept, see below).
- **Study roadmap:** generated from weak areas; completing items shrinks the preparation gap.
- **Performance report:** one downloadable PDF.

**Experience**
- Modern responsive UI with light and dark themes (follows the system setting, remembered per browser).
- ⌘K / Ctrl+K command palette to jump between pages.
- Theme-aware charts and code editor, page transitions, loading placeholders, and keyboard and screen-reader support.
- The product name lives in one constant (`BRAND` in `frontend/src/lib/theme.ts`).

**TPO**
- Batch table with branch and readiness filters, averages, and a per-student score drill-down that never shows interview transcripts.

**Security**
- Role checks on every route, sign-in throttling (5 failures per 15 minutes), TPO registration by emailed code and allowlist, a production start-up check that refuses unsafe settings, and code execution isolated in Judge0 in production.

## Run it locally

Prerequisites: Python 3.12, **Node.js 20.19+ or 22.12+** (Vite 8), and PostgreSQL (Docker Desktop, or a local install).

### 1. Configure

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # run twice
```

In `.env`:
- Put the two values in `SECRET_KEY` and `JWT_SECRET`.
- Set `PASSWORD_RESET_DEV_EXPOSE=true` so reset links and TPO codes appear on the page without a mail server (local only).
- Add an AI key. **Gemini is free:** create a key at https://aistudio.google.com/app/apikey, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=...`. OpenAI and Anthropic keys work too (`LLM_PROVIDER=openai` / `anthropic`). Without a key, AI actions return a clear configuration error and never a made-up score.

### 2. Database

With Docker:

```bash
docker compose up -d        # Postgres on localhost:5433
```

Or with a local PostgreSQL on 5432:

```bash
psql -d postgres -c "CREATE ROLE interview LOGIN PASSWORD 'interview';"
psql -d postgres -c "CREATE DATABASE interview_prep OWNER interview;"
```

and change `DATABASE_URL` in `.env` to port `5432`.

### 3. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app run.py db upgrade
python -m pytest
python run.py                      # http://127.0.0.1:5001
```

### 4. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

The Vite dev server proxies `/api` to the backend. API docs (Swagger) are at http://127.0.0.1:5001/api/v1/docs.

### Accounts

Nothing is seeded. Students register from the site. TPO registration sends a 6-digit code to the email on the form; locally, with `PASSWORD_RESET_DEV_EXPOSE=true`, the code is shown on the page. Set `TPO_ALLOWED_EMAILS` to restrict who can become a TPO.

## Tests and checks

```bash
cd backend && python -m pytest && ruff check .
cd frontend && npm run lint && npm run build
curl http://127.0.0.1:5001/api/v1/health      # {"database":"ok","status":"ok"}
```

The backend suite covers auth, roles, practice flows, catalog and coding, insights, and the security safeguards (sandbox escapes, login throttling, production settings).

## Deploy

Recommended free/student setup: **Render** (API + Postgres) and **Vercel** (frontend). Push this repository to GitHub first.

### Backend on Render
1. In Render, choose **New → Blueprint** and pick the repository. `render.yaml` creates the API (Docker, gunicorn, migrations on start) and a Postgres database. `SECRET_KEY` and `JWT_SECRET` are generated for you.
2. Fill in the prompted values:
   - `GEMINI_API_KEY`: your AI key.
   - `TPO_ALLOWED_EMAILS`: the placement office emails (required in production).
   - `FRONTEND_URL` and `CORS_ORIGINS`: your Vercel URL, for example `https://your-app.vercel.app`.
   - `JUDGE0_URL`, `JUDGE0_API_KEY`, `JUDGE0_HOST`: a hosted Judge0, such as Judge0 CE on RapidAPI (`https://judge0-ce.p.rapidapi.com`, host `judge0-ce.p.rapidapi.com`). Without Judge0, production returns a clear "code execution needs JUDGE0_URL" message instead of running student code on the server.
3. Optional: set `SMTP_*` so reset links and TPO codes are emailed.

Notes: Render's free Postgres expires after 30 days; Neon's free tier does not (paste its URL into `DATABASE_URL`; `postgres://` URLs are converted automatically). Uploaded resumes live on the container disk, which the free plan resets on redeploy; attach a Render disk at `/data/uploads` to keep them.

### Frontend on Vercel
1. Import the repository and set **Root Directory** to `frontend`.
2. Add the environment variable `VITE_API_URL` = your Render URL, for example `https://interview-prep-api.onrender.com`.
3. Deploy. `frontend/vercel.json` rewrites routes to `index.html` for client-side routing.

### Other options
- **Railway or Fly.io:** deploy `backend/Dockerfile` the same way and attach their Postgres.
- **One machine:** `docker build -f backend/Dockerfile -t interview-api .` and run it next to Postgres, behind a reverse proxy that also serves `frontend/dist`.

## Readiness model

`backend/app/services/readiness.py` trains a Random Forest on a synthetic dataset with correlated features, because real institutional placement outcomes are not available. The API also reports Logistic Regression accuracy on the same data for comparison. Treat it as a proof of concept, not a validated hiring predictor; the UI says so.

## Project layout

```
backend/    Flask API: app/routes, app/services, app/models, migrations, tests, Dockerfile
frontend/   React app: src/pages, src/components, src/layouts, src/services
docs/       Architecture and design decisions
render.yaml Render Blueprint for the API and database
```
