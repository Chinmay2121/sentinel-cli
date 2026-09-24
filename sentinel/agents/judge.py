from pathlib import Path

from sentinel.foundry.runner import FoundryRunner
from sentinel.schemas.execution import JudgeResult
from sentinel.schemas.state import RuntimeState


class Judge:
    """Layer 4: deterministic build, exploit-defense, and regression gate."""

    def __init__(self, foundry: FoundryRunner) -> None:
        self.foundry = foundry

    def verify(self, state: RuntimeState) -> RuntimeState:
        project = Path(state.workspace_path or state.project_path)
        build = self.foundry.build(project)
        state.compilation_result = build
        if not build.success:
            reason = "forge build failed"
            state.judge_result = JudgeResult(failure_reason=reason, feedback=build.stderr or build.stdout)
            state.feedback.append(state.judge_result.feedback)
            state.final_verification_state = "retry_required"
            return state
        exploit = self.foundry.exploit(project)
        state.exploit_result = exploit
        # A normal Forge assertion failure returns 1. Tool failures and timeouts are
        # inconclusive, never evidence that a patch neutralized an exploit.
        neutralized = exploit.exit_code == 1 and not exploit.timed_out
        regression = self.foundry.regression(project)
        state.regression_result = regression
        state.judge_result = JudgeResult(
            build_passed=True, exploit_neutralized=neutralized,
            regression_passed=regression.success,
            verified=neutralized and regression.success,
            failure_reason="" if neutralized and regression.success else "Exploit or regression gate failed",
            feedback=(exploit.stderr or exploit.stdout or "") + (regression.stderr or regression.stdout or ""),
        )
        state.final_verification_state = "verified" if state.judge_result.verified else "retry_required"
        return state
