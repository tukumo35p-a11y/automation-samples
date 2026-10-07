# Style notes: Tasklane, Japanese

Rules followed in this localization. Agreeing on these with the client before translating keeps every later string consistent.

## Tone

| Text | Tone | Example |
|---|---|---|
| Interface | Polite and short. です・ます form for sentences, noun phrases for buttons and labels | 保存 / 変更を保存しました |
| Marketing | Polite and warm. Invites rather than commands | 今日から始めましょう |
| Email | Business polite, with 様 and a customary opening and closing | いつも…ありがとうございます |

- The reader is never addressed as あなた. The subject is left out, as is natural in Japanese.
- User names take さん in the app and 様 in email.

## Wording

- Buttons and menu items are noun phrases or verb stems without a period: 保存, タスクを作成.
- Full sentences end with 。 Labels and headings do not.
- Counters follow numbers: 件 for tasks, 人 for people, 日 for days.
- Product and plan names stay in English: Tasklane, Pro.
- Loanwords follow common usage rather than the English spelling: ログイン, not サインイン.

## Punctuation and characters

- Japanese text uses full-width punctuation: 、。？:「」
- Numbers and Latin letters are half-width: 14日間, 8ドル.
- No space between Japanese text and half-width letters or numbers.
- No exclamation marks in the interface.
- Half-width katakana is not used.

## Placeholders

- Placeholders such as `{name}` are kept exactly as in the source and never translated.
- Sentences are rebuilt so the placeholder sits where Japanese grammar needs it: `{name}さんが「{task}」を完了しました`.

## Formats

- Currency: amount followed by the unit in running text (8ドル). Prices passed in as `{price}` are shown as provided.
- Quotation marks: 「」 for names of tasks and items.
