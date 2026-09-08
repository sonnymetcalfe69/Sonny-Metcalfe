#!/usr/bin/env python3
"""CLI for the side business agent ecosystem.

    python cli.py run [--business ID]
    python cli.py list-outbox
    python cli.py approve ITEM_ID
    python cli.py reject ITEM_ID
    python cli.py record-ledger BUSINESS_ID {revenue|expense} AMOUNT "description"
    python cli.py add-idea BUSINESS_ID "idea text"
    python cli.py list-ideas BUSINESS_ID
    python cli.py hire BUSINESS_ID ROLE "focus description"
"""

from __future__ import annotations

import argparse
import sys

import yaml

from src.config import CONFIG_DIR, load_businesses, load_settings
from src.llm import DEFAULT_MODEL
from src.orchestrator import run_all
from src.tools import ideas, ledger, outbox


def cmd_run(args: argparse.Namespace) -> None:
    settings = load_settings()
    businesses = load_businesses()
    if args.business:
        businesses = [b for b in businesses if b["id"] == args.business]
        if not businesses:
            sys.exit(f"No business with id '{args.business}' in config/businesses.yaml")

    model = settings.get("model", DEFAULT_MODEL)
    global_cap = settings.get("global_monthly_budget_cap", 0)
    report_path = run_all(businesses, model, global_budget_cap=global_cap)
    print(f"Cycle complete. Report written to {report_path}")
    print("Run `python cli.py list-outbox` to see items awaiting your approval.")


def cmd_list_outbox(args: argparse.Namespace) -> None:
    items = outbox.list_pending()
    if not items:
        print("Nothing pending.")
        return
    for item in items:
        print(f"[{item['id']}] {item['business_id']} / {item['channel']} / {item['action_type']}")
        payload = item["payload"]
        preview = payload.get("body") or payload.get("description") or ""
        print(f"    {preview[:120]}{'...' if len(preview) > 120 else ''}")


def cmd_approve(args: argparse.Namespace) -> None:
    if outbox.approve(args.item_id):
        print(f"Approved {args.item_id} -> outbox/approved/. Nothing was sent automatically.")
    else:
        sys.exit(f"No pending item with id {args.item_id}")


def cmd_reject(args: argparse.Namespace) -> None:
    if outbox.reject(args.item_id):
        print(f"Rejected {args.item_id} -> outbox/rejected/.")
    else:
        sys.exit(f"No pending item with id {args.item_id}")


def cmd_record_ledger(args: argparse.Namespace) -> None:
    entry = ledger.add_entry(args.business_id, args.kind, args.amount, args.description)
    print(f"Recorded {entry['kind']} of ${entry['amount']:.2f} for {args.business_id} ({entry['id']})")


def cmd_add_idea(args: argparse.Namespace) -> None:
    idea = ideas.add_idea(args.business_id, args.text)
    print(f"Added idea {idea['id']} for {args.business_id}. It'll be expanded next cycle: `python cli.py run --business {args.business_id}`")


def cmd_list_ideas(args: argparse.Namespace) -> None:
    items = ideas.list_ideas(args.business_id)
    if not items:
        print("No ideas queued.")
        return
    for idea in items:
        print(f"[{idea['id']}] ({idea['status']}) {idea['text']}")


def cmd_hire(args: argparse.Namespace) -> None:
    path = CONFIG_DIR / "businesses.yaml"
    if not path.exists():
        sys.exit(f"Missing {path}. Copy config/businesses.example.yaml to config/businesses.yaml first.")
    raw = yaml.safe_load(path.read_text()) or {}
    business = next((b for b in raw.get("businesses", []) if b["id"] == args.business_id), None)
    if business is None:
        sys.exit(f"No business with id '{args.business_id}' in config/businesses.yaml")

    business.setdefault("extra_agents", []).append({"role": args.role, "focus": args.focus})
    path.write_text(yaml.safe_dump(raw, sort_keys=False, default_flow_style=False))
    print(
        f"Hired '{args.role}' for {args.business_id} (focus: {args.focus}). "
        "They'll show up at their own station starting next cycle."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run one cycle for all (or one) business")
    p_run.add_argument("--business", help="Only run this business id")
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list-outbox", help="List items pending approval")
    p_list.set_defaults(func=cmd_list_outbox)

    p_approve = sub.add_parser("approve", help="Approve a pending outbox item")
    p_approve.add_argument("item_id")
    p_approve.set_defaults(func=cmd_approve)

    p_reject = sub.add_parser("reject", help="Reject a pending outbox item")
    p_reject.add_argument("item_id")
    p_reject.set_defaults(func=cmd_reject)

    p_ledger = sub.add_parser("record-ledger", help="Manually record a real revenue/expense entry")
    p_ledger.add_argument("business_id")
    p_ledger.add_argument("kind", choices=["revenue", "expense"])
    p_ledger.add_argument("amount", type=float)
    p_ledger.add_argument("description")
    p_ledger.set_defaults(func=cmd_record_ledger)

    p_add_idea = sub.add_parser("add-idea", help="Queue a raw idea for a business to expand next cycle")
    p_add_idea.add_argument("business_id")
    p_add_idea.add_argument("text")
    p_add_idea.set_defaults(func=cmd_add_idea)

    p_list_ideas = sub.add_parser("list-ideas", help="List queued ideas for a business")
    p_list_ideas.add_argument("business_id")
    p_list_ideas.set_defaults(func=cmd_list_ideas)

    p_hire = sub.add_parser("hire", help="Add a new specialist agent role to a business's hierarchy")
    p_hire.add_argument("business_id")
    p_hire.add_argument("role", help="e.g. seo_specialist, video_editor, customer_support")
    p_hire.add_argument("focus", help="What this agent should specifically focus on")
    p_hire.set_defaults(func=cmd_hire)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
