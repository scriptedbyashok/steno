# Steno

A stenographer dictation practice app. Listen to audio, type what you hear,
and get a word-by-word accuracy diff. See `CLAUDE.md` for the full feature
spec and conventions.

## Stack

- **Backend**: FastAPI (Python 3.11+), Supabase Postgres + Storage (used
  purely as a database/file store — auth is our own, not Supabase Auth).
- **Frontend**: plain HTML/CSS/JS, served as static files from the same
  FastAPI app — one deployed service, no CORS in production.

## Authentication & roles

The app has its own `users` table (bcrypt-hashed passwords, no Supabase
Auth involved) with two roles:

- **admin** — everything a `user` can do, plus: upload/delete dictations
  (`config.html`) and manage user accounts (`admin.html`).
- **user** — browse dictations, take tests, and see their own attempt
  history only. Dictations themselves are shared content everyone
  practices from; **attempts are private per user** — nobody sees anyone
  else's practice history or accuracy stats, including other users' best
  score / last-attempt date on the homepage cards.

Every page requires login (`login.html` is the only page reachable
unauthenticated). Sessions are a backend-issued JWT (7-day expiry) held in
`sessionStorage`, sent as a `Bearer` token — the same pattern the admin
upload flow already used before this feature, just no longer tied to
Supabase Auth. The admin console and its API routes are guarded on both
sides: the frontend redirects non-admins away from `admin.html`/
`config.html` (even via direct URL), and the backend independently
rejects non-admin requests to `/api/admin/*` with 403, so the frontend
guard is a UX nicety, not the actual security boundary.

**Deleting a user cascades to their attempts** (`attempts.user_id` has
`ON DELETE CASCADE`) — their personal practice history has no meaning
once the account is gone, and there's no cross-user data left orphaned.
An admin cannot delete their own account (prevents accidentally locking
everyone out).

### Seed accounts

Migration `003_users_and_scoping.sql` seeds three accounts on first run,
password **`Welcome@123`** for all of them:

| Username | Role | Password |
|---|---|---|
| `ashok` | admin | `Welcome@123` |
| `priya` | user | `Welcome@123` |
| `rahul` | user | `Welcome@123` |

Change these passwords (via the admin console, or by logging in and using
`PATCH /api/admin/users/{id}`) before using this anywhere but local
development — they're seeded in plaintext right here in the README.

## Supabase setup (one-time, manual)

1. Create a project at [supabase.com](https://supabase.com).
2. In **SQL Editor**, run the migrations in order:
   - `supabase/migrations/001_init.sql`
   - `supabase/migrations/002_attempt_word_diff.sql`
   - `supabase/migrations/003_users_and_scoping.sql`
3. In **Storage**, create a bucket named exactly `dictation-audio`, **private**
   (not public).
4. In **Settings → API**, copy the Project URL and the `service_role`/secret
   key for the env vars below. (No Supabase Auth setup needed — login is
   handled by our own `users` table.)

## Environment variables

| Variable | Where used | Notes |
|---|---|---|
| `SUPABASE_URL` | backend `.env` | Project base URL, no `/rest/v1` suffix |
| `SUPABASE_SERVICE_KEY` | backend `.env` only | Secret — bypasses RLS, never expose to the browser |
| `JWT_SECRET` | backend `.env` only | Signs/verifies session tokens — keep secret, rotate to invalidate all sessions |

Copy `.env.example` to `.env` and fill in the three values for local
development (generate `JWT_SECRET` with e.g. `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`).

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
`/config.html`, `/admin.html`, `/login.html`) from one process. You'll be
redirected to `/login.html` until you sign in with one of the seed
accounts above.

Run tests:

```bash
cd backend
pytest
```

## Deployment (Render)

1. Push this repo to GitHub.
2. In Render, create a **New Web Service** from the repo — Render will
   auto-detect `render.yaml` (build/start commands, health check).
3. In the service's **Environment** settings, add `SUPABASE_URL` and
   `SUPABASE_SERVICE_KEY` (marked `sync: false` in `render.yaml`, so set
   them manually). `JWT_SECRET` is generated automatically by Render
   (`generateValue: true`) — no action needed there.
4. Deploy. The service serves both the API and the frontend from the
   single URL Render gives you.

**Cold starts**: Render's free tier spins down after inactivity and can
take up to ~30s to wake on the next request. The frontend already handles
this — `frontend/api.js`'s `fetchWithColdStartRetry` shows a friendly
"Server is waking up…" toast and retries once automatically.
