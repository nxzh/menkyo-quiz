# menkyo-quiz

Original practice questions for the Japanese driver's licence knowledge tests, in
five languages: 日本語 · 简体中文 · English · Tiếng Việt · Português.

**仮免許 (provisional licence, first stage): 1000 questions, complete.** Every one is
written from the official sources and carried in all five languages: 500 true and 500
false, 160 of them with a road-sign or road-marking image, spread over about 190
knowledge points of the 教則 and the 道路交通法.

```
questions/karimen/batch-01.json …   50 batches of 20, Japanese master + i18n
data/taxonomy.<lang>.json           9 教則 chapters and 32 sections, five languages
docs/authoring.md                   how a question is written — read this first
docs/glossary-v7.md                 the binding terminology glossary, 203 terms
docs/coverage-plan.md               what the 1000 cover, and in what order
schema/question.schema.json         the question object
tools/validate.py                   structure, trap/answer pairing, glossary bans
tools/stats.py                      coverage, trap mix, ○× balance
tools/build_packs.py                builds dist/ — the packs the app downloads
signs/                              road-sign SVGs used by image questions
dist/                               generated content packs + manifest.json
```

## Content packs

The Menkyo app never reads this repository's question files directly. It reads
`dist/`, which `tools/build_packs.py` generates:

| file | what it is |
|---|---|
| `manifest.json` | what the app fetches first: `content_version`, `min_app_version`, `law_revision_date`, `hidden_ids`, which exams the bank can serve, the per-version notes, and every pack's version, size, sha256 and URL |
| `core-free.json` / `core-full.json` | the questions without any question text: answers, chapter, knowledge point, citation, trap type, tier |
| `<lang>-free.json` / `<lang>-full.json` | the same questions as text only — question and explanation, **never an answer** |
| `taxonomy.json` | chapter and section names in all five languages |

The core/language split is a requirement, not a convenience: the answer key
exists only in the core pack, so a language pack can be read by anyone without
giving the answers away.

The free/full split is what the app's one purchase buys — 120 questions or all
1000. It is a visibility limit and nothing more: every pack is published in the
clear, because these questions are public and a cipher over a plaintext
published beside it would protect nothing.

```sh
python3 tools/build_packs.py            # regenerate dist/
python3 tools/build_packs.py --check    # CI: is dist/ what the questions say it is?
```

The build needs no secret and no environment. Unchanged questions produce
byte-identical packs, so a pack's version moves only when its bytes do and the
app never re-downloads one that did not change.

## Which exams the bank serves

`data/exams.json` declares it, and the manifest carries it. Most 仮免 questions
are also valid for 本免 and 外免切替, so counting a question's `exam_scope`
would claim an exam this bank cannot fill. Today that is 仮免 alone; the app
shows the other two as not yet available rather than offering an exam it cannot
give.

## Sources

Questions derive only from:

- 交通の方法に関する教則 (令和6年9月4日 国家公安委員会告示第37号)
- 道路交通法 and its 施行令 / 施行規則
- 道路標識、区画線及び道路標示に関する命令 (標識令)

Driving-school textbooks and commercial question banks are **not** sources. They were
read only to see what the real exams emphasise; no wording, sentence structure, number
combination or illustration from them appears here.

English, Vietnamese and Portuguese terminology follows the official multilingual
traffic materials published by the 警察庁 / 警視庁 / prefectural police, as recorded in
`docs/glossary-v7.md`.

## Statutory currency

Traffic law moves. These questions are written against the state of the law recorded
in `docs/coverage-plan.md`, including the 30 km/h default speed limit on residential
roads in force since 2026-09-01 and the 2026-04-01 amendments. A question whose exact
figure or condition could not be confirmed against a primary source carries
`"verify": true` and is not shipped until it has been.

**This repository is study material, not legal advice.** For anything that matters,
read the 教則 and the law.

## Checking a change

```sh
python3 tools/validate.py      # stdlib only; exits non-zero on an error
python3 tools/stats.py karimen
```

`validate.py` checks structure, that `trap_type: N` and `answer: true` correspond one
to one, that a non-text question never carries the 外免 scope, ○× balance, id and
fingerprint uniqueness, that every referenced sign file exists, sentence-count parity
across the five languages, and the glossary's banned Chinese renderings. `stats.py`
prints knowledge-point coverage and the trap mix against the authoring targets.

## Licence

- Question content, explanations and translations: [CC BY-NC-SA 4.0](LICENSE-CONTENT).
- Tooling and schema: [MIT](LICENSE-CODE).
- Road-sign SVGs under `signs/`: the signs themselves are reproductions of the 標識令
  catalogue (PD-Japan-exempt); per-file provenance is in `signs/index.csv`.
