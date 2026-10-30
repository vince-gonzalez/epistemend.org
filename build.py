#!/usr/bin/env python3
# ============================================================
# EPISTEMEND — static site generator
# The published record of Vince Gonzalez, academic home.
# F-Keys Creative LLC | www.f-keys.com
# ------------------------------------------------------------
# WORKFLOW STACK
#   1. shell()   — menu bar + desktop + window, written once
#   2. landing   — the "About the Author" window + the folders
#   3. papers    — read from papers/papers.json, grouped
#   4. programs / measurement / record / cv — content as data
#   5. main()    — writes index.html and one folder per section
#
# No typeface, script or tracker is fetched from another server.
# Run:  py -3 build.py
# ============================================================

import html
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
ORCID = "0009-0005-3640-014X"
NAME = "Vince Gonzalez"

# (label, href, menu-key)
MENU = [
    ("Epistemend", "/", "home"),
    ("Papers", "/papers/", "papers"),
    ("Programs", "/programs/", "programs"),
    ("Measurement", "/measurement/", "measurement"),
    ("Record", "/record/", "record"),
    ("CV", "/cv/", "cv"),
]


def esc(s):
    return html.escape(s or "", quote=True)


def menubar(active):
    items = ['<span class="mark chicago">&#8251;</span>']
    for label, href, key in MENU:
        cls = "chicago" if key == "home" else ""
        if key == active:
            cls = (cls + " on").strip()
        attr = (' class="%s"' % cls) if cls else ""
        items.append('<a%s href="%s">%s</a>' % (attr, href, esc(label)))
    items.append('<span class="right chicago">Research</span>')
    return '<div class="menubar">\n  ' + "\n  ".join(items) + "\n</div>"


def shell(title, desc, active, body, noindex=False):
    robots = ("noindex, nofollow, noarchive" if noindex
              else "index, follow")
    canon = "https://epistemend.org%s" % (
        dict((k, h) for _, h, k in MENU).get(active, "/"))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<meta name="description" content="%s">
<meta name="author" content="Vince Gonzalez">
<meta name="robots" content="%s">
<link rel="canonical" href="%s">
<link rel="stylesheet" href="/assets/mac.css">
</head>
<body>
%s
<div class="desktop">
%s
</div>
</body>
</html>
""" % (esc(title), esc(desc), robots, canon, menubar(active), body)


def window(win_title, inner, wide=False):
    cls = "win wide" if wide else "win"
    return ('<section class="%s" aria-label="%s">\n'
            '  <div class="titlebar"><span class="closebox" aria-hidden="true"></span>'
            '<span class="title chicago">%s</span></div>\n'
            '  <div class="body">%s</div>\n'
            '</section>') % (cls, esc(win_title), esc(win_title), inner)


FOLDER_SVG = (
    '<svg width="54" height="42" viewBox="0 0 54 42" aria-hidden="true">'
    '<path d="M2 8 h16 l5 5 h28 a1 1 0 0 1 1 1 v24 a1 1 0 0 1 -1 1 H2 '
    'a1 1 0 0 1 -1 -1 V9 a1 1 0 0 1 1 -1 z" fill="#f2f2f2" stroke="#000" '
    'stroke-width="1.4"/><path d="M2 13 h50" stroke="#000" stroke-width="1" '
    'opacity=".5"/></svg>')
DOC_SVG = (
    '<svg width="54" height="42" viewBox="0 0 54 42" aria-hidden="true">'
    '<rect x="11" y="3" width="32" height="38" fill="#fff" stroke="#000" '
    'stroke-width="1.4"/><path d="M16 12 h22 M16 18 h22 M16 24 h22 M16 30 h14" '
    'stroke="#000" stroke-width="1" opacity=".55"/></svg>')


def back(extra=""):
    return ('<p class="back">%sThe business &mdash; software, websites and the '
            'tools that check them &mdash; is at '
            '<a href="https://f-keys.com" rel="noopener">f-keys.com</a>.</p>'
            % extra)


# ------------------------------------------------------------ landing
def landing():
    win = window("About the Author", """
      <h1 class="name chicago">Vince Gonzalez</h1>
      <p class="subline">Independent researcher &middot;
        <a href="https://orcid.org/%s" rel="noopener">ORCID&nbsp;%s</a></p>
      <p class="lede">Most of the work asks one question: <em>what does a claim
      actually rest on, and does the record agree with itself?</em></p>
      <p class="lede small">It runs from the axioms a formal proof spends &mdash;
      measured from the source rather than assumed &mdash; through machine-checked
      bounds in discrete geometry, to a formal account of testimony and the colour
      science behind accessible vision tests. The papers are open access and every
      one carries a DOI; the tools that produced them are public.</p>
      <hr class="rule">
      <p class="lede small" style="margin-bottom:10px;">Open a folder:</p>
      <nav class="jump" aria-label="Sections">
        <a href="/papers/">Papers</a>
        <a href="/programs/">Programs</a>
        <a href="/measurement/">Measurement</a>
        <a href="/record/">The record</a>
        <a href="/cv/">CV</a>
      </nav>
      <p class="backbiz">The business &mdash; software, websites, and the tools that
      check them &mdash; is at <a href="https://f-keys.com" rel="noopener">f-keys.com</a>.</p>
    """ % (ORCID, ORCID))

    folders = ['<nav class="folders" aria-label="Desktop">']
    for label, href, _key in MENU[1:]:
        svg = DOC_SVG if label == "CV" else FOLDER_SVG
        lbl = label.replace(" ", "&nbsp;")
        folders.append('    <a class="folder" href="%s">%s<span class="lbl">%s</span></a>'
                       % (href, svg, lbl))
    folders.append('  </nav>')

    body = "  " + win + "\n\n  " + "\n".join(folders)
    return shell("Epistemend — the published record",
                 "The published research of Vince Gonzalez: axiom dependence in "
                 "formal mathematics, certified bounds in discrete geometry, formal "
                 "epistemology, and colour-vision methodology. Open access, every "
                 "work with a DOI.",
                 "home", body)


# ------------------------------------------------------------ papers
def papers_page():
    with open(os.path.join(ROOT, "papers", "papers.json"), encoding="utf-8") as f:
        data = json.load(f)
    groups = data["groups"]
    total = sum(len(g["entries"]) for g in groups)
    with_doi = sum(1 for g in groups for e in g["entries"] if e.get("doi"))
    doi_line = ("every one open access, every one with a DOI"
                if with_doi == total
                else "open access; %d of %d carry a DOI" % (with_doi, total))

    def sort_entries(entries):
        return sorted(entries, key=lambda e: (e.get("date") or ""), reverse=True)

    out = [
        '<div class="doc">',
        '<p class="kicker">Papers</p>',
        '<h1>The deposited work</h1>',
        '<p class="intro">%s. Full texts are served from this domain where they '
        'live here, and otherwise resolve to Zenodo. Most recent first within each '
        'group.</p>' % (doi_line[0].upper() + doi_line[1:]),
        '<p class="by">%s &middot; '
        '<a href="https://orcid.org/%s" rel="noopener">ORCID %s</a> &middot; '
        'the tooling is at <a href="https://f-keys.com/gonzalgo/" rel="noopener">gonzalgo</a></p>'
        % (esc(NAME), ORCID, ORCID),
    ]
    for g in groups:
        out.append('<h2>%s <span class="count">%d</span></h2>'
                   % (esc(g["title"]), len(g["entries"])))
        if g.get("note"):
            out.append('<p class="note">%s</p>' % esc(g["note"]))
        for e in sort_entries(g["entries"]):
            meta = " &middot; ".join(esc(x) for x in (e.get("date"), e.get("kind")) if x)
            linkbits = []
            for l in (e.get("links") or []):
                rel = ' rel="noopener"' if l["href"].startswith("http") else ""
                linkbits.append('<a href="%s"%s>%s</a>' % (esc(l["href"]), rel, esc(l["label"])))
            links = " &middot; ".join(linkbits)
            out.append('<h3><a href="%s">%s</a></h3>' % (esc(e["url"]), esc(e["title"])))
            if meta:
                out.append('<p class="meta">%s</p>' % meta)
            if e.get("abstract"):
                out.append('<p class="abs">%s</p>' % esc(e["abstract"]))
            if links:
                out.append('<p class="links">%s</p>' % links)
        out.append("")
    out.append(back())
    out.append("</div>")
    inner = "\n".join(out)
    return shell("Papers — Epistemend",
                 "Deposited works by Vince Gonzalez: axiom dependence, discrete "
                 "geometry, formal epistemology, the Modulign standard, colour "
                 "vision. Open access, every one with a DOI.",
                 "papers", "  " + window("Papers", inner, wide=True))


# ------------------------------------------------------------ programs
PROGRAMS = [
    ("Axiom hygiene", """
<p>A proof assistant records what a theorem <em>reaches</em>, not what it
<em>needs</em>. The axiom-hygiene program measures the difference &mdash; what a
machine-checked result actually rests on, read from the source rather than
assumed &mdash; and removes the assumptions a theorem was paying for and did not
use.</p>
<p>The dominator analysis over 766,564 constants found that reachability
overstates responsibility by up to 58&times;, and that 60.1% of classically
dependent theorems have no single constant responsible for the dependence at
all. In Lean's Mathlib the removable classical dependence has a measured ceiling
of 13.1%, and an avoidable classical dependency sits inside <code>omega</code>
itself.</p>
<p>The instrument is <a href="https://f-keys.com/gonzalgo/" rel="noopener">gonzalgo</a>,
an axiom-provenance auditor for Lean 4 and Metamath; the repairs it finds are
contributed upstream.</p>
"""),
    ("set.mm contributions", """
<p>Where the analysis finds an avoidable axiom use, the construction half writes
the replacement proof and verifies it. Those repairs are merged into
<a href="https://github.com/metamath/set.mm" rel="noopener">metamath/set.mm</a>
and the Metamath executable, removing a dependence rather than only reporting
it.</p>
"""),
    ("Certified bounds in discrete geometry", """
<p>Machine-checked upper and lower bounds for covering, packing and opacity
problems &mdash; results where a published bound has to survive someone
re-running it on different hardware. The arithmetic is carried in a certified
enclosure rather than a float, so a computed inequality becomes a proof. The
deposited results include a certified upper bound for the Fejes T&oacute;th
point-goalie problem at n = 4 and the maximality of the added-vector codes in
the Cohn&ndash;Li kissing construction.</p>
"""),
    ("Integer sequences (OEIS)", """
<p>Sequences contributed to the On-Line Encyclopedia of Integer Sequences under
the name Vincent Gonzalez: <a href="https://oeis.org/A398262" rel="noopener">A398262</a>
published, with A398309 and A398310 in review, each linked to the paper it comes
from.</p>
"""),
    ("The Kernel Index", """
<p>A standing, machine-readable measurement of what fourteen formal libraries
across six foundations rest on &mdash; recomputed rather than quoted, and
published CC&nbsp;BY so the numbers can be checked against the libraries
themselves.</p>
"""),
]


def programs_page():
    out = ['<div class="doc">',
           '<p class="kicker">Programs</p>',
           '<h1>The research behind the papers</h1>',
           '<p class="intro">Each paper comes out of a standing program. These are '
           'the questions the work keeps returning to, and the tools built to '
           'answer them.</p>',
           '<p class="by">%s &middot; '
           '<a href="https://orcid.org/%s" rel="noopener">ORCID %s</a></p>'
           % (esc(NAME), ORCID, ORCID)]
    for title, html_body in PROGRAMS:
        out.append('<h2>%s</h2>' % esc(title))
        out.append(html_body.strip())
    out.append(back())
    out.append("</div>")
    return shell("Programs — Epistemend",
                 "Research programs by Vince Gonzalez: axiom hygiene, set.mm "
                 "contributions, certified bounds in discrete geometry, integer "
                 "sequences, the Kernel Index.",
                 "programs", "  " + window("Programs", "\n".join(out), wide=True))


# ------------------------------------------------------------ measurement
BENCHES = [
    ("kv-bench", "https://github.com/vince-gonzalez/kv-bench",
     "Cross-region staleness in Cloudflare Workers KV: how long a read keeps "
     "serving the old value after a write, and how that window scales with the "
     "cacheTtl you set. Timed from a clock outside the edge, reproducible, and "
     "archived with a DOI."),
    ("d1-replica-bench", "https://github.com/vince-gonzalez/d1-replica-bench",
     "Read-replica lag in Cloudflare D1: after a primary write, how long a "
     "replica in another region can still answer stale. Sub-round-trip in "
     "practice &mdash; and the finding that replicas are traffic-provisioned, not "
     "toggle-provisioned, published alongside the poll-scheduling correction that "
     "got there."),
    ("locationhint-bench", "https://github.com/vince-gonzalez/locationhint-bench",
     "Where a Durable Object actually lands when you ask for a region. Three of "
     "the documented location hints never reach their named region; placement is "
     "verified by trace rather than assumed."),
    ("d1bench", "https://github.com/vince-gonzalez/d1bench",
     "Which D1 bulk-write strategy wins, and which limit stops you first. A single "
     "<code>batch()</code> took 150,000 statements without refusal &mdash; the real "
     "ceiling is a thirty-second time budget, not a statement count &mdash; and "
     "literal SQL runs 2.7&times; faster at 64 columns until a row passes the "
     "statement-length limit and it stops being expressible at all. The upstream "
     "documentation was corrected from this measurement."),
    ("plateaudit", "https://github.com/vince-gonzalez/plateaudit",
     "Measuring pseudoisochromatic colour-vision plates from the stimulus a "
     "browser actually delivers, rather than the one the generator intended."),
]


def measurement_page():
    out = ['<div class="doc">',
           '<p class="kicker">Measurement</p>',
           '<h1>What the platform actually does</h1>',
           '<p class="intro">Documentation describes the limits one at a time and '
           'does not say how they interact. These harnesses measure the behaviour '
           'from outside and publish the raw data &mdash; the reproducible half of '
           'the research.</p>',
           '<p class="by">%s &middot; '
           '<a href="https://orcid.org/%s" rel="noopener">ORCID %s</a></p>'
           % (esc(NAME), ORCID, ORCID)]
    for name, url, blurb in BENCHES:
        out.append('<h3><a href="%s" rel="noopener">%s</a></h3>' % (esc(url), esc(name)))
        out.append('<p class="abs">%s</p>' % blurb)
    out.append(back())
    out.append("</div>")
    return shell("Measurement — Epistemend",
                 "Platform-measurement harnesses by Vince Gonzalez: Cloudflare KV "
                 "staleness, D1 replica lag and write ceilings, Durable Object "
                 "placement, colour-plate delivery.",
                 "measurement", "  " + window("Measurement", "\n".join(out), wide=True))


# ------------------------------------------------------------ record
RECORD = [
    ("ORCID", "https://orcid.org/" + ORCID, "0009-0005-3640-014X",
     "The canonical identifier; every deposit is claimed here."),
    ("OpenAlex", "https://openalex.org/works?filter=author.orcid:" + ORCID,
     "author works", "The works as an open bibliographic index records them."),
    ("Zenodo", "https://zenodo.org/search?q=orcid:" + ORCID,
     "deposits", "Where the full texts live, each immutable with a DOI."),
    ("OEIS", "https://oeis.org/search?q=Vincent+Gonzalez",
     "Vincent Gonzalez", "Contributed integer sequences."),
    ("Scholia", "https://scholia.toolforge.org/author/Q140936504",
     "author profile", "A live, auto-generated profile built from Wikidata."),
]


def record_page():
    rows = []
    for label, url, linklabel, note in RECORD:
        rows.append('<li><span class="k">%s</span><span>'
                    '<a href="%s" rel="noopener">%s</a> &mdash; %s</span></li>'
                    % (esc(label), esc(url), esc(linklabel), esc(note)))
    inner = ('<div class="doc">'
             '<p class="kicker">The record</p>'
             '<h1>Where the work is indexed</h1>'
             '<p class="intro">One identity, resolved across the places the work '
             'lives. Nothing here is a claim this site makes about itself &mdash; '
             'each is an outside index you can check.</p>'
             '<ul class="reclist">%s</ul>%s</div>'
             % ("".join(rows), back()))
    return shell("The Record — Epistemend",
                 "Vince Gonzalez across ORCID, OpenAlex, Zenodo, OEIS and Wikidata "
                 "/ Scholia.",
                 "record", "  " + window("The Record", inner))


# ------------------------------------------------------------ cv (academic)
def cv_page():
    inner = """<div class="doc">
<div class="banner">Academic CV. Unlisted: search engines are asked not to index
or follow it. Share the URL directly. Contact is on request through
<a href="https://f-keys.com/contact.html" rel="noopener">f-keys.com/contact</a>.</div>
<p class="kicker">Curriculum Vit&aelig;</p>
<h1>Vince Gonzalez</h1>
<p class="by">Independent researcher &middot; formal methods, discrete geometry,
formal epistemology &middot;
<a href="https://orcid.org/%s" rel="noopener">ORCID %s</a></p>

<h2>Research</h2>
<ul>
<li><strong>Formal methods.</strong> Axiom provenance for Lean&nbsp;4 and Metamath:
separating what a theorem states from what its proof consumes, measured across
libraries, with the avoidable dependencies removed upstream.</li>
<li><strong>Discrete geometry.</strong> Certified upper and lower bounds for
covering, packing and opacity problems, carried in exact and interval arithmetic
so a computed inequality becomes a proof.</li>
<li><strong>Formal epistemology.</strong> Formal accounts of testimony,
attestation and the admissibility of machine-generated evidence; the Modulign
dimensional-address standard and its application to law and regulation.</li>
<li><strong>Colour-vision methodology.</strong> Reproducible pseudoisochromatic
plate generation and recovery, with a published off-axis palette limitation
reported rather than corrected silently
(<a href="https://doi.org/10.5281/zenodo.21310578" rel="noopener">DOI
10.5281/zenodo.21310578</a>).</li>
</ul>

<h2>Publications</h2>
<p>Open access, every one with a DOI. The full record is in
<a href="/papers/">Papers</a>; integer sequences are in
<a href="/programs/">Programs</a>.</p>

<h2>Education</h2>
<p>Ohio University &mdash; B.A., Pre-Law Philosophy, Minor in History, 2012.
Gateway Scholarship Award.</p>

<h2>Technical</h2>
<ul>
<li><strong>Languages.</strong> JavaScript, Python, C#/.NET, SQL, GLSL, HTML, CSS.</li>
<li><strong>Formal &amp; AI.</strong> Lean&nbsp;4 proof auditing, Metamath, local
LLM deployment, evaluation pipelines.</li>
<li><strong>Infrastructure.</strong> Git/GitHub, GitHub Actions and Pages,
Cloudflare (DNS, CDN, Pages, Workers, D1), Linux, SSH.</li>
<li><strong>Frontend &amp; docs.</strong> WCAG&nbsp;2.2 AA, responsive design,
WebGL and Canvas, Schema.org, DOI publication.</li>
</ul>
%s</div>""" % (ORCID, ORCID, back())
    return shell("Academic CV — Epistemend",
                 "Academic CV of Vince Gonzalez: formal methods, discrete geometry, "
                 "formal epistemology, colour-vision methodology.",
                 "cv", "  " + window("Curriculum Vitæ", inner), noindex=True)


# ------------------------------------------------------------ main
def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    # Write LF; Pages serves either, and a stable newline keeps diffs honest.
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return len(content)


def main():
    pages = [
        ("index.html", landing()),
        ("papers/index.html", papers_page()),
        ("programs/index.html", programs_page()),
        ("measurement/index.html", measurement_page()),
        ("record/index.html", record_page()),
        ("cv/index.html", cv_page()),
    ]
    for path, content in pages:
        n = write(path, content)
        print("wrote %-24s %6d bytes" % (path, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
