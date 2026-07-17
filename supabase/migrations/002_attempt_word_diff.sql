-- Phase 5: store each attempt's word_diff so history can re-render it
-- without recomputing against the (server-only) transcript.
alter table attempts add column if not exists word_diff jsonb;
