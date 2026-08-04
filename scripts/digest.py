#!/usr/bin/env python3
"""Weekly digest generator: deadlines in the next 60 days + entries verified in
the last 7 days. Prints markdown (for email/newsletter use). Read-only."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JUR = {"UK": "United Kingdom", "FR": "France", "DE": "Germany", "PL": "Poland",
       "BE": "Belgium", "RO": "Romania", "EU": "European Union"}


def main():
    entries = json.loads((ROOT / "data" / "ledger" / "entries.json").read_text(encoding="utf-8"))
    today = date.today()
    horizon = (today + timedelta(days=60)).isoformat()
    week_ago = (today - timedelta(days=7)).isoformat()

    upcoming = sorted([e for e in entries if e["date"] and today.isoformat() <= e["date"] <= horizon],
                      key=lambda e: e["date"])
    fresh = [e for e in entries if e["verified"] >= week_ago]

    print(f"# Compliance Check — week of {today.strftime('%d/%m/%Y')}\n")
    print("## Due in the next 60 days\n")
    if not upcoming:
        print("No tracked deadlines in the next 60 days.\n")
    for e in upcoming:
        d = date.fromisoformat(e["date"]).strftime("%d/%m/%Y")
        print(f"- **{d} · {JUR.get(e['jurisdiction'], e['jurisdiction'])}** — {e['title']} "
              f"({e['who']}) [{e['status']}]")
    status = {}
    status_file = ROOT / "data" / "status.json"
    if status_file.exists():
        status = json.loads(status_file.read_text(encoding="utf-8")).get("sources", {})
    troubled = {sid: st for sid, st in status.items() if st.get("consecutive_failures", 0) > 0}
    if troubled:
        print("\n## Watcher health — needs attention\n")
        for sid, st in troubled.items():
            if st.get("escalated"):
                print(f"- **{sid}: ESCALATED** — all official urls unavailable for "
                      f"{st['consecutive_failures']} runs; re-route to another official "
                      f"source or switch to manual verification")
            else:
                print(f"- {sid}: {st['consecutive_failures']} consecutive failure(s) — "
                      f"retrying daily, escalates at 5")

    print("\n## Newly verified this week\n")
    if not fresh:
        print("No new or re-verified entries this week.\n")
    for e in fresh:
        print(f"- {JUR.get(e['jurisdiction'], e['jurisdiction'])}: {e['title']} — {e['summary']}")
    print("\n*Every entry links to its official source at the website. "
          "Not legal or tax advice.*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
