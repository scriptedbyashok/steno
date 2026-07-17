# Steno Practice

A stenographer dictation practice app. Listen to audio, type what you hear,
and get a word-by-word accuracy diff. See `CLAUDE.md` for the full feature
spec and conventions.

## Stack

- **Backend**: FastAPI (Python 3.11+), Supabase (Postgres + Storage + Auth).
- **Frontend**: plain HTML/CSS/JS, served as static files from the same
  FastAPI app — one deployed service, no CORS in production.

## Supabase setup (one-time, manual)

1. Create a project at [supabase.com](https://supabase.com).
2. In **SQL Editor**, run the migrations in order:
   - `supabase/migrations/001_init.sql`
   - `supabase/migrations/002_attempt_word_diff.sql`
3. In **Storage**, create a bucket named exactly `dictation-audio`, **private**
   (not public).
4. In **Authentication → Users**, add an admin user (email + password) —
   this account logs into `config.html` to upload/delete dictations.
5. In **Settings → API**, copy the Project URL, `anon` key, and
   `service_role`/secret key for the env vars below.

## Environment variables

| Variable | Where used | Notes |
|---|---|---|
| `SUPABASE_URL` | backend `.env`, `frontend/config.js` | Project base URL, no `/rest/v1` suffix |
| `SUPABASE_SERVICE_KEY` | backend `.env` only | Secret — bypasses RLS, never expose to the browser |
| `SUPABASE_ANON_KEY` | backend `.env`, `frontend/config.js` | Public — only used for Supabase Auth calls |

Copy `.env.example` to `.env` and fill in the three values for local
development. `frontend/config.js` also embeds `SUPABASE_URL` and
`SUPABASE_ANON_KEY` directly (they're meant to be public — RLS denies all
direct table access, so the anon key alone can't read/write data).

## Local development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` — the FastAPI app serves both the API
(`/api/*`, `/health`) and the static frontend (`/`, `/test.html`,
`/config.html`, ...) from one process.

Run tests:

```bash
cd backend
pytest
```

## Deployment (Render)

1. Push this repo to GitHub.
2. In Render, create a **New Web Service** from the repo — Render will
   auto-detect `render.yaml` (build/start commands, health check).
3. In the service's **Environment** settings, add `SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY`, and `SUPABASE_ANON_KEY` (these are marked
   `sync: false` in `render.yaml`, so they're not committed to git —
   set them manually in the dashboard).
4. Deploy. The service serves both the API and the frontend from the
   single URL Render gives you.

**Cold starts**: Render's free tier spins down after inactivity and can
take up to ~30s to wake on the next request. The frontend already handles
this — `frontend/api.js`'s `fetchWithColdStartRetry` shows a friendly
"Server is waking up…" toast and retries once automatically.
