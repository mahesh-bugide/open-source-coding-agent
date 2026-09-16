from __future__ import annotations

import subprocess
from pathlib import Path

from enterprise_agent.tools.schemas import GitDiffInput, GitDiffOutput, GitStatusInput, GitStatusOutput


class GitTools:
    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def git_status(self, payload: GitStatusInput) -> GitStatusOutput:
        args = ["git", "status"]
        if payload.porcelain:
            args.append("--porcelain")

        completed = subprocess.run(
            args,
            cwd=self._workspace_root,
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "git status failed")

        return GitStatusOutput(status=completed.stdout)

    def git_diff(self, payload: GitDiffInput) -> GitDiffOutput:
        args = ["git", "diff", "--no-color"]
        if payload.pathspec:
            args.extend(["--", payload.pathspec])

        completed = subprocess.run(
            args,
            cwd=self._workspace_root,
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "git diff failed")

        return GitDiffOutput(diff=completed.stdout)
