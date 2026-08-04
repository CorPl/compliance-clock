#!/usr/bin/env python3
"""Ledger validation gate. build_site.py refuses to run if this fails.

Checks every entry for: required fields, allowed enum values, date formats,
unique ids, source URLs present and https, verification dates. Fail-closed:
any error blocks publication of the whole batch.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "ledger" / "entries.json"

JURISDICTIONS = {"UK", "FR", "DE", "PL", "BE", "RO", "EU"}
DOMAINS = {"tax-filing", "e-invoicing", "vat", "company-register", "employer", "landlord", "ai-act"}
TYPES = {"deadline", "rule-change", "recurring-rule"}
STATUSES = {"confirmed", "announced", "proposed", "unverified"}
RECURRENCES = {"quarterly", "annual", "monthly", None}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED = ["id", "jurisdiction", "domain", "type", "title", "summary", "who",
            "date", "recurrence", "status", "sources", "verified", "notes"]


def check_date(value, field, eid, errors, allow_null=False):
    if value is None:
        if not allow_null:
            errors.append(f"{eid}: {field} is null but required")
        return
    if not isinstance(value, str) or not DATE_RE.match(value):
        errors.append(f"{eid}: {field} '{value}' is not YYYY-MM-DD")
        return
    y, m, d = map(int, value.split("-"))
    try:
        date(y, m, d)
    except ValueError:
        errors.append(f"{eid}: {field} '{value}' is not a real date")


def main():
    try:
        entries = json.loads(LEDGER.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"FAIL: ledger not found at {LEDGER}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: ledger is not valid JSON: {exc}")
        return 1

    if not isinstance(entries, list) or not entries:
        print("FAIL: ledger must be a non-empty JSON array")
        return 1

    errors, seen_ids = [], set()
    for i, e in enumerate(entries):
        eid = e.get("id", f"<entry #{i}>")
        for f in REQUIRED:
            if f not in e:
                errors.append(f"{eid}: missing field '{f}'")
        if e.get("id") in seen_ids:
            errors.append(f"{eid}: duplicate id")
        seen_ids.add(e.get("id"))
        if e.get("jurisdiction") not in JURISDICTIONS:
            errors.append(f"{eid}: bad jurisdiction '{e.get('jurisdiction')}'")
        if e.get("domain") not in DOMAINS:
            errors.append(f"{eid}: bad domain '{e.get('domain')}'")
        if e.get("type") not in TYPES:
            errors.append(f"{eid}: bad type '{e.get('type')}'")
        if e.get("status") not in STATUSES:
            errors.append(f"{eid}: bad status '{e.get('status')}'")
        if e.get("recurrence") not in RECURRENCES:
            errors.append(f"{eid}: bad recurrence '{e.get('recurrence')}'")
        # date may be null for standing rules, and for announced/proposed changes
        # whose commencement date is genuinely not yet fixed in law
        null_date_ok = (e.get("type") == "recurring-rule"
                        or e.get("status") in ("announced", "proposed"))
        check_date(e.get("date"), "date", eid, errors, allow_null=null_date_ok)
        check_date(e.get("verified"), "verified", eid, errors)
        srcs = e.get("sources")
        if not isinstance(srcs, list) or not srcs:
            errors.append(f"{eid}: sources must be a non-empty list")
        else:
            for s in srcs:
                if not (isinstance(s, str) and s.startswith("https://")):
                    errors.append(f"{eid}: source '{s}' is not an https URL")
        for f in ("title", "summary", "who"):
            if not str(e.get(f, "")).strip():
                errors.append(f"{eid}: '{f}' is empty")

    if errors:
        print(f"FAIL: {len(errors)} problem(s):")
        for msg in errors:
            print("  -", msg)
        return 1
    print(f"OK: {len(entries)} entries valid, ids unique, all sourced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
