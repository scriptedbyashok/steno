// Public runtime config. The anon key is meant to be public — it only
// grants Supabase Auth calls; RLS denies all direct table/anon access,
// so all data access still goes through the FastAPI backend.
const SUPABASE_URL = "https://ljifmuibxqnbdzcgsjpk.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqaWZtdWlieHFuYmR6Y2dzanBrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyOTk5MjQsImV4cCI6MjA5OTg3NTkyNH0.JrWyKteKkrBBIWCgKc9tjD-S9GuIUpRDTVxbDtaJYh4";

// The frontend is served same-origin from the FastAPI app (mounted at "/"),
// both locally and in production, so API calls are relative.
const API_BASE_URL = "";
