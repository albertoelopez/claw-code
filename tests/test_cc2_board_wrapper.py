from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "build_cc2_board.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("build_cc2_board", WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CC2BoardWrapperTests(unittest.TestCase):
    def test_build_command_reconstructs_source_then_generates_board(self) -> None:
        wrapper = load_wrapper()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "repo"
            source_root = root / "source" / ".omx"
            out_dir = root / "board"
            repo_root.mkdir()
            calls: list[list[str]] = []

            def fake_run(command: list[str], **kwargs: object) -> object:
                calls.append(command)
                return object()

            wrapper.build_cc2_board(
                repo_root=repo_root,
                source_root=source_root,
                out_dir=out_dir,
                run=fake_run,
            )

        self.assertEqual(2, len(calls))
        self.assertEqual(sys.executable, calls[0][0])
        self.assertEqual(str(repo_root / "scripts" / "reconstruct_cc2_source.py"), calls[0][1])
        self.assertIn("--out-root", calls[0])
        self.assertIn(str(source_root), calls[0])
        self.assertEqual(sys.executable, calls[1][0])
        self.assertEqual(str(repo_root / "scripts" / "generate_cc2_board.py"), calls[1][1])
        self.assertIn("--out-dir", calls[1])
        self.assertIn(str(out_dir), calls[1])

    def test_build_command_passes_cc2_source_env_to_generator(self) -> None:
        wrapper = load_wrapper()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo_root = root / "repo"
            source_root = root / "source" / ".omx"
            out_dir = root / "board"
            repo_root.mkdir()
            environments: list[dict[str, str]] = []

            def fake_run(command: list[str], **kwargs: object) -> object:
                env = kwargs.get("env")
                if isinstance(env, dict):
                    environments.append(env)
                return object()

            wrapper.build_cc2_board(
                repo_root=repo_root,
                source_root=source_root,
                out_dir=out_dir,
                run=fake_run,
            )

        self.assertEqual(str(source_root), environments[-1]["CC2_SOURCE_OMX"])


if __name__ == "__main__":
    unittest.main()
