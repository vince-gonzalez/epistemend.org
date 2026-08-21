-- ============================================================
-- epistemend orders — the state behind a paid check
-- F-Keys | www.f-keys.com
-- ------------------------------------------------------------
-- Four tables and one rule: nothing is ever silently lost. An
-- order that was paid for and produced nothing is a row that
-- says so, not an absence.
--
--   wrangler d1 execute epistemend --remote --file=schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS orders (
  id            TEXT PRIMARY KEY,          -- ord_<random>
  sku           TEXT NOT NULL,             -- reference-check | record-report
  email         TEXT NOT NULL,
  payload       TEXT NOT NULL,             -- what to check, as JSON
  amount_cents  INTEGER NOT NULL,          -- decided server side, never sent by the browser
  currency      TEXT NOT NULL DEFAULT 'usd',
  status        TEXT NOT NULL DEFAULT 'pending_payment',
                                           -- pending_payment | paid | refunded | abandoned
  stripe_session TEXT,
  created_at    TEXT NOT NULL,
  paid_at       TEXT
);

CREATE INDEX IF NOT EXISTS orders_status ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS orders_session ON orders(stripe_session);

-- A payment confirmation may arrive more than once. Recording the event id
-- is what makes a repeat delivery change nothing, and Stripe does retry.
CREATE TABLE IF NOT EXISTS stripe_events (
  id         TEXT PRIMARY KEY,
  kind       TEXT NOT NULL,
  seen_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id          TEXT PRIMARY KEY,            -- job_<random>
  order_id    TEXT NOT NULL REFERENCES orders(id),
  status      TEXT NOT NULL DEFAULT 'queued',
                                           -- queued | running | complete | needs_attention
  attempts    INTEGER NOT NULL DEFAULT 0,
  token       TEXT NOT NULL,               -- the unguessable half of the report address
  result      TEXT,                        -- the findings, as JSON
  created_at  TEXT NOT NULL,
  started_at  TEXT,
  finished_at TEXT
);

CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS jobs_token ON jobs(token);

-- One row per thing that happened to a job. A report that is queried later
-- has a timeline behind it rather than a claim.
CREATE TABLE IF NOT EXISTS job_events (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id    TEXT NOT NULL REFERENCES jobs(id),
  at        TEXT NOT NULL,
  event     TEXT NOT NULL,
  detail    TEXT
);

CREATE INDEX IF NOT EXISTS job_events_job ON job_events(job_id, at);
