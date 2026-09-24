from sentinel.llm.base import LLMProvider
from sentinel.schemas.state import RuntimeState


class Scout:
    """Layer 1: Perceive. Static findings remain candidates until execution proves them."""

    def __init__(self, provider: LLMProvider[str]) -> None:
        self.provider = provider

    def analyze(self, state: RuntimeState) -> RuntimeState:
        try:
            response = self.provider.generate("Return candidate-only JSON for these static findings.")
            state.scout_results.append(response)
        except (RuntimeError, ValueError) as exc:
            state.feedback.append(f"Scout provider unavailable: {exc}")
        for finding in state.findings:
            finding.semantic_context = "Static evidence supplied to Scout; empirical confirmation is pending."
        state.candidate_id = state.findings[0].id if state.findings else None
        return state
