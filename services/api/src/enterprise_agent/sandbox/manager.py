from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from enterprise_agent.core.config import Settings


@dataclass(slots=True)
class CommandExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int


class SandboxManager:
    def execute(self, command: str, timeout_sec: int) -> CommandExecutionResult:
        raise NotImplementedError


class LocalSandboxManager(SandboxManager):
    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def execute(self, command: str, timeout_sec: int) -> CommandExecutionResult:
        start = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=self._workspace_root,
                shell=True,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
            )
            duration_ms = int((time.perf_counter() - start) * 1000)
            return CommandExecutionResult(
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                timed_out=False,
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return CommandExecutionResult(
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Command timed out",
                timed_out=True,
                duration_ms=duration_ms,
            )


class DockerSandboxManager(SandboxManager):
    def __init__(self, workspace_root: Path, settings: Settings) -> None:
        self._workspace_root = workspace_root
        self._settings = settings

    def execute(self, command: str, timeout_sec: int) -> CommandExecutionResult:
        docker_command = self._build_docker_command(command)
        start = time.perf_counter()
        try:
            completed = subprocess.run(
                docker_command,
                cwd=self._workspace_root,
                shell=False,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
            )
            duration_ms = int((time.perf_counter() - start) * 1000)
            return CommandExecutionResult(
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                timed_out=False,
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return CommandExecutionResult(
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Command timed out",
                timed_out=True,
                duration_ms=duration_ms,
            )

    def _build_docker_command(self, command: str) -> list[str]:
        memory = f"{self._settings.sandbox_memory_limit_mb}m"
        cpus = str(self._settings.sandbox_cpu_limit)
        network = "none" if self._settings.sandbox_network_disabled else "bridge"

        return [
            "docker",
            "run",
            "--rm",
            "--network",
            network,
            "--cpus",
            cpus,
            "--memory",
            memory,
            "--pids-limit",
            str(self._settings.sandbox_pids_limit),
            "-v",
            f"{self._workspace_root}:/workspace",
            "-w",
            "/workspace",
            self._settings.sandbox_image,
            "sh",
            "-lc",
            command,
        ]


def create_sandbox_manager(workspace_root: Path, settings: Settings) -> SandboxManager:
    if settings.sandbox_mode == "docker":
        return DockerSandboxManager(workspace_root, settings)
    return LocalSandboxManager(workspace_root)
