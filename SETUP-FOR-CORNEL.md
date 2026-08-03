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

## Step 2 — Buy the domain (~£10–15/year, ~10 min)

The website works free on GitHub's address (yourname.github.io/compliance-clock),
so the domain can wait until you're happy. When ready:

1. Use a UK-friendly registrar: **Cloudflare Registrar** (at-cost pricing) or
   **Namecheap**. Avoid add-ons — you need nothing except the domain itself.
2. Name ideas (check availability): `complianceclock.eu`, `complianceclock.co.uk`,
   `theclock.tax`. My preference: **.eu** — it says exactly what the product
   covers and travels well across the UK+EU audience.
3. Buy it in your own account with your own card. Then tell me — I'll give you
   the two DNS values to copy-paste so it points at the site.

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
