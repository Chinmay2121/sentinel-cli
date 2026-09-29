# Implementation audit and plan

Sources: supplied Phase-1 updated PPT (34 slides), supplied PoCo v3 PDF (21 pages), all tracked source/configuration/tests. Initial git status clean; 6 Python tests and Ruff passed, but no Forge on PATH. Generated reports and tool caches are historical artifacts, not proof of correctness. .env values were not printed.

## Priority plan
| Priority | Objective | Files | Dependencies | Result and test |
|---|---|---|---|---|
| P0 | Honest execution outcomes, valid fixtures, isolated workspace | runner, foundry, examples, service | Forge/solc | Real pre/post patch tests; missing-tool failures never verify |
| P1 | Evidence parsing, all-candidate loop, real PoCs and repairs | analyzers, agents, graph, llm | optional analyzers/models | Fixture and transport tests; bounded retries |
| P2 | Persistent review API, dashboard, JSON/SARIF, CI gates | api, storage, web, reporting, cli | FastAPI | API integration and CLI smoke tests |
| P3 | Path validation, stale-patch rejection, execution isolation | patching, runner, service | Docker for untrusted inputs | Security and rollback tests |
| P3 | Dataset manifest evaluation with honest denominators | evaluation, tests | prepared local Foundry projects | Reproducible fixture benchmark |
| P4 | Review UX and viva/demo documentation | web, docs, README | core flow | Build dashboard; demo instructions |
| P5 | Full distributed services and broad research validation | documented service boundaries | external infra/datasets | Mark unverified or missing explicitly |

## Source reconciliation
PPT slide 18 misidentifies PoCo dataset as SmartBugs. Supplied paper uses PRoof-of-Patch: 23 real-world audit cases, 3 models, 69 runs per approach. Table 2: 50 well-formed PoCs; Table 3: 32 logically correct (7 GLM, 14 o3, 11 Sonnet). Narrative mentions 13/19 for o3 despite Table 3 reporting 14; use table counts and flag inconsistency. PoCo is annotation-driven and has no discovery/repair agent. No trained model, feature-engineering pipeline, or equations are needed to reproduce its prompting methodology.

Retain Python/LangGraph rather than introducing the PPT Rust CLI alongside existing Python. Local artifact files are the default deployment. Failed exploit generation is inconclusive, never proof of a false positive. Failed test execution alone never proves mitigation.

## Scout milestone (2026-09-24)

User requested Slither and Mythril integration as the next implementation slice.
Implemented their execution adapters and JSON parsers in `sentinel/analyzers`, normalized candidate schemas, analyzer status ledger, deterministic deduplication/ranking, and actual analyzer context in Scout's provider prompt. The graph now persists Scout outcomes in nodes, exposes `--scout-only`, guards real findings from fixture-only PoC generation, and writes JSON alongside Markdown.

Verified: Python parser/runner/workflow tests, Ruff and a CLI missing-tools smoke run. See `SCOUT_INTEGRATION.md` for exact external dependencies and limitations. Live Slither/Mythril analysis remains NEEDS VERIFICATION. The earlier P0 remediation defects, general Red Team/Blue Team integration, dashboard, distributed storage and benchmarking remain open; this milestone does not declare the entire plan complete.
