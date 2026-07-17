PROJECT: "Steno" — a stenographer dictation practice app, multi-user.
- Every page requires login (login.html only page reachable unauthenticated).
- Homepage lists dictation cards. Each card opens a test page.
- Test page: audio player with unlimited replay → user clicks "Start Test" →
  audio is hidden/disabled → textarea appears → optional countdown timer
  (per-dictation config) → Submit or Cancel. Timer expiry auto-submits.
- Submit compares typed text vs reference transcript word-by-word
  (server-side, using difflib.SequenceMatcher on normalized words) and
  returns per-word statuses: correct | wrong | missed | extra, plus accuracy %.
- Cancel returns to audio view; nothing saved.
- Dictations are shared content (uploaded by admins, practiced by everyone).
  Attempts are private per user — each user only sees their own attempt
  history, best accuracy, and last-attempt date.
- Config page (admin only) uploads audio + transcript + title + optional
  time limit. Admin page (admin only) manages user accounts.
- Roles: admin | user. Deleting a user cascades to their attempts. Admins
  cannot delete their own account.

STACK & CONVENTIONS:
- FastAPI with routers: auth, users, dictations, attempts, admin. Pydantic models.
- Supabase Python client for Postgres + Storage only — NOT Supabase Auth.
  Auth is our own `users` table (bcrypt password hashes) + backend-issued
  JWTs (see backend/app/auth.py). Audio in Storage bucket "dictation-audio",
  served via signed URLs.
- Transcript stored as a text column, NOT a file.
- Frontend: login.html, index.html (cards), test.html (player + test),
  config.html (admin: dictations), admin.html (admin: users), shared
  app.js/api.js/styles.css. Fetch API only. Every protected page calls
  `requireAuth()` (optionally `{ adminOnly: true }`) before rendering.
- Environment via .env: SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET.
- Server-side diffing only — transcript must never reach the browser before submit.
