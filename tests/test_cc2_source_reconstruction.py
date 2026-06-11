import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reconstruct_cc2_source.py"


def load_module():
    spec = importlib.util.spec_from_file_location("reconstruct_cc2_source", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CC2SourceReconstructionTests(unittest.TestCase):
    def test_writes_expected_source_bundle_shape_from_supplied_data(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / ".omx"
            module.write_source_bundle(
                out,
                latest_issues=[{"number": 2, "title": "latest", "state": "OPEN", "url": "https://example.test/2"}],
                all_issues=[{"number": 1, "title": "all", "state": "CLOSED", "url": "https://example.test/1"}],
                repo_metadata={
                    "opencode": {"nameWithOwner": "anomalyco/opencode", "url": "https://github.com/anomalyco/opencode"},
                    "codex": {"nameWithOwner": "openai/codex", "url": "https://github.com/openai/codex"},
                },
                provenance={"source": "unit-test"},
            )

            self.assertTrue((out / "plans" / "claw-code-2-0-adaptive-plan.md").exists())
            self.assertEqual(json.loads((out / "research" / "claw-open-latest.json").read_text())[0]["number"], 2)
            self.assertEqual(json.loads((out / "research" / "claw-issues.json").read_text())[0]["number"], 1)
            self.assertEqual(json.loads((out / "research" / "opencode-repo.json").read_text())["nameWithOwner"], "anomalyco/opencode")
            self.assertEqual(json.loads((out / "research" / "codex-repo.json").read_text())["nameWithOwner"], "openai/codex")
            manifest = json.loads((out / "research" / "reconstruction-manifest.json").read_text())
            self.assertEqual(manifest["provenance"]["source"], "unit-test")
            self.assertFalse(manifest["frozen_source_bundle"])

    def test_parses_github_json_arrays_and_objects(self):
        module = load_module()
        self.assertEqual(module.parse_json_output('[{"number": 1}]'), [{"number": 1}])
        self.assertEqual(module.parse_json_output('{"nameWithOwner": "openai/codex"}')["nameWithOwner"], "openai/codex")


if __name__ == "__main__":
    unittest.main()
