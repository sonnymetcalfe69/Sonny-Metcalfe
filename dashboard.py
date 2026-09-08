#!/usr/bin/env python3
"""Local web dashboard for the side business agent ecosystem.

    python dashboard.py

Opens on http://127.0.0.1:5050 — a "station" view of your businesses
(rooms), pending approvals (outbox), and past daily reports. Reads only
the same on-disk files cli.py writes (state/, outbox/, reports/,
config/); it doesn't call the LLM or any external service itself.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from flask import Flask, redirect, render_template, url_for

from src.webapp import data as dashboard_data
from src.tools import outbox

CONFIG_DIR = Path(__file__).resolve().parent / "config"

app = Flask(__name__)


def _load_businesses() -> list[dict] | None:
    path = CONFIG_DIR / "businesses.yaml"
    if not path.exists():
        return None
    return (yaml.safe_load(path.read_text()) or {}).get("businesses", [])


def _find_business(businesses: list[dict], business_id: str) -> dict | None:
    return next((b for b in businesses if b["id"] == business_id), None)


@app.route("/")
def station():
    businesses = _load_businesses()
    if businesses is None:
        return render_template("setup.html")
    rooms = dashboard_data.station_overview(businesses)
    return render_template("station.html", rooms=rooms, active="station")


@app.route("/business/<business_id>")
def business_detail(business_id: str):
    businesses = _load_businesses() or []
    business = _find_business(businesses, business_id)
    if business is None:
        return render_template("setup.html"), 404
    detail = dashboard_data.business_detail(business)
    return render_template("business.html", detail=detail, active="station")


@app.route("/outbox")
def outbox_view():
    businesses = _load_businesses() or []
    items = dashboard_data.all_pending_by_business(businesses)
    return render_template("outbox.html", items=items, active="outbox")


@app.route("/outbox/<item_id>/approve", methods=["POST"])
def outbox_approve(item_id: str):
    outbox.approve(item_id)
    return redirect(url_for("outbox_view"))


@app.route("/outbox/<item_id>/reject", methods=["POST"])
def outbox_reject(item_id: str):
    outbox.reject(item_id)
    return redirect(url_for("outbox_view"))


@app.route("/reports")
def reports_view():
    return render_template("reports.html", filenames=dashboard_data.list_reports(), active="reports")


@app.route("/reports/<filename>")
def report_detail(filename: str):
    content = dashboard_data.read_report(filename)
    if content is None:
        return render_template("setup.html"), 404
    return render_template("report_detail.html", filename=filename, content=content, active="reports")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
