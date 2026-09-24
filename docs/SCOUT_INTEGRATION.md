# Slither and Mythril Scout integration

## Workflow

`ingest → compiler metadata → Scout (Slither + Mythril → parse → deduplicate → rank → optional semantic summary) → report`

Scout runs `slither . --json -` in the Foundry project. It runs `myth analyze <absolute-source-file> -o json --no-onchain-data --execution-timeout 60 --transaction-count 2 --solc-json <temporary-settings>` for each recursively discovered Solidity source. An exact compiler version in the default Foundry profile is forwarded with `--solv`.

The default profile's source directory, explicit remappings, `remappings.txt`, optimizer, EVM version and via-IR settings are honored. The source tree and reported file locations must remain inside the project. Source files and tests are not edited by Sentinel during Scout-only execution; external analyzers may create compiler caches.

## Setup

Install the analyzers as separate command-line tools to avoid mixing their dependency constraints into Sentinel's Python environment:

```bash
pipx install slither-analyzer
pipx install mythril
slither --version
myth version
```

A compatible Python interpreter and native build dependencies may be required by Mythril. Follow its upstream installation instructions if the local interpreter is unsupported; `pipx install --python /path/to/compatible/python mythril` selects a separate interpreter. Install Foundry and the target Solidity compiler as required by your project. Ensure `slither`, `myth`, `forge` and `solc` are visible on the PATH inherited by Sentinel. If Mythril cannot resolve the correct platform compiler, set `SOLC_BINARY` to an executable matching the project profile. Sentinel passes that path only as Mythril's `SOLC` compiler override.

```bash
source .venv/bin/activate
sentinel scan ./examples/vulnerable_reentrancy --scout-only --mock
```

`--mock` substitutes only the semantic summary provider and permits explicitly labeled fixture heuristics if neither analyzer returns findings. It still attempts real analyzers and never fabricates their output. Omit `--mock` to disable heuristic fallback. The current Gemini transport remains unfinished, so its failure is recorded while deterministic analyzer findings are retained.

Scout-only exit code 0 means both configured analyzers completed their runs; it does **not** mean the contract is secure. Exit code 2 means coverage was incomplete or the project was invalid. Findings and diagnostics are written to Markdown and a JSON state ledger with the same basename. All findings remain `candidate`.

## Normalized evidence

Slither: detector, severity, confidence, source path, line, contract/function when supplied, description, original detector JSON.

Mythril: SWC ID, severity, source path/line when supplied, contract/function, description and original issue JSON including transaction sequence. Mythril does not supply confidence, so it remains `unknown`, with score 0 representing unknown confidence rather than a measured probability. Slither high/medium/low scores (0.9/0.6/0.3) are fixed sorting weights, not calibrated probabilities.

Candidates are ranked by severity, then confidence weight, then stable location/ID. Repeated matching evidence from the same tool is deduplicated. Findings from different tools are deliberately retained separately: sharing a line or a broad SWC class does not establish that two findings are the same defect.

Successful JSON can contain findings even with a nonzero tool exit code. Raw execution success is preserved separately from analyzer completion. Missing binaries, timeouts, malformed output, compiler failures and unexpected process exits cannot produce successful coverage. Partial findings from the other analyzer survive a failure.

## Boundaries and remaining work

- No Medusa adapter yet. The old Aderyn placeholder, which fabricated a finding for every successful command, is replaced by actual Slither/Mythril parsers. Its legacy ledger field remains readable.
- No contract-safety or false-positive-rate claim follows from a clean or incomplete scan.
- Mythril analysis is bounded and uses its normal source-file contract selection. This adapter does not claim full multi-contract or cross-contract coverage.
- Foundry profile inheritance, environment overrides, automatic library remapping discovery, multi-version projects, and all compiler settings are not reconstructed. Provide explicit default-profile settings/remappings; inspect recorded compilation failures.
- The runner invokes local installed tools. `--no-docker` is still a legacy no-op; container orchestration remains a separate plan task. `--no-onchain-data` disables Mythril chain-state lookup, but compiler downloads may still need network access.
- The existing Red Team is fixture-specific. Real analyzer findings stop at `human_review_required` rather than being processed by an unrelated fixture PoC.
- Live Slither execution was verified on the local reentrancy fixture on 2026-09-24. It produced `reentrancy-eth`, `solc-version`, and `low-level-calls` results. Mythril's 0.24.8 release was installed and starts. It needs `SOLC_BINARY` on this ARM64 host because its own resolver requests an unavailable macOS x86_64 artifact from `solc-bin.ethereum.org`. Parser/command/workflow tests use controlled test doubles, not benchmark results.

## References

Adapters follow the [Slither JSON schema](https://github.com/crytic/slither/wiki/JSON-output), [Slither usage](https://github.com/crytic/slither/wiki/Usage), [Mythril JSON report implementation](https://github.com/ConsenSysDiligence/mythril/blob/develop/mythril/analysis/report.py), and [Mythril CLI](https://github.com/ConsenSysDiligence/mythril/blob/develop/mythril/interfaces/cli.py). These are interface references, not instructions for Sentinel to execute arbitrary commands.
