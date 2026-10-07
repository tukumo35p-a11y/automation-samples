# English to Japanese localization with automated QA

A sample localization of a fictional task-management app, Tasklane, from English into Japanese. It covers the three kinds of text most products need translated, and includes a script that checks the translation for the mistakes that break a product.

## What was localized

| File | Content | English | Japanese |
|---|---|---|---|
| `ui.json` | 28 interface strings with `{placeholders}` | [source/en/ui.json](source/en/ui.json) | [ja/ui.json](ja/ui.json) |
| `landing.md` | Landing page copy | [source/en/landing.md](source/en/landing.md) | [ja/landing.md](ja/landing.md) |
| `email.md` | Trial-ending email | [source/en/email.md](source/en/email.md) | [ja/email.md](ja/email.md) |

The English source text was written for this sample.

## Localized, not word for word

Each kind of text is written the way a Japanese product would write it. A few examples:

| English | Japanese | Why |
|---|---|---|
| Sign in | ログイン | The usual word in Japanese apps; サインイン reads as a direct import |
| Welcome back, {name}! | {name}さん、おかえりなさい | Name first with さん; no exclamation mark, which reads as too loud in an app |
| {count} tasks are overdue | 期限切れのタスクが{count}件あります | Word order rebuilt around the number, with the counter 件 |
| Invite teammates | メンバーを招待 | チームメイト sounds like a sports team |
| Hi {first_name}, | {first_name}様 | Business email uses 様, followed by a customary line of thanks that the English does not have |
| Stop chasing updates in chat. | 進捗の確認でチャットをさかのぼるのは、もう終わりにしませんか。 | A direct command reads as pushy in Japanese marketing; a question invites instead |

The choices are recorded so they stay consistent as the product grows: terms in [glossary.csv](glossary.csv), tone and punctuation rules in [STYLE_NOTES.md](STYLE_NOTES.md).

## Automated checks

`check_localization.py` compares the Japanese files with the English source and reports:

- Missing, extra, or empty strings
- Broken placeholders, such as `{name}` deleted or translated into `{名前}`, which would crash or show raw text in the app
- Strings left in English
- Numbers, links, headings, and list items that were dropped
- Terms that do not follow the glossary
- Half-width `?` and `!` in Japanese text, and half-width katakana

```
python check_localization.py --source source/en --target ja
```

The finished translation passes with no errors or warnings: [sample_output/final_report.txt](sample_output/final_report.txt).

To show what the checker catches, [examples/draft/ui.json](examples/draft/ui.json) is an earlier draft with ten typical mistakes left in. The checker finds all ten: [sample_output/draft_report.txt](sample_output/draft_report.txt).

```
python check_localization.py --source source/en --target examples/draft --only ui.json
```

```
ui.json
  ERROR   common.learn_more       missing in translation
  ERROR   common.ok               not in source (extra or misspelled key)
  WARNING auth.sign_in            glossary: "sign in" should be "ログイン"
  WARNING auth.forgot_password    half-width ? or ! after Japanese text; use the full-width mark
  ERROR   task.overdue            placeholders differ: source {count}, translation (none)
  ERROR   task.assigned_to        placeholders differ: source {name}, translation {名前}
  WARNING project.invite          glossary: "teammate" should be "メンバー"
  WARNING billing.upgrade         looks untranslated (no Japanese text)
  WARNING error.required          sentence-ending period does not match the source
  ERROR   error.file_too_large    empty translation

5 error(s), 5 warning(s) in 1 file(s)
```

Add `--html review.html` to get a side-by-side page for review, with each issue shown under the string it belongs to. The script uses only the Python standard library and exits with code 1 on errors, so it can run in CI.

## How I work

I am a native Japanese speaker. I use AI assistance for first drafts, review every line myself against the glossary and style notes, and run the automated checks before delivery.
