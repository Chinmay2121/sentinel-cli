from sentinel.agents.judge import Judge
from sentinel.schemas.execution import ExecutionResult
from sentinel.schemas.state import RuntimeState
from sentinel.validation import ValidationProfile, declared_public_api, declared_storage


def test_declared_compatibility_fingerprints_detect_surface_changes() -> None:
    original = {"src/Vault.sol": "contract Vault { uint256 balance; function withdraw(uint256 amount) external {} }"}
    changed_api = {"src/Vault.sol": "contract Vault { uint256 balance; function withdraw(address to) external {} }"}
    changed_storage = {"src/Vault.sol": "contract Vault { address owner; function withdraw(uint256 amount) external {} }"}

    assert declared_public_api(original) != declared_public_api(changed_api)
    assert declared_storage(original) != declared_storage(changed_storage)


def test_validation_profile_rejects_non_identifier_test_selectors() -> None:
    try:
        ValidationProfile(positive_tests=["testGood; forge build"])
    except ValueError as exc:
        assert "test selectors" in str(exc)
    else:
        raise AssertionError("Unsafe test selector must be rejected")


def test_judge_rejects_patch_that_breaks_required_declared_abi(tmp_path) -> None:
    (tmp_path / "sentinel-validation.yml").write_text("require_abi_compatibility: true\n")

    class PassingFoundry:
        @staticmethod
        def build(project):
            return ExecutionResult(command=["forge", "build"], cwd=str(project), exit_code=0, success=True)

        @staticmethod
        def exploit(project):
            return ExecutionResult(command=["forge", "test"], cwd=str(project), exit_code=1, success=False)

        @staticmethod
        def regression(project):
            return ExecutionResult(command=["forge", "test"], cwd=str(project), exit_code=0, success=True)

        @staticmethod
        def named_test(project, name):
            return ExecutionResult(command=["forge", "test", "--match-test", name], cwd=str(project), exit_code=0, success=True)

    original = {"src/Vault.sol": "contract Vault { function withdraw(uint256 amount) external {} }"}
    patched = {"src/Vault.sol": "contract Vault { function withdraw(address recipient) external {} }"}
    state = Judge(PassingFoundry()).verify(
        RuntimeState(project_path=str(tmp_path), original_source=original, patched_source=patched)
    )

    assert state.judge_result is not None
    assert state.judge_result.abi_compatible is False
    assert not state.judge_result.verified
