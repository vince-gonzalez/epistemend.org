#!/usr/bin/env bash
# ============================================================
# epistemend — put the secrets in, one at a time
# F-Keys | www.f-keys.com
# ------------------------------------------------------------
# Run this in YOUR terminal, from the worker/ directory:
#
#     bash set-secrets.sh
#
# It asks for ONE key at a time and tells you where that key
# lives before it asks. Go and get that one, come back, paste,
# press Enter. Then it asks for the next one.
#
# There is nothing to prepare and nothing to write down first.
# An earlier version told you to open five tabs and copy five
# values before starting, which cannot be done: there is one
# clipboard. It also said to park them in a text file, which is
# how live keys end up somewhere they get synced.
#
# Nothing you type is echoed. Nothing is written to disk.
# Nothing is left in shell history.
#
# Press Enter on an empty prompt to skip that one. Run the
# script again later for just the ones you skipped.
# ============================================================

set -uo pipefail
umask 077

# ── refuse to start unless it can actually succeed ───────────
# Each of these was a way to ask for five secrets, print FAILED
# five times, and explain none of it.

if ! command -v wrangler >/dev/null 2>&1; then
  echo "STOP: wrangler is not installed." >&2
  echo "  Run this, then run this script again:" >&2
  echo "    npm install -g wrangler" >&2
  exit 1
fi

if [ ! -f wrangler.toml ]; then
  echo "STOP: no wrangler.toml here, so this is the wrong folder." >&2
  echo "  Run:  cd C:/tmp/epistemend.org/worker" >&2
  exit 1
fi

if ! wrangler whoami >/dev/null 2>&1; then
  echo "STOP: wrangler is not logged in to Cloudflare." >&2
  echo "  Run this, approve in the browser, then run this again:" >&2
  echo "    wrangler login" >&2
  exit 1
fi

echo
echo "Signed in to Cloudflare as:"
wrangler whoami 2>/dev/null | grep -iE "email|account" | head -3 | sed 's/^/  /'

# ── one at a time ────────────────────────────────────────────

STEP=0

put() {
  local name="$1" where="$2" value=""
  STEP=$((STEP + 1))
  echo
  echo "------------------------------------------------------------"
  echo " $STEP of 5   $name"
  echo "------------------------------------------------------------"
  printf '%s\n' "$where"
  echo
  echo " Go and get it now. Come back, paste it below, press Enter."
  echo " (Nothing appears as you paste. That is deliberate.)"
  echo " (Nothing to paste yet? Just press Enter to skip.)"
  echo
  read -rsp "  paste $name here: " value
  echo
  if [ -z "$value" ]; then
    echo "  skipped - run this script again when you have it."
    return 0
  fi
  if printf '%s' "$value" | wrangler secret put "$name" >/dev/null 2>&1; then
    echo "  SET."
  else
    echo "  FAILED - the value was not stored. Send me this line." >&2
  fi
  unset value
}

put TURNSTILE_SECRET \
" 1. Go to  dash.cloudflare.com
 2. Left sidebar, scroll down, click  Turnstile
 3. Click your widget (Site Key 0x4AAAAAAEe8cYI_dbLQ1XgY)
 4. Click the  Settings  tab
 5. Find  Secret Key  and click the eye icon to reveal it
 6. Select it and copy"

put STRIPE_SECRET_KEY \
" 1. Go to  dashboard.stripe.com
 2. Check the  Test mode  toggle, top right, is ON
 3. Click  Developers  (top right)
 4. Click the  API keys  tab
 5. On the  Secret key  row, click  Reveal test key
 6. Copy it. It starts with  sk_test_"

put STRIPE_WEBHOOK_SECRET \
" YOU DO NOT HAVE THIS YET, and that is expected.
 It does not exist until the webhook endpoint is created,
 which is the next thing you do after this script.

 >>> PRESS ENTER TO SKIP THIS ONE. <<<"

put RESEND_API_KEY \
" 1. Go to  resend.com  and sign in
 2. Left sidebar, click  API Keys
 3. Click  Create API Key
 4. Name it     epistemend
 5. Permission  Sending access
 6. Click  Add
 7. Copy it NOW - Resend shows it once. It starts with  re_

 You will need this SAME value again for GitHub later, so
 leave the tab open until the very end."

put GITHUB_TOKEN \
" 1. Go to  github.com
 2. Click your avatar, top right, then  Settings
 3. Bottom of the left sidebar, click  Developer settings
 4. Click  Personal access tokens  then  Fine-grained tokens
 5. Click  Generate new token
 6. Token name        epistemend-runner
 7. Expiration        90 days
 8. Repository access Only select repositories -> epistemend.org
 9. Permissions -> Repository permissions -> Contents
                   set the dropdown to  Read and write
10. Scroll down, click  Generate token
11. Copy it NOW - shown once. It starts with  github_pat_"

# ── the runner key ──────────────────────────────────────────
# Generated, not asked for. It is a shared secret between the
# worker and the GitHub runner and has no dashboard of its own,
# so both halves must come from one place. When they drift the
# symptom is not an error: paid orders queue and never run, and
# somebody has paid and is waiting.

# Only ever generated ONCE. The second run of this script exists to
# add the Stripe webhook secret, and regenerating here would quietly
# replace the worker's half while GitHub kept the old one. The two
# would then disagree, and disagreeing is silent: orders take payment,
# queue, and never run.
echo
echo "------------------------------------------------------------"
echo " RUNNER_KEY"
echo "------------------------------------------------------------"
if wrangler secret list 2>/dev/null | grep -q '"RUNNER_KEY"'; then
  echo "  Already set on the worker. Leaving it alone."
  echo "  If GitHub does not have the matching value, delete the"
  echo "  secret with:  wrangler secret delete RUNNER_KEY"
  echo "  then run this script again to make a fresh pair."
  RUNNER_KEY=""
else
  RUNNER_KEY="$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")"
  if printf '%s' "$RUNNER_KEY" | wrangler secret put RUNNER_KEY >/dev/null 2>&1; then
    echo "  Generated and SET on the worker."
  else
    echo "  FAILED to set on the worker." >&2
  fi
fi

echo
echo "What the worker holds now:"
wrangler secret list 2>/dev/null | sed 's/^/  /'

if [ -n "$RUNNER_KEY" ]; then
cat <<'HOWTO'

============================================================
 DO THIS NEXT, BEFORE YOU CLOSE THIS WINDOW
============================================================
 The key printed below is shown once and saved nowhere. Put
 it into GitHub now, while it is on screen.

  1. Go to  github.com/vince-gonzalez/epistemend.org
  2. Click the  Settings  tab (top of the repo, far right)
  3. Left sidebar: Secrets and variables -> Actions
  4. Click  New repository secret

     Name    RUNNER_KEY
     Secret  the line below, copied exactly

  5. Click  Add secret
  6. Click  New repository secret  again

     Name    RESEND_API_KEY
     Secret  the same re_... you pasted earlier

  7. Click  Add secret
  8. Click  New repository secret  once more

     Name    ORDERS_API
     Secret  https://orders.epistemend.org

  9. Click  Add secret

 RUNNER_KEY and RESEND_API_KEY must match Cloudflare exactly.
 If they differ, orders take payment, queue, and never run.
============================================================

HOWTO
fi

if [ -n "$RUNNER_KEY" ]; then
  echo "RUNNER_KEY:"
  echo
  echo "   $RUNNER_KEY"
  echo
  unset RUNNER_KEY
  printf 'Press Enter once all three GitHub secrets are saved. '
  read -r _
else
  echo "No new RUNNER_KEY this run, so GitHub already has its copy."
  echo "Nothing to paste."
fi
echo
echo "Done here. Next: create the Stripe webhook, then run this"
echo "script again and paste ONLY the whsec_ value, skipping the"
echo "rest. Then run:  wrangler deploy"
echo
