-- Phase 8: soft-delete for dictations.
--
-- Admins can now hide a dictation (recoverable) instead of only being able
-- to permanently remove it. A null deleted_at means "active"; a timestamp
-- means "hidden from users as of that time" but the row/attempts remain
-- intact until an explicit permanent delete.
alter table dictations add column if not exists deleted_at timestamptz null;
create index if not exists dictations_deleted_at_idx on dictations(deleted_at);
