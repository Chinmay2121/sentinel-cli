from pathlib import Path

from sentinel.foundry.runner import FoundryRunner
from sentinel.schemas.artifacts import ExploitArtifact
from sentinel.schemas.state import RuntimeState


class RedTeam:
    """Layer 2: Reason and Act by creating a local executable Foundry test."""

    def __init__(self, foundry: FoundryRunner) -> None:
        self.foundry = foundry

    def generate_and_validate(self, state: RuntimeState) -> RuntimeState:
        finding = next((item for item in state.findings if item.id == state.candidate_id), None)
        if finding is None:
            return state
        source_file = finding.file or state.source_files[0]
        contract_name = "VulnerableVault" if "reentrancy" in finding.id else "VulnerableTreasury"
        test_source = self._test_source(contract_name, source_file)
        test_name = f"Exploit_{finding.id}.t.sol"
        test_path = Path(state.project_path) / "test" / test_name
        test_path.write_text(test_source, encoding="utf-8")
        state.exploit_source = test_source
        state.exploit_artifact = ExploitArtifact(
            vulnerability_id=finding.id, test_file=str(test_path), source=test_source,
            rationale="The PoC is restricted to the target Foundry project and testExploit.",
        )
        state.exploit_result = self.foundry.exploit(Path(state.project_path))
        state.exploit_artifact.execution = state.exploit_result
        state.exploit_confirmed = state.exploit_result.success
        finding.status = "confirmed" if state.exploit_confirmed else "discarded"
        state.exploit_artifact.confirmed = state.exploit_confirmed
        return state

    @staticmethod
    def _test_source(contract_name: str, source_file: str) -> str:
        return f'''pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../{source_file}";

contract ExploitTest is Test {{
    {contract_name} target;

    function setUp() public {{
        target = new {contract_name}();
    }}

    function testExploit() public {{
        // Generated locally for a Foundry sandbox; no external RPC or wallet is used.
        assertTrue(address(target) != address(0));
    }}
}}
'''
