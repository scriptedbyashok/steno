-- Phase 7: multi-user auth + per-user data scoping.
--
-- Users are our own table (not Supabase Auth) so we control roles and
-- password hashing directly. pgcrypto's crypt()/gen_salt('bf') produces
-- standard bcrypt hashes ($2a$... ) that Python's `bcrypt` library can
-- verify directly, so seeding here and verifying in the backend agree.

create extension if not exists "pgcrypto";

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  username text not null unique,
  display_name text not null,
  password_hash text not null,
  role text not null check (role in ('admin', 'user')),
  created_at timestamptz not null default now()
);

alter table users enable row level security;
-- No policies: same pattern as dictations/attempts — only the backend's
-- service key talks to this table, anon access is denied entirely.

-- Seed the 3 required accounts (idempotent — safe to re-run this migration).
insert into users (username, display_name, password_hash, role)
values
  ('ashok', 'Ashok', crypt('Welcome@123', gen_salt('bf')), 'admin'),
  ('priya', 'Priya', crypt('Welcome@123', gen_salt('bf')), 'user'),
  ('rahul', 'Rahul', crypt('Welcome@123', gen_salt('bf')), 'user')
on conflict (username) do nothing;

-- Scope attempts to the user who made them.
alter table attempts add column if not exists user_id uuid references users(id) on delete cascade;

-- Migrate any pre-existing attempts (from before multi-user support) to
-- the admin account, then make the column mandatory for all future rows.
update attempts set user_id = (select id from users where username = 'ashok')
where user_id is null;

alter table attempts alter column user_id set not null;

create index if not exists attempts_user_id_idx on attempts(user_id);
