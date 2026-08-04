#!/usr/bin/env python3
"""Generate the static site + machine feed from the ledger.

Fail-closed: refuses to build unless validate.py passes. Output is pure static
files — nothing intelligent runs at serve time, so nothing can fail when a
reader or an AI agent queries the feed.

Pages: index.html (the clock), about.html (what/how/methodology),
disclaimer.html (legal + privacy), status.html (source freshness),
plus feed.json, llms.txt, robots.txt for machines.
"""
import html
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
TODAY = date.today()
SITE_URL = "https://compliancecheck.uk"
CONTACT = "a2a@compliancecheck.uk"

JUR_NAMES = {"UK": "United Kingdom", "FR": "France", "DE": "Germany", "PL": "Poland",
             "BE": "Belgium", "RO": "Romania", "EU": "European Union"}
DOMAIN_NAMES = {"tax-filing": "Tax filing", "e-invoicing": "E-invoicing", "vat": "VAT",
                "company-register": "Company register", "employer": "Employer duties",
                "landlord": "Landlord rules", "ai-act": "AI Act"}

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='7' fill='%231d4d3b'/%3E"
           "%3Cpath d='M9 17l5 5 9-11' stroke='white' stroke-width='3.5' fill='none' "
           "stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")

CSS = """
:root{--paper:#f6f7f4;--card:#fff;--ink:#1d2521;--soft:#4b564f;--line:#d9ded9;
--green:#1d4d3b;--green-soft:#e7efe9;--brass:#8a6d1a;--warn:#a33d2a;--warn-soft:#f7e9e5}
@media(prefers-color-scheme:dark){:root{--paper:#131916;--card:#1a211d;--ink:#e6eae6;
--soft:#a4b0a8;--line:#2c3630;--green:#6fbf9a;--green-soft:#1e2f26;--brass:#d4b04a;
--warn:#e08a74;--warn-soft:#33201a}}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);margin:0;
font-family:Seravek,'Gill Sans Nova',Ubuntu,Calibri,'Trebuchet MS',sans-serif;line-height:1.55;
padding:0 1rem 4rem}.page{max-width:46rem;margin:0 auto}
h1,h2,h3.serif{font-family:Charter,'Bitstream Charter','Sitka Text',Cambria,Georgia,serif;margin:0;line-height:1.2}
h1{font-size:1.9rem}h2{font-size:1.2rem;margin:2.2rem 0 .8rem}
.lede{color:var(--soft);margin:.6rem 0 0;font-size:1.02rem;max-width:38rem}
.topbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.6rem;
padding:1rem 0;border-bottom:1px solid var(--line);margin-bottom:1.6rem}
.wordmark{display:flex;align-items:center;gap:.55rem;text-decoration:none;color:var(--ink)}
.wordmark .mark{width:1.45rem;height:1.45rem;border-radius:.33rem;background:var(--green);
display:inline-flex;align-items:center;justify-content:center;flex:none}
.wordmark .mark svg{width:.95rem;height:.95rem}
.wordmark .name{font-family:Charter,'Bitstream Charter','Sitka Text',Cambria,Georgia,serif;
font-weight:700;font-size:1.08rem}
nav.site{display:flex;gap:1rem;font-size:.85rem}
nav.site a{color:var(--soft);text-decoration:none}
nav.site a:hover,nav.site a[aria-current=page]{color:var(--green)}
.stats{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:1rem}
.stat{font-size:.78rem;padding:.22rem .7rem;border-radius:99px;background:var(--green-soft);
color:var(--green);font-weight:600}
.nextup{display:flex;gap:.7rem;align-items:baseline;background:var(--card);
border:1px solid var(--green);border-left:4px solid var(--green);border-radius:6px;
padding:.75rem 1rem;margin:1.4rem 0 .4rem;font-size:.95rem}
.nextup .d{font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace;font-weight:700;
color:var(--green);white-space:nowrap}
.meta{font-size:.78rem;color:var(--soft);margin-top:.8rem}
.filters{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0}
.filters button{font:inherit;font-size:.8rem;padding:.25rem .7rem;border-radius:99px;
border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.filters button[aria-pressed=true]{background:var(--green);border-color:var(--green);color:#fff}
.entry{background:var(--card);border:1px solid var(--line);border-radius:6px;
padding:.9rem 1.1rem;margin:.6rem 0}
.entry .top{display:flex;flex-wrap:wrap;gap:.5rem;align-items:baseline}
.date{font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace;font-weight:700;
color:var(--green);font-size:.9rem;white-space:nowrap}
.chip{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;padding:.1rem .5rem;
border-radius:99px;background:var(--green-soft);color:var(--green);font-weight:600}
.chip.status-announced{background:var(--warn-soft);color:var(--warn)}
.chip.status-proposed,.chip.status-unverified{background:transparent;border:1px dashed var(--line);color:var(--soft)}
.entry h3{font-size:1rem;margin:.35rem 0 .2rem;font-family:inherit}
.entry p{margin:.25rem 0;font-size:.92rem}.who{color:var(--soft);font-size:.85rem}
.src{font-size:.78rem;color:var(--soft)}.src a{color:var(--green);word-break:break-all}
.stale{background:var(--warn-soft);border:1px solid var(--warn);color:var(--ink);
border-radius:6px;padding:.7rem 1rem;font-size:.88rem;margin:1rem 0}
.prose p{margin:.7rem 0;max-width:40rem}.prose ul{max-width:40rem}
.prose li{margin:.4rem 0}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.8rem;margin:1.2rem 0}
.pillar{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:.9rem 1rem}
.pillar h3{font-size:.95rem;margin:0 0 .3rem;color:var(--green)}
.pillar p{font-size:.86rem;margin:0;color:var(--soft)}
code,pre{font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace;font-size:.85em;
background:var(--green-soft);border-radius:4px;padding:.1rem .35rem}
pre{padding:.8rem 1rem;overflow-x:auto}
footer{margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem;
font-size:.8rem;color:var(--soft)}
footer a{color:var(--green)}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{text-align:left;padding:.45rem .6rem .45rem 0;border-bottom:1px solid var(--line)}
th{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--soft)}
.ok{color:var(--green);font-weight:600}.err{color:var(--warn);font-weight:600}
a{color:var(--green)}
"""

FILTER_JS = """
document.querySelectorAll('.filters button').forEach(function(btn){
  btn.addEventListener('click',function(){
    var group=btn.closest('.filters');
    group.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed','false')});
    btn.setAttribute('aria-pressed','true');apply();
  });
});
function apply(){
  var j=document.querySelector('#jur button[aria-pressed=true]').dataset.v;
  var d=document.querySelector('#dom button[aria-pressed=true]').dataset.v;
  document.querySelectorAll('.entry').forEach(function(el){
    var show=(j==='all'||el.dataset.jur===j)&&(d==='all'||el.dataset.dom===d);
    el.style.display=show?'':'none';
  });
}
"""

TICK_SVG = ("<svg viewBox='0 0 32 32' aria-hidden='true'><path d='M9 17l5 5 9-11' "
            "stroke='white' stroke-width='4' fill='none' stroke-linecap='round' "
            "stroke-linejoin='round'/></svg>")


def esc(s):
    return html.escape(str(s), quote=True)


def gen_stamp():
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def shell(title, desc, current, body, head_extra=""):
    """Shared page shell: head, topbar nav, footer."""
    nav_items = [("index.html", "The clock"), ("about.html", "About"),
                 ("status.html", "Source freshness"), ("disclaimer.html", "Legal"),
                 ("feed.json", "Feed")]
    nav = "".join(
        f'<a href="{h}"{" aria-current=page" if h == current else ""}>{esc(t)}</a>'
        for h, t in nav_items)
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}/{current if current != "index.html" else ""}">
<link rel="icon" href="{FAVICON}">
<link rel="canonical" href="{SITE_URL}/{current if current != "index.html" else ""}">
{head_extra}<style>{CSS}</style></head><body><div class="page">
<div class="topbar">
<a class="wordmark" href="index.html"><span class="mark">{TICK_SVG}</span>
<span class="name">Compliance Check</span></a>
<nav class="site">{nav}</nav>
</div>
{body}
<footer>Compliance Check is an information service reporting what official sources say,
with links and verification dates — it is not legal, tax or professional advice:
<a href="disclaimer.html">read the full disclaimer</a>.
Entries are append-only; corrections are published openly, never silently edited.<br>
Data licence: <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">CC BY 4.0</a>
(free to use with attribution to Compliance Check — compliancecheck.uk) ·
Contact: <a href="mailto:{CONTACT}">{CONTACT}</a></footer>
</div></body></html>'''


def freshness(status):
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
    by_jur, failing = {}, []
    for src in sources:
        st = status.get("sources", {}).get(src["id"], {})
        jur = src["jurisdiction"]
        ok = st.get("last_ok")
        prev = by_jur.get(jur)
        if ok is None or (prev is not None and ok < prev) or jur not in by_jur:
            by_jur[jur] = ok if (prev is None or ok is None or ok < prev) else prev
        if st.get("consecutive_failures", 0) >= 3:
            failing.append(src["id"])
    return by_jur, failing


def entry_html(e):
    when = e["date"] or (e["recurrence"] or "ongoing")
    status_chip = f'<span class="chip status-{esc(e["status"])}">{esc(e["status"])}</span>'
    srcs = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(u.split("//")[1].split("/")[0])}</a>'
                      for u in e["sources"])
    notes = f'<p class="who">{esc(e["notes"])}</p>' if e.get("notes") else ""
    return f'''<article class="entry" data-jur="{esc(e["jurisdiction"])}" data-dom="{esc(e["domain"])}">
<div class="top"><span class="date">{esc(when)}</span>
<span class="chip">{esc(JUR_NAMES.get(e["jurisdiction"], e["jurisdiction"]))}</span>
<span class="chip">{esc(DOMAIN_NAMES.get(e["domain"], e["domain"]))}</span>{status_chip}</div>
<h3>{esc(e["title"])}</h3><p>{esc(e["summary"])}</p>
<p class="who">Applies to: {esc(e["who"])}</p>{notes}
<p class="src">Source: {srcs} · verified {esc(e["verified"])}</p></article>'''


def build_index(entries, status):
    upcoming = sorted([e for e in entries if e["date"] and e["date"] >= TODAY.isoformat()],
                      key=lambda e: e["date"])
    recurring = [e for e in entries if e["type"] == "recurring-rule"]
    in_force = sorted([e for e in entries if e["date"] and e["date"] < TODAY.isoformat()],
                      key=lambda e: e["date"], reverse=True)
    by_jur, failing = freshness(status)

    stale_note = ""
    if failing:
        stale_note = ('<div class="stale"><strong>Transparency note:</strong> '
                      f'{len(failing)} monitored source(s) are currently failing checks '
                      f'({esc(", ".join(failing))}). Entries from these sources may lag. '
                      'We show this rather than hide it.</div>')

    nextup = ""
    if upcoming:
        nxt = upcoming[0]
        days = (date.fromisoformat(nxt["date"]) - TODAY).days
        when = "today" if days == 0 else ("tomorrow" if days == 1 else f"in {days} days")
        nextup = (f'<div class="nextup"><span class="d">{esc(nxt["date"])}</span>'
                  f'<span><strong>Next deadline ({esc(when)}):</strong> {esc(nxt["title"])} '
                  f'— {esc(JUR_NAMES.get(nxt["jurisdiction"], nxt["jurisdiction"]))}</span></div>')

    jur_buttons = '<button data-v="all" aria-pressed="true">All countries</button>' + "".join(
        f'<button data-v="{j}" aria-pressed="false">{esc(n)}</button>' for j, n in JUR_NAMES.items())
    dom_buttons = '<button data-v="all" aria-pressed="true">All topics</button>' + "".join(
        f'<button data-v="{d}" aria-pressed="false">{esc(n)}</button>' for d, n in DOMAIN_NAMES.items())

    desc = ("Verified compliance deadlines and rule changes for small businesses in the UK, "
            "France, Germany, Poland, Belgium and Romania. Every entry links to its official "
            "government source. Machine-readable feed for AI tools and agents.")
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Compliance Check — UK & EU small-business compliance deadlines",
        "description": desc, "url": SITE_URL,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "creator": {"@type": "Organization", "name": "Compliance Check",
                    "url": SITE_URL, "email": CONTACT},
        "dateModified": TODAY.isoformat(),
        "spatialCoverage": list(JUR_NAMES.values()),
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json",
                          "contentUrl": f"{SITE_URL}/feed.json"}],
        "isAccessibleForFree": True,
    }, ensure_ascii=False)
    head_extra = f'<script type="application/ld+json">{jsonld}</script>\n'

    body = [f'''<header>
<h1>Verified compliance deadlines for small businesses — UK &amp; Europe</h1>
<p class="lede">Every deadline and rule change below is verified against its official
government source, dated, and never silently edited. Built for busy owners — and for
the AI tools and agents that increasingly act on their behalf.</p>
<div class="stats"><span class="stat">{len(entries)} verified entries</span>
<span class="stat">{len(JUR_NAMES)} jurisdictions</span>
<span class="stat">checked daily</span>
<span class="stat">every entry sourced</span></div>
{nextup}
<p class="meta">Generated {gen_stamp()} ·
<a href="feed.json">machine-readable feed</a> · <a href="about.html">how this works</a> ·
<a href="status.html">source freshness</a></p>
</header>
{stale_note}
<div class="filters" id="jur">{jur_buttons}</div>
<div class="filters" id="dom">{dom_buttons}</div>
<h2>Upcoming deadlines</h2>''']
    body += [entry_html(e) for e in upcoming] or ["<p>None in scope yet.</p>"]
    body.append("<h2>Standing rules (always in force)</h2>")
    body += [entry_html(e) for e in recurring]
    body.append("<h2>Recently in force</h2>")
    body += [entry_html(e) for e in in_force]
    body.append(f"<script>{FILTER_JS}</script>")
    return shell("Compliance Check — verified UK & EU small-business deadlines",
                 desc, "index.html", "".join(body), head_extra)


def build_about(entries):
    counts = {}
    for e in entries:
        counts[e["jurisdiction"]] = counts.get(e["jurisdiction"], 0) + 1
    per_jur = " · ".join(f"{JUR_NAMES[j]}: {n}" for j, n in sorted(counts.items(),
                         key=lambda kv: -kv[1]))
    body = f'''<header><h1>What Compliance Check is</h1>
<p class="lede">A continuously verified record of the deadlines and rule changes that
hit small businesses across the UK and Europe — published for people and machines.</p></header>
<div class="prose">
<p>Small-business compliance truth is scattered across dozens of official websites in a
dozen languages: HMRC and Companies House in the UK, the tax authorities of France,
Germany, Poland, Belgium and Romania, and the EU institutions. Compliance Check watches
those official sources, verifies every change, and publishes one clean, dated record —
free to read, free to build on.</p>
<p>It is built as much for <strong>software and AI agents</strong> as for people. As
tools increasingly file, invoice and keep books on a business's behalf, they need a
source of truth that is provably current and honest about its own freshness. That is
the entire design brief of this site.</p>
</div>
<h2>How every entry earns its place</h2>
<div class="pillars">
<div class="pillar"><h3>Official sources only</h3><p>Every entry cites government or
EU pages — never news articles, never consultancy blogs. The source link and the date
we verified it are printed on the entry itself.</p></div>
<div class="pillar"><h3>Honest status labels</h3><p>Each entry is marked
<em>confirmed</em> (in force or in law), <em>announced</em> (stated by government, not
yet law), <em>proposed</em>, or <em>unverified</em> — we publish uncertainty rather
than hide it.</p></div>
<div class="pillar"><h3>Append-only record</h3><p>Published entries are never silently
edited. Corrections are published as new entries that reference what they supersede —
so the record of what we said, and when, is permanent.</p></div>
<div class="pillar"><h3>Freshness in the open</h3><p>Automated watchers check every
official source daily. When each source was last successfully checked — including any
failures — is public on the <a href="status.html">source freshness page</a>.</p></div>
<div class="pillar"><h3>Fail-closed publishing</h3><p>Nothing reaches this site without
passing validation, and detected changes are verified by a human editor before
publication. A failure can delay an update; it can never corrupt one.</p></div>
<div class="pillar"><h3>Free and reusable</h3><p>The data is licensed
<a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">CC BY 4.0</a>:
use it in your product, app or agent with attribution to Compliance Check.</p></div>
</div>
<h2>For developers and AI agents</h2>
<div class="prose">
<p>The whole dataset is served as one static JSON document —
<a href="feed.json"><code>{SITE_URL}/feed.json</code></a> — with per-jurisdiction
freshness metadata, entry statuses and official source URLs. There is no API key, no
rate ceremony and nothing dynamic to fail: it is a flat file behind a CDN, rebuilt
after every verified update. A machine-oriented site summary lives at
<a href="llms.txt"><code>/llms.txt</code></a>.</p>
<p>Current coverage: {per_jur}. Scope grows as the record matures; suggestions to
<a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
</div>
<h2>Who runs it</h2>
<div class="prose"><p>Compliance Check is an independent, UK-based information service,
launched in August 2026. It reports what official sources say — it does not interpret
the law and it is <a href="disclaimer.html">not legal, tax or professional advice</a>.
Contact: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p></div>'''
    return shell("About — Compliance Check",
                 "How Compliance Check verifies UK & EU small-business compliance "
                 "deadlines: official sources only, append-only record, public freshness.",
                 "about.html", body)


def build_disclaimer():
    body = f'''<header><h1>Legal disclaimer &amp; privacy</h1>
<p class="lede">Plain English, as short as we can responsibly make it.</p></header>
<div class="prose">
<h2>What this service is — and is not</h2>
<p>Compliance Check is an <strong>information service</strong>. It reports compliance
deadlines and rule changes for small businesses as published by official government and
EU sources, with links to those sources and the date each entry was verified.</p>
<p><strong>Nothing on this website or in its data feed is legal, tax, accounting,
financial or other professional advice</strong>, and none of it is a substitute for
advice from a qualified professional — a solicitor, accountant or tax adviser — who
knows your specific circumstances. Using this site does not create any professional
or client relationship.</p>
<h2>Accuracy — our effort and its limits</h2>
<ul>
<li>We verify every entry against official sources and print the source link and
verification date on the entry itself.</li>
<li>Laws and deadlines change, official pages are sometimes corrected, and despite our
care errors are possible. Information is provided <strong>"as is", without warranty of
any kind</strong> — including accuracy, completeness or timeliness.</li>
<li>Status labels (<em>confirmed / announced / proposed / unverified</em>) reflect our
good-faith assessment on the verification date shown, not a guarantee.</li>
<li><strong>Always check the linked official source before acting</strong> or making
decisions that depend on a date or rule shown here.</li>
</ul>
<h2>Liability</h2>
<p>To the fullest extent permitted by law, Compliance Check and its operator accept no
liability for any loss or damage — including lost profits, penalties, interest or
missed deadlines — arising from use of, or reliance on, this website or its data feed.
Nothing in this disclaimer excludes or limits any liability that cannot be excluded or
limited under applicable law.</p>
<h2>Third-party links</h2>
<p>Entries link to official government and EU websites. We are not responsible for the
content or availability of external sites.</p>
<h2>Reusing the data</h2>
<p>The dataset (including <code>feed.json</code>) is licensed under
<a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener">Creative Commons
Attribution 4.0 (CC BY 4.0)</a>. You may use it, including commercially, provided you
attribute "Compliance Check (compliancecheck.uk)". The disclaimers above travel with
the data: reusers must not present it as professional advice.</p>
<h2>Privacy</h2>
<ul>
<li>This site has <strong>no accounts, no cookies, and no analytics or tracking
scripts</strong>. We collect nothing about you.</li>
<li>Hosting (GitHub Pages) and DNS/network services (Cloudflare) may process standard
technical data such as IP addresses and browser types in their server logs, under
their own privacy policies, as with any website.</li>
<li>If you email us, we use your address only to reply, and share it with no one.</li>
</ul>
<h2>Contact</h2>
<p><a href="mailto:{CONTACT}">{CONTACT}</a> — corrections are especially welcome, and
are published openly per our append-only policy.</p>
<p class="meta">Last updated: {TODAY.strftime("%d/%m/%Y")}</p>
</div>'''
    return shell("Legal disclaimer & privacy — Compliance Check",
                 "Compliance Check is an information service, not legal or tax advice. "
                 "Accuracy limits, liability, data licence (CC BY 4.0) and privacy.",
                 "disclaimer.html", body)


def build_status(status):
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
    rows = []
    for src in sources:
        st = status.get("sources", {}).get(src["id"], {})
        ok = st.get("last_ok") or "never"
        fails = st.get("consecutive_failures", 0)
        if st.get("escalated"):
            state = '<span class="err">escalated — being re-routed to another official source</span>'
        elif fails == 0 and st.get("last_ok"):
            state = '<span class="ok">healthy</span>'
            if st.get("last_ok_url") and st.get("last_ok_url") != src["url"]:
                state += ' <span class="ok">(via fallback source)</span>'
        else:
            state = f'<span class="err">{fails} consecutive failures</span>'
        rows.append(f"<tr><td>{esc(src['id'])}</td><td>{esc(JUR_NAMES.get(src['jurisdiction'], src['jurisdiction']))}</td>"
                    f"<td>{esc(src['topic'])}</td><td>{esc(ok)}</td><td>{state}</td></tr>")
    body = f'''<header><h1>Source freshness</h1>
<p class="lede">When each official source was last successfully checked. If a watcher
breaks, it shows here — we display staleness rather than hide it.</p>
<p class="meta">Generated {gen_stamp()} · last watcher run:
{esc(status.get("last_run") or "never")}</p></header>
<table><tr><th>Source</th><th>Country</th><th>Topic</th><th>Last checked OK</th><th>State</th></tr>
{"".join(rows)}</table>'''
    return shell("Source freshness — Compliance Check",
                 "Live health of every official source Compliance Check monitors, "
                 "including failures — staleness is displayed, never hidden.",
                 "status.html", body)


def build_feed(entries, status):
    by_jur, failing = freshness(status)
    return {
        "project": "Compliance Check",
        "website": SITE_URL,
        "contact": CONTACT,
        "schema_version": "1.0",
        "description": ("Verified compliance deadlines and rule changes for small businesses "
                        "(UK, FR, DE, PL, BE, RO, EU). Official sources only; append-only; "
                        "statuses: confirmed/announced/proposed/unverified."),
        "license": "CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/ — attribute 'Compliance Check (compliancecheck.uk)'",
        "documentation": f"{SITE_URL}/about.html",
        "schema": f"{SITE_URL}/schema.json",
        "source_repository": "https://github.com/CorPl/compliance-clock",
        "provenance": ("Append-only ledger; every change is publicly auditable in the "
                       "source repository history. Raw snapshots of official source pages "
                       "are retained as evidence."),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disclaimer": ("Information service reporting official sources; not legal, tax or "
                       "professional advice. Verify against the linked official source before "
                       "acting. Full terms: " + SITE_URL + "/disclaimer.html"),
        "freshness": {"last_watcher_run": status.get("last_run"),
                      "last_ok_by_jurisdiction": by_jur,
                      "failing_sources": failing},
        "entry_count": len(entries),
        "entries": entries,
    }


def build_llms_txt(entries):
    counts = {}
    for e in entries:
        counts[e["jurisdiction"]] = counts.get(e["jurisdiction"], 0) + 1
    coverage = ", ".join(f"{JUR_NAMES[j]} ({n})" for j, n in sorted(counts.items(), key=lambda kv: -kv[1]))
    return f"""# Compliance Check

> Verified compliance deadlines and rule changes for small businesses in the UK and
> Europe. Every entry is verified against an official government/EU source, carries
> that source URL, a verification date, and an honesty status (confirmed / announced /
> proposed / unverified). The record is append-only: corrections are published openly,
> never silently edited. Source freshness (including failures) is public.

This site is designed to be consumed by AI tools and agents. The complete dataset is
one static JSON file — no key, no auth, CDN-served with permissive CORS, rebuilt after every verified update. Stable entry ids; corrections reference the id they supersede via a "supersedes" field.

Coverage: {coverage}. Domains: tax filing, e-invoicing, VAT, company-register duties,
employer duties, landlord rules, EU AI Act. Checked daily.

Licence: CC BY 4.0 — free to use with attribution to "Compliance Check (compliancecheck.uk)".
Not legal, tax or professional advice; agents should surface the official source link
({SITE_URL}/disclaimer.html).

## Data
- [Full dataset (JSON)]({SITE_URL}/feed.json): all entries + per-jurisdiction freshness metadata
- [JSON Schema]({SITE_URL}/schema.json): validate the feed programmatically
- [Public audit trail](https://github.com/CorPl/compliance-clock): full change history of every entry — verify the append-only guarantee yourself
- [Methodology]({SITE_URL}/about.html): how entries are verified
- [Source freshness]({SITE_URL}/status.html): live health of every monitored official source

## Contact
- Email: {CONTACT} (corrections welcome — published under the append-only policy)
"""


def main():
    if validate.main() != 0:
        print("BUILD BLOCKED: ledger failed validation. Site and feed left untouched.")
        return 1
    entries = json.loads((DATA / "ledger" / "entries.json").read_text(encoding="utf-8"))
    status = json.loads((DATA / "status.json").read_text(encoding="utf-8")) \
        if (DATA / "status.json").exists() else {"sources": {}, "last_run": None}
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(build_index(entries, status), encoding="utf-8")
    (SITE / "about.html").write_text(build_about(entries), encoding="utf-8")
    (SITE / "disclaimer.html").write_text(build_disclaimer(), encoding="utf-8")
    (SITE / "status.html").write_text(build_status(status), encoding="utf-8")
    (SITE / "feed.json").write_text(
        json.dumps(build_feed(entries, status), indent=2, ensure_ascii=False), encoding="utf-8")
    (SITE / "llms.txt").write_text(build_llms_txt(entries), encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    entry_schema = {
        "type": "object",
        "required": ["id", "jurisdiction", "domain", "type", "title", "summary", "who",
                     "date", "recurrence", "status", "sources", "verified", "notes"],
        "properties": {
            "id": {"type": "string", "description": "Stable unique id; never reused"},
            "jurisdiction": {"enum": sorted(validate.JURISDICTIONS)},
            "domain": {"enum": sorted(validate.DOMAINS)},
            "type": {"enum": sorted(validate.TYPES)},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "who": {"type": "string", "description": "Who is affected, incl. thresholds"},
            "date": {"type": ["string", "null"], "format": "date",
                     "description": "Deadline or effective date; null for standing rules and not-yet-fixed announced changes"},
            "recurrence": {"enum": ["quarterly", "annual", "monthly", None]},
            "status": {"enum": sorted(validate.STATUSES),
                       "description": "confirmed=in force/in law; announced=stated by government, not yet law; proposed=consultation/bill; unverified=could not confirm on an accessible official page"},
            "sources": {"type": "array", "minItems": 1,
                        "items": {"type": "string", "format": "uri"},
                        "description": "Official government/EU source URLs only"},
            "verified": {"type": "string", "format": "date",
                         "description": "Date we last verified this entry against its sources"},
            "notes": {"type": "string"},
            "supersedes": {"type": "string",
                           "description": "Id of the entry this correction supersedes (append-only policy)"},
        },
    }
    feed_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"{SITE_URL}/schema.json",
        "title": "Compliance Check feed",
        "description": "Schema for the Compliance Check dataset at " + SITE_URL + "/feed.json",
        "type": "object",
        "required": ["project", "schema_version", "generated_at", "freshness",
                     "entry_count", "entries"],
        "properties": {
            "project": {"const": "Compliance Check"},
            "schema_version": {"type": "string"},
            "generated_at": {"type": "string", "format": "date-time"},
            "freshness": {
                "type": "object",
                "properties": {
                    "last_watcher_run": {"type": ["string", "null"], "format": "date-time"},
                    "last_ok_by_jurisdiction": {"type": "object",
                                                "additionalProperties": {"type": ["string", "null"]}},
                    "failing_sources": {"type": "array", "items": {"type": "string"}},
                },
            },
            "entry_count": {"type": "integer"},
            "entries": {"type": "array", "items": entry_schema},
        },
    }
    (SITE / "schema.json").write_text(
        json.dumps(feed_schema, indent=2, ensure_ascii=False), encoding="utf-8")
    well_known = SITE / ".well-known"
    well_known.mkdir(exist_ok=True)
    expires = date(TODAY.year + 1, TODAY.month, 1).isoformat()
    (well_known / "security.txt").write_text(
        f"Contact: mailto:{CONTACT}\nExpires: {expires}T00:00:00Z\n"
        f"Preferred-Languages: en, ro\nCanonical: {SITE_URL}/.well-known/security.txt\n",
        encoding="utf-8")
    pages = ["", "about.html", "disclaimer.html", "status.html"]
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"<url><loc>{SITE_URL}/{p}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>\n"
                         for p in pages)
               + "</urlset>\n")
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"Built site/ — {len(entries)} entries → index, about, disclaimer, status, "
          f"feed.json, llms.txt, robots.txt, sitemap.xml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
