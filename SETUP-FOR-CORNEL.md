# Your setup steps — The Compliance Clock

Everything technical is built and runs by itself. These are the only steps that
must be done by you, because they involve creating accounts and paying — things
I will never do on your behalf. Total time: ~25 minutes. Total cost: ~£10–15/year.

## Step 1 — Use your existing GitHub account (~4 min) — DONE? tick here ☐

You already have a GitHub account, which is all we need (a new project = a new
"repository" inside it; no separate account required).

1. **Authorise your Mac:** go to **github.com/settings/keys** → **New SSH key** →
   title `Cornel Mac — Compliance Clock` → paste the key line Claude gave you
   (it's also saved at `~/.ssh/id_ed25519.pub` on this Mac) → **Add SSH key**.
   This is the public half of a key that lives on your Mac — no passwords are
   shared, ever.
2. **Create the repository:** github.com → **+** → **New repository** → name
   `compliance-clock` → **Public** → leave all boxes unticked → **Create**.
3. **Tell Claude your GitHub username.** Claude pushes the project, switches on
   free hosting (GitHub Pages) and the daily automatic runs, and gives you the
   live address.

## Step 2 — Connect your domain compliancecheck.uk (~10 min) — bought 04/08/2026 ✓

Two halves: DNS records at your registrar, and one setting on GitHub.

**A. At your domain registrar** (wherever you bought compliancecheck.uk), find
"DNS settings" / "Manage DNS" and add these records:

| Type  | Name/Host        | Value                  |
|-------|------------------|------------------------|
| A     | @ (or blank)     | 185.199.108.153        |
| A     | @ (or blank)     | 185.199.109.153        |
| A     | @ (or blank)     | 185.199.110.153        |
| A     | @ (or blank)     | 185.199.111.153        |
| CNAME | www              | corpl.github.io        |

Delete any pre-existing "parking" A/CNAME records the registrar added.

**B. On GitHub:** github.com/CorPl/compliance-clock/settings/pages →
"Custom domain" → type `compliancecheck.uk` → **Save**. When the DNS check
passes (minutes to a few hours), tick **Enforce HTTPS**.

## Step 2b — Make a2a@compliancecheck.uk receive email (free, ~5 min)

Registrars don't include a mailbox — use free **email forwarding** so mail to
a2a@compliancecheck.uk lands in your normal inbox:

- **Cloudflare:** Email → Email Routing → create address `a2a` → forward to
  your real email → follow the prompts (it adds the MX records itself).
- **Namecheap:** Domain → Redirect Email → add `a2a` → your real email.
- Other registrars: look for "Email forwarding" — same idea everywhere.

To also SEND from that address later, your mail provider needs it added as a
send-as alias — ask me when you want that and I'll give exact steps for your
setup.

## Step 3 — Weekly digest email (free, later, ~10 min)

Wait until the site is public and has content. Then create a free account at
**Buttondown** (buttondown.com) or **Substack** — I'll draft every issue; you
paste and press send (or we automate it — my recommendation once you've seen
a couple of issues go out).

## What you should NOT do

- Don't pay for anything beyond the domain. Hosting, automation, and the feed
  are free at this scale.
- Don't buy "SEO packages", logo gigs, or marketing services — not needed at
  this stage, and mostly a waste at any stage.
- Never share passwords with anyone — including me. I will never ask for them;
  I'll always hand you click-by-click steps instead.

## What happens automatically once GitHub is set up

- Watchers check all official sources **daily** and record freshness publicly.
- Any detected change waits for my verification before it can be published —
  failures delay updates but can never corrupt the feed.
- The site and machine feed rebuild only after the data passes validation.
- You get a short weekly summary from me: what changed, what was published,
  what (if anything) needs a decision from you.
