#!/usr/bin/env python3
"""Watchers: check official sources for changes. FAIL-CLOSED by design.

- Detect + queue only. This script NEVER writes to the ledger or the site.
- Each source is independent: one failure never blocks the others.
- Every outcome (ok / changed / blocked / error) is recorded in data/status.json,
  which the status page displays publicly.
- On change: the raw page is snapshotted to data/snapshots/<source>/ and a
  review item is appended to data/queue.json.

Persistent-block escalation ladder (a CAPTCHA that never goes away must not
mean silent daily failure forever):
  1. Each source may list several OFFICIAL urls for the same facts (primary +
     fallbacks — ministry page, official portal, the law text itself). The
     watcher tries them in order; any one succeeding keeps the source healthy.
  2. Transient blocks clear on the next daily run.
  3. After ESCALATE_AT consecutive all-url failures the source is marked
     "escalated": shown prominently on the public status page and in the
     weekly digest, meaning: re-route this source (find another official
     witness) or switch it to scheduled manual verification.
  4. We NEVER bypass CAPTCHAs, rotate proxies, or disguise the client.
     Blocked means unavailable — recorded honestly, never faked around.

Stdlib only — no dependencies to break.
"""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAPSHOTS = DATA / "snapshots"
STATUS_FILE = DATA / "status.json"
QUEUE_FILE = DATA / "queue.json"
TIMEOUT = 30
UA = "ComplianceCheckWatcher/0.1 (+https://compliancecheck.uk; a2a@compliancecheck.uk)"
ESCALATE_AT = 5

# Signatures of bot-block / CAPTCHA / outage pages. A blocked fetch is an ERROR
# (source unavailable), never a "change".
BLOCK_SIGNS = [
    "radware captcha", "you are a bot", "request unblock", "access denied",
    "just a moment", "attention required", "pardon our interruption",
    "verify you are human", "ddos protection", "checking your browser",
]
# If the page text collapses to under this fraction of its last good size,
# treat it as an outage/soft-block rather than a real change.
COLLAPSE_RATIO = 0.3


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # atomic: a crash mid-write can't corrupt the file


def visible_text(html):
    """Crude but stable text extraction so cosmetic markup changes don't fire."""
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def try_url(url, baseline):
    """Attempt one url. Returns (outcome, detail) where outcome is
    'ok'|'changed'|'blocked'|'collapsed'|'error'."""
    try:
        html = fetch(url)
    except Exception as exc:
        return "error", f"{type(exc).__name__}: {exc}"[:300]
    text = visible_text(html)
    lowered = text.lower()
    hit = next((s for s in BLOCK_SIGNS if s in lowered), None)
    if hit:
        return "blocked", f"bot-block page (matched '{hit}')"
    last_len = baseline.get("last_len")
    if last_len and len(text) < COLLAPSE_RATIO * last_len:
        return "collapsed", f"content collapsed {last_len}->{len(text)} chars"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = baseline.get("last_hash") is not None and digest != baseline["last_hash"]
    return ("changed" if changed else "ok"), {"hash": digest, "len": len(text), "html": html}


def migrate(st, primary_url):
    """Old format kept last_hash/last_len at source level for the primary url."""
    if "last_hash" in st:
        st.setdefault("urls", {})[primary_url] = {
            "last_hash": st.pop("last_hash"), "last_len": st.pop("last_len", None)}
    st.setdefault("urls", {})
    return st


def check_source(src, status, queue):
    sid = src["id"]
    urls = [src["url"]] + src.get("fallback_urls", [])
    st = migrate(status["sources"].setdefault(sid, {}), src["url"])
    st.setdefault("consecutive_failures", 0)

    failures = []
    for url in urls:
        baseline = st["urls"].setdefault(url, {"last_hash": None, "last_len": None})
        outcome, detail = try_url(url, baseline)
        if outcome in ("error", "blocked", "collapsed"):
            failures.append(f"{url} -> {outcome}: {detail}")
            continue

        first_seen = baseline["last_hash"] is None
        if outcome == "changed" or first_seen:
            snap_dir = SNAPSHOTS / sid
            snap_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            (snap_dir / f"{stamp}.html").write_text(detail["html"], encoding="utf-8")
            if outcome == "changed":
                queue.append({
                    "source": sid, "url": url, "topic": src.get("topic", ""),
                    "detected": now_iso(), "snapshot": f"{sid}/{stamp}.html",
                    "state": "pending-review",
                })
        baseline["last_hash"] = detail["hash"]
        baseline["last_len"] = detail["len"]
        st["last_ok"] = now_iso()
        st["last_ok_url"] = url
        st["consecutive_failures"] = 0
        st["escalated"] = False
        via = "" if url == src["url"] else "  (via fallback url)"
        if failures:
            st["last_error"] = {"at": now_iso(), "error": "; ".join(failures)[:400]}
            print(f"  ok     {sid}{via} — primary blocked/erred, fallback healthy")
        elif outcome == "changed":
            print(f"  CHANGE {sid}{via}: queued for review")
        else:
            print(f"  ok     {sid}{via}" + ("  (baseline saved)" if first_seen else ""))
        return "changed" if outcome == "changed" else "ok"

    # every url failed
    st["last_error"] = {"at": now_iso(), "error": "; ".join(failures)[:400]}
    st["consecutive_failures"] += 1
    st["escalated"] = st["consecutive_failures"] >= ESCALATE_AT
    tag = "ESCALATED — needs re-routing or manual verification" if st["escalated"] \
        else f"failure #{st['consecutive_failures']}"
    print(f"  FAIL   {sid}: all {len(urls)} url(s) unavailable ({tag})")
    return "error"


def main():
    sources = load_json(DATA / "sources.json", {"sources": []})["sources"]
    status = load_json(STATUS_FILE, {"sources": {}, "last_run": None})
    queue = load_json(QUEUE_FILE, [])

    print(f"Compliance Check watchers — {len(sources)} sources, {now_iso()}")
    results = {"ok": 0, "changed": 0, "error": 0}
    for src in sources:
        results[check_source(src, status, queue)] += 1

    status["last_run"] = now_iso()
    save_json(STATUS_FILE, status)
    save_json(QUEUE_FILE, queue)
    escalated = [s for s, v in status["sources"].items() if v.get("escalated")]
    print(f"Done: {results['ok']} ok, {results['changed']} changed (queued), {results['error']} failing")
    if escalated:
        print(f"NEEDS ATTENTION (escalated): {', '.join(escalated)}")
    # Exit 0 even with per-source failures: they are recorded and displayed, not fatal.
    return 0


if __name__ == "__main__":
    sys.exit(main())
