# The Compliance Clock

A continuously verified record of compliance deadlines and rule changes for small
businesses across the UK and Europe — published for people (website + weekly digest)
and machines (JSON feed, later an MCP connector).

Pilot scope: UK, France, Germany, Poland, Belgium, Romania.
Domains: tax filing, e-invoicing, VAT, company-register duties, employer duties, landlord rules.

## Architecture (three layers)

1. **Watchers** (`scripts/watch.py` + `data/sources.json`) — fetch official government
   pages on a schedule, snapshot them, and detect changes by content hash.
   Detected changes go to `data/queue.json` for editorial review. Watchers never
   publish anything.
2. **Ledger** (`data/ledger/entries.json`) — the asset. Append-only list of verified
   entries; every entry carries official source URLs, a verification date, and a
   status (`confirmed` / `announced` / `proposed` / `unverified`). Corrections are
   appended (see `supersedes` field), never silently edited.
3. **Taps** (`scripts/build_site.py`, `scripts/digest.py`) — generate the static
   website (`site/index.html`), the machine feed (`site/feed.json`), the public
   status page (`site/status.html`), and the weekly digest markdown.

## Fail-safe principles (requested by Cornel, 2026-08-03)

- **Fail closed.** Errors can delay an update; they can never corrupt the feed.
  Watcher/AI failure leaves the last-known-good site and feed serving untouched.
- **No AI at serve time.** The site and feed are static files; nothing intelligent
  runs when a reader or agent queries them.
- **Staleness is public.** Every source shows "last successfully checked" on the
  status page; the feed carries per-jurisdiction freshness metadata. If a watcher
  breaks, the site says so instead of pretending.
- **Independence.** Each watcher runs and fails alone; one broken source never
  blocks the others.
- **Nothing lost.** Raw page snapshots are kept in `data/snapshots/<source>/` so
  failed parses can be reprocessed later. The ledger is append-only.

## Entry schema

```json
{
  "id": "uk-mtd-q1-2026",
  "jurisdiction": "UK|FR|DE|PL|BE|RO|EU",
  "domain": "tax-filing|e-invoicing|vat|company-register|employer|landlord|ai-act",
  "type": "deadline|rule-change|recurring-rule",
  "title": "Plain-English title",
  "summary": "1-2 sentences, UK spelling.",
  "who": "Who is affected, incl. thresholds",
  "date": "YYYY-MM-DD or null (recurring rules)",
  "recurrence": "quarterly|annual|monthly|null",
  "status": "confirmed|announced|proposed|unverified",
  "sources": ["https://official.gov/..."],
  "verified": "YYYY-MM-DD",
  "notes": "",
  "supersedes": "id-of-corrected-entry (optional)"
}
```

## Running the pipeline (all stdlib Python — no installs, by design)

```bash
python3 scripts/validate.py          # schema + sanity check of the ledger
python3 scripts/watch.py             # check all sources, snapshot changes, update status
python3 scripts/build_site.py        # regenerate site/ from the ledger
python3 scripts/digest.py            # print this week's digest (markdown)
```

Order of a publishing cycle: watch → review queue → append verified entries to
ledger → validate → build_site. The site is only rebuilt after validation passes.

Deployment target: GitHub repository (public spec + data) + GitHub Pages for the
site + GitHub Actions cron for the watchers. Until those accounts exist, everything
runs locally and the generated `site/` can be previewed in a browser.

*The Compliance Clock reports what official sources say, with links and dates.
It is an information service, not legal or tax advice.*
