import hashlib
import json
import re
import unittest
from pathlib import Path

from ch11.report import load_case, tables

# Configuration
ROOT = Path(__file__).resolve().parents[2]
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)*(?:-\d+(?:[.,]\d+)*)*(?:%|x)?")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\([^)]+\)")


class ProvenanceTests(unittest.TestCase):
    def test_snapshot_hash_and_primary_urls(self):
        snapshot = ROOT / "data/case_inputs.json"
        manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), manifest["sha256"])
        for source in manifest["sources"].values():
            self.assertTrue(source["url"].startswith("https://www.sec.gov/Archives/edgar/data/1592058/"))
            self.assertEqual(source["retrieved"], "2026-11-09")

    def test_every_note_number_has_matching_ledger_evidence(self):
        note = (ROOT / "docs/strategy_note.md").read_text(encoding="utf-8")
        ledger = (ROOT / "docs/source_verification.md").read_text(encoding="utf-8")
        audit = json.loads((ROOT / "data/note_claims.json").read_text(encoding="utf-8"))
        plain = MARKDOWN_LINK_PATTERN.sub("", note)
        note_tokens = set(NUMBER_PATTERN.findall(plain))
        audit_tokens = {claim["token"] for claim in audit["claims"]}
        self.assertEqual(note_tokens, audit_tokens)
        for claim in audit["claims"]:
            matched = False
            for identifier in claim["evidence"]:
                anchor = f'<a id="{identifier.lower()}"></a>'
                row = next(line for line in ledger.splitlines() if anchor in line)
                evidence_value = row.split("|")[3]
                matched |= claim["token"] in NUMBER_PATTERN.findall(evidence_value)
                self.assertIn(f"source_verification.md#{identifier.lower()}", note)
            self.assertTrue(matched, claim)

    def test_exported_tables_reproduce(self):
        stored = json.loads((ROOT / "examples/output/results.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, tables(load_case()))

    def test_library_has_no_network_imports(self):
        import ast
        for path in (ROOT / "python/ch11").glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    modules = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                else:
                    continue
                self.assertFalse(any(module.split(".")[0] in {"urllib", "requests", "http", "socket"} for module in modules), path)

    def test_required_text_and_punctuation(self):
        for path in (ROOT / "docs").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", text, path)
            self.assertNotIn(" -- ", text, path)
        note = (ROOT / "docs/strategy_note.md").read_text(encoding="utf-8").lower()
        self.assertIn("retrospective study", note)
        self.assertIn("not investment advice", note)
