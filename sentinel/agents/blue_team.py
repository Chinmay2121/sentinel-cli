import difflib
from pathlib import Path

from sentinel.patching.applier import apply_replacement
from sentinel.schemas.artifacts import PatchArtifact
from sentinel.schemas.state import RuntimeState


class BlueTeam:
    """Layer 3: Minimal Invasive Change patch synthesis for the MVP demonstrations."""

    def generate_and_apply(self, state: RuntimeState) -> RuntimeState:
        finding = next((item for item in state.findings if item.id == state.candidate_id), None)
        if finding is None or not state.exploit_confirmed:
            return state
        relative = finding.file
        workspace = Path(state.workspace_path or state.project_path)
        path = workspace / relative
        original = path.read_text(encoding="utf-8")
        if finding.id == "heuristic-reentrancy":
            old = '''        uint256 amount = balances[msg.sender];
        (bool sent,) = msg.sender.call{value: amount}(""); // reentrancy demo
        require(sent, "send failed");
        balances[msg.sender] = 0;'''
            new = '''        uint256 amount = balances[msg.sender];
        balances[msg.sender] = 0;
        (bool sent,) = msg.sender.call{value: amount}(""); // reentrancy demo
        require(sent, "send failed");'''
        elif finding.id == "heuristic-access-control":
            old = "function sweep(address payable recipient) external {"
            new = "function sweep(address payable recipient) external {\n        require(msg.sender == owner, \"not owner\");"
        elif finding.id == "heuristic-tx-origin":
            old = "require(tx.origin == owner, \"not owner\");"
            new = "require(msg.sender == owner, \"not owner\");"
        elif finding.id == "heuristic-unchecked-call":
            old = "        recipient.call{value: amount}(\"\"); // unchecked low-level call"
            new = "        (bool sent,) = recipient.call{value: amount}(\"\");\n        require(sent, \"send failed\");"
        else:
            state.feedback.append("Blue Team has no reviewed patch template for this candidate.")
            return state
        if old not in original:
            state.feedback.append("Blue Team could not locate a minimal patch anchor")
            return state
        apply_replacement(workspace, relative, old, new, set(state.original_source))
        patched = path.read_text(encoding="utf-8")
        state.patched_source[relative] = patched
        state.patch_diff = "".join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True), fromfile=relative, tofile=relative))
        state.patch_artifact = PatchArtifact(
            vulnerability_id=finding.id, original_file=relative, patch=state.patch_diff,
            rationale="Only the vulnerable state-update/authorization region was changed.",
            attempt=state.retry_count + 1,
        )
        return state
