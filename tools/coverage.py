#!/usr/bin/env python3
"""Generate docs/coverage.md from the fingerprint ledger.

Zero dependencies (stdlib only). Run from the repository root:

    python3 tools/coverage.py            # write docs/coverage.md
    python3 tools/coverage.py --check    # fail if it is not current

The ledger (data/fingerprints.json) is the source of truth for what the bank
contains and why. This file is the readable version of it: unchanged input
produces byte-identical output, so a stale coverage document fails CI rather
than drifting quietly.
"""
import json
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "fingerprints.json"
OUT = ROOT / "docs" / "coverage.md"

GROUP_NAMES = {
    "A": "信号灯", "B": "手势信号", "C": "标志标示总论", "D": "个别标志标示",
    "E": "驾驶前心得", "F": "驾照制度", "G": "上车·安全带", "H": "通行区分",
    "I": "紧急车·公交优先", "J": "行人道路", "K": "行人等保护", "L": "停止距离",
    "M": "徐行", "N": "示意·喇叭", "O": "变道·横穿掉头", "P": "超车·让行",
    "Q": "交叉路口", "R": "AT车", "S": "道口", "T": "二轮车", "U": "其他",
}
TRAP_NAMES = {
    "N": "no trap", "SW": "swapped condition", "EI": "invented exemption",
    "EO": "exception omitted", "SS": "similar sign", "AB": "absolute wording",
    "EX": "scope widened", "NU": "number substituted", "OR": "order reversed",
    "SC": "offence described", "NR": "factor excluded",
}


def sets_of(row):
    return "".join(a["set"] for a in row["attested_by"])


def render(doc):
    rows = doc["fingerprints"]
    live = [r for r in rows if r["status"] != "dropped"]
    covered = [r for r in rows if r["status"] == "covered"]
    dropped = [r for r in rows if r["status"] == "dropped"]

    out = []
    w = out.append
    w("# 仮免 coverage")
    w("")
    w("Generated from `data/fingerprints.json` by `tools/coverage.py`. Do not edit by hand.")
    w("")
    w("Every question in this bank exists because at least one reference source set asks")
    w("that fingerprint — a knowledge point, a direction, a trap and a tested condition.")
    w("A fingerprint no source set asks is not in the bank, and a fingerprint that may not")
    w("be asked is listed below with its reason. Nothing here reproduces a reference bank's")
    w("wording: the conditions are this project's own analytical labels, and the questions")
    w("are written from the 教則 and the 道路交通法.")
    w("")
    w("## Totals")
    w("")
    w("| | |")
    w("|---|---|")
    w(f"| reference items read | {doc['counts']['raw_items']} |")
    w(f"| distinct fingerprints | {len(rows)} |")
    w(f"| authorable | {len(live)} |")
    w(f"| written | {len(covered)} |")
    w(f"| still to write | {len(live) - len(covered)} |")
    w(f"| dropped | {len(dropped)} |")
    w("")

    w("## Source sets")
    w("")
    w("| set | items | attests | unique to it | what it is |")
    w("|---|---|---|---|---|")
    by_set = defaultdict(set)
    for r in live:
        for a in r["attested_by"]:
            by_set[a["set"]].add(r["qf"])
    for s in doc["source_sets"]:
        letter = s["set"]
        others = set().union(*[v for k, v in by_set.items() if k != letter]) \
            if len(by_set) > 1 else set()
        w(f"| {letter} | {s['items']} | {len(by_set[letter])} | "
          f"{len(by_set[letter] - others)} | {s['note']} |")
    w("")

    w("## By knowledge-point group")
    w("")
    w("| group | | fingerprints | written | ○ | × | with an image |")
    w("|---|---|---|---|---|---|---|")
    for g in sorted(GROUP_NAMES):
        rs = [r for r in live if r["group"] == g]
        if not rs:
            continue
        done = sum(1 for r in rs if r["status"] == "covered")
        yes = sum(1 for r in rs if r["answer"])
        img = sum(1 for r in rs if r["question_type"] != "text")
        w(f"| {g} | {GROUP_NAMES[g]} | {len(rs)} | {done} | {yes} | "
          f"{len(rs) - yes} | {img} |")
    w(f"| | **total** | **{len(live)}** | "
      f"**{len(covered)}** | **{sum(1 for r in live if r['answer'])}** | "
      f"**{sum(1 for r in live if not r['answer'])}** | "
      f"**{sum(1 for r in live if r['question_type'] != 'text')}** |")
    w("")

    w("## Trap mix")
    w("")
    neg = [r for r in live if not r["answer"]]
    w("| trap | | fingerprints | share of × |")
    w("|---|---|---|---|")
    for trap, n in Counter(r["trap"] for r in neg).most_common():
        w(f"| {trap} | {TRAP_NAMES.get(trap, '')} | {n} | {n / len(neg):.0%} |")
    w("")

    if dropped:
        w("## Dropped fingerprints")
        w("")
        w("Attested by a source set, but not asked here.")
        w("")
        w("| fingerprint | code | condition | reason |")
        w("|---|---|---|---|")
        for r in sorted(dropped, key=lambda r: r["qf"]):
            w(f"| `{r['qf']}` | {r['drop_code']} | {r['condition']} | {r['reason']} |")
        w("")

    w("## Every fingerprint")
    w("")
    w("`sets` cites the source sets that attest it. `question` is the question that")
    w("tests it, or a dash while it is still to be written.")
    w("")
    for g in sorted(GROUP_NAMES):
        rs = sorted([r for r in live if r["group"] == g], key=lambda r: r["qf"])
        if not rs:
            continue
        w(f"### {g} — {GROUP_NAMES[g]} ({len(rs)})")
        w("")
        w("| fingerprint | ans | trap | type | sets | question | condition |")
        w("|---|---|---|---|---|---|---|")
        for r in rs:
            w(f"| `{r['qf']}` | {'○' if r['answer'] else '×'} | {r['trap']} | "
              f"{r['question_type']} | {sets_of(r)} | "
              f"{r['question_id'] or '—'} | {r['condition']} |")
        w("")
    return "\n".join(out).rstrip() + "\n"


def main(argv):
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    text = render(doc)
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("coverage --check: docs/coverage.md is stale; run tools/coverage.py")
            return 1
        print(f"coverage is current — {len(doc['fingerprints'])} fingerprints")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(doc['fingerprints'])} fingerprints")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
