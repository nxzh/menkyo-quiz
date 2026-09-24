#!/usr/bin/env python3
"""Does the bank render one glossary term two ways?

Substring matching, so inflection and plurals show up as misses: read a finding
before acting on it. What it catches reliably is a noun phrase chosen twice.
"""
import glob, json, re, sys
from pathlib import Path

QUIZ = Path.home() / "GitHub" / "menkyo-quiz"
LANGS = {"zh": 1, "en": 2, "vi": 3, "pt": 4}


def glossary_terms(path: Path) -> dict[str, list[str]]:
    """Only the term tables — the 官方核对结果 table below them has five columns
    too, and reading it as terms silently overwrites the real rows."""
    rows, in_terms = {}, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("| 日文 "):
            in_terms = True
            continue
        if line.startswith("#") or (line.startswith("| ") and "| 术语 " in line):
            in_terms = False
        if not in_terms or not line.startswith("| ") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0]:
            rows.setdefault(cells[0], cells)
    return rows


def bare(rendering: str) -> str:
    return re.sub(r"[（(][^（()）]*[）)]", "", rendering).strip() or rendering


def main() -> int:
    terms = glossary_terms(QUIZ / "docs" / "glossary-v7.md")
    bank = {}
    for path in sorted(glob.glob(str(QUIZ / "questions" / "*" / "*.json"))):
        for q in json.loads(Path(path).read_text(encoding="utf-8")):
            bank[q["id"]] = (q, Path(path).name)
    watch = sys.argv[1:] or sorted(terms)
    findings = 0
    for term in watch:
        if term not in terms:
            print(f"!! {term} is not a glossary term")
            continue
        holders = [(q, b) for q, b in bank.values()
                   if term in q["question_ja"] + q["explanation_ja"]]
        if len(holders) < 2:
            continue
        for lang, col in LANGS.items():
            want = bare(terms[term][col]).lower()
            if len(want) < 2:
                continue
            miss = [f"{q['id']} ({b})" for q, b in holders
                    if want not in (q["i18n"][lang]["question"]
                                    + q["i18n"][lang]["explanation"]).lower()]
            hits = len(holders) - len(miss)
            if hits and miss and len(miss) <= max(6, len(holders) // 3):
                findings += 1
                print(f"{term} [{lang}] wants {want!r}: {hits} do, {len(miss)} do not "
                      f"— {', '.join(miss[:8])}")
    print(f"\n{findings} term/language pair(s) to read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
