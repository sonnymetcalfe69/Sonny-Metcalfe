#!/usr/bin/env python3
"""CLI for the side business agent ecosystem.

    python cli.py run [--business ID]
    python cli.py list-outbox
    python cli.py approve ITEM_ID
    python cli.py reject ITEM_ID
    python cli.py record-ledger BUSINESS_ID {revenue|expense} AMOUNT "description"
"""

from __future__ import annotations

import argparse
import sys

from src.config import load_businesses, load_settings
from src.llm import DEFAULT_MODEL
from src.orchestrator import run_all
from src.tools import ledger, outbox


def cmd_run(args: argparse.Namespace) -> None:
    settings = load_settings()
    businesses = load_businesses()
    if args.business:
        businesses = [b for b in businesses if b["id"] == args.business]
        if not businesses:
            sys.exit(f"No business with id '{args.business}' in config/businesses.yaml")

    model = settings.get("model", DEFAULT_MODEL)
    report_path = run_all(businesses, model)
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
