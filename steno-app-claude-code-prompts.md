# Stenographer Practice App — Claude Code Phased Prompts

**How to use:** Run Phase 0 first (project context), then paste each phase prompt one at a time. Verify the checkpoint before moving to the next phase. Don't combine phases — smaller scopes give better results.

---

## Phase 0 — Project Setup & CLAUDE.md

```
Create a new project called "steno-practice" with this structure:
- backend/ → FastAPI (Python 3.11+)
- frontend/ → plain HTML/CSS/JS (no framework), mobile-friendly
- Supabase for DB + Storage + Auth

Create a CLAUDE.md at the root documenting:

PROJECT: Stenographer dictation practice app.
- Homepage lists dictation cards. Each card opens a test page.
- Test page: audio player with unlimited replay → user clicks "Start Test" →
  audio is hidden/disabled → textarea appears → optional countdown timer
  (per-dictation config) → Submit or Cancel. Timer expiry auto-submits.
- Submit compares typed text vs reference transcript word-by-word
  (server-side, using difflib.SequenceMatcher on normalized words) and
  returns per-word statuses: correct | wrong | missed | extra, plus accuracy %.
- Cancel returns to audio view; nothing saved.
- Config page (admin only, Supabase Auth JWT) uploads audio + transcript +
  title + optional time limit.
- Attempt history saved per dictation.

STACK & CONVENTIONS:
- FastAPI with routers: dictations, attempts, admin. Pydantic models.
- Supabase Python client for DB; audio in a Storage bucket "dictation-audio",
  served via signed URLs.
- Transcript stored as a text column, NOT a file.
- Frontend: index.html (cards), test.html (player + test), config.html (admin),
  shared app.js/api.js/styles.css. Fetch API only.
- Environment via .env: SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY.
- Server-side diffing only — transcript must never reach the browser before submit.

Do not write feature code yet. Only scaffold folders, requirements.txt,
.env.example, .gitignore, and CLAUDE.md.
```

**Checkpoint:** Folder structure + CLAUDE.md exist. `pip install -r requirements.txt` works.

---

## Phase 1 — Database Schema & Supabase Setup

```
Create a SQL migration file (supabase/migrations/001_init.sql) with:

dictations:
  id uuid pk default gen_random_uuid(),
  title text not null,
  audio_path text not null,
  transcript text not null,
  time_limit_seconds int null,   -- null = untimed
  created_at timestamptz default now()

attempts:
  id uuid pk default gen_random_uuid(),
  dictation_id uuid references dictations(id) on delete cascade,
  typed_text text not null,
  accuracy numeric not null,
  total_words int, correct int, wrong int, missed int, extra int,
  time_taken_seconds int,
  created_at timestamptz default now()

Add RLS policies: public read on dictations (excluding transcript is not
possible via RLS column-level, so all reads go through the FastAPI backend —
enable RLS and deny anon access entirely; backend uses service key).

Also write backend/app/db.py with a Supabase client singleton reading from .env,
and backend/app/models.py with Pydantic schemas for both tables
(DictationCard must EXCLUDE transcript).
```

**Checkpoint:** Run migration in Supabase SQL editor. Tables visible. Create the `dictation-audio` storage bucket manually (private).

---

## Phase 2 — Backend API (Core)

```
Implement the FastAPI backend per CLAUDE.md:

1. GET /api/dictations → list cards: id, title, time_limit_seconds,
   audio duration (nullable), attempt_count. NO transcript.
2. GET /api/dictations/{id} → same fields + signed audio URL (1 hour expiry).
   NO transcript.
3. POST /api/dictations/{id}/submit → body: { typed_text, time_taken_seconds }.
   - Fetch transcript server-side.
   - Normalize both texts: lowercase, strip punctuation, split on whitespace.
   - Use difflib.SequenceMatcher.get_opcodes() on the word lists to classify
     each reference word as correct/wrong/missed and typed-only words as extra.
     "replace" opcodes = wrong (pair them positionally; leftover ref words =
     missed, leftover typed words = extra).
   - accuracy = correct / total_reference_words * 100, rounded to 2 decimals.
   - Save attempt row. Return JSON: accuracy, counts, and a word_diff array of
     { word, status } preserving ORIGINAL (un-normalized) reference/typed words
     so the frontend can render them faithfully.
4. GET /api/dictations/{id}/attempts → history, newest first.

Add CORS middleware (allow the frontend origin), and a /health endpoint.
Write unit tests for the diff function covering: perfect match, one wrong word,
missed word mid-sentence, extra word, punctuation/case differences, empty input.
Run the tests and fix until green.
```

**Checkpoint:** `pytest` green. Test endpoints with curl/HTTPie against a manually inserted dictation row.

---

## Phase 3 — Admin Config (Auth + Upload)

```
1. Backend: POST /api/admin/dictations (multipart form): audio file (mp3/wav/m4a,
   max 25 MB), title, transcript (text field), time_limit_seconds (optional).
   - Verify Supabase Auth JWT from Authorization header via a FastAPI dependency
     (decode with SUPABASE_JWT_SECRET or call supabase.auth.get_user).
   - Upload audio to dictation-audio bucket at {uuid}.{ext}, insert row.
   Also: DELETE /api/admin/dictations/{id} (removes storage object + row).

2. Frontend config.html:
   - Login form (email/password) using Supabase Auth REST via fetch; store
     access token in memory/sessionStorage.
   - After login: upload form (file picker, title, transcript textarea,
     optional time limit input with a "Timed test?" toggle), list of existing
     dictations with delete buttons.
   - Show upload progress and success/error toasts.
```

**Checkpoint:** Create an admin user in Supabase Auth dashboard. Log in, upload one real audio + transcript, see it via GET /api/dictations.

---

## Phase 4 — Test Flow Frontend

```
Build index.html and test.html:

index.html:
- Fetch /api/dictations, render cards: title, timed badge ("⏱ 10:00" or
  "Untimed"), attempt count. Card click → test.html?id={id}.

test.html — a small state machine with states: LISTENING, TESTING, RESULT.

LISTENING:
- <audio controls> with the signed URL. Unlimited replay.
- "Start Test" button.

TESTING (on Start Test):
- Remove/pause the audio element entirely from the DOM (not just hide via CSS).
- Show a large textarea (disable paste, spellcheck off, autocomplete off).
- If time_limit_seconds set: countdown timer top-right; auto-submit at 0.
  Else: count-up elapsed timer.
- Buttons: Submit and Cancel. Cancel → confirm dialog → back to LISTENING
  (restore audio, clear textarea, nothing sent).
- Warn on page unload during TESTING.

RESULT (after submit response):
- Accuracy % prominently, counts (correct/wrong/missed/extra).
- Render word_diff: correct = green, wrong = red with the typed word shown
  struck-through next to expected, missed = red underline, extra = orange
  strikethrough.
- Buttons: "Try Again" (back to LISTENING) and "Home".

Keep it mobile-friendly (this will be used on phones too).
```

**Checkpoint:** Full happy path works end-to-end: play → start → type → submit → see highlighted diff. Verify audio is truly gone from DOM during TESTING and transcript never appears in any network response before submit.

---

## Phase 5 — Attempt History + Polish

```
1. On test.html RESULT state and on each homepage card, show best accuracy and
   last attempt date from /api/dictations/{id}/attempts.
2. Add an "Attempts" section on test.html (collapsible list: date, accuracy,
   time taken; click to re-view that attempt's diff — store word_diff JSON in
   the attempts table as a jsonb column, add migration 002).
3. Empty states: no dictations yet (homepage), no attempts yet.
4. Loading spinners on all fetches; friendly error messages if backend is
   cold-starting (Render free tier can take ~30s).
```

**Checkpoint:** History persists across refresh; re-viewing an old attempt shows its original diff.

---

## Phase 6 — Deployment

```
Prepare for deployment:
1. Backend → Render web service: render.yaml or start command
   "uvicorn app.main:app --host 0.0.0.0 --port $PORT", env vars documented
   in README.
2. Frontend → serve as static files from FastAPI (mount frontend/ at /) so
   one Render service hosts everything, avoiding CORS in production.
3. README.md: setup steps, Supabase manual steps (bucket, auth user,
   migrations), env vars, local run instructions.
```

**Checkpoint:** Deployed URL works on your iPhone; cold-start message shows gracefully.

---

## Tips for running these with Claude Code

- After each phase, commit: `git add -A && git commit -m "Phase N: ..."` — easy rollback if a phase goes sideways.
- If a phase output drifts, say: "Re-read CLAUDE.md and fix X to match the conventions there" instead of re-explaining.
- Phase 2's diff tests are the most important checkpoint — don't skip running them; scoring correctness is the heart of the app.
- You can add later phases: WPM calculation, difficulty tags on cards, multiple admin users, or Hindi/regional language transcript support (normalization rules differ — worth a dedicated phase if needed).
