from __future__ import annotations

from enterprise_agent.sandbox.manager import SandboxManager
from enterprise_agent.tools.schemas import (
    RunCommandInput,
    RunCommandOutput,
    RunTestsInput,
    RunTestsOutput,
)


class CommandTools:
    def __init__(self, sandbox: SandboxManager) -> None:
        self._sandbox = sandbox

    def run_command(self, payload: RunCommandInput) -> RunCommandOutput:
        result = self._sandbox.execute(payload.command, payload.timeout_sec)
        return RunCommandOutput(
            command=payload.command,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )

    def run_tests(self, payload: RunTestsInput) -> RunTestsOutput:
        result = self._sandbox.execute(payload.command, payload.timeout_sec)
        return RunTestsOutput(
            command=payload.command,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
        )
