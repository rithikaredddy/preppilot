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

## Deploy for free

Everything below runs on free plans with no credit card: **Neon** (database), **Render** (API), **Vercel** (website), **Google AI Studio** (Gemini key) and **Gmail** (emails). Do the steps in order; each one gives you a value the next one needs.

### 1. Database on Neon (about 3 minutes)
1. Sign up at https://neon.tech with GitHub and create a project (any name, nearest region).
2. On the project dashboard, copy the **connection string**. It looks like `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`. Keep it for step 3.

Neon's free database does not expire. Render's free Postgres is deleted after 30 days, so it is not used here.

### 2. Gmail app password (about 3 minutes)
TPO sign-up codes and password-reset links are emailed, so the live site needs a mail account.
1. Turn on 2-Step Verification for the Gmail account at https://myaccount.google.com/security.
2. Create an app password at https://myaccount.google.com/apppasswords (name it "PrepPilot") and copy the 16-character password.

### 3. API on Render (about 10 minutes, mostly waiting for the build)
1. Sign up at https://render.com with GitHub and allow access to the `preppilot` repository.
2. Choose **New → Blueprint**, pick the repository, and click **Apply**. `render.yaml` creates the `preppilot-api` service and generates `SECRET_KEY` and `JWT_SECRET`.
3. Fill in the values it asks for:

| Setting | Value |
| --- | --- |
| `DATABASE_URL` | Neon connection string from step 1 |
| `GEMINI_API_KEY` | Your key from https://aistudio.google.com/app/apikey |
| `TPO_ALLOWED_EMAILS` | Placement office email(s), comma-separated |
| `SMTP_USERNAME` / `SMTP_FROM` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail app password from step 2 |
| `FRONTEND_URL` / `CORS_ORIGINS` | Leave as `https://example.com` for now; fixed in step 5 |
| `JUDGE0_URL`, `JUDGE0_API_KEY`, `JUDGE0_HOST` | Leave empty (optional, see below) |

4. Wait for the deploy to finish (first build takes 5–10 minutes). Migrations run automatically on start.
5. Open `https://<your-service>.onrender.com/api/v1/health`. It should show `{"database":"ok","status":"ok"}`. Copy the service URL.

### 4. Website on Vercel (about 3 minutes)
1. Sign up at https://vercel.com with GitHub and **Add New → Project**, then import `preppilot`.
2. Set **Root Directory** to `frontend`. The framework is detected as Vite.
3. Add the environment variable `VITE_API_URL` = your Render URL from step 3, without a trailing slash.
4. Click **Deploy** and copy the site URL, for example `https://preppilot.vercel.app`.

### 5. Connect the two
In Render, open the service's **Environment** tab and set both `FRONTEND_URL` and `CORS_ORIGINS` to the Vercel URL, then save. Render redeploys by itself. Open the Vercel URL, register a student and try a resume analysis.

From now on, every `git push` to `main` redeploys both sites automatically.

### What the free plans mean
- **Cold starts:** Render's free API sleeps after 15 minutes without traffic, and the first request then takes about a minute. Open the site a few minutes before a demo. A free monitor such as UptimeRobot pinging `/api/v1/health` every 10 minutes keeps it awake.
- **Coding languages:** the live site runs **Python** submissions on the server with the guarded runner. Java and C++ show a clear "not available" message unless you add a Judge0 key. Judge0 CE on RapidAPI has a free Basic plan: set `JUDGE0_URL=https://judge0-ce.p.rapidapi.com`, `JUDGE0_HOST=judge0-ce.p.rapidapi.com` and your RapidAPI key as `JUDGE0_API_KEY`. Its daily quota is small, and each test case counts as one request.
- **Uploaded resumes** are stored on the server's disk, which the free plan resets on each redeploy. Scores and analyses are kept in the database; only the original files are lost.
- **Gemini free tier** has per-minute and per-day request limits, which are plenty for a class demo.

## Readiness model

`backend/app/services/readiness.py` trains a Random Forest on a synthetic dataset with correlated features, because real institutional placement outcomes are not available. The API also reports Logistic Regression accuracy on the same data for comparison. Treat it as a proof of concept, not a validated hiring predictor; the UI says so.

## Project layout

```
backend/    Flask API: app/routes, app/services, app/models, migrations, tests, Dockerfile
frontend/   React app: src/pages, src/components, src/layouts, src/services
docs/       Architecture and design decisions
render.yaml Render Blueprint for the API and database
```
