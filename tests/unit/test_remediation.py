from pathlib import Path

from sentinel.agents.blue_team import BlueTeam
from sentinel.agents.judge import Judge
from sentinel.agents.red_team import RedTeam
from sentinel.foundry.runner import FoundryRunner
from sentinel.schemas.execution import ExecutionResult
from sentinel.schemas.state import RuntimeState
from sentinel.schemas.vulnerability import VulnerabilityFinding


class FakeFoundry:
    def __init__(self, build: ExecutionResult, exploit: ExecutionResult, regression: ExecutionResult) -> None:
        self.build_result = build
        self.exploit_result = exploit
        self.regression_result = regression

    def build(self, project: Path) -> ExecutionResult:
        return self.build_result

    def exploit(self, project: Path) -> ExecutionResult:
        return self.exploit_result

    def regression(self, project: Path) -> ExecutionResult:
        return self.regression_result


def execution(code: int, *, timed_out: bool = False) -> ExecutionResult:
    return ExecutionResult(command=["forge"], cwd="/tmp", exit_code=code, success=code == 0, timed_out=timed_out)


def state_for(tmp_path: Path, identifier: str) -> RuntimeState:
    fixtures = {
        "heuristic-reentrancy": ("vulnerable_reentrancy", "src/VulnerableVault.sol"),
        "heuristic-access-control": ("vulnerable_access_control", "src/VulnerableTreasury.sol"),
        "heuristic-tx-origin": ("vulnerable_tx_origin", "src/TxOriginWallet.sol"),
        "heuristic-unchecked-call": ("vulnerable_unchecked_call", "src/UncheckedCallWallet.sol"),
    }
    fixture, file = fixtures[identifier]
    source = (Path(__file__).parents[2] / "examples" / fixture / file).read_text()
    target = tmp_path / file
    target.parent.mkdir(parents=True)
    target.write_text(source)
    finding = VulnerabilityFinding(id=identifier, source="local-heuristic", detector="fixture", description="fixture", file=file)
    return RuntimeState(project_path=str(tmp_path), findings=[finding], candidate_id=identifier, source_files=[file], original_source={file: source}, exploit_confirmed=True)


def test_fixture_pocs_assert_real_security_impact(tmp_path: Path) -> None:
    reentrancy = RedTeam(FoundryRunner(None))._fixture_test("heuristic-reentrancy", "src/VulnerableVault.sol")
    access = RedTeam(FoundryRunner(None))._fixture_test("heuristic-access-control", "src/VulnerableTreasury.sol")
    assert "reentrancy did not drain victim funds" in reentrancy
    assert "unauthorized sweep was blocked" in access
    assert RedTeam(FoundryRunner(None))._fixture_test("other", "src/C.sol") is None


def test_new_fixture_templates_cover_tx_origin_and_unchecked_call() -> None:
    red_team = RedTeam(FoundryRunner(None))
    assert "tx.origin phishing was blocked" in red_team._fixture_test("heuristic-tx-origin", "src/TxOriginWallet.sol")
    assert "unchecked call did not lose accounting credit" in red_team._fixture_test("heuristic-unchecked-call", "src/UncheckedCallWallet.sol")


def test_blue_team_moves_effect_before_external_interaction(tmp_path: Path) -> None:
    state = state_for(tmp_path, "heuristic-reentrancy")
    BlueTeam().generate_and_apply(state)
    patched = (tmp_path / "src/VulnerableVault.sol").read_text()
    assert patched.index("balances[msg.sender] = 0") < patched.index("msg.sender.call")
    assert state.patch_artifact and state.patch_diff


def test_blue_team_adds_treasury_authorization(tmp_path: Path) -> None:
    state = state_for(tmp_path, "heuristic-access-control")
    BlueTeam().generate_and_apply(state)
    assert 'require(msg.sender == owner, "not owner")' in (tmp_path / "src/VulnerableTreasury.sol").read_text()


def test_blue_team_patches_tx_origin_and_unchecked_call(tmp_path: Path) -> None:
    tx_origin = state_for(tmp_path / "tx-origin", "heuristic-tx-origin")
    BlueTeam().generate_and_apply(tx_origin)
    assert "require(msg.sender == owner" in (tmp_path / "tx-origin/src/TxOriginWallet.sol").read_text()
    unchecked = state_for(tmp_path / "unchecked", "heuristic-unchecked-call")
    BlueTeam().generate_and_apply(unchecked)
    assert 'require(sent, "send failed")' in (tmp_path / "unchecked/src/UncheckedCallWallet.sol").read_text()


def test_judge_requires_a_real_forge_test_failure(tmp_path: Path) -> None:
    state = RuntimeState(project_path=str(tmp_path))
    judge = Judge(FakeFoundry(execution(0), execution(-1), execution(0)))
    judge.verify(state)
    assert state.judge_result and not state.judge_result.exploit_neutralized
    state = RuntimeState(project_path=str(tmp_path))
    judge = Judge(FakeFoundry(execution(0), execution(1), execution(0)))
    judge.verify(state)
    assert state.judge_result and state.judge_result.verified


def test_blue_team_only_modifies_explicit_workspace(tmp_path: Path) -> None:
    original = state_for(tmp_path / "original", "heuristic-access-control")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    copied = state_for(workspace, "heuristic-access-control")
    copied.project_path = original.project_path
    copied.workspace_path = str(workspace)
    BlueTeam().generate_and_apply(copied)
    assert "require(msg.sender == owner" not in (tmp_path / "original/src/VulnerableTreasury.sol").read_text()
    assert "require(msg.sender == owner" in (workspace / "src/VulnerableTreasury.sol").read_text()
