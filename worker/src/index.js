/* ============================================================
   epistemend-orders — the path from a filled-in form to a
                       queued job
   F-Keys | www.f-keys.com
   ------------------------------------------------------------
   ROUTES

     POST /api/checkout   an order arrives; returns a Stripe
                          Checkout address to send them to
     POST /api/stripe     Stripe says the payment cleared; the
                          job is queued and the runner woken
     GET  /api/status     what happened to one order
     GET  /api/report     the findings, by their token

   WHAT IS DELIBERATE

   The price is decided here and never read from the request.
   A browser that can name its own amount is a browser that
   will.

   The Stripe signature is verified before the body is
   believed. An endpoint that queues work for anyone who posts
   to it is an endpoint that will be found.

   Every payment event id is written down. Stripe retries
   delivery, and a retry has to change nothing.

   A job that fails three times stops, says so, and refunds.
   Work that cannot be done is not work that gets billed.

   No dependencies.
   ============================================================ */

/* The Terms will change. "They agreed to the Terms" is unfalsifiable
   unless the record says WHICH Terms, so every order stores this and it
   is bumped whenever the wording changes. */
const TERMS_VERSION = '2026-09-07';

const SKUS = {
  'reference-check': {
    amount: 1900,
    name: 'Reference Check',
    blurb: 'Every reference resolved, and every link followed'
  },
  'record-report': {
    amount: 3900,
    name: 'Record Report',
    blurb: 'A full sweep of one author’s published record'
  }
};

const SITE = 'https://www.epistemend.org';
const MAX_ATTEMPTS = 3;

/* ── small helpers ───────────────────────────────────────── */

const now = () => new Date().toISOString();

const id = (prefix) => {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return prefix + Array.from(bytes, (b) => b.toString(16).padStart(2, '0'))
    .join('');
};

const json = (body, status = 200, origin = SITE) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin,
      'Cache-Control': 'no-store'
    }
  });

const bad = (message, status = 400) => json({ error: message }, status);

/* ── Stripe ──────────────────────────────────────────────── */

async function stripe(env, path, params) {
  const body = new URLSearchParams(params).toString();
  const r = await fetch('https://api.stripe.com/v1/' + path, {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + env.STRIPE_SECRET_KEY,
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body
  });
  const out = await r.json();
  if (!r.ok) {
    throw new Error((out.error && out.error.message) || 'stripe ' + r.status);
  }
  return out;
}

/*
  Verify the payload came from Stripe before anything is done about it.

  The header carries a timestamp and a signature over "<timestamp>.<body>".
  The timestamp is checked as well as the signature, because a valid
  signature replayed a week later is still a valid signature.
*/
async function verifyStripe(env, raw, header) {
  if (!header) { return false; }
  const parts = Object.fromEntries(
    header.split(',').map((p) => p.split('=', 2))
  );
  if (!parts.t || !parts.v1) { return false; }

  const age = Math.abs(Date.now() / 1000 - Number(parts.t));
  if (!Number.isFinite(age) || age > 300) { return false; }

  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(env.STRIPE_WEBHOOK_SECRET),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const mac = await crypto.subtle.sign(
    'HMAC', key, new TextEncoder().encode(parts.t + '.' + raw)
  );
  const expected = Array.from(new Uint8Array(mac),
    (b) => b.toString(16).padStart(2, '0')).join('');

  /* Compared without an early return, so the time taken says nothing about
     how much of the signature was right. */
  if (expected.length !== parts.v1.length) { return false; }
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ parts.v1.charCodeAt(i);
  }
  return diff === 0;
}

/* ── mail ────────────────────────────────────────────────── */

/*
  Three things get said to a customer, and only one of them was being said.

  A charge that appears and reverses with no explanation reads as a fault
  rather than as the policy working, so the refund carries a message. The
  confirmation exists for the same reason: silence between paying and
  receiving is where somebody writes to ask whether it went through.
*/
async function mail(env, to, subject, lines) {
  if (!env.RESEND_API_KEY) { return false; }
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + env.RESEND_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      from: 'Epistemend <reports@epistemend.org>',
      to: [to],
      reply_to: 'hello@epistemend.org',
      subject,
      text: lines.join('\n')
    })
  });
  if (!r.ok) {
    /* Resend refuses for reasons that are not outages: an unverified
       domain, a suppressed address, a rate limit. Each returns a body
       saying which. Discarding it is how "the customer never got the
       email" becomes unanswerable. */
    let why = '';
    try { why = (await r.text()).slice(0, 300); } catch (e) { }
    return { ok: false, status: r.status, why: why };
  }
  return { ok: true, status: r.status, why: '' };
}

/* ── the runner ──────────────────────────────────────────── */

async function wakeRunner(env, jobId) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) { return false; }
  const r = await fetch(
    'https://api.github.com/repos/' + env.GITHUB_REPO + '/dispatches', {
      method: 'POST',
      headers: {
        Authorization: 'Bearer ' + env.GITHUB_TOKEN,
        Accept: 'application/vnd.github+json',
        'User-Agent': 'epistemend-orders',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: 'epistemend-job',
        client_payload: { job: jobId }
      })
    });
  return r.ok;
}

async function note(env, jobId, event, detail) {
  await env.DB.prepare(
    'INSERT INTO job_events (job_id, at, event, detail) VALUES (?, ?, ?, ?)'
  ).bind(jobId, now(), event, detail ? String(detail).slice(0, 500) : null)
   .run();
}

/* ── Turnstile ─────────────────────────────────────────────── */

/*
  Checked before anything is written down.

  /api/checkout used to insert the order row and open a Stripe session
  for anyone who posted to it. Each call cost a D1 write of up to 200KB
  and a session creation, and cost the sender nothing, which is the shape
  of a bill somebody else runs up for you.

  Fails closed. If siteverify cannot be reached, or answers with
  something that is not JSON, the order does not proceed - an outage of
  the check is not a reason to stop checking.

  The hostname compared here is where the widget was SOLVED, which is the
  site, not this worker. localhost is never in the deployed list.
*/
async function turnstileOk(env, token, ip) {

  if (typeof token !== 'string' || !token || token.length > 2048) {
    return false;
  }
  const allowed = new Set(
    String(env.TURNSTILE_HOSTNAMES || '')
      .split(',').map((h) => h.trim()).filter(Boolean)
  );
  if (!env.TURNSTILE_SECRET || allowed.size === 0) {
    return false;
  }

  let out;
  try {
    const r = await fetch(
      'https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        signal: AbortSignal.timeout(10000),
        body: new URLSearchParams({
          secret: env.TURNSTILE_SECRET,
          response: token,
          remoteip: ip || ''
        })
      });
    if (!r.ok) { throw new Error('siteverify ' + r.status); }
    out = await r.json();
  } catch (e) {
    return false;
  }

  /* Say why, in the log. The browser still gets one flat refusal -- a
     rejection that explains itself to the client explains itself to
     whoever is probing it. But refusing with the reason discarded is
     how an afternoon goes: the check states its objection and nobody
     is listening. Visible with: wrangler tail */
  const ok = out.success === true &&
             out.action === 'order' &&
             allowed.has(out.hostname);
  if (!ok) {
    console.log('turnstile refused', JSON.stringify({
      success: out.success,
      errors: out['error-codes'] || [],
      action_seen: out.action,
      action_wanted: 'order',
      hostname_seen: out.hostname,
      hostnames_allowed: Array.from(allowed)
    }));
  }
  return ok;
}

/* ── objections ──────────────────────────────────────────── */

/*
  Article 21 gives a person an unconditional right to object to
  processing carried out on legitimate interests, and requires no reason
  from them. The privacy notice promises the objection persists rather
  than lapsing at the next request, and this is the table that makes that
  true rather than aspirational.

  Scope, deliberately: an objection stops a report ABOUT that person. It
  does not stop their published work appearing in a bibliography somebody
  else submits for a reference check. That data arrives in the customer's
  own document and from the indexes, the report is about the documents
  rather than the person, and blocking it would be both impossible and
  disproportionate. Article 21 protects against processing, not against
  being cited.

  Checked BEFORE the order row is written and before Stripe is called.
  Taking the money and refunding it afterwards would mean processing the
  objection had already forbidden.
*/

function normaliseOrcid(text) {
  const bare = String(text || '').toUpperCase().replace(/[^0-9X]/g, '');
  if (bare.length !== 16) { return ''; }
  return bare.slice(0, 4) + '-' + bare.slice(4, 8) + '-' +
         bare.slice(8, 12) + '-' + bare.slice(12);
}

async function isSuppressed(env, orcid) {
  if (!orcid) { return false; }
  const row = await env.DB.prepare(
    'SELECT orcid FROM suppressions WHERE orcid = ?'
  ).bind(orcid).first();
  return !!row;
}

/* ── an order arrives ────────────────────────────────────── */

async function checkout(request, env) {
  let body;
  try { body = await request.json(); } catch { return bad('Unreadable request'); }

  /* Before the row, before the session, before anything that costs. */
  const passed = await turnstileOk(
    env, body && body['cf-turnstile-response'],
    request.headers.get('CF-Connecting-IP'));
  if (!passed) {
    return bad('That check did not pass. Reload the page and try again.', 403);
  }

  /* Enforced here, not only on the page. A checkbox the server does not

     check is a decoration anyone can post around, and the whole point

     of it is to be evidence. */

  if (body.agreed !== true) {

    return bad('The order cannot be placed without agreeing to the terms');

  }


  const sku = SKUS[body.sku];
  if (!sku) { return bad('Unknown product'); }

  const email = String(body.email || '').trim();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return bad('That email address does not look right');
  }

  const payload = String(body.payload || '').trim();

  /* What counts as enough depends on what was bought.
     A flat 24-character floor made the record report impossible to
     order: an ORCID is 19 characters, and an ORCID is precisely what
     that product asks for. The field said "by ORCID or by name" and
     then refused an ORCID. */
  const ORCID = /^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$/;
  const first = payload.split(/\s+/)[0] || '';
  if (body.sku === 'record-report') {
    if (!ORCID.test(first) && payload.length < 6) {
      return bad('Name the author to sweep, by ORCID or by name');
    }
  } else if (payload.length <= 24) {
    /* The engine keeps reference blocks of length > 24 and discards the
       rest. This gate said >= 24. A payload of exactly 24 characters
       therefore cleared the gate, was charged for, and was thrown away
       before anything was looked up. The two numbers have to agree, and
       the engine's is the one that decides. */
    return bad('That is too short to be a reference. A reference needs '
             + 'author, year and title at least.');
  }
  if (payload.length > 200000) {
    return bad('That is larger than a single document; send it in parts');
  }

  /* An objection on file stops a report about that person, before an
     order exists and before a payment is opened. */
  if (body.sku === 'record-report') {
    const subject = normaliseOrcid(payload.split(/\s+/)[0] || '');
    if (subject && await isSuppressed(env, subject)) {
      return bad('That researcher has asked not to be the subject of '
               + 'these reports, and we have agreed. Nothing has been '
               + 'charged.', 451);
    }
  }

  const orderId = id('ord_');
  await env.DB.prepare(
    `INSERT INTO orders (id, sku, email, payload, amount_cents, status,
                         created_at, agreed_at, agreed_ip, terms_version)
     VALUES (?, ?, ?, ?, ?, 'pending_payment', ?, ?, ?, ?)`
  ).bind(orderId, body.sku, email, payload, sku.amount, now(),
         now(), request.headers.get('CF-Connecting-IP') || '',
         TERMS_VERSION).run();

  const session = await stripe(env, 'checkout/sessions', {
    mode: 'payment',
    'line_items[0][quantity]': '1',
    'line_items[0][price_data][currency]': 'usd',
    'line_items[0][price_data][unit_amount]': String(sku.amount),
    'line_items[0][price_data][product_data][name]': sku.name,
    'line_items[0][price_data][product_data][description]': sku.blurb,
    customer_email: email,
    client_reference_id: orderId,
    'metadata[order_id]': orderId,
    success_url: SITE + '/order/thanks/?order=' + orderId,
    cancel_url: SITE + '/order/?cancelled=1'
  });

  await env.DB.prepare('UPDATE orders SET stripe_session = ? WHERE id = ?')
    .bind(session.id, orderId).run();

  return json({ order: orderId, url: session.url });
}

/* ── the payment clears ──────────────────────────────────── */

async function stripeHook(request, env) {
  const raw = await request.text();
  const sig = request.headers.get('Stripe-Signature');
  const ok = await verifyStripe(env, raw, sig);
  if (!ok) {
    return bad('Signature did not verify', 400);
  }

  const event = JSON.parse(raw);

  /* Delivered twice is delivered once. */
  const seen = await env.DB.prepare('SELECT id FROM stripe_events WHERE id = ?')
    .bind(event.id).first();
  if (seen) { return json({ ok: true, repeated: true }); }
  await env.DB.prepare(
    'INSERT INTO stripe_events (id, kind, seen_at) VALUES (?, ?, ?)'
  ).bind(event.id, event.type, now()).run();

  if (event.type !== 'checkout.session.completed') {
    return json({ ok: true, ignored: event.type });
  }

  const session = (event.data || {}).object || {};
  const orderId = (session.metadata && session.metadata.order_id) ||
                  session.client_reference_id;
  if (!orderId) { return json({ ok: true, note: 'no order on session' }); }

  const order = await env.DB.prepare('SELECT * FROM orders WHERE id = ?')
    .bind(orderId).first();
  if (!order) { return json({ ok: true, note: 'unknown order' }); }
  if (order.status === 'paid') { return json({ ok: true, already: true }); }

  await env.DB.prepare(
    "UPDATE orders SET status = 'paid', paid_at = ? WHERE id = ?"
  ).bind(now(), orderId).run();

  const jobId = id('job_');
  const token = id('');
  await env.DB.prepare(
    `INSERT INTO jobs (id, order_id, status, token, created_at)
     VALUES (?, ?, 'queued', ?, ?)`
  ).bind(jobId, orderId, token, now()).run();

  const woke = await wakeRunner(env, jobId);

  const named = SKUS[order.sku] ? SKUS[order.sku].name : order.sku;
  const sent = await mail(env, order.email, 'Your ' + named + ' is under way', [
    'Thank you — the payment went through and the check has started.',
    '',
    'Ordered   ' + named,
    'Reference ' + order.id,
    '',
    'The report usually arrives within the hour. It comes as a link you',
    'control, which you can send on to anyone who needs to see it.',
    '',
    'Nothing else is needed from you. If anything looks wrong, reply to',
    'this message and quote the reference above.',
    '',
    '— Epistemend',
    'www.epistemend.org'
  ]);
  /* Written down either way. A confirmation that silently failed to send
     is indistinguishable from one that was never attempted, and the
     customer has paid by this point. */
  /* Records THAT it was mailed, not the address. The order row already
     holds the address; a second copy in a diagnostic log is personal data
     kept for no reason, and the log is the part most likely to be read
     by somebody who had no business seeing it. */
  await note(env, jobId, sent.ok ? 'confirmation mailed' : 'confirmation FAILED',
             sent.ok ? null : (sent.status + ' ' + sent.why));

  return json({ ok: true, job: jobId });
}

/* ── what happened to my order ───────────────────────────── */

async function status(request, env) {
  const orderId = new URL(request.url).searchParams.get('order');
  if (!orderId) { return bad('Name an order'); }

  const order = await env.DB.prepare(
    'SELECT id, sku, status, created_at FROM orders WHERE id = ?'
  ).bind(orderId).first();
  if (!order) { return bad('No such order', 404); }

  const job = await env.DB.prepare(
    'SELECT id, status, token, finished_at FROM jobs WHERE order_id = ?'
  ).bind(orderId).first();

  return json({
    order: order.id,
    product: order.sku,
    paid: order.status === 'paid',
    state: job ? job.status : 'awaiting payment',
    report: job && job.status === 'complete'
      ? SITE + '/r/#' + job.token : null
  });
}

/* ── the findings ────────────────────────────────────────── */

async function report(request, env) {
  const token = new URL(request.url).searchParams.get('t');
  if (!token) { return bad('Name a report'); }

  const job = await env.DB.prepare(
    "SELECT result, finished_at FROM jobs WHERE token = ? AND status = 'complete'"
  ).bind(token).first();
  if (!job) { return bad('No report at that address', 404); }

  return json({ finished: job.finished_at, result: JSON.parse(job.result) });
}

/* ── erasure ─────────────────────────────────────────────── */

/*
  A report has to be removable by the person who bought it, or the
  retention notice cannot be honoured and Article 17 has no mechanism
  behind it.

  Two things are required, not one. The token alone is read access, and
  a report is meant to be forwarded -- so token-only deletion would let
  any recipient destroy the purchaser's copy. The email that placed the
  order is the second factor, compared case-insensitively because people
  type their own address in whatever case they please.
*/
async function forget(request, env) {
  let body;
  try { body = await request.json(); } catch { return bad('Unreadable request'); }

  const token = String((body && body.token) || '').trim();
  const email = String((body && body.email) || '').trim().toLowerCase();
  if (!token || !email) {
    return bad('Give the report address and the email that ordered it');
  }

  const row = await env.DB.prepare(
    `SELECT j.id AS job_id, o.id AS order_id, lower(o.email) AS email
     FROM jobs j JOIN orders o ON o.id = j.order_id
     WHERE j.token = ?`
  ).bind(token).first();

  /* Same answer whether the report does not exist or the email does not
     match, so this cannot be used to discover which reports exist. */
  if (!row || row.email !== email) {
    return json({ ok: true, removed: false,
                  note: 'If a report matches those details it has been removed.' });
  }

  await env.DB.prepare(
    "UPDATE jobs SET result = NULL, status = 'erased' WHERE id = ?"
  ).bind(row.job_id).run();
  await env.DB.prepare(
    "UPDATE orders SET payload = '' WHERE id = ?"
  ).bind(row.order_id).run();
  await note(env, row.job_id, 'erased at the purchaser request', null);

  return json({ ok: true, removed: true,
                note: 'The report and its contents have been removed. The '
                    + 'record that an order was placed is kept for tax and '
                    + 'chargeback purposes and holds no report content.' });
}

/* ── the runner talks back ───────────────────────────────── */

async function runnerClaim(request, env) {
  const body = await request.json();
  const job = await env.DB.prepare(
    `SELECT j.*, o.sku, o.email, o.payload
     FROM jobs j JOIN orders o ON o.id = j.order_id
     WHERE j.id = ?`
  ).bind(body.job).first();
  if (!job) { return bad('No such job', 404); }
  if (job.status === 'complete') { return bad('Already finished', 409); }
  if (job.attempts >= MAX_ATTEMPTS) { return bad('Given up on this one', 409); }

  /* An objection can arrive between paying and running -- the gap is
     seconds to minutes, but it is the gap in which a person exercises
     a right. Checked again here, and the order is refunded rather than
     fulfilled, because the alternative is completing processing that
     has already been objected to. */
  if (job.sku === 'record-report') {
    const subject = normaliseOrcid(String(job.payload || '').split(/\s+/)[0] || '');
    if (subject && await isSuppressed(env, subject)) {
      await env.DB.prepare(
        "UPDATE jobs SET status = 'needs_attention', finished_at = ? WHERE id = ?"
      ).bind(now(), job.id).run();
      await env.DB.prepare(
        "UPDATE orders SET payload = '' WHERE id = ?"
      ).bind(job.order_id).run();
      await note(env, job.id, 'stopped: objection on file', null);
      return bad('That subject has objected; this job will not run', 451);
    }
  }

  await env.DB.prepare(
    `UPDATE jobs SET status = 'running', attempts = attempts + 1,
     started_at = ? WHERE id = ?`
  ).bind(now(), job.id).run();

  return json({
    job: job.id, sku: job.sku, email: job.email,
    payload: job.payload, token: job.token
  });
}

async function runnerFinish(request, env) {
  const body = await request.json();
  const job = await env.DB.prepare('SELECT * FROM jobs WHERE id = ?')
    .bind(body.job).first();
  if (!job) { return bad('No such job', 404); }

  const order = await env.DB.prepare('SELECT * FROM orders WHERE id = ?')
    .bind(job.order_id).first();

  if (body.ok) {
    await env.DB.prepare(
      `UPDATE jobs SET status = 'complete', result = ?, finished_at = ?
       WHERE id = ?`
    ).bind(JSON.stringify(body.result || {}), now(), job.id).run();

    /* The submitted list is discarded the moment the report exists.
       The order page tells the purchaser it is not kept, and until now
       it was kept -- every payload still sat in the orders table hours
       after delivery. A sentence on a page taking card payments is a
       representation, not a sentiment.
       What remains is the report itself, at the customer's own address,
       which is the thing they bought. That is a different retention with
       a different reason and the notice says so separately. */
    await env.DB.prepare(
      "UPDATE orders SET payload = '' WHERE id = ?"
    ).bind(job.order_id).run();
    await note(env, job.id, 'submitted list discarded', null);

    return json({ ok: true, report: SITE + '/r/#' + job.token });
  }

  /* A sweep that could not be completed is not a sweep that gets billed. */
  if (job.attempts >= MAX_ATTEMPTS) {
    await env.DB.prepare(
      "UPDATE jobs SET status = 'needs_attention', finished_at = ? WHERE id = ?"
    ).bind(now(), job.id).run();

    try {
      const session = await stripe(env, 'checkout/sessions/' +
        order.stripe_session, {});
      if (session.payment_intent) {
        await stripe(env, 'refunds', { payment_intent: session.payment_intent });
        await env.DB.prepare(
          "UPDATE orders SET status = 'refunded' WHERE id = ?"
        ).bind(order.id).run();

        const refundMail = await mail(env, order.email, 'Your Epistemend order has been refunded', [
          'The check you ordered could not be completed, so the charge has',
          'been reversed in full. Nothing is owed and nothing is outstanding.',
          '',
          'Reference ' + order.id,
          '',
          'This happens when a source we rely on will not answer for long',
          'enough that we stop trying rather than send you something',
          'incomplete. The refund takes a few days to appear, depending on',
          'your bank.',
          '',
          'You are welcome to try again later, and if you would like us to',
          'look at what went wrong, reply to this message with the reference',
          'above and we will.',
          '',
          '— Epistemend',
          'www.epistemend.org'
        ]);
        await note(env, job.id,
                   refundMail.ok ? 'refund mailed' : 'refund mail FAILED',
                   refundMail.ok ? null
                                 : (refundMail.status + ' ' + refundMail.why));
      }
    } catch (err) {
    }

    /* The operator hears about it either way, because a refund that failed
       is money that stayed taken. */
    if (env.OPERATOR_EMAIL) {
      const opMail = await mail(env, env.OPERATOR_EMAIL, 'A job needs attention: ' + job.id, [
        'Job     ' + job.id,
        'Order   ' + job.order_id,
        'Attempts ' + job.attempts,
        '',
        'It has stopped and the customer has been told.',
        'The last error: ' + String(body.error || 'not recorded').slice(0, 300)
      ]);
    }
    return json({ ok: true, gaveUp: true });
  }

  await env.DB.prepare("UPDATE jobs SET status = 'queued' WHERE id = ?")
    .bind(job.id).run();
  return json({ ok: true, requeued: true });
}

/* Jobs the runner should pick up: queued, or running for long enough that
   whatever was running them is gone. */
async function runnerPending(request, env) {
  const stale = new Date(Date.now() - 30 * 60 * 1000).toISOString();
  const { results } = await env.DB.prepare(
    `SELECT id FROM jobs
     WHERE (status = 'queued' OR (status = 'running' AND started_at < ?))
       AND attempts < ?
     ORDER BY created_at LIMIT 20`
  ).bind(stale, MAX_ATTEMPTS).all();
  return json({ jobs: (results || []).map((r) => r.id) });
}

/* ── routing ─────────────────────────────────────────────── */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': SITE,
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, X-Runner-Key',
          'Access-Control-Max-Age': '86400'
        }
      });
    }

    /* The runner's endpoints are not for the public. */
    if (url.pathname.startsWith('/api/runner/')) {
      if (request.headers.get('X-Runner-Key') !== env.RUNNER_KEY) {
        return bad('No', 401);
      }
    }

    try {
      if (url.pathname === '/api/checkout' && request.method === 'POST') {
        return await checkout(request, env);
      }
      if (url.pathname === '/api/stripe' && request.method === 'POST') {
        return await stripeHook(request, env);
      }
      if (url.pathname === '/api/status') { return await status(request, env); }
      if (url.pathname === '/api/report') { return await report(request, env); }
      if (url.pathname === '/api/forget' && request.method === 'POST') {
        return await forget(request, env);
      }

      if (url.pathname === '/api/runner/pending') {
        return await runnerPending(request, env);
      }
      if (url.pathname === '/api/runner/claim') {
        return await runnerClaim(request, env);
      }
      if (url.pathname === '/api/runner/finish') {
        return await runnerFinish(request, env);
      }
      return bad('No such route', 404);
    } catch (err) {
      /* The customer is told the truth and the detail stays in the log. */
      console.error(url.pathname, err && err.stack);
      return json({ error: 'That did not go through. Nothing was charged.' },
                  500);
    }
  }
};
