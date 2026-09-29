#!/usr/bin/env python3
"""
============================================================
epistemend runner — claim a job, do the work, send the report
F-Keys | www.f-keys.com
------------------------------------------------------------
Runs on a dispatch when a payment clears, and on a schedule so
a dispatch that never arrives costs a delay rather than an
order.

Every exit tells the worker what happened. A job that ends
without a word is a job that hangs, and a customer who paid
and heard nothing.
============================================================
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.environ["ORDERS_API"].rstrip("/")
KEY = os.environ["RUNNER_KEY"]
RESEND = os.environ.get("RESEND_API_KEY")
FROM = "Epistemend <reports@epistemend.org>"
REPLY_TO = "hello@epistemend.org"


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data,
        headers={"X-Runner-Key": KEY, "Content-Type": "application/json",
                 "User-Agent": "epistemend-runner"},
        method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def send(to, subject, lines):
    if not RESEND:
        print("  no mail key set; not sending", file=sys.stderr)
        return
    body = json.dumps({
        "from": FROM, "to": [to], "reply_to": REPLY_TO,
        "subject": subject, "text": "\n".join(lines)}).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails", data=body,
        headers={"Authorization": "Bearer " + RESEND,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        print("  mailed {}".format(to))
    except urllib.error.HTTPError as err:
        print("  mail failed: {} {}".format(err.code, err.read()[:200]),
              file=sys.stderr)


def do_reference_check(payload):
    from authorecon import reference_check as rc
    rows = rc.run(payload, log=lambda m: print(m, file=sys.stderr))
    # An empty report is not a report, and it must never be delivered as a
    # finished one. This shipped: a 24-character payload cleared the
    # worker's floor of >= 24 and was discarded by the splitter, which
    # keeps blocks of > 24. The order was charged, the job completed, and
    # the customer received a document containing nothing.
    #
    # Raising here puts the job on the failure path, which stops after
    # three attempts and refunds. Work that cannot be done is not work
    # that gets billed.
    if not rows:
        raise ValueError(
            "No references could be read from that text. A reference needs "
            "enough of itself to look one up - author, year and title at "
            "least. Nothing has been charged for this."
        )
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    return {"kind": "reference-check", "counts": counts, "references": rows,
            "bibliography": bibliography(rows)}


# ── the corrected bibliography ────────────────────────────────

#: (key, CSL style the DOI resolver knows, name on the page)
STYLES = (("apa", "apa", "APA"),
          ("mla", "modern-language-association", "MLA"),
          ("chicago", "chicago-author-date", "Chicago"))

#: Only a reference matched to its record goes in the fixed list. One that
#: needs a look, points elsewhere or was not found stays out, and so does a
#: retracted work: it is shown on the report and left to the writer.
USABLE = ("confirmed", "located")


def tidy(text):
    """The resolver's output, made pasteable.

    Seen in its answers on 2026-09-29: MLA prints an empty "edited by ,"
    for every Crossref record and names Crossref as though it were a
    database; DataCite answers with HTML entities and <i> tags."""
    text = html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    # At the start of a sentence first ("Zion. Edited by , Dec."), then
    # mid-sentence ("Econometrica, edited by , vol. 47").
    text = re.sub(r"\.\s*Edited by\s*,\s*", ". ", text)
    text = re.sub(r"(?i),\s*edited by\s*,", ",", text)
    text = re.sub(r"([.,])\s*Crossref,\s*", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace(" ,", ",")


def cite(doi, csl):
    """One formatted entry for one DOI, from the DOI resolver itself, so
    the wording comes from the record rather than from a guess."""
    req = urllib.request.Request(
        "https://doi.org/" + urllib.parse.quote(doi, safe="/()"),
        headers={"Accept": "text/x-bibliography; style=" + csl,
                 "User-Agent": "epistemend-runner (mailto:hello@epistemend.org)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return tidy(r.read().decode("utf-8", "replace"))


def bibliography(rows):
    """Every matched reference, in the order written, in three styles.

    A DOI the resolver cannot format is listed by itself rather than
    formatted by hand: an entry built from guesses is the thing this
    report exists to catch."""
    out = {key: [] for key, _, _ in STYLES}
    out["unformatted"] = []
    for row in rows:
        doi = (row.get("found") or {}).get("doi")
        if row.get("state") not in USABLE or not doi:
            continue
        try:
            entries = {key: cite(doi, csl) for key, csl, _ in STYLES}
        except (urllib.error.URLError, OSError, ValueError) as err:
            print("  could not format {}: {}".format(doi, err), file=sys.stderr)
            out["unformatted"].append(doi)
            continue
        if not all(entries.values()):
            out["unformatted"].append(doi)
            continue
        for key, _, _ in STYLES:
            out[key].append(entries[key])
    out["styles"] = [[key, name] for key, _, name in STYLES]
    return out


def do_record_report(payload):
    from authorecon import report as rp
    from authorecon.discover import normalise_orcid, valid_checksum, Problem
    orcid = normalise_orcid(payload.strip().split()[0])
    if not valid_checksum(orcid):
        raise Problem("{} is not a valid ORCID".format(orcid))
    sections = rp.build(orcid, log=lambda m: print(m, file=sys.stderr))
    return {"kind": "record-report", "orcid": orcid,
            "sections": [{"title": s.title, "lines": s.lines,
                          "error": s.error} for s in sections]}


WORK = {"reference-check": do_reference_check,
        "record-report": do_record_report}


def headline(result):
    if result["kind"] != "reference-check":
        return ["The full record is in the report."]
    c = result["counts"]
    out = ["{} references read.".format(len(result["references"]))]
    fixed = len((result.get("bibliography") or {}).get("apa") or [])
    if fixed:
        out.append("Your corrected bibliography is at the top of the report, "
                   "{} entr{}, in APA, MLA and Chicago."
                   .format(fixed, "y" if fixed == 1 else "ies"))
    for state in ("divergent", "unlocatable", "retracted"):
        if c.get(state):
            out.append("  {} {}".format(c[state], state))
    if not any(c.get(s) for s in ("divergent", "unlocatable", "retracted")):
        out.append("Every reference resolved to a record that matches it.")
    return out


def work(job_id):
    print("== {}".format(job_id))
    try:
        job = call("/api/runner/claim", {"job": job_id})
    except urllib.error.HTTPError as err:
        print("  not claimable: {}".format(err.code), file=sys.stderr)
        return

    try:
        result = WORK[job["sku"]](job["payload"])
    except Exception as err:                       # noqa: BLE001
        print("  failed: {}".format(err), file=sys.stderr)
        call("/api/runner/finish",
             {"job": job_id, "ok": False, "error": str(err)[:400]})
        return

    done = call("/api/runner/finish",
                {"job": job_id, "ok": True, "result": result})
    link = done.get("report", "")
    send(job["email"], "Your Epistemend report is ready",
         ["Your report is ready to read:", "", "    " + link, ""] +
         headline(result) +
         ["", "The address above is yours; send it to anyone who needs it.",
          "", "— Epistemend", "www.epistemend.org"])


def main():
    named = os.environ.get("DISPATCHED_JOB", "").strip()
    jobs = [named] if named else call("/api/runner/pending").get("jobs", [])
    if not jobs:
        print("nothing queued")
        return 0
    for job_id in jobs:
        work(job_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
