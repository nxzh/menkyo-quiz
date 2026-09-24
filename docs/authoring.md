# 出题规范 — how a question in this bank is written

Operative rules for `questions/`. Derived from the Menkyo project's
`题型分析与出题规范 v8`; where this file and that spec disagree, the spec wins.

**Which questions exist is not decided here.** The bank is the deduplicated
fingerprint set of the reference source sets: one question per fingerprint, and a
knowledge point no reference bank asks is recorded rather than written. The set is
`data/fingerprints.json`, readable as [`coverage.md`](coverage.md), and spec v8 §9
is the rule. This file decides how a question is written once the fingerprint says
it should exist.

## 1. Sources

- A question may derive **only** from 交通の方法に関する教則 (the official rules of
  the road), the 道路交通法 and its 施行令 / 施行規則, and the 標識令.
- Driving-school textbooks and commercial question banks are used for **verification
  and trend analysis only**. Never their wording, sentence structure, number
  combinations or illustrations.
- Where the 教則 and current law conflict, the law governs and `source` cites the article.
- Every question is original: same knowledge point, different sentence, scenario and numbers.

## 2. Shape

One JSON object per question, in `questions/{scope}/batch-NN.json`. One batch holds
one knowledge-point group, up to 20 questions; a group larger than 20 runs over
several batches. The validator warns on a batch that is not 20 — that warning is
expected on the batch that closes a group.

```json
{
  "id": "K5-7-001",
  "category": "交差点",
  "kp": "5-7-4",
  "group": "Q",
  "source": "教則 第5章第7節4(3) / 道交法第37条の2第2項",
  "question_type": "text",
  "qf": "QF-5-7-4-D-SW-01",
  "question_ja": "…",
  "answer": false,
  "explanation_ja": "…",
  "i18n": {
    "zh": { "question": "…", "explanation": "…" },
    "en": { "question": "…", "explanation": "…" },
    "vi": { "question": "…", "explanation": "…" },
    "pt": { "question": "…", "explanation": "…" }
  },
  "trap_type": "SW",
  "difficulty": 2,
  "exam_scope": "仮免|本免|外免"
}
```

- Japanese is the master. Every other language lives in `i18n`.
- `id` — text `K{chapter}-{section}-{nnn}`, sign `KS-{nnn}`, marking `KM-{nnn}`,
  outside the 教則 `KL-{nnn}`.
- `qf` — question fingerprint `QF-{KP}-{direction}-{trap}-{nn}`, direction `A`
  affirmative / `D` negative-or-reversed. Two questions with the same KP, direction
  and trap testing the same condition are the same QF; the bank never holds two.
- `exam_scope` — 仮免-stage knowledge is `仮免|本免|外免`, second-stage is `本免|外免`.
  **A question whose `question_type` is not `text` never carries 外免**: since the
  2025-10-01 施行規則 revision the 外免切替 knowledge test is 50 text questions only.
- `verify` — written **only when true**, on any question whose exact number or
  condition could not be confirmed against a source in this repository.
  Never guess a numeric value.
- `image` — required on `sign` / `marking` / `signal`, forbidden on `text`.

## 3. Codes

**Knowledge-point groups** — A 信号灯 / B 手势信号 / C 标志标示总论 / D 个别标志标示 /
E 驾驶前心得 / F 驾照制度 / G 上车·安全带 / H 通行区分 / I 紧急车·公交优先 /
J 行人道路 / K 行人等保护 / L 停止距离 / M 徐行 / N 示意·喇叭 / O 变道·横穿掉头 /
P 超车·让行 / Q 交叉路口 / R AT车 / S 道口 / T 二轮车 / U 其他

**Traps**

| code | name | what it does |
|---|---|---|
| N | 无陷阱 | a correct statement; `answer` is always `true` |
| SW | 条件互换 | 徐行 ↔ 一時停止, definitions, left ↔ right, subject swapped |
| EI | 例外捏造 | invents an exemption the law does not grant |
| EO | 例外省略 | drops a real exception, making the statement too broad |
| SS | 相似标志混淆 | image and description do not match |
| AB | 绝对化措辞 | 必ず / どんな場合でも / 一切 |
| EX | 条件扩大 | scope or subject widened |
| NU | 数字替换 | 30m ↔ 3秒, 1m ↔ 3m |
| OR | 顺序互换 | order of actions reversed |
| SC | 情景判断 | plainly describes an offence |
| NR | 要素缺漏 | excludes a real factor, making the statement too narrow |

`trap_type: N` and `answer: true` correspond one to one. The validator enforces it.

## 4. Writing

- True/false (○×) only, about half and half in each batch.
- One knowledge point per question. Name the subject (車 / 一般原動機付自転車 /
  歩行者) and the place.
- **A ○ question states its conditions and exceptions in full.** `EO` is for ×
  questions only, and an × question has exactly one reason for being wrong.
- Explanations cite the provision first; an × explanation then states what is correct.
- At most one affirmative/negative mirror pair per KP per batch.
- **The trap mix is an observation, not a quota.** It falls out of the fingerprint
  set: each question's trap is the one its fingerprint carries, so the finished bank
  reproduces what the reference banks actually ask (spec v8 §4.3 measured EI 30%,
  SW 18%, SS 15% of the × questions). `tools/stats.py` prints the running mix
  against the old v7 target bands; a band it flags on a part-built bank is
  information, not a defect to author around.
- Image questions are 109 of the 507 fingerprints, 108 of them authored. Every sign
  and marking maps to a 標識令 catalogue number in `signs/index.csv`; the three
  signal questions use drawings made for this project, with no lettering, so the
  image is the same in every language.

## 5. Translation

- Every legal term follows [`glossary-v7.md`](glossary-v7.md) exactly, including its
  bracket rule (a parenthesised gloss appears only on a term's first occurrence in a
  question) and the fixed distinctions that may never be swapped:
  停车 / 驻车 / 暂停 / 停留 · 超车 / 超过 (「超越」 banned) · 标识 / 标示.
- EN / VI / PT follow the glossary's rule 7: **the official 警察庁 / 警視庁 / 県警
  translation wins.**
- Translate meaning, not word by word, for learners rather than lawyers.
- **Answer and explanation structure is identical across languages, sentence for
  sentence.** A translation may not widen or narrow the statement: if the Japanese
  has an exception the translation keeps it; if the Japanese has no absolute wording
  the translation does not add any.
- A term missing from the glossary is translated and listed in
  [`new-terms.md`](new-terms.md), with the question it was first used in.
- Image captions are identical across languages; the image itself is not localised.

## 6. Checking

```
python3 tools/validate.py            # structure, trap/answer pairing, scope, glossary bans, ledger
python3 tools/validate.py --complete # the above, and fail while any fingerprint is unwritten
python3 tools/link_ledger.py         # point the ledger at the questions that now cover it
python3 tools/coverage.py            # regenerate docs/coverage.md from the ledger
python3 tools/stats.py               # KP coverage, trap mix, ○× balance
```

After adding or editing questions, run `link_ledger.py` and then `coverage.py`:
`validate.py` fails while the ledger and the bank disagree, and CI checks that both
generated files are current.

`validate.py` fails the build on an error. Warnings — absolute wording outside an
`AB` trap, sentence-count drift between languages — are for a human to read.
