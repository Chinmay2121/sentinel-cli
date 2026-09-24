# Requirement traceability

Status after the Slither/Mythril Scout milestone. COMPLETE means implemented with local tests; it does not imply real external service verification. PPT references refer to the supplied updated deck.

| Requirement | Source | Existing implementation | Status | Files/modules | Missing work |
|---|---|---|---|---|---|
| Slither + Mythril candidate aggregation | PPT 6, 28–29 | Real adapters, JSON parsers, execution ledger | NEEDS VERIFICATION | analyzers, agents/scout | Run installed analyzers on live fixtures |
| Rank, deduplicate, confidence | PPT 6, 29 | Deterministic severity/confidence sorting; conservative same-tool dedupe | COMPLETE | analyzers/parsers | Cross-tool semantic dedupe is not claimed |
| Medusa and broader detection substrate | PPT 28–29 | No adapters | MISSING | analyzers | Medusa, Solhint, eThor/Echidna as appropriate |
| Semantic Scout | PPT 28 | Evidence-bearing prompt; Gemini transport unfinished | PARTIAL | agents/scout, llm/gemini | Real provider transport and validation |
| Source/ABI/bytecode context | PPT 29 | Recursive default source profile, lexical context | PARTIAL | analyzers/tools | AST/ABI/bytecode and full Foundry profile resolution |
| Local PoC generation and feedback loop | PPT 6, 29; PoCo §§3–4 | Reviewed executable reentrancy and access-control fixture PoCs | PARTIAL | agents/red_team, foundry | General synthesis and multi-candidate retries |
| Triggerability/profitability | PPT 6, 26 | Not measured | MISSING | agents/red_team | Impact assertions and value evidence |
| Minimal patching and ABI preservation | Project scope | Reviewed minimal fixture patches; repair stays in a temporary workspace | PARTIAL | agents/blue_team, patching | Broader patch templates and ABI validation |
| Deterministic exploit/regression gate | PPT 6, 29; PoCo §4.6 | Build, expected assertion failure, and non-exploit regression gate | COMPLETE for fixtures | agents/judge, foundry | General PoC and patch cases |
| CLI JSON/human reports | PPT 28–30 | Scout mode, Markdown + JSON ledger | PARTIAL | cli, reporting | SARIF, budgets, models, progress, severity gating |
| CI hook and PR annotations | PPT 28–30 | Basic action with loose result check | PARTIAL | .github/workflows | Correct gate, SARIF/review comments |
| Dashboard + REST + trace stream | PPT 28–30 | Loopback REST scan/history endpoints and evidence/patch review page | PARTIAL | api, service, web | Authentication, streaming trace and patch acceptance |
| PostgreSQL/S3 artifacts | PPT 28 | Local report files only | PARTIAL | reporting, schemas | Database and object-store integration |
| Telemetry, gas, invariant checks | PPT 28–29 | Execution durations recorded | PARTIAL | runner, schemas | Agent/token metrics, gas deltas, invariants |
| Modern Solidity challenge corpus | Project scope | Damn Vulnerable DeFi is stored locally with Solidity 0.8.25 sources | PARTIAL | datasets/damn-vulnerable-defi | Complete Foundry build configuration and measured Scout results |
| Execution containment | PoCo §3.5; project architecture | Allowlisted subprocesses and timeouts | PARTIAL | runner, docker | Actual container isolation and restricted mounts |
| Cross-contract reasoning | PPT 26, 29 | No general implementation | MISSING | agents | Multi-contract synthesis and evaluation |
| Full implementation/viva/demo docs | User request | Plan, Scout guide, matrix | PARTIAL | docs | Technical summary, demo guide and final full-system checks |

The paper's actual dataset is PRoof-of-Patch (23 cases), not the SmartBugs description in PPT slide 18. Sentinel has not reproduced PoCo's experimental results. Missing/failed PoCs are inconclusive, not automatically false positives.
