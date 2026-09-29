# Sentinel CLI technical summary

## Project overview

Sentinel addresses the gap between a static smart-contract warning and a repair that a developer can trust. A local Foundry project enters Scout, which records Slither and Mythril evidence. A candidate then requires an executable Forge proof-of-concept before Sentinel produces a narrow repair and re-runs both the exploit and the normal regression tests.

The target user is a Solidity developer or reviewer. The project uses local source only and does not connect to a wallet, private key, public RPC endpoint, or deployed contract.

## Relationship to PoCo

The supplied PoCo paper focuses on agentic Foundry PoC generation from a human-written vulnerability annotation. It evaluates 23 PRoof-of-Patch audit cases and checks logical correctness by running each PoC against the developer's patch. Sentinel adopts the executable-PoC and patch-as-oracle ideas, then extends the workflow with Scout detection and a repair gate. It does not claim to reproduce PoCo's dataset or reported scores.

## Implemented architecture

```mermaid
flowchart LR
    A[Foundry project] --> B[Temporary workspace copy]
    B --> C[Scout: Slither and Mythril]
    C --> D[Candidate evidence ledger]
    D --> E[Reviewed fixture PoC template]
    E --> F[Forge exploit test]
    F --> G[Minimal repair diff]
    G --> H[Forge build and exploit defense]
    H --> I[Regression tests]
    I --> J[Markdown and JSON report]
    J --> K[Local API and dashboard]
```

The temporary workspace is the only location changed by a scan. The original project receives neither a generated test nor a patch. A reviewer can inspect the report diff and apply it separately.

## Modules

- `sentinel.analyzers`: source discovery, Foundry profile handling, Slither/Mythril command construction and JSON normalization.
- `sentinel.agents.scout`: candidate aggregation and optional semantic summary.
- `sentinel.agents.red_team`: executable fixture templates for reentrancy and missing authorization.
- `sentinel.agents.blue_team`: effects-before-interactions repair for the vault and owner authorization repair for the treasury.
- `sentinel.agents.judge`: requires successful build, a normal failed exploit assertion after the patch, and successful non-exploit regression tests.
- `sentinel.service`, `sentinel.api`, `sentinel.web`: common scan service, loopback REST API and browser review page.

## Method and evaluation

Slither findings preserve detector, impact, confidence, source location, and raw JSON. Mythril findings preserve SWC ID, severity, source location, transaction-sequence evidence, and raw JSON. Candidate rank uses severity and a fixed confidence ordering for display; it is not a calibrated probability.

The valid fixture criterion is the same direction as PoCo's patch oracle: the exploit must pass on vulnerable source and fail from an assertion on the patched source. A tool timeout, missing executable, crash, or build error is inconclusive and cannot count as mitigation.

## Actual results and limits

The supplied reentrancy and access-control fixture PoCs pass with Forge on their vulnerable source. Both full loops were run successfully on 2026-09-24 and reached `verified`; the target source was unchanged. Slither and Mythril also ran successfully against the reentrancy fixture with a configured native `SOLC_BINARY`, producing three findings each. Python tests cover command safety, parser behavior, API validation, workspace isolation, PoC content, patch behavior, provider transports, and Judge outcome handling.

The implementation does not yet provide arbitrary-contract PoC synthesis, Medusa/Echidna integration, authentication, remote deployment, measured corpus results, or production telemetry. Those features must not be described as complete during a viva.
