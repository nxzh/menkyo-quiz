#!/usr/bin/env python3
"""Validate every question batch against the authoring rules.

Zero dependencies (stdlib only). Run from the repository root:

    python3 tools/validate.py                 # all batches
    python3 tools/validate.py questions/karimen/batch-01.json

Exit code 1 if any ERROR is reported. WARNs do not fail the build; they mark
things a human has to look at (absolute wording, sentence-count drift).

The sign index (signs/index.csv) is checked too: every artwork file has a row,
every row a file, every row a licence and a source URL, and every question's
declared image licence is the one its file's row carries.

The fingerprint ledger (data/fingerprints.json) is checked both ways: every
`covered` row names a question that exists and carries that qf, every question
appears in exactly one row, and every `dropped` row states its code and reason.
`--complete` additionally fails on any row still `pending`, which is what the
cutover commit runs.
"""
import csv
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

# A period is a sentence end only when it really ends a sentence: not inside a
# decimal (1.5 metres vs 1,5 metro) and not closing an abbreviation (etc., v.v.).
DECIMAL = re.compile(r"(?<=\d)[.,](?=\d)")
ABBREV = re.compile(r"\b(etc|Dr|Mr|Mrs|Ms|vs|No|v\.v|Sr|Sra)\.", re.IGNORECASE)
SENT_END = re.compile(r"[。．！？]|[.!?](?=[\s\u00a0]|$)")


SIGN_INDEX = ROOT / "signs" / "index.csv"
SIGN_FIELDS = ("license", "source_url")

LEDGER = ROOT / "data" / "fingerprints.json"
LEDGER_FIELDS = ("qf", "kp", "group", "direction", "trap", "condition",
                 "attested_by", "status")
DROP_CODES = {"C1", "C2", "C3", "C6"}


def check_ledger(items, errors, warns, complete=False):
    """The bank and the fingerprint ledger must agree in both directions."""
    if not LEDGER.exists():
        errors.append("data/fingerprints.json is missing")
        return
    try:
        doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"data/fingerprints.json: not valid JSON — {e}")
        return
    rows = doc.get("fingerprints")
    if not isinstance(rows, list):
        errors.append("data/fingerprints.json: no fingerprints array")
        return

    by_qf, pending = {}, 0
    for n, r in enumerate(rows, 1):
        tag = r.get("qf") or f"row #{n}"
        missing = [k for k in LEDGER_FIELDS if k not in r]
        if missing:
            errors.append(f"ledger {tag}: missing {', '.join(missing)}")
            continue
        if not QF_RE.match(r["qf"]):
            errors.append(f"ledger {tag}: malformed qf")
        if r["qf"] in by_qf:
            errors.append(f"ledger {tag}: duplicate row")
        by_qf[r["qf"]] = r
        if not r["attested_by"]:
            errors.append(f"ledger {tag}: no source set attests it")
        status = r["status"]
        if status == "dropped":
            if r.get("drop_code") not in DROP_CODES:
                errors.append(f"ledger {tag}: dropped without a valid drop_code")
            if not r.get("reason"):
                errors.append(f"ledger {tag}: dropped without a reason")
        elif status == "covered":
            if not r.get("question_id"):
                errors.append(f"ledger {tag}: covered without a question_id")
        elif status == "pending":
            pending += 1
        else:
            errors.append(f"ledger {tag}: unknown status {status!r}")

    by_id = {q["id"]: q for q in items if "id" in q}
    for r in rows:
        if r.get("status") != "covered":
            continue
        qid = r.get("question_id")
        q = by_id.get(qid)
        if q is None:
            errors.append(f"ledger {r['qf']}: names question {qid}, which does not exist")
        elif q.get("qf") != r["qf"]:
            errors.append(f"ledger {r['qf']}: {qid} carries qf {q.get('qf')}")

    claimed = Counter(r.get("question_id") for r in rows
                      if r.get("status") == "covered" and r.get("question_id"))
    for qid, n in claimed.items():
        if n > 1:
            errors.append(f"ledger: question {qid} is claimed by {n} rows")
    for q in items:
        row = by_qf.get(q.get("qf"))
        if row is None:
            errors.append(f"{q.get('id')}: qf {q.get('qf')} is not in the ledger")
        elif row.get("question_id") != q.get("id"):
            errors.append(f"{q.get('id')}: the ledger row for {q.get('qf')} "
                          f"names {row.get('question_id')!r}")

    line = (f"ledger: {len(rows)} fingerprints, "
            f"{sum(1 for r in rows if r.get('status') == 'covered')} covered, "
            f"{pending} pending, "
            f"{sum(1 for r in rows if r.get('status') == 'dropped')} dropped")
    if pending and complete:
        errors.append(f"{line} — --complete requires every fingerprint to be covered")
    elif pending:
        warns.append(line)


def sign_index(errors):
    """file name -> its index row. The only index: there is no index.json."""
    if not SIGN_INDEX.exists():
        errors.append("signs/index.csv: not found")
        return {}
    with SIGN_INDEX.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    index = {}
    for row in rows:
        name = (row.get("file") or "").strip()
        if not name:
            errors.append("signs/index.csv: a row has no file name")
            continue
        if name in index:
            errors.append(f"signs/index.csv: duplicate row for {name}")
        index[name] = row
    return index


def check_signs(index, errors):
    """Provenance is per file or it is not provenance (CLAUDE.md compliance)."""
    for name, row in sorted(index.items()):
        for field in SIGN_FIELDS:
            if not (row.get(field) or "").strip():
                errors.append(f"signs/index.csv: {name} has no {field}")
        if not (ROOT / "signs" / name).exists():
            errors.append(f"signs/index.csv: {name} has a row but no file")
    on_disk = {p.name for p in (ROOT / "signs").glob("*.svg")}
    for name in sorted(on_disk - set(index)):
        errors.append(f"signs/{name}: artwork with no row in index.csv")


def sentences(text):
    t = DECIMAL.sub("", text)
    t = ABBREV.sub(lambda m: m.group(0)[:-1], t)
    return len(SENT_END.findall(t.strip()))


def check_batch(path, seen_ids, seen_qf, signs, errors, warns):
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
            name = q["image"]["file"]
            if not (ROOT / "signs" / name).exists():
                err(f"{tag}: image file signs/{name} not found")
            row = signs.get(name)
            if row is None:
                err(f"{tag}: image file signs/{name} has no row in index.csv")
            elif q["image"].get("license") != row.get("license"):
                err(f"{tag}: image licence {q['image'].get('license')!r} differs "
                    f"from signs/index.csv {row.get('license')!r} for {name}")

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
    argv = list(argv)
    complete = "--complete" in argv
    if complete:
        argv.remove("--complete")
    # --no-ledger checks a batch on its own, for work in progress on a batch
    # whose questions the ledger does not point at yet. CI never passes it.
    no_ledger = "--no-ledger" in argv
    if no_ledger:
        argv.remove("--no-ledger")
    paths = [pathlib.Path(p) for p in argv[1:]]
    if not paths:
        paths = sorted((ROOT / "questions").rglob("batch-*.json"))
    if not paths:
        # an empty bank is a valid state between the clear and the rebuild;
        # the ledger is still checked, and every row is expected to be pending
        errors, warns = [], []
        if not no_ledger:
            check_ledger([], errors, warns, complete)
        for w in warns:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}")
        print("no batches found — the bank is empty")
        print(f"{len(errors)} error(s), {len(warns)} warning(s)")
        return 1 if errors else 0

    errors, warns, all_items = [], [], []
    seen_ids, seen_qf = {}, {}
    signs = sign_index(errors)
    check_signs(signs, errors)
    for p in paths:
        all_items += check_batch(p, seen_ids, seen_qf, signs, errors, warns)
    if not no_ledger:
        check_ledger(all_items, errors, warns, complete)

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
