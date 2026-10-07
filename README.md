# Automation samples

Four small projects that show the kind of work I do: collecting data, cleaning it up, connecting services so routine checks run on their own, and localizing software into Japanese with automated quality checks.

These are personal sample projects, built to demonstrate my approach. Each one runs as-is and includes real output you can open.

| Sample | What it does | Output |
|---|---|---|
| [01-web-scraper](01-web-scraper/) | Collects 1,000 product listings from a public practice site | CSV and Excel |
| [02-sales-report](02-sales-report/) | Cleans a messy sales export and builds a summary report | Clean CSV and a 5-sheet Excel report with a chart |
| [03-rate-alert](03-rate-alert/) | Watches exchange rates and posts to Slack when a rule is met | Slack message |
| [04-en-ja-localization](04-en-ja-localization/) | Localizes an app's interface, landing page, and email into Japanese, and checks the result automatically | Japanese files, glossary, style notes, QA report |

## Setup

Python 3.10 or newer.

```
pip install -r requirements.txt
```

Each folder has its own README with the commands to run. Sample 04 needs no extra packages.

## How these were built

I use AI-assisted development and test every tool before publishing it. The sample output in each folder comes from an actual run.
