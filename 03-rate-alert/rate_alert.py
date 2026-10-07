"""Watch exchange rates and send a Slack message when a rule is met.

Rates come from the free Frankfurter API (no key needed). Alerts go to a Slack
incoming webhook. Run it on a schedule (cron / Task Scheduler) to get alerts
without checking rates by hand.

Usage:
    python rate_alert.py --dry-run          # print what would be sent, change nothing
    python rate_alert.py                    # send alerts, remember what was sent

The webhook URL is read from the SLACK_WEBHOOK_URL environment variable so it
never has to be written into a file.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

DEFAULT_API = "https://api.frankfurter.app/latest"


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        sys.exit(f"File not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch_rates(api_url, base, symbols):
    resp = requests.get(api_url, params={"from": base, "to": ",".join(symbols)}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    missing = [s for s in symbols if s not in data.get("rates", {})]
    if missing:
        raise ValueError(f"API returned no rate for: {', '.join(missing)}")
    return data["date"], data["rates"]


def zone_for(rate, rule):
    if rule.get("above") is not None and rate >= rule["above"]:
        return "above"
    if rule.get("below") is not None and rate <= rule["below"]:
        return "below"
    return "normal"


def evaluate(base, rule, rate, previous):
    """Return (alert messages, new state) for one currency pair.

    previous is the saved state for this pair, or None on the first run.
    A threshold alert fires only when the rate crosses into a new zone, so the
    same alert is not repeated on every run. A change alert compares against
    the rate at the last alert.
    """
    symbol = rule["symbol"]
    pair = f"{base}/{symbol}"
    zone = zone_for(rate, rule)

    if previous is None:
        # First run: record a baseline. Alert only if already past a threshold.
        messages = []
        if zone != "normal":
            messages.append(f"{pair} is {rate:g}, {zone} your limit of {rule[zone]:g}")
        return messages, {"zone": zone, "reference_rate": rate}

    messages = []
    reference = previous["reference_rate"]
    if zone != previous["zone"]:
        if zone == "normal":
            messages.append(f"{pair} is back in range at {rate:g}")
        else:
            messages.append(f"{pair} is {rate:g}, {zone} your limit of {rule[zone]:g}")

    change_pct = rule.get("change_pct")
    if change_pct:
        moved = (rate - reference) / reference * 100
        if abs(moved) >= change_pct:
            direction = "up" if moved > 0 else "down"
            messages.append(f"{pair} moved {direction} {abs(moved):.2f}% ({reference:g} -> {rate:g})")

    if messages:
        reference = rate
    return messages, {"zone": zone, "reference_rate": reference}


def send_slack(webhook_url, text):
    resp = requests.post(webhook_url, json={"text": text}, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"Slack returned {resp.status_code}: {resp.text[:200]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="config.json", help="path to the rules file")
    parser.add_argument("--state", default="state.json", help="where to remember the last alert")
    parser.add_argument("--dry-run", action="store_true", help="print alerts instead of sending; do not save state")
    args = parser.parse_args()

    config = load_json(args.config)
    state = load_json(args.state, default={})
    base = config["base"]
    rules = config["pairs"]

    rate_date, rates = fetch_rates(config.get("api_url", DEFAULT_API), base, [r["symbol"] for r in rules])

    messages = []
    new_state = {}
    for rule in rules:
        symbol = rule["symbol"]
        rate = rates[symbol]
        print(f"{base}/{symbol}: {rate:g}")
        found, new_state[symbol] = evaluate(base, rule, rate, state.get(symbol))
        messages.extend(found)

    if not messages:
        print("no alerts")
    else:
        text = f"Exchange rate alert ({rate_date})\n" + "\n".join(f"- {m}" for m in messages)
        if args.dry_run:
            print("--- would send to Slack ---")
            print(text)
        else:
            webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
            if not webhook_url:
                sys.exit("Set the SLACK_WEBHOOK_URL environment variable, or use --dry-run.")
            send_slack(webhook_url, text)
            print(f"sent {len(messages)} alert(s) to Slack")

    if not args.dry_run:
        # Saved only after a successful send, so a failed alert is retried next run.
        with open(args.state, "w", encoding="utf-8") as f:
            json.dump(new_state, f, indent=2)


if __name__ == "__main__":
    main()
