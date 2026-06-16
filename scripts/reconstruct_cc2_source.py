#!/usr/bin/env python3
"""Reconstruct a local CC2 source bundle from live GitHub data.

This helper is a recovery tool for checkouts that contain the generated CC2 board
scripts but not the original frozen `.omx/plans` and `.omx/research` bundle.
The output is intentionally marked as non-frozen so release/audit workflows do
not mistake it for the original approved plan evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CLAW_REPO = "ultraworkers/claw-code"
DEFAULT_PARITY_REPOS = {
    "opencode": "anomalyco/opencode",
    "codex": "openai/codex",
}

PLACEHOLDER_PLAN = """# Reconstructed Claw Code 2.0 source placeholder

This local source bundle was reconstructed from live GitHub API data because the
original frozen `.omx/plans` and `.omx/research` source bundle is not present in
this checkout.

Use this bundle to exercise `scripts/generate_cc2_board.py` locally. Do not treat
it as the original approved plan. Historical generated board artifacts record the
frozen approved-plan SHA-256 prefix separately.
"""


def parse_json_output(output: str) -> Any:
    return json.loads(output)


def run_json(command: list[str]) -> Any:
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return parse_json_output(completed.stdout)


def gh_issue_list(repo: str, state: str, limit: int) -> list[dict[str, Any]]:
    data = run_json(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,body,state,url",
        ]
    )
    if not isinstance(data, list):
        raise TypeError(f"expected gh issue list to return a JSON array, got {type(data).__name__}")
    return data


def gh_repo_metadata(repo: str) -> dict[str, Any]:
    data = run_json(
        [
            "gh",
            "repo",
            "view",
            repo,
            "--json",
            "nameWithOwner,url,pushedAt,latestRelease,licenseInfo",
        ]
    )
    if not isinstance(data, dict):
        raise TypeError(f"expected gh repo view to return a JSON object, got {type(data).__name__}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_source_bundle(
    out_root: Path,
    *,
    latest_issues: list[dict[str, Any]],
    all_issues: list[dict[str, Any]],
    repo_metadata: dict[str, dict[str, Any]],
    provenance: dict[str, Any],
) -> None:
    plans = out_root / "plans"
    research = out_root / "research"
    plans.mkdir(parents=True, exist_ok=True)
    research.mkdir(parents=True, exist_ok=True)

    (plans / "claw-code-2-0-adaptive-plan.md").write_text(PLACEHOLDER_PLAN, encoding="utf-8")
    write_json(research / "claw-open-latest.json", latest_issues)
    write_json(research / "claw-issues.json", all_issues)
    for name in sorted(repo_metadata):
        write_json(research / f"{name}-repo.json", repo_metadata[name])

    write_json(
        research / "reconstruction-manifest.json",
        {
            "schema_version": "cc2.source_reconstruction.v1",
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "frozen_source_bundle": False,
            "provenance": provenance,
            "outputs": {
                "plan": "plans/claw-code-2-0-adaptive-plan.md",
                "latest_issues": "research/claw-open-latest.json",
                "all_issues": "research/claw-issues.json",
                "repo_metadata": [f"research/{name}-repo.json" for name in sorted(repo_metadata)],
            },
        },
    )


def reconstruct(args: argparse.Namespace) -> Path:
    parity_repos = dict(DEFAULT_PARITY_REPOS)
    latest_issues = gh_issue_list(args.claw_repo, "open", args.latest_limit)
    all_issues = gh_issue_list(args.claw_repo, "all", args.all_limit)
    repo_metadata = {name: gh_repo_metadata(repo) for name, repo in parity_repos.items()}
    write_source_bundle(
        args.out_root,
        latest_issues=latest_issues,
        all_issues=all_issues,
        repo_metadata=repo_metadata,
        provenance={
            "source": "live-github-api",
            "claw_repo": args.claw_repo,
            "latest_limit": args.latest_limit,
            "all_limit": args.all_limit,
            "parity_repos": parity_repos,
        },
    )
    return args.out_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=Path("/tmp/cc2-reconstructed-source/.omx"))
    parser.add_argument("--claw-repo", default=DEFAULT_CLAW_REPO)
    parser.add_argument("--latest-limit", type=int, default=30)
    parser.add_argument("--all-limit", type=int, default=1000)
    args = parser.parse_args()

    out_root = reconstruct(args)
    print(f"wrote reconstructed CC2 source bundle: {out_root}")
    print("not frozen: use for local generation only, not as original approved-plan evidence")
    print(f"run: CC2_SOURCE_OMX={out_root} python3 scripts/generate_cc2_board.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
