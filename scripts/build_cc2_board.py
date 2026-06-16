#!/usr/bin/env python3
"""Reconstruct CC2 source evidence and generate the canonical board in one command."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

RunFn = Callable[..., object]


def build_cc2_board(
    *,
    repo_root: Path,
    source_root: Path,
    out_dir: Path,
    run: RunFn = subprocess.run,
    latest_limit: int = 30,
    all_limit: int = 1000,
    claw_repo: str = "ultraworkers/claw-code",
) -> Path:
    """Reconstruct the source bundle, generate the board, and return board.json."""
    repo_root = repo_root.resolve()
    source_root = source_root.resolve()
    out_dir = out_dir.resolve()
    reconstruct_script = repo_root / "scripts" / "reconstruct_cc2_source.py"
    generate_script = repo_root / "scripts" / "generate_cc2_board.py"

    run(
        [
            sys.executable,
            str(reconstruct_script),
            "--out-root",
            str(source_root),
            "--claw-repo",
            claw_repo,
            "--latest-limit",
            str(latest_limit),
            "--all-limit",
            str(all_limit),
        ],
        check=True,
        cwd=str(repo_root),
    )

    env = os.environ.copy()
    env["CC2_SOURCE_OMX"] = str(source_root)
    run(
        [
            sys.executable,
            str(generate_script),
            "--repo-root",
            str(repo_root),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        cwd=str(repo_root),
        env=env,
    )
    return out_dir / "board.json"


def print_board_summary(board_json: Path) -> None:
    board: dict[str, Any] = json.loads(board_json.read_text(encoding="utf-8"))
    coverage = board["coverage"]
    items = board["items"]
    print(f"board: {board_json}")
    print(f"board markdown: {board_json.with_suffix('.md')}")
    print(f"total board items: {len(items)}")
    print(
        "roadmap headings mapped: "
        f"{coverage['roadmap_headings_mapped']}/{coverage['roadmap_headings_total']}"
    )
    print(
        "roadmap actions mapped: "
        f"{coverage['roadmap_actions_mapped']}/{coverage['roadmap_actions_total']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-root", type=Path, default=Path(".omx/reconstructed-source"))
    parser.add_argument("--out-dir", type=Path, default=Path(".omx/cc2"))
    parser.add_argument("--claw-repo", default="ultraworkers/claw-code")
    parser.add_argument("--latest-limit", type=int, default=30)
    parser.add_argument("--all-limit", type=int, default=1000)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    source_root = args.source_root if args.source_root.is_absolute() else repo_root / args.source_root
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    board_json = build_cc2_board(
        repo_root=repo_root,
        source_root=source_root,
        out_dir=out_dir,
        latest_limit=args.latest_limit,
        all_limit=args.all_limit,
        claw_repo=args.claw_repo,
    )
    print_board_summary(board_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
