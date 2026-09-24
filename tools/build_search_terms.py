#!/usr/bin/env python3
"""Build the search terms document from the glossary and the alias file.

    python3 assets/tools/build_search_terms.py --out dist/terms.json
    python3 assets/tools/build_search_terms.py --check dist/terms.json

One group per glossary row. Position 0 of every language is the glossary's
bound translation — that is what the app's matched-term line names, so it is
also what the generator refuses to let drift. Positions 1+ come from two
places:

  * the glossary's own record of what it set aside — 「v7 官方核对结果」's four
    tables. A wording the 警察庁 uses and this project does not is exactly what
    a learner who read the police leaflet will type.
  * `assets/搜索别名_v1.md`, the colloquial writings nothing else records.

The reader stops at 「官方来源」. `menkyo-quiz/tools/check_glossary.py` says it
stops at the 官方核对结果 tables and does not: those tables' header row also
begins `| 日文 `, which switches its term-table flag back on, and five of their
rows come back as terms. Here the term sections are taken by name instead, and
the record tables are read deliberately, by their own shapes.

Stdlib only, like every other tool in here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


class BuildError(Exception):
    pass


# This file is mirrored, byte for byte, into `menkyo-quiz/tools/` — the way
# the glossary itself already is. So it finds its inputs rather than assuming
# a layout: `assets/` in the app repository, `docs/` in the question
# repository, where the pack is actually generated.
LAYOUTS = [
    ("assets/术语表_v7_JA-ZH-EN-VI-PT.md", "assets/搜索别名_v1.md"),
    ("docs/glossary-v7.md", "docs/search-aliases-v1.md"),
]


def inputs() -> tuple[Path, Path]:
    here = Path(__file__).resolve()
    for root in [*here.parents, here.parents[2].parent / "menkyo"]:
        for glossary, aliases in LAYOUTS:
            if (root / glossary).exists() and (root / aliases).exists():
                return root / glossary, root / aliases
    raise BuildError(
        "no glossary and alias file found above " + str(here.parent)
        + " — expected " + " or ".join(g for g, _ in LAYOUTS)
    )


def dist_manifest() -> Path | None:
    here = Path(__file__).resolve()
    for root in here.parents:
        if (root / "dist" / "manifest.json").exists():
            return root / "dist" / "manifest.json"
    sibling = here.parents[2].parent / "menkyo-quiz" / "dist" / "manifest.json"
    return sibling if sibling.exists() else None


# The glossary's nine term sections, in its own order. Anything after them is
# provenance and record-keeping, not terms.
TERM_SECTIONS = [
    "信号", "标志标示", "道路·场所", "车辆", "驾驶操作",
    "距离·特性", "驾照·制度", "人", "乘车·装载",
]

# The glossary's column order, and the pack's language codes.
LANGS = ["ja", "zh-Hans", "en", "vi", "pt-BR"]
COLUMN_LANG = {0: "ja", 1: "zh-Hans", 2: "en", 3: "vi", 4: "pt-BR"}
# How the record tables name a language.
RECORD_LANG = {"ZH": "zh-Hans", "EN": "en", "VI": "vi", "PT": "pt-BR"}

SPLIT = re.compile(r"[；;、]")
# 「（NPA）」「(NPA 正文)」 — the source a recorded wording is credited to.
SOURCE = re.compile(r"[（(][^（()）]*[)）]\s*$")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def sections(text: str) -> dict[str, list[str]]:
    """The file split by its `##` headings, `###` kept inside its `##`."""
    out: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out.setdefault(current, [])
        elif line.startswith("### "):
            current = line[4:].strip()
            out.setdefault(current, [])
        elif current:
            out[current].append(line)
    return out


def rows(lines: list[str], width: int) -> list[list[str]]:
    return [
        c for c in (cells(line) for line in lines
                    if line.startswith("| ") and not line.startswith("| ---"))
        if len(c) == width and c[0] and c[0] != "日文"
    ]


# --- the glossary ----------------------------------------------------------

def glossary_terms(by_section: dict[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    """Every term section's rows, as {japanese: {lang: [bound translation]}}."""
    terms: dict[str, dict[str, list[str]]] = {}
    for name in TERM_SECTIONS:
        if name not in by_section:
            raise BuildError(f"the glossary has no 「{name}」 section")
        for row in rows(by_section[name], 5):
            if row[0] in terms:
                continue          # the glossary's own rule 2: one row per term
            terms[row[0]] = {COLUMN_LANG[i]: [row[i]] for i in range(5)}
    if not terms:
        raise BuildError("no terms read from the glossary")
    return terms


def recorded(by_section: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    """What the glossary set aside, as (japanese, lang, wording).

    Four tables, four shapes. A wording carrying its source in brackets keeps
    only the wording.
    """
    out: list[tuple[str, str, str]] = []

    # | 日文 | 语言 | v6 | v7 | 依据 |  — the wording v7 moved away from.
    for row in rows(by_section.get("改从官方译法（v6 → v7）", []), 5):
        if row[1] in RECORD_LANG:
            out.append((row[0], RECORD_LANG[row[1]], row[2]))

    # | 日文 | 选定 | 弃用（及出处） | 理由 |  — 选定 carries the language.
    for row in rows(by_section.get("官方内部冲突，本表选定", []), 4):
        head = row[1].split(":", 1)
        if len(head) != 2 or head[0].strip() not in RECORD_LANG:
            continue              # 徐行's row names a sign face, not a wording
        lang = RECORD_LANG[head[0].strip()]
        for part in SPLIT.split(row[2]):
            out.append((row[0], lang, part))

    # | 日文 | 语言 | 本表 | 官方 | 不改从的理由 |
    for row in rows(by_section.get("有意不改从官方（规则7要求记录理由）", []), 5):
        if row[1] in RECORD_LANG:
            out.append((row[0], RECORD_LANG[row[1]], row[3]))

    # | 日文 | 本表 ZH | NPA 官方中文 |
    for row in rows(by_section.get("官方译法与 ZH 列不一致（**未改**，待定）", []), 3):
        out.append((row[0], "zh-Hans", row[2]))

    return [(ja, lang, clean(w)) for ja, lang, w in out if clean(w)]


def clean(wording: str) -> str:
    """One wording, without its credited source or its markdown emphasis."""
    wording = wording.replace("**", "").strip()
    while True:
        stripped = SOURCE.sub("", wording).strip()
        if stripped == wording:
            return wording.strip(" 。.")
        wording = stripped


# --- the alias file --------------------------------------------------------

def aliases(text: str) -> tuple[list[tuple[str, str, str]], set[tuple[str, str]]]:
    by_section = sections(text)
    out: list[tuple[str, str, str]] = []

    for row in rows(by_section.get("别名", []), 5):
        for i in range(1, 5):
            for part in SPLIT.split(row[i]):
                if part.strip():
                    out.append((row[0], COLUMN_LANG[i], part.strip()))

    for row in rows(by_section.get("日文别名", []), 2):
        for part in SPLIT.split(row[1]):
            if part.strip():
                out.append((row[0], "ja", part.strip()))

    banned = {
        (RECORD_LANG[row[1]], row[0])
        for row in rows(by_section.get("禁用", []), 3)
        if row[1] in RECORD_LANG
    }
    return out, banned


# --- the document ----------------------------------------------------------

def fold(text: str) -> str:
    """The app's normalisation, so the generator sees what the device will.

    NFKC, case-folded, then combining marks dropped — the same widening
    `SearchNormalizer.fold` does on iOS (design.md D2).
    """
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def build(glossary_text: str, alias_text: str, licence: dict) -> dict:
    by_section = sections(glossary_text)
    terms = glossary_terms(by_section)
    extra, banned = aliases(alias_text)

    for japanese, _, _ in extra:
        if japanese not in terms:
            raise BuildError(
                f"搜索别名_v1.md names 「{japanese}」, which is in no glossary row"
            )

    for japanese, lang, wording in recorded(by_section) + extra:
        if japanese not in terms:
            continue              # a record row naming a pair, e.g. 標識 / 標示
        forms = terms[japanese][lang]
        if (lang, wording) in banned:
            continue
        if not any(fold(wording) == fold(f) for f in forms):
            forms.append(wording)

    groups = []
    for japanese, forms in terms.items():
        bound = terms[japanese]["ja"][0]
        if bound != japanese:
            raise BuildError(f"「{japanese}」: position 0 is not the glossary's own term")
        groups.append({"id": japanese, "forms": {lang: forms[lang] for lang in LANGS}})

    return {"license": licence, "groups": groups}


def dumps(document: dict) -> bytes:
    """Byte-identical between runs: sorted keys, no spare whitespace."""
    return json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate(document: dict, glossary_text: str) -> list[str]:
    """A terms document against the glossary, whoever emitted it.

    This is the check the question repository's CI runs over the pack it is
    about to publish: the pack is generated there, and a pack whose position 0
    has drifted would have the app's matched-term line teaching a wording the
    glossary does not use.
    """
    terms = glossary_terms(sections(glossary_text))
    problems: list[str] = []
    for group in document.get("groups", []):
        japanese = group.get("id", "")
        if japanese not in terms:
            problems.append(f"group 「{japanese}」 is in no glossary row")
            continue
        for lang in LANGS:
            forms = group.get("forms", {}).get(lang) or []
            bound = terms[japanese][lang][0]
            if not forms:
                problems.append(f"「{japanese}」 {lang}: no writing at all")
            elif forms[0] != bound:
                problems.append(
                    f"「{japanese}」 {lang}: position 0 is 「{forms[0]}」, "
                    f"the glossary binds 「{bound}」"
                )
    missing = set(terms) - {g.get("id") for g in document.get("groups", [])}
    problems.extend(f"「{japanese}」 has no group" for japanese in sorted(missing))
    return problems


def licence_statement() -> dict:
    """The statement every pack carries, read from the published manifest so
    there is one copy of it and not two. `build_packs.py` passes its own
    `LICENSE` instead and never calls this."""
    if manifest := dist_manifest():
        return json.loads(manifest.read_text(encoding="utf-8"))["license"]
    raise BuildError(
        "no licence statement to copy: no dist/manifest.json found. "
        "The terms pack carries the same statement as every other pack."
    )


def groups(licence: dict) -> dict:
    """The terms document, for a caller that already knows the licence —
    `menkyo-quiz/tools/build_packs.py`, which emits it as the `terms` pack."""
    glossary, aliases = inputs()
    return build(glossary.read_text(encoding="utf-8"),
                 aliases.read_text(encoding="utf-8"), licence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="write the document here")
    parser.add_argument("--check", type=Path, help="fail if this file is not what we would write")
    parser.add_argument("--validate", type=Path,
                        help="check this terms document against the glossary")
    parser.add_argument("--stats", action="store_true", help="print what was built")
    args = parser.parse_args()

    if args.validate:
        problems = validate(
            json.loads(args.validate.read_text(encoding="utf-8")),
            inputs()[0].read_text(encoding="utf-8"),
        )
        for problem in problems:
            print(f"build_search_terms: {args.validate.name}: {problem}", file=sys.stderr)
        if problems:
            return 1
        print(f"{args.validate} agrees with the glossary")
        if not (args.out or args.check or args.stats):
            return 0

    try:
        glossary, aliases = inputs()
        document = build(
            glossary.read_text(encoding="utf-8"),
            aliases.read_text(encoding="utf-8"),
            licence_statement(),
        )
    except BuildError as error:
        print(f"build_search_terms: {error}", file=sys.stderr)
        return 1

    payload = dumps(document)

    if args.stats:
        extra = sum(len(f) - 1 for g in document["groups"] for f in g["forms"].values())
        print(f"{len(document['groups'])} groups, {extra} writings beyond the bound "
              f"translations, {len(payload)} bytes")

    if args.check:
        if not args.check.exists():
            print(f"build_search_terms: {args.check} does not exist", file=sys.stderr)
            return 1
        if args.check.read_bytes() != payload:
            print(f"build_search_terms: {args.check} is stale", file=sys.stderr)
            return 1
        print(f"{args.check} is up to date")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(payload)
        print(f"{len(document['groups'])} groups -> {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
