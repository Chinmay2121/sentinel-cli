import shutil
import tempfile
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from sentinel.agents.blue_team import BlueTeam
from sentinel.agents.judge import Judge
from sentinel.agents.red_team import RedTeam
from sentinel.agents.scout import Scout
from sentinel.analyzers.tools import extract_solidity_context
from sentinel.config import settings
from sentinel.foundry.runner import FoundryRunner
from sentinel.llm.gemini import GeminiScout
from sentinel.llm.mock import MockProvider
from sentinel.runner import ControlledRunner
from sentinel.schemas.state import RetryRecord, RuntimeState


def build_workflow(runner: ControlledRunner | None = None):
    controlled = runner or ControlledRunner(settings.command_timeout_seconds)
    foundry = FoundryRunner(controlled)
    red_team = RedTeam(foundry)
    blue_team = BlueTeam()
    judge = Judge(foundry)

    def ingest(state: RuntimeState) -> RuntimeState:
        project = Path(state.project_path).resolve()
        if not (project / "foundry.toml").is_file():
            state.feedback.append("Target is not a Foundry project: foundry.toml is missing")
            state.final_verification_state = "invalid_project"
            return state
        workspace = Path(tempfile.mkdtemp(prefix="sentinel-workspace-")) / "project"
        try:
            shutil.copytree(project, workspace, ignore=shutil.ignore_patterns("out", "cache", ".git", "__pycache__"))
            files, original, context = extract_solidity_context(workspace)
        except (OSError, ValueError, TypeError) as exc:
            state.feedback.append(f"Invalid project source configuration: {exc}")
            state.final_verification_state = "invalid_project"
            return state
        state.workspace_path = str(workspace)
        state.source_files, state.original_source, state.ast_context = files, original, context
        return state

    def static_analysis(state: RuntimeState) -> RuntimeState:
        project = Path(state.workspace_path or state.project_path)
        compiler = controlled.run(["solc", "--version"], project)
        state.compiler_info = {"command": "solc --version", "output": compiler.stdout or compiler.stderr}
        return state

    def scout_node(state: RuntimeState) -> RuntimeState:
        scout = Scout(MockProvider() if state.mock_mode else GeminiScout(), controlled)
        state = scout.analyze(state)
        complete = bool(state.analyzer_runs) and all(r.status == "completed" for r in state.analyzer_runs)
        if state.scout_only:
            state.final_verification_state = "scout_complete" if complete else "scout_incomplete"
        elif not state.findings:
            state.final_verification_state = "no_candidates" if complete else "analysis_incomplete"
        elif any(f.source != "local-heuristic" for f in state.findings):
            state.final_verification_state = "human_review_required"
            state.feedback.append("Real analyzer candidates require general PoC synthesis; fixture-only Red Team is not applicable.")
        return state

    def route_after_scout(state: RuntimeState) -> str:
        return "red_team" if state.final_verification_state == "not_started" else "report"

    def red_team_node(state: RuntimeState) -> RuntimeState:
        return red_team.generate_and_validate(state)

    def discard_node(state: RuntimeState) -> RuntimeState:
        state.final_verification_state = "finding_discarded"
        state.feedback.append("Red Team PoC did not empirically confirm the candidate.")
        return state

    def blue_team_node(state: RuntimeState) -> RuntimeState:
        if state.retry_count and state.candidate_id:
            finding = next((item for item in state.findings if item.id == state.candidate_id), None)
            if finding and finding.file in state.original_source:
                (Path(state.workspace_path or state.project_path) / finding.file).write_text(state.original_source[finding.file], encoding="utf-8")
        return blue_team.generate_and_apply(state)

    def judge_node(state: RuntimeState) -> RuntimeState:
        result = judge.verify(state)
        if result.final_verification_state == "retry_required":
            state.retry_count += 1
            feedback = state.judge_result.feedback if state.judge_result else "Judge failure"
            state.retry_history.append(RetryRecord(
                attempt=state.retry_count, failure_type=state.judge_result.failure_reason if state.judge_result else "unknown",
                feedback=feedback, patch=state.patch_diff, execution=state.compilation_result,
            ))
            if state.retry_count >= state.max_retries:
                state.final_verification_state = "human_review_required"
        return result

    def route_after_exploit(state: RuntimeState) -> str:
        return "blue_team" if state.exploit_confirmed else "discard"

    def route_after_judge(state: RuntimeState) -> str:
        if state.final_verification_state == "verified":
            return "report"
        if state.retry_count >= state.max_retries:
            return "report"
        return "blue_team"

    def report_node(state: RuntimeState) -> RuntimeState:
        if state.final_verification_state == "not_started":
            state.final_verification_state = "completed_without_confirmation"
        return state

    graph = StateGraph(RuntimeState)
    graph.add_node("ingest", ingest)
    graph.add_node("static_analysis", static_analysis)
    graph.add_node("scout", scout_node)
    graph.add_node("red_team", red_team_node)
    graph.add_node("discard", discard_node)
    graph.add_node("blue_team", blue_team_node)
    graph.add_node("judge", judge_node)
    graph.add_node("report", report_node)
    graph.add_edge(START, "ingest")
    graph.add_conditional_edges("ingest", lambda state: "report" if state.final_verification_state == "invalid_project" else "static_analysis")
    graph.add_edge("static_analysis", "scout")
    graph.add_conditional_edges("scout", route_after_scout, {"report": "report", "red_team": "red_team"})
    graph.add_conditional_edges("red_team", route_after_exploit, {"blue_team": "blue_team", "discard": "discard"})
    graph.add_edge("discard", "report")
    graph.add_edge("blue_team", "judge")
    graph.add_conditional_edges("judge", route_after_judge, {"blue_team": "blue_team", "report": "report"})
    graph.add_edge("report", END)
    return graph.compile()
