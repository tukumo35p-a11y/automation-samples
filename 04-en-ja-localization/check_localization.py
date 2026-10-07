"""Check a Japanese localization against its English source.

Catches the mistakes that break a product or slip past a read-through:
missing keys, broken {placeholders}, untranslated strings, dropped numbers
and links, glossary inconsistencies, and punctuation style.

Usage:
    python check_localization.py --source source/en --target ja
    python check_localization.py --source source/en --target examples/draft --only ui.json --html review.html

Exit code is 1 when any error is found, so it can run in CI.
"""

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{[^{}]*\}")
JAPANESE = re.compile(r"[぀-ヿ一-鿿]")
LATIN = re.compile(r"[A-Za-z]")
NUMBER = re.compile(r"\d+(?:\.\d+)?")
LINK_TARGET = re.compile(r"\]\(([^)]+)\)")
# half-width ? or ! directly after Japanese text; Japanese copy uses full-width marks
HALF_WIDTH_MARK = re.compile(r"(?<=[぀-ヿ一-鿿])[?!]")
HALF_WIDTH_KANA = re.compile(r"[ｦ-ﾟ]")

ERROR, WARNING = "ERROR", "WARNING"


def load_glossary(path):
    """Return [(compiled source pattern, source term, required Japanese term)]."""
    terms = []
    if not path or not Path(path).exists():
        return terms
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            en, ja = row["en"].strip(), row["ja"].strip()
            # terms written with a capital (plan names) match case-sensitively
            flags = 0 if any(c.isupper() for c in en) else re.IGNORECASE
            pattern = re.compile(rf"(?<![A-Za-z]){re.escape(en)}(?:s|es)?(?![A-Za-z])", flags)
            terms.append((pattern, en, ja))
    return terms


def placeholders(text):
    return sorted(PLACEHOLDER.findall(text))


def check_style(target):
    problems = []
    if HALF_WIDTH_MARK.search(target):
        problems.append("half-width ? or ! after Japanese text; use the full-width mark")
    if HALF_WIDTH_KANA.search(target):
        problems.append("half-width katakana")
    return problems


def check_glossary(source, target, glossary):
    plain = PLACEHOLDER.sub("", source)
    return [
        f'glossary: "{en}" should be "{ja}"'
        for pattern, en, ja in glossary
        if pattern.search(plain) and ja not in target
    ]


def check_ui(source, target, glossary):
    """Compare two flat JSON string tables. Returns [(level, key, message)]."""
    issues = []
    for key in source:
        if key not in target:
            issues.append((ERROR, key, "missing in translation"))
    for key in target:
        if key not in source:
            issues.append((ERROR, key, "not in source (extra or misspelled key)"))

    for key, src in source.items():
        if key not in target:
            continue
        tgt = target[key]
        if not tgt.strip():
            issues.append((ERROR, key, "empty translation"))
            continue
        if placeholders(src) != placeholders(tgt):
            issues.append(
                (ERROR, key, f"placeholders differ: source {' '.join(placeholders(src)) or '(none)'}, "
                             f"translation {' '.join(placeholders(tgt)) or '(none)'}")
            )
        if LATIN.search(src) and not JAPANESE.search(tgt):
            issues.append((WARNING, key, "looks untranslated (no Japanese text)"))
            continue
        if src.rstrip().endswith(".") != tgt.rstrip().endswith("。"):
            issues.append((WARNING, key, "sentence-ending period does not match the source"))
        for message in check_style(tgt) + check_glossary(src, tgt, glossary):
            issues.append((WARNING, key, message))
    return issues


def check_doc(source, target, glossary):
    """Compare two Markdown documents. Returns [(level, location, message)]."""
    issues = []
    if not JAPANESE.search(target):
        return [(ERROR, "document", "no Japanese text found")]

    if placeholders(source) != placeholders(target):
        missing = set(placeholders(source)) - set(placeholders(target))
        extra = set(placeholders(target)) - set(placeholders(source))
        detail = "; ".join(
            part for part in (
                f"missing {' '.join(sorted(missing))}" if missing else "",
                f"unexpected {' '.join(sorted(extra))}" if extra else "",
                "count differs" if not missing and not extra else "",
            ) if part
        )
        issues.append((ERROR, "placeholders", detail))

    for label, prefix in (("headings", "#"), ("list items", "- ")):
        src_count = sum(line.startswith(prefix) for line in source.splitlines())
        tgt_count = sum(line.startswith(prefix) for line in target.splitlines())
        if src_count != tgt_count:
            issues.append((ERROR, label, f"source has {src_count}, translation has {tgt_count}"))

    if sorted(LINK_TARGET.findall(source)) != sorted(LINK_TARGET.findall(target)):
        issues.append((ERROR, "links", "link targets differ from the source"))

    dropped = sorted(set(NUMBER.findall(source)) - set(NUMBER.findall(target)), key=float)
    if dropped:
        issues.append((WARNING, "numbers", f"in source but not in translation: {', '.join(dropped)}"))

    for message in check_style(target) + check_glossary(source, target, glossary):
        issues.append((WARNING, "document", message))
    return issues


def run(source_dir, target_dir, glossary, only=None):
    """Check every source file. Returns {file name: (issues, source data, target data)}."""
    results = {}
    for src_path in sorted(Path(source_dir).iterdir()):
        tgt_path = Path(target_dir) / src_path.name
        if src_path.suffix not in (".json", ".md") or (only and src_path.name not in only):
            continue
        if not tgt_path.exists():
            results[src_path.name] = ([(ERROR, "file", "translation file is missing")], None, None)
            continue
        src_text = src_path.read_text(encoding="utf-8")
        tgt_text = tgt_path.read_text(encoding="utf-8")
        if src_path.suffix == ".json":
            src, tgt = json.loads(src_text), json.loads(tgt_text)
            results[src_path.name] = (check_ui(src, tgt, glossary), src, tgt)
        else:
            results[src_path.name] = (check_doc(src_text, tgt_text, glossary), src_text, tgt_text)
    return results


def print_report(results):
    errors = warnings = 0
    for name, (issues, _, _) in results.items():
        print(name)
        if not issues:
            print("  OK")
        for level, where, message in issues:
            print(f"  {level:<8}{where:<24}{message}")
            errors += level == ERROR
            warnings += level == WARNING
    print(f"\n{errors} error(s), {warnings} warning(s) in {len(results)} file(s)")
    return errors


def write_html(results, path):
    """Side-by-side review page: source, translation, and any issues per string."""
    rows = []
    for name, (issues, src, tgt) in results.items():
        if src is None:
            continue
        rows.append(f'<tr class="file"><td colspan="2">{html.escape(name)}</td></tr>')
        if isinstance(src, dict):
            by_key = {}
            for level, key, message in issues:
                by_key.setdefault(key, []).append((level, message))
            for key in list(src) + [k for k in tgt if k not in src]:
                notes = "".join(
                    f'<div class="{level.lower()}">{level}: {html.escape(message)}</div>'
                    for level, message in by_key.get(key, [])
                )
                rows.append(
                    f'<tr><td><span class="key">{html.escape(key)}</span>{html.escape(src.get(key, ""))}</td>'
                    f'<td lang="ja">{html.escape(tgt.get(key, ""))}{notes}</td></tr>'
                )
        else:
            notes = "".join(
                f'<div class="{level.lower()}">{level}: {html.escape(where)}: {html.escape(message)}</div>'
                for level, where, message in issues
            )
            rows.append(
                f'<tr><td class="doc">{html.escape(src)}</td>'
                f'<td class="doc" lang="ja">{html.escape(tgt)}{notes}</td></tr>'
            )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Localization review</title>
<style>
body {{ font-family: "Segoe UI", "Yu Gothic UI", "Meiryo", sans-serif; margin: 24px; color: #1f2933; }}
h1 {{ font-size: 20px; }}
table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
th, td {{ border: 1px solid #d9dee4; padding: 8px 12px; vertical-align: top; text-align: left; font-size: 14px; line-height: 1.6; }}
th {{ background: #2f5597; color: #fff; }}
tr.file td {{ background: #eef2f7; font-weight: 600; }}
td.doc {{ white-space: pre-wrap; }}
.key {{ display: block; color: #7b8794; font-family: Consolas, monospace; font-size: 12px; }}
.error {{ color: #b42318; font-size: 12px; margin-top: 4px; }}
.warning {{ color: #b54708; font-size: 12px; margin-top: 4px; }}
</style></head><body>
<h1>Localization review: English to Japanese</h1>
<table><tr><th>English (source)</th><th>Japanese</th></tr>
{''.join(rows)}
</table></body></html>"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, help="folder with the English source files")
    parser.add_argument("--target", required=True, help="folder with the Japanese files (same file names)")
    parser.add_argument("--glossary", default="glossary.csv", help="CSV with en,ja columns")
    parser.add_argument("--only", nargs="+", metavar="FILE", help="check only these file names")
    parser.add_argument("--html", help="also write a side-by-side review page to this path")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    results = run(args.source, args.target, load_glossary(args.glossary), args.only)
    errors = print_report(results)
    if args.html:
        write_html(results, args.html)
        print(f"review page -> {args.html}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
