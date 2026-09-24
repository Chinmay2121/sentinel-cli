# Demonstration guide

## Prerequisites

Use Python 3.11+ and Foundry. Install project dependencies with `python3 -m pip install '.[dev]'`. Install Slither and Mythril separately if the demonstration includes live Scout evidence. Their absence is recorded, not hidden.

## Core offline demonstration

1. Run `sentinel scan ./examples/vulnerable_reentrancy --mock --output ./reports`.
2. Open the newest Markdown report in `reports/`.
3. Show the candidate, generated exploit source, patch diff, and Judge gates. The expected final state is `verified` when Forge is available.
4. Confirm `examples/vulnerable_reentrancy/src/VulnerableVault.sol` remains vulnerable and unchanged. Sentinel worked in a temporary copy.
5. Repeat with `./examples/vulnerable_access_control` to demonstrate the authorization path.

The reentrancy PoC deposits victim funds, makes the attacker reenter once, and requires the attacker to hold two ether. The repaired workspace clears the balance before calling the attacker, so the same assertion fails. The regression test still passes.

## Scout and dashboard

Run `sentinel scan ./examples/vulnerable_reentrancy --scout-only --mock` to show evidence collection and coverage status. Start `make serve`, then visit `http://127.0.0.1:8000`. Enter an absolute Foundry project path, optionally choose development mock mode, and inspect the saved report list.

## Backup path

If Slither or Mythril is unavailable, use `--mock` only with the provided fixtures. The report labels the fallback evidence as `local-heuristic`. If Forge is unavailable, show the existing JSON report and explain that a `verified` result cannot be produced without Forge. Do not claim live analyzer coverage or PoC verification in that case.
