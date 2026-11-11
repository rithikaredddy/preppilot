# Architecture and implementation plan

Phase 1 source of truth for the AI Interview Preparation Platform. Later phases implement this document. They do not invent a parallel design.

## 1. Product understanding

Students prepare for campus placements in one system: resume analysis, HR and technical mock interviews, coding assessment, company-specific practice, communication feedback, a performance dashboard, a placement-readiness estimate, a personalized roadmap, and a PDF report.

A Training & Placement Officer sees batch readiness, filters students, and drills into score breakdowns. The TPO does not see interview transcripts or private answers.

The twelve modules:

| Module | What it does | Completion signal |
| --- | --- | --- |
| 1. Authentication | Student self-registration. TPO accounts require an emailed 6-digit code. JWT access, bcrypt passwords, forgot/reset password, profile fields (name, email, branch, roll number). Backend role checks. | A student token cannot call TPO routes. A TPO token cannot call student practice routes. |
| 2. Resume analyzer | PDF and DOCX upload, text extraction, structured parse of skills, education, projects, experience, and certifications. ATS-style score and skill-match percentage against a selected job description. Missing skills, formatting issues, suggestions, downloadable analysis report. | Upload of a real file produces a stored analysis. Invalid type or oversize file is rejected. |
| 3. HR mock interview | Multi-turn interview grounded in the student profile and resume. Adaptive follow-ups. Rubric over answer specificity, communication, relevance, and professionalism. Textual confidence indicators are labeled as language signals, not measured emotion. Sessions and scores are stored. | A completed session has turns, scores, strengths, and improvements in the database. |
| 4. Technical interview | Topics: Java, Python, SQL, DBMS, OS, Computer Networks, OOP, DSA, ML. Difficulties: beginner, intermediate, advanced. Adaptive follow-ups and a shared rubric. Topic scores and weak areas are stored. | Scores are queryable by topic after a completed session. |
| 5. Coding assessment | CodeMirror editor. Python, Java, and C++. Execution goes to a Judge0-compatible service in production; local development uses a guarded subprocess runner (see section 3). Hidden tests stay hidden. Time and memory are shown when the executor returns them. AI review covers correctness, time complexity, space complexity, and improvements. Timeouts and unsafe code are handled by the sandbox. | A submission record stores per-test results without leaking hidden expected output. |
| 6. Company preparation | Curated question sets for selected companies, plus separately labeled AI-generated practice questions. HR, technical, and coding items with difficulty, topic, and tips. Content is loaded and updated from the backend, not from the TPO UI. | Each question row has `source = curated` or `source = ai_generated`. |
| 7. Communication analysis | Record or upload audio for selected interview answers. Speech-to-text, speaking rate, filler words, pauses when the transcript timing supports them, and clarity feedback. The UI states that this does not measure confidence, personality, or emotion. | Missing speech-to-text credentials return a configuration error. The API never invents a transcript. |
| 8. Performance dashboard | History, resume / HR / technical / coding / communication scores, strengths and weaknesses, Recharts trends. All series come from API data. | Charts match rows in `performance_events` for that student. |
| 9. Placement readiness | Reproducible synthetic dataset of 3,000 rows. Logistic Regression and Random Forest compared with a stratified split and no leakage. Saved model and preprocessing pipeline. `POST /api/v1/predict-placement` returns a percentage, a category, and top contributing factors from the student's real scores. Predictions are timestamped. Copy states that synthetic training data does not validate real hiring accuracy. | Training script prints accuracy, precision, recall, and F1 for both models. Inference refuses to run when required real scores are missing. |
| 10. Learning roadmap | Prioritized items from the student's weak areas, interview results, coding results, resume analysis, and ML factors. Each item has topic, priority, action, resource, and completion status. | Generated topics trace back to stored weakness records. |
| 11. Interview report | PDF built from stored scores: resume, interviews, coding, communication, readiness estimate, strengths, weaknesses, and actions. | The PDF content matches the database snapshot used to generate it. |
| 12. TPO dashboard | Read-only. Sortable, filterable student list (branch, readiness threshold). Average readiness and weak-area trends by branch. Drill-down shows score breakdown and weak areas only. | TPO detail payload has no question text, answer text, or source code. Aggregates match a manual calculation on the same rows. |

## 2. Architecture

Monorepo. The browser talks only to the Flask API. Flask talks to PostgreSQL, object storage on disk in development, the configured LLM, the speech-to-text provider, and the code-execution service.

```
frontend (Vite/React) -- HTTPS /api/v1 --> Flask
                                              |-- PostgreSQL
                                              |-- upload directory
                                              |-- LLM provider (Gemini, OpenAI or Anthropic)
                                              |-- speech-to-text provider
                                              |-- Judge0 (production) or local runner (dev)
                                              '-- ml/models (joblib pipeline)
```

Major decisions:

- Flask, as specified for this build. SQLAlchemy models and Alembic migrations via Flask-Migrate. Tables are not created only by `create_all` in production.
- JWT access tokens (short-lived) and rotating refresh tokens stored hashed in the database.
- Role checks live in backend decorators: `student_required` and `tpo_required`.
- One LLM provider interface (`complete_json`) with timeouts, retries, and JSON schema validation before any insert. Provider is `LLM_PROVIDER=gemini|openai|anthropic`.
- Resume parsing is deterministic (pypdf / python-docx) plus a skill taxonomy and an LLM structured analysis. A local Hugging Face embedding model is optional and is not required for the first working analyzer.
- Code execution goes to Judge0 when `JUDGE0_URL` is set. Without it, development runs code in a short-lived subprocess: a private temp folder, an environment with no secrets, CPU and file-size limits, and (for Python) guards that block networking, child processes and file access outside the temp folder. That runner is defence in depth, not an isolation boundary, so production refuses it unless `ALLOW_LOCAL_CODE_RUNNER=true` is set deliberately.
- Speech-to-text is a provider interface: Gemini audio input or OpenAI Whisper, whichever provider is configured (Anthropic has no speech-to-text, so voice transcription needs one of those two). Without credentials the endpoint returns HTTP 503 with a clear configuration message.
- Password reset emails go out through SMTP when configured. In development, `PASSWORD_RESET_DEV_EXPOSE=true` may return the reset token in the API response so the flow can be tested. That flag must stay false in production.
- Students self-register. TPO registration requires a 6-digit code emailed to that address. `TPO_ALLOWED_EMAILS` can limit which addresses may request a code.
- Company content is backend-managed: seed command plus an internal service. The TPO UI is read-only. A full admin panel is out of scope in the proposal.
- Uploaded files stay under `UPLOAD_DIR`, outside git, with allow-listed extensions and a size cap.
- Performance totals are stored as `performance_events` (append-only) and a `performance_summaries` row per student so the TPO list does not recompute every session on each page view. Summary updates happen in the same transaction as the scoring write.
- Placement prediction requires stored resume, interview, coding, and communication scores. Academic profile fields (CGPA, backlogs, internships, certifications, projects) come from the student profile. Missing academic fields use documented neutral defaults and the response says so. Missing practice scores abort the prediction.

## 3. Database schema

PostgreSQL. UUID primary keys. `created_at` and `updated_at` on mutable tables. Foreign keys indexed. Passwords and reset/refresh tokens stored only as hashes.

### Identity

`users`

- `id`, `email` unique, `password_hash`, `role` (`student` | `tpo`), `is_active`, `created_at`, `updated_at`

`refresh_tokens`

- `id`, `user_id` FK, `token_hash` unique, `expires_at`, `revoked_at`, `created_at`

`password_reset_tokens`

- `id`, `user_id` FK, `token_hash` unique, `expires_at`, `used_at`, `created_at`

`student_profiles`

- `user_id` unique FK, `full_name`, `roll_number` unique, `branch`, `graduation_year`
- Optional inputs for the model: `cgpa`, `backlogs`, `internship_count`, `certification_count`, `project_count`
- `phone` optional

`tpo_profiles`

- `user_id` unique FK, `full_name`, `department`, `designation`

Branch is a validated string (length-limited), not a hard-coded enum, so different colleges can use their own branch names. TPO filters use the distinct values present in the data.

### Resume

`resumes`

- `id`, `student_id` FK, `original_filename`, `stored_path`, `mime_type`, `file_size_bytes`, `extracted_text`, `created_at`

`resume_analyses`

- `id`, `resume_id` FK, `student_id` FK
- `target_role`, `job_description_text`
- `ats_score` numeric(5,2), `skill_match_percentage` numeric(5,2)
- JSON columns: `skills`, `education`, `projects`, `experience`, `certifications`, `missing_skills`, `formatting_issues`, `suggestions`
- `provider`, `model_name`, `created_at`

### Interviews

`interview_sessions`

- `id`, `student_id` FK, `kind` (`hr` | `technical`)
- `topic`, `difficulty` nullable
- `resume_id` nullable FK
- `status` (`in_progress` | `completed` | `abandoned`)
- `overall_score`, JSON `dimension_scores`, `strengths`, `improvements`, `weak_areas`
- `started_at`, `completed_at`

`interview_turns`

- `id`, `session_id` FK, `turn_index`, `question_text`, `answer_text` nullable
- `is_follow_up`, JSON `evaluation` nullable, `created_at`
- Private to the student. No TPO serializer reads this table.

### Coding

`coding_problems`

- `id`, `title`, `statement`, `difficulty`, `topic`, `starter_code` JSON by language
- `time_limit_ms`, `memory_limit_kb`, `source` (`curated` | `ai_generated`)
- `company_id` nullable FK

`coding_test_cases`

- `id`, `problem_id` FK, `stdin`, `expected_stdout`, `is_hidden`, `weight`

`coding_submissions`

- `id`, `student_id` FK, `problem_id` FK, `language`, `source_code`
- `status`, `passed_count`, `total_count`, `score`
- `execution_time_ms`, `memory_kb` nullable
- JSON `ai_review`, `created_at`

`coding_submission_results`

- `id`, `submission_id` FK, `test_case_id` FK, `passed`, `time_ms`, `memory_kb`, `stderr`
- Hidden cases omit `expected_stdout` from API responses. `stdout` for hidden failures is truncated.

### Company preparation

`companies`

- `id`, `name`, `slug` unique, `overview`

`company_questions`

- `id`, `company_id` FK, `category` (`hr` | `technical` | `coding`)
- `topic`, `difficulty`, `prompt`, `preparation_tip`
- `source` (`curated` | `ai_generated`), `created_at`

### Communication, scores, ML, roadmap, reports

`communication_analyses`

- `id`, `student_id` FK, `session_id` nullable FK, `turn_id` nullable FK
- `audio_path`, `transcript`, `duration_seconds`, `words_per_minute`
- `filler_count`, JSON `filler_words`, `pause_count` nullable
- `clarity_feedback`, `communication_score`, `created_at`

`performance_events`

- `id`, `student_id` FK, `category` (`resume` | `hr` | `technical` | `coding` | `communication`)
- `score`, `source_type`, `source_id`, `recorded_at`
- Index on `(student_id, recorded_at)`

`performance_summaries`

- `student_id` PK/FK, `resume_score`, `hr_score`, `technical_score`, `coding_score`, `communication_score`
- JSON `strengths`, `weaknesses`, `updated_at`
- Latest score per category, recomputed from events.

`placement_predictions`

- `id`, `student_id` FK, `model_name`, `model_version`
- `readiness_percentage`, `category` (`needs_support` | `developing` | `ready`)
- JSON `feature_inputs`, `contributing_factors`, `academic_defaults_used`
- `created_at`
- Categories are product bands on the model's probability: under 45, 45–69, 70 and above. They are not hiring cutoffs.

`roadmaps`

- `id`, `student_id` FK, JSON `basis` (the weakness snapshot used), `created_at`

`roadmap_items`

- `id`, `roadmap_id` FK, `topic`, `priority` (`high` | `medium` | `low`)
- `recommended_action`, `resource_title`, `resource_url`
- `source_weakness`, `status` (`pending` | `completed`), `sort_order`

`reports`

- `id`, `student_id` FK, `stored_path`, JSON `snapshot`, `created_at`

### Relationships

- A user has one student profile or one TPO profile.
- A student has many resumes, analyses, sessions, submissions, communication analyses, events, predictions, roadmaps, and reports.
- A session has many turns. A problem has many test cases and submissions. A submission has many results.
- A company has many questions and optional coding problems.
- `performance_summaries.student_id` is what the TPO list reads. Drill-down adds category scores and `weaknesses`. It does not join `interview_turns` or `coding_submissions.source_code`.

## 4. API plan

Base path: `/api/v1`. JSON errors use `{ "error": { "code", "message", "details" } }`. List endpoints accept `page` and `page_size` (max 50). OpenAPI UI at `/api/v1/docs`.

### Auth and profile

| Method | Path | Access |
| --- | --- | --- |
| POST | `/auth/tpo-otp` | Public. Sends a 6-digit TPO registration code to the email. |
| POST | `/auth/register` | Public. Body includes `role`. `tpo` requires the emailed `otp`. |
| POST | `/auth/login` | Public |
| POST | `/auth/refresh` | Refresh token |
| POST | `/auth/logout` | Authenticated. Revokes the refresh token. |
| POST | `/auth/forgot-password` | Public. Always returns a generic message. |
| POST | `/auth/reset-password` | Public, with valid reset token |
| GET | `/auth/me` | Authenticated |
| GET, PATCH | `/profile` | Student or TPO, own profile only |

### Student practice

| Method | Path | Access |
| --- | --- | --- |
| POST | `/resumes` | Student. Multipart file. |
| GET | `/resumes` | Student, own rows |
| GET | `/resumes/{id}` | Student owner |
| POST | `/resumes/{id}/analyze` | Student owner. Body: `target_role`, `job_description` |
| GET | `/resume-analyses/{id}` | Student owner |
| GET | `/resume-analyses/{id}/report` | Student owner. PDF download |
| POST | `/interviews` | Student. Body: `kind`, and for technical `topic`, `difficulty` |
| GET | `/interviews` | Student, paginated own sessions, no full turn dump in the list |
| GET | `/interviews/{id}` | Student owner, includes turns |
| POST | `/interviews/{id}/answers` | Student owner. Body: `answer` |
| POST | `/interviews/{id}/complete` | Student owner. Finalizes scores |
| GET | `/coding/problems` | Student |
| GET | `/coding/problems/{id}` | Student. Hidden tests excluded |
| POST | `/coding/problems/{id}/submit` | Student. Body: `language`, `source_code` |
| GET | `/coding/submissions` | Student, own |
| GET | `/coding/submissions/{id}` | Student owner |
| GET | `/companies` | Student |
| GET | `/companies/{slug}/questions` | Student. Query: `category`, `source` |
| POST | `/companies/{slug}/practice-questions` | Student. Generates questions and stores them as `ai_generated` |
| POST | `/communication/analyses` | Student. Multipart audio, optional `session_id` / `turn_id` |
| GET | `/communication/analyses` | Student, own |
| GET | `/dashboard/summary` | Student |
| GET | `/dashboard/history` | Student, paginated events |
| GET | `/dashboard/trends` | Student |
| POST | `/predict-placement` | Student. Uses stored scores |
| GET | `/predictions` | Student, own history |
| POST | `/roadmaps` | Student. Generates from current weaknesses |
| GET | `/roadmaps/current` | Student |
| PATCH | `/roadmap-items/{id}` | Student owner. Body: `status` |
| POST | `/reports` | Student. Builds PDF from current stored results |
| GET | `/reports` | Student, own |
| GET | `/reports/{id}/download` | Student owner |

`POST /api/v1/predict-placement` is the placement endpoint. The proposal's `/predict-placement` name is preserved under the versioned prefix.

### TPO

| Method | Path | Access |
| --- | --- | --- |
| GET | `/tpo/students` | TPO. Query: `branch`, `max_readiness`, `sort`, `page` |
| GET | `/tpo/students/{student_id}` | TPO. Scores and weak areas only |
| GET | `/tpo/analytics/branches` | TPO. Average readiness and weak-area counts by branch |

Student tokens receive 403 on `/tpo/*`. TPO tokens receive 403 on practice-write routes.

### Operational

| Method | Path | Access |
| --- | --- | --- |
| GET | `/health` | Public. Database connectivity, no secrets |

## 5. Frontend plan

Visual identity: a calm placement-office product. Off-white background, ink text, one deep blue accent, hairline borders, no decorative gradients. Shared components: `Button`, `TextField`, `Select`, `Card`, `Badge`, `Table`, `EmptyState`, `ErrorState`, `Spinner`, `PageHeader`, `ScoreBar`, `Toast`. Sidebar and top bar for authenticated shells. Student and TPO layouts are separate route trees.

### Public

- `/login`
- `/register` with role and a TPO email-code field
- `/forgot-password`
- `/reset-password`

### Student shell

- `/app` dashboard (module entry points and latest scores)
- `/app/profile`
- `/app/resume` upload, job description, analysis, report download
- `/app/interview/hr` active session
- `/app/interview/technical` topic and difficulty, then session
- `/app/interview/history`
- `/app/coding` problem list
- `/app/coding/:problemId` Monaco editor and results
- `/app/companies` and `/app/companies/:slug`
- `/app/communication` record/upload and feedback, with the limitation notice
- `/app/readiness` current estimate and trend
- `/app/roadmap`
- `/app/reports`

### TPO shell

- `/tpo` student table, branch filter, readiness threshold, sort
- `/tpo/analytics` branch averages and weak-area trends
- `/tpo/students/:studentId` score breakdown and weak areas

Data loading uses a typed API client. Pages render loading, empty, and error states from real responses.

## 6. External services and environment

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL (local Docker, Neon, or Supabase) |
| `JWT_SECRET` | Access token signing |
| `LLM_PROVIDER` | `gemini`, `openai` or `anthropic` |
| `OPENAI_API_KEY` | Used when the provider is OpenAI, and for Whisper |
| `OPENAI_MODEL` | Chat model name |
| `GEMINI_API_KEY` | Used when the provider is Gemini |
| `GEMINI_MODEL` | Gemini model name |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ANTHROPIC_EFFORT` | Used when the provider is Anthropic |
| `JUDGE0_URL` | Isolated code execution base URL |
| `JUDGE0_API_KEY`, `JUDGE0_HOST` | Hosted Judge0 (RapidAPI) credentials |
| `ALLOW_LOCAL_CODE_RUNNER` | Local subprocess runner; defaults on in development, off in production |
| `LOCAL_RUNNER_LANGUAGES` | Languages the local runner accepts (`python,java,cpp`); the free deployment uses `python` |
| `LOGIN_MAX_FAILURES`, `LOGIN_LOCKOUT_MINUTES` | Failed sign-in throttle (default 5 per 15 minutes) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | Password reset mail |
| `PASSWORD_RESET_DEV_EXPOSE` | Development-only reset token echo |
| `TPO_ALLOWED_EMAILS` | Comma-separated emails allowed to request a TPO code; required in production |
| `UPLOAD_DIR` | Resume and audio storage |
| `MAX_UPLOAD_BYTES` | Default 5 MB |
| `CORS_ORIGINS` | Frontend origin |
| `FRONTEND_URL` | Links inside reset emails |

Dependencies are pinned at install time after a compatibility check. Expected backend libraries: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended or PyJWT, bcrypt, psycopg, marshmallow, flask-smorest or flasgger for OpenAPI, pypdf, python-docx, reportlab, httpx, scikit-learn, pandas, joblib. Frontend: React 19, Vite, TypeScript, Tailwind, React Router, Recharts, CodeMirror. ML extras: scikit-learn, pandas, joblib. Hugging Face Transformers is optional for a later embedding skill-match and is not on the critical path.

Local Docker Compose provides PostgreSQL. The backend ships as a Docker image (`backend/Dockerfile`, gunicorn) with a Render Blueprint (`render.yaml`); the frontend deploys to Vercel (`frontend/vercel.json`); the database can be Render Postgres, Neon or Supabase. Production code execution uses hosted Judge0. API keys stay in environment variables.

## 7. Phase plan

| Phase | Build | Done when |
| --- | --- | --- |
| 1 | This document | Schema, APIs, pages, and decisions are written and the email-scheduler repo is unchanged. |
| 2 | Scaffold, env example, Compose, migrations, auth, profile, role guards, auth tests | Register, login, refresh, reset, and a 403 test for cross-role access pass. |
| 3 | Resume upload, parse, LLM analysis, analysis PDF | A PDF and a DOCX fixture produce stored scores. A bad file is rejected. Provider errors surface when no key is set. |
| 4 | HR and technical interview sessions | Multi-turn fixture flow stores scores and weak areas. |
| 5 | Coding problems, Judge0 client, AI review | Hidden tests are absent from the problem payload. A sample Python solution passes visible tests through the configured executor. |
| 6 | Company seed data and communication analysis | Curated vs AI source is visible. Audio without speech credentials returns 503. |
| 7 | Dashboard APIs and Recharts pages | Summary numbers equal the event rows for a seeded student. |
| 8 | Synthetic data, training, evaluation report, predict API | Both models' metrics are written to `ml/`. Predict uses stored scores and appends history. |
| 9 | Roadmap and performance PDF | Roadmap topics match stored weaknesses. Report PDF opens and lists stored scores. |
| 10 | TPO list, filters, analytics, drill-down, privacy tests | Branch averages match SQL. Detail JSON has no transcripts or source code. |
| 11 | End-to-end pass, deployment docs, viva notes | Seeded student and TPO can walk the proposal workflow. README covers macOS and Windows. |

## 8. Locked decisions and proposal risks

- The workspace that was open at the start is the Outbox email scheduler (`outbox-email-scheduler`, Express/Prisma/BullMQ). This capstone lives in `ai-interview-platform`.
- "Confidence" in the HR rubric is a text score for specificity, hedging, and structure. The product copy calls it confidence-related language. Voice analysis does not output confidence, personality, or emotion.
- Production code runs only in Judge0. If Judge0 is down, submission returns a service error and stores nothing that looks like a passing result.
- LLM and speech calls fail visibly when keys are missing. There is no canned interview score or fake transcript.
- Prediction is a proof of concept trained on synthetic labels. UI and API include that limitation. The model is not described as a validated hiring predictor.
- Readiness bands (needs support / developing / ready) are display thresholds on predicted probability.
- TPO accounts require an emailed code. `TPO_ALLOWED_EMAILS` can restrict which addresses may request one, because an open TPO registration would expose every student's scores.
- Company question management is a backend seed and service. The proposal puts a full admin panel out of scope, and the TPO dashboard is read-only.
- CGPA, backlogs, internships, certifications, and projects are profile fields because they are training features the practice modules do not produce. Practice scores must be real before prediction.
- Resume "ATS score" is a documented heuristic plus LLM structured feedback, not a vendor ATS.
- LLM scores can vary between runs. That limitation stays visible in the report and viva notes.
- Voice is available on communication analysis and as an optional attachment to interview answers. Text remains the primary interview mode.
