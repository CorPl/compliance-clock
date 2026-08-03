#!/usr/bin/env python3
"""Generate the static site + machine feed from the ledger.

Fail-closed: refuses to build unless validate.py passes. Output is pure static
files — nothing intelligent runs at serve time, so nothing can fail when a
reader or an AI agent queries the feed.
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

JUR_NAMES = {"UK": "United Kingdom", "FR": "France", "DE": "Germany", "PL": "Poland",
             "BE": "Belgium", "RO": "Romania", "EU": "European Union"}
DOMAIN_NAMES = {"tax-filing": "Tax filing", "e-invoicing": "E-invoicing", "vat": "VAT",
                "company-register": "Company register", "employer": "Employer duties",
                "landlord": "Landlord rules", "ai-act": "AI Act"}

CSS = """
:root{--paper:#f6f7f4;--card:#fff;--ink:#1d2521;--soft:#4b564f;--line:#d9ded9;
--green:#1d4d3b;--green-soft:#e7efe9;--brass:#8a6d1a;--warn:#a33d2a;--warn-soft:#f7e9e5}
@media(prefers-color-scheme:dark){:root{--paper:#131916;--card:#1a211d;--ink:#e6eae6;
--soft:#a4b0a8;--line:#2c3630;--green:#6fbf9a;--green-soft:#1e2f26;--brass:#d4b04a;
--warn:#e08a74;--warn-soft:#33201a}}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);margin:0;
font-family:Seravek,'Gill Sans Nova',Ubuntu,Calibri,'Trebuchet MS',sans-serif;line-height:1.55;
padding:2.2rem 1rem 4rem}.page{max-width:46rem;margin:0 auto}
h1,h2{font-family:Charter,'Bitstream Charter','Sitka Text',Cambria,Georgia,serif;margin:0;line-height:1.2}
h1{font-size:1.9rem}h2{font-size:1.15rem;margin:2rem 0 .8rem}
.lede{color:var(--soft);margin:.5rem 0 0;font-size:1rem}
header{border-bottom:3px double var(--line);padding-bottom:1.2rem;margin-bottom:1.4rem}
.meta{font-size:.78rem;color:var(--soft);margin-top:.6rem}
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
footer{margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem;
font-size:.8rem;color:var(--soft)}
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


def esc(s):
    return html.escape(str(s), quote=True)


def freshness(status):
    """Per-jurisdiction oldest successful check + any failing sources."""
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

    jur_buttons = '<button data-v="all" aria-pressed="true">All countries</button>' + "".join(
        f'<button data-v="{j}" aria-pressed="false">{esc(n)}</button>' for j, n in JUR_NAMES.items())
    dom_buttons = '<button data-v="all" aria-pressed="true">All topics</button>' + "".join(
        f'<button data-v="{d}" aria-pressed="false">{esc(n)}</button>' for d, n in DOMAIN_NAMES.items())

    gen = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    parts = [f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Compliance Clock — verified UK &amp; EU small-business deadlines</title>
<meta name="description" content="A continuously verified feed of compliance deadlines and rule changes for small businesses in the UK, France, Germany, Poland, Belgium and Romania. Every entry linked to its official source.">
<style>{CSS}</style></head><body><div class="page">
<header><h1>The Compliance Clock</h1>
<p class="lede">Verified deadlines and rule changes for small businesses — UK &amp; Europe.
Every entry links to its official government source, with the date we verified it.</p>
<p class="meta">Generated {gen} · <a href="feed.json">machine-readable feed</a> ·
<a href="status.html">source freshness</a> · {len(entries)} entries</p></header>
{stale_note}
<div class="filters" id="jur">{jur_buttons}</div>
<div class="filters" id="dom">{dom_buttons}</div>
<h2>Upcoming deadlines</h2>''']
    parts += [entry_html(e) for e in upcoming] or ["<p>None in scope yet.</p>"]
    parts.append("<h2>Standing rules (always in force)</h2>")
    parts += [entry_html(e) for e in recurring]
    parts.append("<h2>Recently in force</h2>")
    parts += [entry_html(e) for e in in_force]
    parts.append(f'''<footer>The Compliance Clock reports what official sources say, with
links and dates. It is an information service, not legal or tax advice.
Corrections are published openly — entries are never silently edited.</footer>
</div><script>{FILTER_JS}</script></body></html>''')
    return "".join(parts)


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
    gen = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Source freshness — The Compliance Clock</title><style>{CSS}</style></head>
<body><div class="page"><header><h1>Source freshness</h1>
<p class="lede">When each official source was last successfully checked. If a watcher
breaks, it shows here — we display staleness rather than hide it.</p>
<p class="meta">Generated {gen} · last watcher run: {esc(status.get("last_run") or "never")} ·
<a href="index.html">back to the Clock</a></p></header>
<table><tr><th>Source</th><th>Country</th><th>Topic</th><th>Last checked OK</th><th>State</th></tr>
{"".join(rows)}</table></div></body></html>'''


def build_feed(entries, status):
    by_jur, failing = freshness(status)
    return {
        "project": "The Compliance Clock",
        "description": "Verified compliance deadlines and rule changes for small businesses (UK, FR, DE, PL, BE, RO, EU). Official sources only.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disclaimer": "Information service reporting official sources; not legal or tax advice. Entries are append-only; corrections reference the id they supersede.",
        "freshness": {"last_watcher_run": status.get("last_run"),
                      "last_ok_by_jurisdiction": by_jur,
                      "failing_sources": failing},
        "entry_count": len(entries),
        "entries": entries,
    }


def main():
    if validate.main() != 0:
        print("BUILD BLOCKED: ledger failed validation. Site and feed left untouched.")
        return 1
    entries = json.loads((DATA / "ledger" / "entries.json").read_text(encoding="utf-8"))
    status = json.loads((DATA / "status.json").read_text(encoding="utf-8")) \
        if (DATA / "status.json").exists() else {"sources": {}, "last_run": None}
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(build_index(entries, status), encoding="utf-8")
    (SITE / "status.html").write_text(build_status(status), encoding="utf-8")
    (SITE / "feed.json").write_text(
        json.dumps(build_feed(entries, status), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built site/ — {len(entries)} entries → index.html, status.html, feed.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
