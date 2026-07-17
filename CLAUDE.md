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
