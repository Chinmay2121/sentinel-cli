import difflib
from pathlib import Path

from sentinel.schemas.artifacts import PatchArtifact
from sentinel.schemas.state import RuntimeState


class BlueTeam:
    """Layer 3: Minimal Invasive Change patch synthesis for the MVP demonstrations."""

    def generate_and_apply(self, state: RuntimeState) -> RuntimeState:
        finding = next((item for item in state.findings if item.id == state.candidate_id), None)
        if finding is None or not state.exploit_confirmed:
            return state
        relative = finding.file
        path = Path(state.project_path) / relative
        original = path.read_text(encoding="utf-8")
        if "reentrancy" in finding.id:
            old, new = "uint256 amount = balances[msg.sender];", "uint256 amount = balances[msg.sender];\n        balances[msg.sender] = 0;"
            old_effect = "        balances[msg.sender] = 0;\n"
            new_effect = ""
        else:
            old, new = "function sweep(address payable recipient) external {", "function sweep(address payable recipient) external {\n        require(msg.sender == owner, \"not owner\");"
            old_effect, new_effect = "", ""
        if old not in original:
            state.feedback.append("Blue Team could not locate a minimal patch anchor")
            return state
        patched = original.replace(old, new, 1)
        if old_effect:
            patched = patched.replace(old_effect, new_effect, 1)
        path.write_text(patched, encoding="utf-8")
        state.patched_source[relative] = patched
        state.patch_diff = "".join(difflib.unified_diff(original.splitlines(True), patched.splitlines(True), fromfile=relative, tofile=relative))
        state.patch_artifact = PatchArtifact(
            vulnerability_id=finding.id, original_file=relative, patch=state.patch_diff,
            rationale="Only the vulnerable state-update/authorization region was changed.",
            attempt=state.retry_count + 1,
        )
        return state
