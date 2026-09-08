# Side Business Agent Ecosystem

A multi-agent automation system that helps you run one or more small side
businesses: it researches, plans, drafts content/outreach, tracks a simple
P&L, and flags what needs your attention. It does **not** autonomously make
or move money — no system honestly can promise that. What it *can* do is
take the repetitive research/drafting/tracking work off your plate and hand
you a short daily digest with things ready for a one-click approval.

## How it's structured

It's a hierarchy, not a flat list of scripts:

```
                    Manager (Overview / HQ)
                            |
        +-------------------+-------------------+
    Business A          Business B          Business C
  Strategist            Strategist            Strategist
  Researcher            Researcher            Researcher
  Marketer              Marketer              Marketer
  Ops                   Ops                   Ops
  (+ any agents you "hire" — see below)
```

Four agents run once per business per cycle, then a fifth — Finance —
closes it out. All but Finance call Claude; Finance is deliberately plain
arithmetic, not an LLM guess, because budget math should be exact:

- **Strategist** — looks at the business's goals, budget, recent history,
  and any queued idea (see "Ideas" below), and decides today's 1-3
  priorities.
- **Researcher** — gathers market/competitor/opportunity notes relevant to
  those priorities (via a pluggable search tool — stubbed by default, see
  below).
- **Marketer** — drafts the actual content: posts, outreach emails,
  listing copy, video scripts — the exact shape depends on the business's
  `business_type` (see below).
- **Ops** — proposes concrete operational actions (price change, restock,
  reply to a customer message, update a listing).
- **Finance** — updates the ledger from anything you've recorded, computes
  rough revenue/spend/runway against the budget cap, and flags overspend
  risk.

Above all of that sits the **Manager** (`src/agents/manager.py`) — it runs
once per `python cli.py run`, after every business's cycle, looks at the
whole portfolio at once (every business's priorities, finance status,
watch items, pending approvals), and decides which single business most
deserves your attention today. It doesn't re-decide any business's own
priorities — that's each strategist's job — it only triages across
businesses. Portfolio-wide budget math is deterministic too (summed from
each business's ledger, checked against `global_monthly_budget_cap` in
`config/settings.yaml`); the manager only writes the narrative around it.

The **Orchestrator** (`src/orchestrator.py`) runs all of this in sequence
and writes a daily Markdown report to `reports/`, with the manager's
overview as the top section.

### Hiring more agents

A business's hierarchy isn't fixed at Strategist/Researcher/Marketer/Ops —
you can hire a specialist into it:

```bash
python cli.py hire my-etsy-shop seo_researcher "Etsy search-tag and title keyword research"
```

This adds an entry to that business's `extra_agents` in
`config/businesses.yaml`. Next cycle, that role runs
(`src/agents/specialist.py`) scoped tightly to the focus you gave it, gets
its own station in the dashboard room, and its outputs land in the outbox
like anyone else's. You can also hand-edit `extra_agents` directly:

```yaml
    extra_agents:
      - role: seo_researcher
        focus: "Etsy search-tag and title keyword research, not general marketing copy"
```

### Ideas: the "just give it an idea" workflow

For idea-driven businesses (see business types below), you don't have to
wait for the strategist to invent something — drop a raw idea in and it
becomes next cycle's top priority, fully expanded into a draft:

```bash
python cli.py add-idea my-shorts-channel "why mechanical keyboards click differently"
python cli.py list-ideas my-shorts-channel
```

You can also queue ideas from the dashboard's business page. An idea moves
pending → in_progress → done as a cycle picks it up and expands it; it
still lands in the outbox as a draft for your approval like everything
else — "automated" means the drafting is automated, not the publishing.

### Business types

Set `business_type` on a business in config to change what shape the
marketer's drafts take:

- `faceless_youtube` — a full short-form script: hook, numbered beats, CTA,
  3 title options, hashtags, and a thumbnail text overlay idea.
- `digital_products` — a full storefront listing: concept, SEO title,
  description, search tags, and a suggested price.
- anything else (or omitted) — generic content/copy, the original
  behavior.

See `config/businesses.example.yaml` for a working example of each.

## Safety model: draft-only by default

Nothing this system produces is sent, posted, listed, or paid for
automatically. Every output that would touch the outside world (an email,
a social post, a marketplace listing, a purchase) is written as a pending
item to `outbox/` for you to read and explicitly approve
(`python cli.py approve <id>`) or reject (`python cli.py reject <id>`).
Approving currently just moves the item to `outbox/approved/` — it does
**not** call any real email/posting/payment API. Wiring a real integration
(SendGrid, a Shopify API, a payment processor, etc.) is a deliberate,
separate step you take in `src/tools/` once you decide you trust the
output and want to automate that specific channel. Start there deliberately,
one channel at a time, not by flipping a global "autonomous" switch.

There is no code anywhere in this repo that can spend money, send an email,
or post to a real account. Treat that as something you add later, with your
own credentials and your own risk tolerance — not something this scaffold
should decide for you.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
cp config/settings.example.yaml config/settings.yaml
cp config/businesses.example.yaml config/businesses.yaml
# edit config/businesses.yaml to describe your actual business(es)
```

## Running it

```bash
python cli.py run                 # runs one cycle for every business in config/businesses.yaml
python cli.py run --business my-etsy-shop   # run just one
python cli.py list-outbox         # see items waiting on your approval
python cli.py approve <item_id>
python cli.py reject <item_id>
python cli.py add-idea <business_id> "raw idea text"
python cli.py list-ideas <business_id>
python cli.py hire <business_id> <role> "what this agent should focus on"
```

Run `python cli.py run` on a schedule (cron, a CI scheduled workflow, or a
Claude Code Routine) to get a daily digest in `reports/`.

## Dashboard

```bash
python dashboard.py
```

Opens a local web UI at `http://127.0.0.1:5050` — an HQ panel at the top
with the manager agent's daily briefing and portfolio-wide budget status,
then one room per configured business below it (priorities, watch items,
budget bar). Each room shows a tiny pixel-art worker standing at a console
for every agent on that business — Strategist, Researcher, Marketer, Ops,
plus any you've hired — lit up and bobbing if that agent produced
something last cycle, dim if it sat idle, so the row doubles as an
at-a-glance activity readout. There's also an Outbox page to
approve/reject pending drafts and proposals from the browser instead of
the CLI, and a Reports page to browse past daily digests. It's a thin
read/write layer over the same `state/`, `outbox/`, and `reports/` files
the CLI uses — it doesn't call the LLM itself, and approving an item there
does exactly what `cli.py approve` does (moves it to `outbox/approved/`,
sends nothing).

The visual style is a deliberate homage to StarNet
(github.com/androoAGI/starnet) — a separate, much larger open-source
"AI agent station" desktop app — but this dashboard is its own small Flask
app with no code or runtime dependency on that project.

## Configuring a business

Edit `config/businesses.yaml`. Each entry is intentionally generic — it
doesn't assume e-commerce vs. content vs. freelance, so describe whatever
you're actually running:

```yaml
businesses:
  - id: my-etsy-shop
    name: "Handmade candle shop"
    business_type: generic   # or faceless_youtube / digital_products — see below
    description: >
      Etsy shop selling soy candles. Currently 3 SKUs, ~$400/mo revenue.
      Goal: grow to $1500/mo without spending more than $150/mo on ads.
    monthly_budget_cap: 150
    goals:
      - "Increase repeat purchase rate"
      - "Test one new scent SKU"
    channels: ["etsy", "instagram"]
    extra_agents: []   # see "Hiring more agents" below
```

## Extending it

- **Real research**: replace the stub in `src/tools/web_research.py` with
  a real search API (or hand the agent the `WebSearch` tool if you run this
  inside Claude Code instead of standalone).
- **Real sending**: add a function in `src/tools/` per channel (email,
  Instagram, Etsy listing update) that only runs on items you've moved to
  `outbox/approved/`.
- **Real bookkeeping**: `src/tools/ledger.py` is a flat JSON ledger per
  business; swap it for a real accounting API if you want it to reconcile
  against a bank feed.

## Honest limitations

- This does not guarantee profit, or any revenue at all — it automates the
  grunt work around running a business, it doesn't invent demand.
- It has no access to your bank, payment processor, or any live store data
  unless you explicitly wire that in.
- LLM output (research notes, drafts, proposed prices) can be wrong. Read
  before approving.
