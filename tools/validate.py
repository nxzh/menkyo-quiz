#!/usr/bin/env python3
"""Validate every question batch against the authoring rules.

Zero dependencies (stdlib only). Run from the repository root:

    python3 tools/validate.py                 # all batches
    python3 tools/validate.py questions/karimen/batch-01.json

Exit code 1 if any ERROR is reported. WARNs do not fail the build; they mark
things a human has to look at (absolute wording, sentence-count drift).
"""
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent

GROUPS = set("ABCDEFGHIJKLMNOPQRSTU")
TRAPS = {"N", "SW", "EI", "EO", "SS", "AB", "EX", "NU", "OR", "SC", "NR"}
TYPES = {"text", "sign", "marking", "signal"}
LANGS = ("zh", "en", "vi", "pt")
SCOPES = {"仮免|本免|外免", "仮免|本免", "本免|外免", "本免"}

ID_RE = re.compile(r"^(K[0-9]+-[0-9]+(?:-[0-9]+)?|KS|KM|KL)-[0-9]{3}$")
QF_RE = re.compile(r"^QF-.+-[AD]-(?:N|SW|EI|EO|SS|AB|EX|NU|OR|SC|NR)-[0-9]{2}$")

REQUIRED = ["id", "category", "kp", "group", "source", "question_type", "qf",
            "question_ja", "answer", "explanation_ja", "i18n",
            "trap_type", "difficulty", "exam_scope"]
OPTIONAL = {"image", "verify"}

# 术语表 v7 rule 5 / rule 6: fixed distinctions that may never be swapped.
ZH_BANNED = {
    "超越": "glossary rule 5 — 「超越」 is banned; use 超车 (追越し) or 超过 (追抜き)",
    "标线": "glossary rule 6 — 標示 is 标示, never 标线",
    "人行道上的横道": "use 人行横道",
}
# Japanese 青 must never surface as 蓝 in Chinese (glossary rule 6).
ZH_BLUE = re.compile(r"蓝(灯|色的灯)")

ABSOLUTE_JA = ("必ず", "どんな場合でも", "一切", "決して", "絶対に")

SENT_END = re.compile(r"[。．.!?！？]")


def sentences(text):
    return len([s for s in SENT_END.split(text) if s.strip()])


def check_batch(path, seen_ids, seen_qf, errors, warns):
    def err(msg):
        errors.append(f"{path.name}: {msg}")

    def warn(msg):
        warns.append(f"{path.name}: {msg}")

    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"not valid JSON — {e}")
        return []
    if not isinstance(items, list):
        err("top level must be a JSON array of questions")
        return []

    if len(items) != 20:
        warn(f"{len(items)} questions; the spec batches in 20s")

    answers = Counter()
    for n, q in enumerate(items, 1):
        tag = q.get("id") or f"#{n}"

        missing = [k for k in REQUIRED if k not in q]
        if missing:
            err(f"{tag}: missing {', '.join(missing)}")
            continue
        extra = set(q) - set(REQUIRED) - OPTIONAL
        if extra:
            err(f"{tag}: unknown field(s) {', '.join(sorted(extra))}")

        if not ID_RE.match(q["id"]):
            err(f"{tag}: malformed id")
        if q["id"] in seen_ids:
            err(f"{tag}: duplicate id (also in {seen_ids[q['id']]})")
        else:
            seen_ids[q["id"]] = path.name

        if not QF_RE.match(q["qf"]):
            err(f"{tag}: malformed qf {q['qf']!r}")
        if q["qf"] in seen_qf:
            err(f"{tag}: duplicate qf {q['qf']} (also in {seen_qf[q['qf']]})")
        else:
            seen_qf[q["qf"]] = path.name

        if q["group"] not in GROUPS:
            err(f"{tag}: unknown group {q['group']!r}")
        if q["trap_type"] not in TRAPS:
            err(f"{tag}: unknown trap_type {q['trap_type']!r}")
        if q["question_type"] not in TYPES:
            err(f"{tag}: unknown question_type {q['question_type']!r}")
        if q["exam_scope"] not in SCOPES:
            err(f"{tag}: unknown exam_scope {q['exam_scope']!r}")
        if not isinstance(q["answer"], bool):
            err(f"{tag}: answer must be true/false")
        if q["difficulty"] not in (1, 2, 3):
            err(f"{tag}: difficulty must be 1–3")
        if q.get("verify") is False:
            err(f"{tag}: verify is written only when true — drop the field")

        # spec §1.4: trap=N and answer=○ correspond one to one.
        if (q["trap_type"] == "N") != (q["answer"] is True):
            err(f"{tag}: trap_type N must pair with answer true and vice versa "
                f"(trap={q['trap_type']}, answer={q['answer']})")

        # spec §6.2: a non-text question is never in the 外免 scope.
        if q["question_type"] != "text" and "外免" in q["exam_scope"]:
            err(f"{tag}: {q['question_type']} question cannot carry 外免")
        if q["question_type"] == "text" and "image" in q:
            err(f"{tag}: text question carries an image")
        if q["question_type"] != "text" and "image" not in q:
            err(f"{tag}: {q['question_type']} question has no image")
        if "image" in q:
            f = ROOT / "signs" / q["image"]["file"]
            if not f.exists():
                err(f"{tag}: image file signs/{q['image']['file']} not found")

        # spec §1.4 AB: absolute wording is a trap, not decoration.
        if q["trap_type"] != "AB":
            hits = [w for w in ABSOLUTE_JA if w in q["question_ja"]]
            if hits:
                warn(f"{tag}: absolute wording {hits} with trap {q['trap_type']}")

        i18n = q["i18n"]
        for lang in LANGS:
            if lang not in i18n:
                err(f"{tag}: i18n missing {lang}")
                continue
            for field in ("question", "explanation"):
                if not i18n[lang].get(field, "").strip():
                    err(f"{tag}: i18n.{lang}.{field} empty")

        # spec §6.4: sentence structure identical across languages.
        if all(l in i18n for l in LANGS):
            for field, ja in (("question", "question_ja"), ("explanation", "explanation_ja")):
                base = sentences(q[ja])
                for lang in LANGS:
                    got = sentences(i18n[lang][field])
                    if got != base:
                        warn(f"{tag}: {field} sentence count {lang}={got} vs ja={base}")

        zh = i18n.get("zh", {})
        zh_text = zh.get("question", "") + zh.get("explanation", "")
        for bad, why in ZH_BANNED.items():
            if bad in zh_text:
                err(f"{tag}: zh contains {bad!r} — {why}")
        if ZH_BLUE.search(zh_text):
            err(f"{tag}: zh renders 青 as 蓝 — glossary rule 6 says 绿")

        answers[q["answer"]] += 1

    if items and abs(answers[True] - answers[False]) > 2:
        warn(f"answer balance {answers[True]}○ / {answers[False]}× — the spec asks for half and half")
    return items


def main(argv):
    paths = [pathlib.Path(p) for p in argv[1:]]
    if not paths:
        paths = sorted((ROOT / "questions").rglob("batch-*.json"))
    if not paths:
        print("no batches found")
        return 0

    errors, warns, all_items = [], [], []
    seen_ids, seen_qf = {}, {}
    for p in paths:
        all_items += check_batch(p, seen_ids, seen_qf, errors, warns)

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    n = len(all_items)
    img = sum(1 for q in all_items if q.get("question_type") != "text")
    ok = sum(1 for q in all_items if q.get("answer") is True)
    print(f"\n{n} questions in {len(paths)} batch(es): {ok}○ / {n - ok}×, "
          f"{img} with an image ({img / n:.0%})" if n else "")
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
