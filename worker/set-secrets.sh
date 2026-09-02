#!/usr/bin/env bash
# ============================================================
# epistemend — put the secrets in, once
# F-Keys | www.f-keys.com
# ------------------------------------------------------------
# Run this in YOUR terminal, from the worker/ directory:
#
#     bash set-secrets.sh
#
# It asks for each value, shows nothing as you type, and pipes
# it straight into wrangler. Nothing is echoed, nothing is
# written to a file, and nothing is left in shell history.
#
# Skip any one by pressing Enter on an empty line.
#
# RUNNER_KEY is generated here rather than asked for, and
# printed ONCE at the end, because the same value has to go
# into GitHub as well. It is the only thing this prints.
# ============================================================

set -uo pipefail
umask 077

# ── refuse to start unless it can actually succeed ───────────
# Every check below was a way this script could ask for five
# secrets, print FAILED five times, and not say why.

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

echo "Signed in to Cloudflare as:"
wrangler whoami 2>/dev/null | grep -iE "email|account" | head -3 | sed 's/^/  /'

cat <<'PREFLIGHT'

------------------------------------------------------------
OPEN THESE FOUR TABS BEFORE YOU START.
The script asks in this order and will not wait for you to
go hunting; skipping one is fine, you can run it again.

  1  Turnstile secret key
     dash.cloudflare.com > Turnstile > your widget
     > Settings > Secret Key > click the eye

  2  Stripe secret key
     dashboard.stripe.com > Developers > API keys
     > Secret key > Reveal test key   (sk_test_...)

  3  Stripe webhook secret
     YOU DO NOT HAVE THIS YET. Press Enter to skip it.

  4  Resend API key
     resend.com > API Keys > Create API Key
     name: epistemend, permission: Sending access  (re_...)

  5  GitHub token
     github.com > your avatar > Settings
     > Developer settings > Personal access tokens
     > Fine-grained tokens > Generate new token
     name: epistemend-runner
     Repository access: Only select repositories > epistemend.org
     Permissions > Repository permissions > Contents: Read and write

Nothing you type is shown on screen. That is deliberate.
------------------------------------------------------------
PREFLIGHT

printf 'Press Enter when those tabs are open. '
read -r _

put() {
  local name="$1" prompt="$2" value=""
  printf '\n%s\n' "$prompt"
  read -rsp "  $name: " value
  echo
  if [ -z "$value" ]; then
    echo "  skipped."
    return 0
  fi
  if printf '%s' "$value" | wrangler secret put "$name" >/dev/null 2>&1; then
    echo "  set."
  else
    echo "  FAILED. Run 'wrangler whoami' and check you are in worker/." >&2
  fi
  unset value
}

echo "============================================================"
echo " Six secrets. Enter on an empty line skips one."
echo "============================================================"

put TURNSTILE_SECRET \
  "Turnstile secret key — dash.cloudflare.com > Turnstile > your widget > Settings."

put STRIPE_SECRET_KEY \
  "Stripe secret key — Developers > API keys > Secret key > Reveal.
  Use sk_test_... until you have run a test order all the way through."

put STRIPE_WEBHOOK_SECRET \
  "Stripe webhook signing secret (whsec_...) — Developers > Webhooks >
  your endpoint > Signing secret > Reveal.
  You will not have this until the endpoint exists. Skip it for now
  and run this script again for just this one afterwards."

put RESEND_API_KEY \
  "Resend API key (re_...) — resend.com > API Keys > Create, sending access.
  The SAME value goes into GitHub later. Keep the tab open."

put GITHUB_TOKEN \
  "GitHub fine-grained token — github.com > Settings > Developer settings >
  Personal access tokens > Fine-grained. Repository: epistemend.org only.
  Permission: Contents = Read and write."

# ── the runner key ──────────────────────────────────────────
# Generated rather than asked for. It is a shared secret between
# the worker and the GitHub runner and has no dashboard of its
# own, so the two halves have to come from one place or they
# drift -- and when they drift, paid orders queue and never run.
RUNNER_KEY="$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")"
printf '\nRUNNER_KEY — generated\n'
if printf '%s' "$RUNNER_KEY" | wrangler secret put RUNNER_KEY >/dev/null 2>&1; then
  echo "  set on the worker."
else
  echo "  FAILED to set on the worker." >&2
fi

echo
echo "============================================================"
echo " What is set on the worker now:"
wrangler secret list 2>/dev/null | sed 's/^/   /'
echo "============================================================"
echo
echo " Copy this into GitHub as the repository secret RUNNER_KEY."
echo " It is shown once and is not saved anywhere:"
echo
echo "   $RUNNER_KEY"
echo
echo " github.com/vince-gonzalez/epistemend.org"
echo "   Settings > Secrets and variables > Actions > New repository secret"
echo
echo " Three GitHub secrets in total:"
echo "   RUNNER_KEY        the line above, exactly"
echo "   RESEND_API_KEY    the same Resend key you just entered"
echo "   ORDERS_API        https://orders.epistemend.org"
echo
unset RUNNER_KEY
