from pathlib import Path

from sentinel.foundry.runner import FoundryRunner
from sentinel.schemas.execution import JudgeResult
from sentinel.schemas.state import RuntimeState
from sentinel.validation import (
    declared_public_api,
    declared_storage,
    load_validation_profile,
)


class Judge:
    """Layer 4: deterministic build, exploit-defense, and regression gate."""

    def __init__(self, foundry: FoundryRunner) -> None:
        self.foundry = foundry

    def verify(self, state: RuntimeState) -> RuntimeState:
        project = Path(state.workspace_path or state.project_path)
        try:
            profile = load_validation_profile(project)
        except (TypeError, ValueError) as exc:
            state.judge_result = JudgeResult(failure_reason="invalid validation profile", feedback=str(exc))
            state.final_verification_state = "human_review_required"
            return state
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
        positive_runs = [self.foundry.named_test(project, name) for name in profile.positive_tests]
        security_runs = [self.foundry.named_test(project, name) for name in profile.security_tests]
        positive_passed = all(run.success for run in positive_runs) if positive_runs else None
        security_passed = all(run.success for run in security_runs) if security_runs else None
        patched = {**state.original_source, **state.patched_source}
        abi_compatible = declared_public_api(state.original_source) == declared_public_api(patched) if profile.require_abi_compatibility else None
        storage_compatible = declared_storage(state.original_source) == declared_storage(patched) if profile.require_storage_declaration_compatibility else None
        additional_checks = [
            *[f"positive:{name}:{'passed' if run.success else 'failed'}" for name, run in zip(profile.positive_tests, positive_runs, strict=True)],
            *[f"security:{name}:{'passed' if run.success else 'failed'}" for name, run in zip(profile.security_tests, security_runs, strict=True)],
            *([f"declared-abi:{'passed' if abi_compatible else 'failed'}"] if abi_compatible is not None else []),
            *([f"declared-storage:{'passed' if storage_compatible else 'failed'}"] if storage_compatible is not None else []),
        ]
        extra_passed = all(value is not False for value in (positive_passed, security_passed, abi_compatible, storage_compatible))
        state.judge_result = JudgeResult(
            build_passed=True, exploit_neutralized=neutralized,
            regression_passed=regression.success, positive_tests_passed=positive_passed,
            security_tests_passed=security_passed, abi_compatible=abi_compatible,
            storage_layout_compatible=storage_compatible, additional_checks=additional_checks,
            verified=neutralized and regression.success and extra_passed,
            failure_reason="" if neutralized and regression.success and extra_passed else "Exploit, regression, or configured validation gate failed",
            feedback=(exploit.stderr or exploit.stdout or "") + (regression.stderr or regression.stdout or "") + "\n".join(run.stderr or run.stdout for run in [*positive_runs, *security_runs]),
        )
        state.final_verification_state = "verified" if state.judge_result.verified else "retry_required"
        return state
