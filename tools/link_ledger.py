#!/usr/bin/env python3
"""Point the fingerprint ledger at the questions that cover it.

Zero dependencies (stdlib only). Run from the repository root:

    python3 tools/link_ledger.py            # update data/fingerprints.json
    python3 tools/link_ledger.py --check    # fail if it is not current

A question carries its fingerprint in `qf`; this writes the other direction —
`status: covered` and `question_id` — so `tools/validate.py` can check the two
against each other. A row whose question no longer exists goes back to
`pending`. Rows that are `dropped` are never touched: a dropped fingerprint may
not be asked, so a question claiming one is an error, not something to link.
"""
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "fingerprints.json"
QUESTIONS = ROOT / "questions"


def load_questions():
    by_qf = {}
    clashes = []
    for path in sorted(QUESTIONS.rglob("batch-*.json")):
        for q in json.loads(path.read_text(encoding="utf-8")):
            qf, qid = q.get("qf"), q.get("id")
            if not qf or not qid:
                continue
            if qf in by_qf:
                clashes.append(f"{qf}: {by_qf[qf]} and {qid}")
            by_qf[qf] = qid
    return by_qf, clashes


def relink(doc, by_qf):
    changed = []
    for row in doc["fingerprints"]:
        if row["status"] == "dropped":
            continue
        qid = by_qf.get(row["qf"])
        want_status = "covered" if qid else "pending"
        if row["status"] != want_status or row.get("question_id") != qid:
            changed.append(f"{row['qf']} -> {qid or 'pending'}")
        row["status"] = want_status
        row["question_id"] = qid
    counts = Counter(r["status"] for r in doc["fingerprints"])
    doc["counts"]["covered"] = counts["covered"]
    doc["counts"]["pending"] = counts["pending"]
    return changed


def main(argv):
    by_qf, clashes = load_questions()
    for c in clashes:
        print(f"ERROR two questions share a fingerprint — {c}")
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    known = {r["qf"] for r in doc["fingerprints"]}
    orphans = sorted(set(by_qf) - known)
    for qf in orphans:
        print(f"ERROR {by_qf[qf]} carries {qf}, which is not in the ledger")
    dropped = {r["qf"] for r in doc["fingerprints"] if r["status"] == "dropped"}
    for qf in sorted(set(by_qf) & dropped):
        print(f"ERROR {by_qf[qf]} carries {qf}, which is a dropped fingerprint")
    if clashes or orphans or (set(by_qf) & dropped):
        return 1

    changed = relink(doc, by_qf)
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if "--check" in argv:
        if text != LEDGER.read_text(encoding="utf-8"):
            print("link_ledger --check: the ledger is stale; run tools/link_ledger.py")
            return 1
        print(f"ledger is current — {doc['counts']['covered']} covered, "
              f"{doc['counts']['pending']} pending")
        return 0
    LEDGER.write_text(text, encoding="utf-8")
    print(f"linked {len(changed)} row(s) — {doc['counts']['covered']} covered, "
          f"{doc['counts']['pending']} pending, "
          f"{doc['counts']['dropped']} dropped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
