# Contributing

Short version: **corrections are very welcome as issues; pull requests that add or
change content are not accepted.**

## What is welcome

Open an issue for anything wrong in the bank:

- a wrong answer, or an explanation that does not match the rule it cites
- a figure or condition that the law no longer says (traffic law moves; see the
  README's statutory-currency note)
- a translation that is wrong, unclear, or not what the police's own multilingual
  material calls that term (`docs/glossary-v7.md` records the official wording)
- a question that references artwork that is missing, or the wrong sign
- anything `tools/validate.py` or `tools/build_packs.py --check` fails on

Please name the question id (`K12-3-045`) and, where you can, the 教則 chapter or
道路交通法 article that settles it. A report of that kind is a fact, not prose we would
copy, which is exactly why it is the form this repository can accept.

## What is not accepted

Pull requests that add or change questions, explanations, translations or sign
artwork are closed unmerged, with a pointer to this file. Two reasons, both about the
content rather than about you:

1. **Provenance.** Every question has to be traceable to 交通の方法に関する教則 or the
   道路交通法 family, written from those sources rather than adapted from a driving
   school's book or a commercial question bank. That is checkable only while one
   author drafts every question from the primary sources.
2. **Licensing.** The bank is published under
   [CC BY-NC-SA 4.0](LICENSE-CONTENT) — free for personal study and non-commercial
   sharing. Driving schools and 登録支援機関 are commercial users, and they can buy a
   separate commercial licence. Merged contributions would arrive under the same NC
   terms, so granting one of those licences would mean chasing permission from every
   past contributor. Keeping copyright in one pair of hands keeps that possible.

Tooling is a different matter: `tools/` and `schema/` are [MIT](LICENSE-CODE). If you
want to fix a bug in the validator or the pack builder, open an issue first and say
what you have in mind.

## If this changes

These terms are not permanent. If contributions are ever opened up, this file will say
so and will state the licence grant a contributor makes at that point. Until then,
there is no CLA to sign because there is nothing to sign it for.

## Commercial licences

For use that CC BY-NC-SA 4.0 does not cover — a driving school, a 登録支援機関, an app
with advertising, anything sold — open an issue titled `Commercial licence` and say
what you want to use and how. Licences are granted by the copyright holder, Naixiao
Zhang.
