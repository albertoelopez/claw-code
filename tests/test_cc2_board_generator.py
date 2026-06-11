from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate_cc2_board.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_cc2_board", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CC2BoardGeneratorTests(unittest.TestCase):
    def test_missing_source_omx_error_lists_searched_paths_and_recovery_steps(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            repo_root.mkdir()
            (repo_root / "ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")

            with self.assertRaises(FileNotFoundError) as caught:
                generator.find_source_omx(repo_root)

        message = str(caught.exception)
        self.assertIn("could not locate source .omx", message)
        self.assertIn("searched:", message)
        self.assertIn(str(repo_root / ".omx"), message)
        self.assertIn("Set CC2_SOURCE_OMX", message)
        self.assertIn("plans/claw-code-2-0-adaptive-plan.md", message)
        self.assertIn("research/", message)

    def test_source_omx_can_be_supplied_by_env(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo_root = temp_root / "repo"
            repo_root.mkdir()
            source = temp_root / "cc2-source"
            (source / "plans").mkdir(parents=True)
            (source / "research").mkdir()
            (source / "plans" / "claw-code-2-0-adaptive-plan.md").write_text(
                "# approved plan\n", encoding="utf-8"
            )

            self.assertEqual(source, generator.find_source_omx(repo_root, env_value=str(source)))


if __name__ == "__main__":
    unittest.main()
