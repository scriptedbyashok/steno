-- Phase 1: initial schema for stenographer dictation practice app

create extension if not exists "pgcrypto";

create table if not exists dictations (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  audio_path text not null,
  transcript text not null,
  time_limit_seconds int null,
  created_at timestamptz not null default now()
);

create table if not exists attempts (
  id uuid primary key default gen_random_uuid(),
  dictation_id uuid not null references dictations(id) on delete cascade,
  typed_text text not null,
  accuracy numeric not null,
  total_words int,
  correct int,
  wrong int,
  missed int,
  extra int,
  time_taken_seconds int,
  created_at timestamptz not null default now()
);

create index if not exists attempts_dictation_id_idx on attempts(dictation_id);

-- RLS: deny all anon access. The FastAPI backend uses the service key
-- (which bypasses RLS), so no policies are defined here on purpose —
-- reads/writes only ever happen through the backend, never directly
-- from the browser via the anon key.
alter table dictations enable row level security;
alter table attempts enable row level security;
