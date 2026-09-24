# Requirement traceability

Status after the Slither/Mythril Scout milestone. COMPLETE means implemented with local tests; it does not imply real external service verification. PPT references refer to the supplied updated deck.

| Requirement | Source | Existing implementation | Status | Files/modules | Missing work |
|---|---|---|---|---|---|
| Slither + Mythril candidate aggregation | PPT 6, 28–29 | Real adapters, JSON parsers, execution ledger | NEEDS VERIFICATION | analyzers, agents/scout | Run installed analyzers on live fixtures |
| Rank, deduplicate, confidence | PPT 6, 29 | Deterministic severity/confidence sorting; conservative same-tool dedupe | COMPLETE | analyzers/parsers | Cross-tool semantic dedupe is not claimed |
| Medusa and broader detection substrate | PPT 28–29 | No adapters | MISSING | analyzers | Medusa, Solhint, eThor/Echidna as appropriate |
| Semantic Scout | PPT 28 | Evidence-bearing prompt; Gemini transport unfinished | PARTIAL | agents/scout, llm/gemini | Real provider transport and validation |
| Source/ABI/bytecode context | PPT 29 | Recursive default source profile, lexical context | PARTIAL | analyzers/tools | AST/ABI/bytecode and full Foundry profile resolution |
| Local PoC generation and feedback loop | PPT 6, 29; PoCo §§3–4 | Fixture deployment assertion only | BROKEN | agents/red_team | Actual exploit assertions, general synthesis, retries |
| Triggerability/profitability | PPT 6, 26 | Not measured | MISSING | agents/red_team | Impact assertions and value evidence |
| RAG/KG repair, ABI preservation | PPT 6, 28–29 | Fixture string replacements; ineffective reentrancy fix | BROKEN | agents/blue_team | Correct repairs, retrieval, ABI validation |
| Deterministic exploit/regression gate | PPT 6, 29; PoCo §4.6 | Forge wrappers; failure misclassification | BROKEN | agents/judge, foundry | Structured test outcomes, real baseline and patch tests |
| CLI JSON/human reports | PPT 28–30 | Scout mode, Markdown + JSON ledger | PARTIAL | cli, reporting | SARIF, budgets, models, progress, severity gating |
| CI hook and PR annotations | PPT 28–30 | Basic action with loose result check | PARTIAL | .github/workflows | Correct gate, SARIF/review comments |
| Dashboard + REST + trace stream | PPT 28–30 | None | MISSING | proposed api/web | Connected review UI, API, patch acceptance |
| PostgreSQL/S3 artifacts | PPT 28 | Local report files only | PARTIAL | reporting, schemas | Database and object-store integration |
| Neo4j/CodeBERT knowledge graph | PPT 28–29 | None | MISSING | proposed retrieval | Knowledge corpus, retrieval, graph ingestion |
| Telemetry, gas, invariant checks | PPT 28–29 | Execution durations recorded | PARTIAL | runner, schemas | Agent/token metrics, gas deltas, invariants |
| SmartBugs and recent exploits benchmark | PPT 6, 32 | Two hand-written fixtures | MISSING | examples | Dataset setup, harness, independently measured results |
| Execution containment | PoCo §3.5; project architecture | Allowlisted subprocesses and timeouts | PARTIAL | runner, docker | Actual container isolation and restricted mounts |
| Cross-contract reasoning | PPT 26, 29 | No general implementation | MISSING | agents | Multi-contract synthesis and evaluation |
| Full implementation/viva/demo docs | User request | Plan, Scout guide, matrix | PARTIAL | docs | Technical summary, demo guide and final full-system checks |

The paper's actual dataset is PRoof-of-Patch (23 cases), not the SmartBugs description in PPT slide 18. Sentinel has not reproduced PoCo's experimental results. Missing/failed PoCs are inconclusive, not automatically false positives.
