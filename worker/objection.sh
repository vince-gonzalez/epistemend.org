#!/usr/bin/env bash
# ============================================================
# epistemend — record or lift an Article 21 objection
# F-Keys | www.f-keys.com
# ------------------------------------------------------------
#   bash objection.sh add    0000-0002-1825-0097 "verified by reply from
#                                                 the address on the ORCID"
#   bash objection.sh lift   0000-0002-1825-0097
#   bash objection.sh list
#
# Article 21 requires no reason from the person objecting, and this
# script asks for none. What it does ask for is a note on how you
# satisfied yourself the request came from the subject, because the
# alternative is that anyone can suppress anyone -- which is its own
# harm, to the subject and to a customer with a legitimate need.
#
# An objection stops a record report ABOUT that person. It does not stop
# their published work appearing in a bibliography somebody else submits.
# Article 21 protects against processing, not against being cited.
# ============================================================

set -uo pipefail

DB="epistemend"

if ! command -v wrangler >/dev/null 2>&1; then
  echo "STOP: wrangler is not installed.  npm install -g wrangler" >&2
  exit 1
fi
if [ ! -f wrangler.toml ]; then
  echo "STOP: run this from the worker/ directory." >&2
  exit 1
fi

normalise() {
  printf '%s' "$1" | tr '[:lower:]' '[:upper:]' | tr -cd '0-9X' |
    sed -E 's/^(.{4})(.{4})(.{4})(.{4})$/\1-\2-\3-\4/'
}

action="${1:-}"
raw="${2:-}"
note="${3:-}"

case "$action" in
  add)
    orcid="$(normalise "$raw")"
    if [ ${#orcid} -ne 19 ]; then
      echo "That is not an ORCID: '$raw'" >&2; exit 1
    fi
    if [ -z "$note" ]; then
      echo "Give a note saying how the request was verified. It is the" >&2
      echo "difference between honouring an objection and letting anyone" >&2
      echo "suppress anyone." >&2
      exit 1
    fi
    wrangler d1 execute "$DB" --remote --yes --command \
      "INSERT OR REPLACE INTO suppressions (orcid, added_at, note, verified_by)
       VALUES ('$orcid', datetime('now'), '$(printf '%s' "$note" | sed "s/'/''/g")', 'operator')"
    echo
    echo "Recorded. $orcid will not be the subject of a report."
    echo "Now check whether a monitoring subscription exists for them:"
    echo "  bash objection.sh list"
    ;;

  lift)
    orcid="$(normalise "$raw")"
    if [ ${#orcid} -ne 19 ]; then
      echo "That is not an ORCID: '$raw'" >&2; exit 1
    fi
    wrangler d1 execute "$DB" --remote --yes --command \
      "DELETE FROM suppressions WHERE orcid = '$orcid'"
    echo
    echo "Lifted. Record the reason somewhere durable: an objection"
    echo "withdrawn should be as documented as one made."
    ;;

  list)
    wrangler d1 execute "$DB" --remote --yes --command \
      "SELECT orcid, added_at, note FROM suppressions ORDER BY added_at DESC"
    ;;

  *)
    echo "Usage:" >&2
    echo "  bash objection.sh add  <orcid> \"how it was verified\"" >&2
    echo "  bash objection.sh lift <orcid>" >&2
    echo "  bash objection.sh list" >&2
    exit 1
    ;;
esac
