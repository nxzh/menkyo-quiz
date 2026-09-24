# Originality

Every question here was written from the 交通の方法に関する教則 and the 道路交通法. The
third-party booklets listed in the repository's README decide *which* questions exist —
the fingerprint set in [`../data/fingerprints.json`](../data/fingerprints.json) is their
deduplicated coverage — and nothing else. No author was shown their wording.

That is a claim, so it is checked. `assets/tools/check_originality.py` in the private
working repository runs two passes over the finished bank. It cannot run from a clean
checkout of this repository: the booklets are third-party material and are not published
here or anywhere else in the project.

## The two passes

**Shared runs.** The longest stretch of text a question and the booklet corpus have in
common, at 20 characters and up, with anything that is a continuous quotation from the
教則 or the 道交法 set aside — both texts are allowed to quote the same provision, and
Japanese statutory phrasing is fixed. What is left is read by a person.

**Item against item.** Each question against the reference items that attest its own
fingerprint, by `difflib` similarity on the normalised text — which is where a
transcription would actually be. This pass is the gate.

## Result, 2026-09-25, 498 questions against 1100 reference items

| | |
|---|---|
| Shared runs of 20+ characters that are 教則 / 道交法 wording outright | 90 |
| … that are that wording with a word or two of a seam | 54 |
| … with 8+ characters outside any continuous quotation, read by hand | 29 |
| Question/item pairs compared | 1079 |
| Pairs at 0.80 similarity or above | **0** |
| Pairs at 0.75 or above | 44 |

The 29 runs read by hand are all the ordinary Japanese for a rule that admits one
phrasing — 「進行を妨げないようにしなければならない」, the list of road users a sign
excludes, 「この標示は…を示している」 for a marking. None carries a scenario, a number
combination or a figure in common.

## What the first run found

The first full run, before this record, put **98 questions at 0.80 or above, 36 of them
at 0.90 or above, and two identical to a reference item character for character**. The
authors had not seen the booklets; a one-sentence true/false statement about a fixed rule
converges on its own. The rule is about the result, not the cause, so all 98 were written
again — a different sentence shape, subject and setting, with the fingerprint, the answer
and the cited provision unchanged, and all four translations redone with the Japanese.
The re-authors were told which questions to redo and the condition each must still test,
and were not shown the reference wording either.

The threshold is 0.80 because the bands below it are what two people independently
quoting the same provision produce. It is a gate, not a target: nothing was tuned to sit
just under it, and the worst pair in the bank now stands at 0.79.
