# Exchange rate alert to Slack

Checks exchange rates on a schedule and posts to a Slack channel when a rule you set is met. It connects two services through their APIs so nobody has to check rates by hand.

## Example alert

```
Exchange rate alert (2026-10-08)
- USD/JPY is 161, above your limit of 160
- USD/JPY moved up 3.87% (155 -> 161)
```

## Rules

Copy `config.example.json` to `config.json` and edit it.

```json
{
  "base": "USD",
  "pairs": [
    { "symbol": "JPY", "above": 160, "below": 150, "change_pct": 1.0 },
    { "symbol": "EUR", "change_pct": 1.0 }
  ]
}
```

| Setting | Alert when |
|---|---|
| `above` | The rate rises to this value or higher |
| `below` | The rate falls to this value or lower |
| `change_pct` | The rate has moved this many percent since the last alert |

Each setting is optional.

## Run it

```
python rate_alert.py --dry-run     # show what would be sent, change nothing
python rate_alert.py               # send alerts
```

Set the Slack incoming webhook URL in the `SLACK_WEBHOOK_URL` environment variable. It is never stored in a file.

To run it every hour, add it to cron (Linux / macOS) or Task Scheduler (Windows).

## How it behaves

- No repeated alerts. A limit alert is sent when the rate crosses the limit, not on every run while it stays there.
- Tells you when the rate comes back into range.
- If Slack cannot be reached, the run fails and the alert is sent again on the next run instead of being lost.
- `--dry-run` lets you test your rules without sending anything.

Rates come from the free [Frankfurter API](https://www.frankfurter.app/), which needs no API key.

## How it was tested

Against a local stand-in for the rates API and the Slack webhook, covering: first run, crossing above and below a limit, staying past a limit, returning to range, a failed Slack request, and a missing webhook setting. It has also been run against the live rates API in dry-run mode.

## Adapting it

The same structure works for other "check a value, notify when it changes" jobs: stock levels, prices, new records in a database or spreadsheet, with email or another chat tool in place of Slack.
