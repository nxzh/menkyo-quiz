#!/usr/bin/env python3
"""Build the content packs the Menkyo app downloads.

Reads questions/karimen/*.json and data/taxonomy.*.json, writes dist/:

    manifest.json           what the app fetches first
    core-<tier>.json        language-neutral: answers, chapter, citation, trap
    <lang>-<tier>.json      question + explanation only, no answers
    taxonomy.json           chapter and section names in five languages
    terms.json              the search vocabulary, five languages in one file

Nothing here is encrypted. The questions are public, so a cipher over a
plaintext published beside it protects nothing; the purchase buys how much of
the bank the app shows, and the app enforces that.

Invariants this script enforces (CLAUDE.md 3 and 4):

  * no language pack carries an answer, or any other core field
  * every core id is present in every language pack
  * output is byte-identical for unchanged input, so an unchanged pack is
    never re-downloaded
  * the manifest and every pack carry the licence the content is published
    under, so a downloaded pack states its own terms

Usage:
    python3 tools/build_packs.py              # write dist/
    python3 tools/build_packs.py --check      # verify dist/ matches the input
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import build_search_terms

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "questions"
DATA = ROOT / "data"
DIST = ROOT / "dist"

REPO_RAW = "https://raw.githubusercontent.com/nxzh/menkyo-quiz/main/dist"

# repo i18n key -> BCP-47 tag the app uses
LANGS = {"ja": "ja", "zh": "zh-Hans", "en": "en", "vi": "vi", "pt": "pt-BR"}
LANG_ORDER = ["ja", "en", "zh-Hans", "vi", "pt-BR"]

FREE_COUNT = 120          # design-spec §7 item 4 (provisional)
ANSWER_BALANCE_SLACK = 4  # |true - false| in the free tier

LAW_REVISION_DATE = "2026-09-01"  # 施行令 revision the bank reflects
MIN_APP_VERSION = "1.0.0"

# The terms the published bytes come under, written once and emitted into the
# manifest *and* into every pack: a pack is fetched by anonymous GET and gets
# copied around on its own, and a licence that lives only in a sibling file is
# a licence nobody carries. `signs/index.csv` holds artwork provenance per file.
LICENSE = {
    "content": {
        "id": "CC-BY-NC-SA-4.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "attribution": "menkyo-quiz © 2026 Naixiao Zhang — CC BY-NC-SA 4.0",
        "source": "https://github.com/nxzh/menkyo-quiz",
    },
    "artwork": {
        "id": "PD-Japan-exempt",
        "note": "標識令 catalogue reproductions; per-file provenance in signs/index.csv",
    },
    "tools": {"id": "MIT"},
}


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- input


def load_questions() -> list[dict]:
    files = sorted(glob.glob(str(QUESTIONS / "*" / "*.json")))
    if not files:
        raise BuildError(f"no question files under {QUESTIONS}")
    out: list[dict] = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            batch = json.load(fh)
        if not isinstance(batch, list):
            raise BuildError(f"{path}: expected a list of questions")
        out.extend(batch)
    ids = [q["id"] for q in out]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise BuildError(f"duplicate question ids: {dupes}")
    return sorted(out, key=lambda q: q["id"])


def load_exams() -> list[str]:
    """The exams this bank can serve, declared rather than inferred."""
    path = DATA / "exams.json"
    if not path.exists():
        raise BuildError(f"missing {path}")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return [exam["code"] for exam in doc["exams"] if exam.get("ready")]


def load_taxonomy() -> dict[str, dict]:
    tax: dict[str, dict] = {}
    for lang in LANG_ORDER:
        path = DATA / f"taxonomy.{lang}.json"
        if not path.exists():
            raise BuildError(f"missing taxonomy for {lang}: {path}")
        with open(path, encoding="utf-8") as fh:
            tax[lang] = json.load(fh)
    base = taxonomy_codes(tax["ja"])
    for lang, doc in tax.items():
        if taxonomy_codes(doc) != base:
            raise BuildError(f"taxonomy.{lang}.json does not match taxonomy.ja.json key for key")
        for chapter in doc["chapters"]:
            if not chapter["name"].strip():
                raise BuildError(f"taxonomy.{lang}.json: empty name for chapter {chapter['code']}")
            for section in chapter["sections"]:
                if not section["name"].strip():
                    raise BuildError(
                        f"taxonomy.{lang}.json: empty name for section {section['code']}"
                    )
    return tax


def taxonomy_codes(doc: dict) -> list[str]:
    codes = []
    for chapter in doc["chapters"]:
        codes.append(chapter["code"])
        codes.extend(s["code"] for s in chapter["sections"])
    return codes


def section_of(kp: str) -> str:
    parts = kp.split("-")
    return "-".join(parts[:2]) if len(parts) > 1 else parts[0]


def chapter_index(tax: dict) -> tuple[dict[str, str], list[str]]:
    """section code -> chapter code, and the section codes in 教則 order."""
    section_to_chapter: dict[str, str] = {}
    order: list[str] = []
    for chapter in tax["ja"]["chapters"]:
        for section in chapter["sections"]:
            section_to_chapter[section["code"]] = chapter["code"]
            order.append(section["code"])
    return section_to_chapter, order


# ---------------------------------------------------------------- tiering


def assign_tiers(questions: list[dict], section_order: list[str]) -> dict[str, str]:
    """Pick the free questions: round-robin over the 教則 sections, image
    question first in an image-bearing section, then balance ○/× by swapping
    within a section. Deterministic - it depends only on question ids."""
    by_section: dict[str, list[dict]] = {code: [] for code in section_order}
    for q in questions:
        by_section[section_of(q["kp"])].append(q)

    # an image-bearing section contributes its artwork to the free tier first,
    # and that one question is then held back from the ○/× balancing swap: a
    # section whose only picked artwork got swapped out would leave the free
    # tier showing no picture at all for a chapter that has them.
    artwork_anchors: set[str] = set()
    for code, items in by_section.items():
        with_image = sorted((q for q in items if "image" in q), key=lambda q: q["id"])
        without = sorted((q for q in items if "image" not in q), key=lambda q: q["id"])
        if with_image:
            artwork_anchors.add(with_image[0]["id"])
            by_section[code] = [with_image[0]] + without + with_image[1:]
        else:
            by_section[code] = without

    picked: list[dict] = []
    cursor = {code: 0 for code in section_order}
    while len(picked) < FREE_COUNT:
        progressed = False
        for code in section_order:
            if len(picked) == FREE_COUNT:
                break
            i = cursor[code]
            if i < len(by_section[code]):
                picked.append(by_section[code][i])
                cursor[code] = i + 1
                progressed = True
        if not progressed:
            raise BuildError(f"only {len(picked)} questions available for a free tier of {FREE_COUNT}")

    picked_ids = {q["id"] for q in picked}
    # balance ○ / ×: swap a picked question for an unpicked one of the other
    # answer in the same section, lowest id first
    def imbalance(sel):
        t = sum(1 for q in sel if q["answer"])
        return t - (len(sel) - t)

    guard = 0
    while abs(imbalance(picked)) > ANSWER_BALANCE_SLACK:
        guard += 1
        if guard > FREE_COUNT:
            raise BuildError("cannot balance the free tier's answers")
        over = imbalance(picked) > 0  # too many true
        swapped = False
        for idx, q in enumerate(picked):
            if q["answer"] is not over:
                continue
            if q["id"] in artwork_anchors:
                continue
            code = section_of(q["kp"])
            for cand in by_section[code]:
                if cand["id"] not in picked_ids and cand["answer"] is not q["answer"]:
                    picked_ids.discard(q["id"])
                    picked_ids.add(cand["id"])
                    picked[idx] = cand
                    swapped = True
                    break
            if swapped:
                break
        if not swapped:
            raise BuildError("no swap available to balance the free tier's answers")

    return {q["id"]: ("free" if q["id"] in picked_ids else "full") for q in questions}


# ---------------------------------------------------------------- packs


def core_entry(q: dict, tier: str, section_to_chapter: dict[str, str]) -> dict:
    section = section_of(q["kp"])
    entry = {
        "id": q["id"],
        "chapter": section_to_chapter[section],
        "section": section,
        "kp": q["kp"],
        "category": q["category"],
        "source": q["source"],
        "question_type": q["question_type"],
        "answer": q["answer"],
        "trap_type": q["trap_type"],
        "difficulty": q["difficulty"],
        "exam_scope": q["exam_scope"],
        "tier": tier,
    }
    if "image" in q:
        entry["image"] = {"sign_no": q["image"]["sign_no"], "file": q["image"]["file"]}
    if q.get("verify"):
        entry["verify"] = True
    return entry


def lang_entry(q: dict, lang: str) -> dict:
    if lang == "ja":
        return {"id": q["id"], "question": q["question_ja"], "explanation": q["explanation_ja"]}
    repo_key = next(k for k, v in LANGS.items() if v == lang)
    block = q["i18n"][repo_key]
    return {"id": q["id"], "question": block["question"], "explanation": block["explanation"]}


def dumps(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=None, separators=(",", ":"),
                       sort_keys=True) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha256(payload: bytes) -> str:
    """The pack's content hash with the licence statement taken out, so a
    licence edit is never mistaken for a content edit (design-spec §5.4)."""
    doc = json.loads(payload)
    doc.pop("license", None)
    return sha256(dumps(doc))


# ---------------------------------------------------------------- build


def release_notes(previous_manifest, content_version, counts, changed,
                  law_revision_date, hidden_ids, text_changed, license_changed):
    """The "what changed" note the app shows, in all five languages.

    Written from what actually moved between the two manifests rather than by
    hand, so a note can never claim something the packs do not say. Older notes
    are carried over, newest first (design-spec §5.4).

    `changed` is which packs' bytes moved — that is what a version bump and a
    re-download follow. `text_changed` is which of them moved because their
    *questions* did: editing the licence statement rewrites every pack, and a
    note claiming corrected translations on that day would be a lie.
    """
    previous_notes = (previous_manifest or {}).get("notes", [])
    if not changed:
        return previous_notes

    old_counts = (previous_manifest or {}).get("counts", {})
    added = counts["total"] - old_counts.get("total", 0)
    withdrawn = len(hidden_ids) - len(((previous_manifest or {}).get("hidden_ids", [])))
    # Only the language packs carry a language in their id. `terms` is one
    # file for all five, so it is reported on its own line, not as a list of
    # languages whose translations moved.
    langs = sorted({pid.rsplit("-", 1)[0] for pid in text_changed
                    if not pid.startswith("core") and pid not in ("taxonomy", "terms")})
    # `text_changed`, not `changed`: a licence edit rewrites every pack's bytes
    # without moving a word of the vocabulary, and the note must not claim it
    # did — the same distinction the translation line already makes. A terms
    # pack the previous manifest did not carry counts too, or the release that
    # first publishes the vocabulary would have nothing to say for itself.
    terms_is_new = previous_manifest is not None and not any(
        p["id"] == "terms" for p in previous_manifest.get("packs", []))
    terms_changed = previous_manifest is not None and (
        "terms" in text_changed or terms_is_new)
    law_changed = (previous_manifest or {}).get("law_revision_date") != law_revision_date

    templates = {
        "ja": {"added": "問題を{n}問追加", "withdrawn": "問題を{n}問取り下げ",
               "translations": "訳文を修正（{langs}）", "law": "{date}時点の法令に対応",
               "license": "ライセンス表記を更新", "first": "最初のリリース", "terms": "検索の語彙を更新"},
        "en": {"added": "{n} questions added", "withdrawn": "{n} questions withdrawn",
               "translations": "Translations corrected ({langs})",
               "law": "Reflects the law as of {date}",
               "license": "Licence statement updated", "first": "First release", "terms": "Search vocabulary updated"},
        "zh-Hans": {"added": "新增 {n} 道题", "withdrawn": "撤回 {n} 道题",
                    "translations": "修正译文（{langs}）", "law": "对应 {date} 的法令",
                    "license": "更新许可证声明", "first": "首次发布", "terms": "更新搜索词表"},
        "vi": {"added": "Thêm {n} câu hỏi", "withdrawn": "Rút {n} câu hỏi",
               "translations": "Sửa bản dịch ({langs})",
               "law": "Theo luật tính đến {date}",
               "license": "Cập nhật thông tin giấy phép", "first": "Phát hành lần đầu", "terms": "Cập nhật từ vựng tìm kiếm"},
        "pt-BR": {"added": "{n} questões adicionadas", "withdrawn": "{n} questões retiradas",
                  "translations": "Traduções corrigidas ({langs})",
                  "law": "Reflete a lei em {date}",
                  "license": "Declaração de licença atualizada", "first": "Primeira versão", "terms": "Vocabulário de busca atualizado"},
    }
    names = {"ja": {"ja": "日本語", "en": "英語", "zh-Hans": "中国語", "vi": "ベトナム語",
                    "pt-BR": "ポルトガル語"},
             "en": {"ja": "Japanese", "en": "English", "zh-Hans": "Chinese",
                    "vi": "Vietnamese", "pt-BR": "Portuguese"},
             "zh-Hans": {"ja": "日语", "en": "英语", "zh-Hans": "中文", "vi": "越南语",
                         "pt-BR": "葡萄牙语"},
             "vi": {"ja": "tiếng Nhật", "en": "tiếng Anh", "zh-Hans": "tiếng Trung",
                    "vi": "tiếng Việt", "pt-BR": "tiếng Bồ Đào Nha"},
             "pt-BR": {"ja": "japonês", "en": "inglês", "zh-Hans": "chinês",
                       "vi": "vietnamita", "pt-BR": "português"}}

    items = {}
    for lang, words in templates.items():
        lines = []
        if previous_manifest is None:
            lines.append(words["first"])
        if added > 0:
            lines.append(words["added"].format(n=added))
        if withdrawn > 0:
            lines.append(words["withdrawn"].format(n=withdrawn))
        if langs and previous_manifest is not None:
            readable = "、".join(names[lang][l] for l in langs) if lang in ("ja", "zh-Hans") \
                else ", ".join(names[lang][l] for l in langs)
            lines.append(words["translations"].format(langs=readable))
        if law_changed:
            lines.append(words["law"].format(date=law_revision_date))
        if terms_changed:
            lines.append(words["terms"])
        if license_changed and previous_manifest is not None:
            lines.append(words["license"])
        items[lang] = lines

    note = {"version": content_version, "date": date.today().isoformat(), "items": items}
    return [note] + previous_notes


def build(dest: Path) -> dict:
    questions = load_questions()
    tax = load_taxonomy()
    section_to_chapter, section_order = chapter_index(tax)

    for q in questions:
        section = section_of(q["kp"])
        if section not in section_to_chapter:
            raise BuildError(
                f"{q['id']}: kp {q['kp']} has no section in data/taxonomy.ja.json"
            )

    tiers = assign_tiers(questions, section_order)

    previous = {}
    prev = None
    prev_path = dest / "manifest.json"
    if prev_path.exists():
        with open(prev_path, encoding="utf-8") as fh:
            prev = json.load(fh)
        previous = {p["id"]: p for p in prev.get("packs", [])}
        prev_version = prev.get("content_version", 0)
        prev_generated = prev.get("generated_at")
    else:
        prev_version = 0
        prev_generated = None

    # ---- bodies (without their version, which depends on whether they changed)
    bodies: dict[str, tuple[str, str, bytes]] = {}  # id -> (kind, tier, payload)
    for tier in ("free", "full"):
        ids = [q["id"] for q in questions if tiers[q["id"]] == tier]
        core = [core_entry(q, tiers[q["id"]], section_to_chapter)
                for q in questions if tiers[q["id"]] == tier]
        bodies[f"core-{tier}"] = ("core", tier,
                                  dumps({"license": LICENSE, "questions": core}))
        for lang in LANG_ORDER:
            items = [lang_entry(q, lang) for q in questions if tiers[q["id"]] == tier]
            if len(items) != len(ids):
                raise BuildError(f"{lang}-{tier}: {len(items)} texts for {len(ids)} questions")
            bodies[f"{lang}-{tier}"] = ("lang", tier,
                                        dumps({"license": LICENSE, "lang": lang,
                                               "questions": items}))
    # The published taxonomy carries only what the bank uses. data/taxonomy.*
    # holds every 教則 chapter and section so a question can cite any of them,
    # but shipping a chapter with no questions would put an empty row on Study
    # home — a chapter the reader can open and find nothing in.
    used_sections = {section_of(q["kp"]) for q in questions}
    used_chapters = {section_to_chapter[code] for code in used_sections}
    shipped = {
        lang: {
            "chapters": [
                {**chapter,
                 "sections": [s for s in chapter["sections"] if s["code"] in used_sections]}
                for chapter in doc["chapters"] if chapter["code"] in used_chapters
            ]
        }
        for lang, doc in tax.items()
    }
    for lang, doc in shipped.items():
        empty = [c["code"] for c in doc["chapters"] if not c["sections"]]
        if empty:
            raise BuildError(f"taxonomy.{lang}: chapter(s) {empty} would ship with no sections")
    bodies["taxonomy"] = ("taxonomy", "free",
                          dumps({"license": LICENSE, "languages": shipped}))

    # The search vocabulary: one multilingual file, free tier, generated from
    # docs/glossary-v7.md and docs/search-aliases-v1.md. Position 0 of every
    # language is the glossary's bound translation, and the generator fails
    # rather than publish a pack where it has drifted — the app's matched-term
    # line names position 0, so a drifted one would teach a wording the
    # glossary does not use.
    try:
        terms = build_search_terms.groups(LICENSE)
    except build_search_terms.BuildError as error:
        raise BuildError(f"terms: {error}") from error
    bodies["terms"] = ("terms", "free", dumps(terms))

    # ---- content_version advances only when some pack's bytes changed
    changed = {
        pid for pid, (_k, _t, payload) in bodies.items()
        if previous.get(pid, {}).get("payload_sha256") != sha256(payload)
    }
    content_version = prev_version + 1 if changed else prev_version or 1

    # What moved *inside* a pack, licence aside. A manifest written before the
    # licence statement existed carries no text hash, so nothing is claimed
    # about it: unknown is not "changed".
    text_hashes = {pid: text_sha256(payload) for pid, (_k, _t, payload) in bodies.items()}
    text_changed = {
        pid for pid, digest in text_hashes.items()
        if "text_sha256" in previous.get(pid, {})
        and previous[pid]["text_sha256"] != digest
    }
    license_changed = (prev or {}).get("license") != LICENSE

    packs = []
    files: dict[str, bytes] = {}
    for pid in sorted(bodies):
        kind, tier, payload = bodies[pid]
        version = content_version if pid in changed else previous[pid]["version"]
        name = f"{pid}.json"
        files[name] = payload
        packs.append({
            "id": pid,
            "kind": kind,
            "tier": tier,
            "lang": None if kind != "lang" else pid.rsplit("-", 1)[0],
            "version": version,
            "payload_sha256": sha256(payload),
            "sha256": sha256(payload),
            "text_sha256": text_hashes[pid],
            "bytes": len(payload),
            "url": f"{REPO_RAW}/{name}",
        })

    notes = release_notes(previous_manifest=prev if prev_version else None,
                          content_version=content_version,
                          counts={"free": sum(1 for t in tiers.values() if t == "free"),
                                  "full": sum(1 for t in tiers.values() if t == "full"),
                                  "total": len(questions)},
                          changed=changed,
                          law_revision_date=LAW_REVISION_DATE,
                          hidden_ids=[],
                          text_changed=text_changed,
                          license_changed=license_changed)

    manifest = {
        "notes": notes,
        "license": LICENSE,
        "content_version": content_version,
        "min_app_version": MIN_APP_VERSION,
        "law_revision_date": LAW_REVISION_DATE,
        # only moves when the content does, so a rebuild of unchanged input
        # stays byte-identical on any later day
        "generated_at": date.today().isoformat() if changed or not prev_generated else prev_generated,
        "hidden_ids": [],
        "counts": {
            "free": sum(1 for t in tiers.values() if t == "free"),
            "full": sum(1 for t in tiers.values() if t == "full"),
            "total": len(questions),
        },
        "languages": LANG_ORDER,
        "exams": load_exams(),
        "packs": packs,
    }
    files["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    check(manifest, bodies, files, questions, tiers, section_to_chapter)
    return {"manifest": manifest, "files": files, "questions": questions, "tiers": tiers}


# ---------------------------------------------------------------- assertions


def check(manifest, bodies, files, questions, tiers, section_to_chapter) -> None:
    core_ids = {tier: {q["id"] for q in questions if tiers[q["id"]] == tier}
                for tier in ("free", "full")}

    if manifest.get("license") != LICENSE:
        raise BuildError("the manifest does not carry the licence statement")

    for pid, (kind, tier, payload) in bodies.items():
        doc = json.loads(payload)
        if doc.get("license") != LICENSE:
            raise BuildError(f"{pid}: pack does not carry the licence statement")
        if kind == "lang":
            leaked = [q["id"] for q in doc["questions"] if set(q) - {"id", "question", "explanation"}]
            if leaked:
                raise BuildError(f"{pid}: language pack carries core fields: {leaked[:3]}")
            if "answer" in payload.decode("utf-8"):
                raise BuildError(f"{pid}: the string 'answer' appears in a language pack")
            if {q["id"] for q in doc["questions"]} != core_ids[tier]:
                raise BuildError(f"{pid}: ids do not match the {tier} core pack")
        elif kind == "core":
            if {q["id"] for q in doc["questions"]} != core_ids[tier]:
                raise BuildError(f"{pid}: ids do not match the {tier} tier")
            if any("question" in q or "explanation" in q for q in doc["questions"]):
                raise BuildError(f"{pid}: core pack carries question text")

    for entry in manifest["packs"]:
        name = None
        for fname, data in files.items():
            if sha256(data) == entry["sha256"]:
                name = fname
                break
        if name is None:
            raise BuildError(f"{entry['id']}: manifest sha256 matches no emitted file")
        if not entry["url"]:
            raise BuildError(f"{entry['id']}: every pack must carry a URL")

    free = [q for q in questions if tiers[q["id"]] == "free"]
    if len(free) != FREE_COUNT:
        raise BuildError(f"free tier is {len(free)}, expected {FREE_COUNT}")
    chapters_all = {section_to_chapter[section_of(q["kp"])] for q in questions}
    chapters_free = {section_to_chapter[section_of(q["kp"])] for q in free}
    if chapters_all != chapters_free:
        raise BuildError(f"free tier misses chapters: {sorted(chapters_all - chapters_free)}")
    true = sum(1 for q in free if q["answer"])
    if abs(true - (len(free) - true)) > ANSWER_BALANCE_SLACK:
        raise BuildError(f"free tier answer balance is {true}/{len(free) - true}")


# ---------------------------------------------------------------- output


def write(dest: Path, files: dict[str, bytes]) -> None:
    # A previous build encrypted the paid packs into p/; nothing writes there now.
    if (dest / "p").exists():
        shutil.rmtree(dest / "p")
    dest.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify dist/ is what the current input produces")
    ap.add_argument("--dest", default=str(DIST))
    args = ap.parse_args()

    dest = Path(args.dest)
    try:
        result = build(dest)
    except BuildError as exc:
        print(f"build_packs: {exc}", file=sys.stderr)
        return 1

    files = result["files"]
    manifest = result["manifest"]

    if args.check:
        problems = []
        for name, data in files.items():
            path = dest / name
            if not path.exists():
                problems.append(f"missing {name}")
            elif path.read_bytes() != data:
                problems.append(f"stale {name}")
        on_disk = {
            str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()
        }
        for extra in sorted(on_disk - set(files)):
            problems.append(f"unexpected {extra}")
        if problems:
            for p in problems:
                print(f"build_packs --check: {p}", file=sys.stderr)
            print("run: python3 tools/build_packs.py", file=sys.stderr)
            return 1
        print(f"dist/ is current — content_version {manifest['content_version']}, "
              f"{manifest['counts']['free']} free / {manifest['counts']['full']} full")
        return 0

    write(dest, files)
    print(f"content_version {manifest['content_version']} → {dest}")
    for entry in manifest["packs"]:
        print(f"  {entry['id']:<16} v{entry['version']:<3} {entry['bytes']:>8}B  {entry['tier']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
