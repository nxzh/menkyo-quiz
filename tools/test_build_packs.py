#!/usr/bin/env python3
"""Tests for tools/build_packs.py.

Run: python3 -m unittest discover -s tools -p 'test_*.py'
"""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import build_packs as bp


class BuildTestCase(unittest.TestCase):
    """Builds once against the real bank; every test reads that result."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="menkyo-packs-"))
        cls.result = bp.build(cls.tmp)
        bp.write(cls.tmp, cls.result["files"])
        cls.manifest = cls.result["manifest"]
        cls.questions = cls.result["questions"]
        cls.tiers = cls.result["tiers"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def pack(self, pack_id):
        return next(p for p in self.manifest["packs"] if p["id"] == pack_id)

    def payload(self, pack_id):
        entry = self.pack(pack_id)
        for name, data in self.result["files"].items():
            if bp.sha256(data) == entry["sha256"]:
                if entry["tier"] == "full":
                    data = bp.decrypt(bp.pack_key()[0], data)
                return json.loads(data)
        self.fail(f"no file for {pack_id}")


class TestTiering(BuildTestCase):
    def test_free_tier_size_and_balance(self):
        free = [q for q in self.questions if self.tiers[q["id"]] == "free"]
        self.assertEqual(len(free), bp.FREE_COUNT)
        true = sum(1 for q in free if q["answer"])
        self.assertLessEqual(abs(true - (len(free) - true)), bp.ANSWER_BALANCE_SLACK)

    def test_every_chapter_is_represented_in_the_free_tier(self):
        tax = bp.load_taxonomy()
        section_to_chapter, _ = bp.chapter_index(tax)
        chapters = {section_to_chapter[bp.section_of(q["kp"])] for q in self.questions}
        free = {
            section_to_chapter[bp.section_of(q["kp"])]
            for q in self.questions
            if self.tiers[q["id"]] == "free"
        }
        self.assertEqual(chapters, free)

    def test_image_sections_contribute_artwork_to_the_free_tier(self):
        by_section = {}
        for q in self.questions:
            by_section.setdefault(bp.section_of(q["kp"]), []).append(q)
        for section, items in by_section.items():
            if not any("image" in q for q in items):
                continue
            free = [q for q in items if self.tiers[q["id"]] == "free"]
            self.assertTrue(
                any("image" in q for q in free),
                f"section {section} has artwork but none of it is free",
            )

    def test_tiering_is_stable(self):
        tax = bp.load_taxonomy()
        _, order = bp.chapter_index(tax)
        again = bp.assign_tiers(bp.load_questions(), order)
        self.assertEqual(again, self.tiers)

    def test_tiering_ignores_input_order(self):
        tax = bp.load_taxonomy()
        _, order = bp.chapter_index(tax)
        shuffled = list(reversed(bp.load_questions()))
        self.assertEqual(bp.assign_tiers(shuffled, order), self.tiers)


class TestPackSplit(BuildTestCase):
    def test_language_packs_carry_no_answer(self):
        for lang in bp.LANG_ORDER:
            for tier in ("free", "full"):
                doc = self.payload(f"{lang}-{tier}")
                for q in doc["questions"]:
                    self.assertEqual(set(q), {"id", "question", "explanation"})

    def test_core_pack_carries_no_text(self):
        for tier in ("free", "full"):
            for q in self.payload(f"core-{tier}")["questions"]:
                self.assertNotIn("question", q)
                self.assertNotIn("explanation", q)
                self.assertIn("answer", q)

    def test_every_core_id_is_in_every_language_pack(self):
        for tier in ("free", "full"):
            core = {q["id"] for q in self.payload(f"core-{tier}")["questions"]}
            self.assertTrue(core)
            for lang in bp.LANG_ORDER:
                ids = {q["id"] for q in self.payload(f"{lang}-{tier}")["questions"]}
                self.assertEqual(core, ids, f"{lang}-{tier}")

    def test_answer_leakage_is_caught(self):
        """The assertion, not the happy path: a hand-built leaky pack must fail."""
        bodies = {
            "en-free": ("lang", "free", bp.dumps({"lang": "en", "questions": [
                {"id": "K1-1-001", "question": "q", "explanation": "e", "answer": True}
            ]}))
        }
        files = {"en-free.json": bodies["en-free"][2]}
        manifest = {"packs": [{"id": "en-free", "kind": "lang", "tier": "free",
                               "sha256": bp.sha256(files["en-free.json"]), "url": "x"}]}
        questions = [{"id": "K1-1-001", "kp": "1-1", "answer": True}]
        with self.assertRaises(bp.BuildError):
            bp.check(manifest, bodies, files, questions, {"K1-1-001": "free"},
                     bp.DEV_KEY, {"1-1": "1"})


class TestManifest(BuildTestCase):
    def test_full_packs_have_no_url_and_no_filename_in_the_manifest(self):
        blob = json.dumps(self.manifest, ensure_ascii=False)
        for entry in self.manifest["packs"]:
            if entry["tier"] == "full":
                self.assertIsNone(entry["url"])
                self.assertTrue(entry.get("encrypted"))
        for path in self.result["files"]:
            if path.startswith("p/"):
                self.assertNotIn(Path(path).name, blob)

    def test_free_packs_are_plain_and_addressable(self):
        for entry in self.manifest["packs"]:
            if entry["tier"] == "free":
                self.assertTrue(entry["url"].startswith("https://"))
                self.assertFalse(entry.get("encrypted"))

    def test_manifest_hashes_match_the_emitted_bytes(self):
        for entry in self.manifest["packs"]:
            match = [n for n, d in self.result["files"].items() if bp.sha256(d) == entry["sha256"]]
            self.assertEqual(len(match), 1, entry["id"])
            self.assertEqual(len(self.result["files"][match[0]]), entry["bytes"])

    def test_law_revision_date_and_counts(self):
        self.assertRegex(self.manifest["law_revision_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(
            self.manifest["counts"]["free"] + self.manifest["counts"]["full"],
            self.manifest["counts"]["total"],
        )
        self.assertEqual(self.manifest["counts"]["total"], len(self.questions))


class TestCrypto(BuildTestCase):
    def test_full_packs_round_trip(self):
        key = bp.pack_key()[0]
        for entry in self.manifest["packs"]:
            if entry["tier"] != "full":
                continue
            name = next(n for n, d in self.result["files"].items() if bp.sha256(d) == entry["sha256"])
            plain = bp.decrypt(key, self.result["files"][name])
            self.assertEqual(bp.sha256(plain), entry["payload_sha256"])
            json.loads(plain)

    def test_ciphertext_hides_the_questions(self):
        entry = self.pack("ja-full")
        name = next(n for n, d in self.result["files"].items() if bp.sha256(d) == entry["sha256"])
        blob = self.result["files"][name]
        self.assertNotIn("運転".encode("utf-8"), blob)
        self.assertNotIn(b'"question"', blob)

    def test_filename_is_unguessable_and_stable(self):
        a = bp.full_pack_name(bp.DEV_KEY, "core-full", 3)
        self.assertEqual(a, bp.full_pack_name(bp.DEV_KEY, "core-full", 3))
        self.assertNotEqual(a, bp.full_pack_name(bp.DEV_KEY, "core-full", 4))
        self.assertNotEqual(a, bp.full_pack_name(b"\x01" * 32, "core-full", 3))

    def test_tampered_ciphertext_is_rejected(self):
        entry = self.pack("core-full")
        name = next(n for n, d in self.result["files"].items() if bp.sha256(d) == entry["sha256"])
        blob = bytearray(self.result["files"][name])
        blob[-1] ^= 0x01
        with self.assertRaises(Exception):
            bp.decrypt(bp.pack_key()[0], bytes(blob))


class TestVersioning(BuildTestCase):
    def test_rebuild_of_unchanged_input_is_byte_identical(self):
        again = bp.build(self.tmp)
        self.assertEqual(again["files"], self.result["files"])
        self.assertEqual(again["manifest"]["content_version"],
                         self.manifest["content_version"])

    def test_only_the_changed_language_pack_bumps(self):
        original = bp.load_questions
        edited = copy.deepcopy(original())
        edited[0]["i18n"]["vi"]["explanation"] += " (sửa)"
        bp.load_questions = lambda: edited
        try:
            after = bp.build(self.tmp)["manifest"]
        finally:
            bp.load_questions = original

        self.assertEqual(after["content_version"], self.manifest["content_version"] + 1)
        by_id = {p["id"]: p for p in after["packs"]}
        before = {p["id"]: p for p in self.manifest["packs"]}
        tier = self.tiers[edited[0]["id"]]
        self.assertEqual(by_id[f"vi-{tier}"]["version"], after["content_version"])
        for pack_id in ("core-free", "core-full", "ja-free", "taxonomy"):
            self.assertEqual(by_id[pack_id]["version"], before[pack_id]["version"], pack_id)

    def test_an_unknown_kp_fails_the_build(self):
        original = bp.load_questions
        edited = copy.deepcopy(original())
        edited[0]["kp"] = "99-9-9"
        bp.load_questions = lambda: edited
        try:
            with self.assertRaises(bp.BuildError):
                bp.build(self.tmp)
        finally:
            bp.load_questions = original


class TestTaxonomy(BuildTestCase):
    def test_every_language_has_every_code(self):
        doc = self.payload("taxonomy")
        base = bp.taxonomy_codes(doc["languages"]["ja"])
        self.assertEqual(len(base), 41)
        for lang in bp.LANG_ORDER:
            self.assertEqual(bp.taxonomy_codes(doc["languages"][lang]), base)

    def test_every_question_section_has_a_name(self):
        doc = self.payload("taxonomy")
        codes = set(bp.taxonomy_codes(doc["languages"]["ja"]))
        for q in self.questions:
            self.assertIn(bp.section_of(q["kp"]), codes)


if __name__ == "__main__":
    unittest.main()
