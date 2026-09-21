# menkyo-quiz

Original practice questions for the Japanese driver's licence knowledge tests, in
five languages: 日本語 · 简体中文 · English · Tiếng Việt · Português.

The first target is **仮免許 (provisional licence, first stage): 1000 questions**,
every one of them written from the official sources and carried in all five languages.

```
questions/karimen/batch-01.json …   20 questions per batch, Japanese master + i18n
docs/authoring.md                   how a question is written — read this first
docs/glossary-v7.md                 the binding terminology glossary, 203 terms
docs/coverage-plan.md               what the 1000 cover, and in what order
schema/question.schema.json         the question object
tools/validate.py                   structure, trap/answer pairing, glossary bans
tools/stats.py                      coverage, trap mix, ○× balance
signs/                              road-sign SVGs used by image questions
```

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

## Licence

- Question content, explanations and translations: [CC BY-NC-SA 4.0](LICENSE-CONTENT).
- Tooling and schema: [MIT](LICENSE-CODE).
- Road-sign SVGs under `signs/`: the signs themselves are reproductions of the 標識令
  catalogue (PD-Japan-exempt); per-file provenance is in `signs/index.csv`.
