# Side Business Agent Ecosystem

A multi-agent automation system that helps you run one or more small side
businesses: it researches, plans, drafts content/outreach, tracks a simple
P&L, and flags what needs your attention. It does **not** autonomously make
or move money — no system honestly can promise that. What it *can* do is
take the repetitive research/drafting/tracking work off your plate and hand
you a short daily digest with things ready for a one-click approval.

## How it's structured

Five agents run once per business per cycle. Four call Claude; Finance is
deliberately plain arithmetic, not an LLM guess, because budget math should
be exact:

- **Strategist** — looks at the business's goals, budget, and recent
  metrics, and decides today's 1-3 priorities.
- **Researcher** — gathers market/competitor/opportunity notes relevant to
  those priorities (via a pluggable search tool — stubbed by default, see
  below).
- **Marketer** — drafts the actual content: posts, outreach emails,
  listing copy, proposal text.
- **Ops** — proposes concrete operational actions (price change, restock,
  reply to a customer message, update a listing).
- **Finance** — updates the ledger from anything you've recorded, computes
  rough revenue/spend/runway against the budget cap, and flags overspend
  risk.

The **Orchestrator** (`src/orchestrator.py`) runs these in sequence per
business and writes a daily Markdown report to `reports/`.

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
```

Run `python cli.py run` on a schedule (cron, a CI scheduled workflow, or a
Claude Code Routine) to get a daily digest in `reports/`.

## Configuring a business

Edit `config/businesses.yaml`. Each entry is intentionally generic — it
doesn't assume e-commerce vs. content vs. freelance, so describe whatever
you're actually running:

```yaml
businesses:
  - id: my-etsy-shop
    name: "Handmade candle shop"
    description: >
      Etsy shop selling soy candles. Currently 3 SKUs, ~$400/mo revenue.
      Goal: grow to $1500/mo without spending more than $150/mo on ads.
    monthly_budget_cap: 150
    goals:
      - "Increase repeat purchase rate"
      - "Test one new scent SKU"
    channels: ["etsy", "instagram"]
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
