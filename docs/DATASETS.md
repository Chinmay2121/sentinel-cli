# Evaluation datasets

Sentinel deliberately keeps third-party corpora outside Git. Fetches go under the ignored `datasets/` directory, record a reviewed commit in `scripts/fetch_datasets.py`, and never replace an existing checkout.

| Dataset | Role | Fetch command |
| --- | --- | --- |
| SmartBugs Curated | Annotated vulnerable Solidity contracts for detection metrics | `make fetch-smartbugs-curated` |
| Damn Vulnerable DeFi | Executable intentionally vulnerable DeFi scenarios | `make fetch-damn-vulnerable-defi` |
| DeFiVulnLabs | Foundry-oriented exploit and defense exercises | `make fetch-defi-vuln-labs` |
| FORGE Artifacts | Audit-derived corpus for broad detection evaluation | `make fetch-forge-artifacts` |

Use the checked-in fixture manifest for engineering regression. For research evaluation, freeze the dataset revision above, write an explicit held-out manifest, retain clean controls, and preserve each output ledger. Do not use training, prompt-design, or fixture cases as held-out test cases.

SmartBugs Curated is appropriate for labeled vulnerable-case detection but needs independently reviewed clean controls before reporting precision or F1. Damn Vulnerable DeFi and DeFiVulnLabs are intentionally vulnerable training corpora; treat them as executable scenarios rather than generalization evidence. FORGE Artifacts is audit-derived and its maintainers recommend FORGE-Curated for moderate-scale benchmark evaluation; validate its source availability and licenses before redistributing any contract material.

```bash
make list-datasets
make fetch-smartbugs-curated
make fetch-damn-vulnerable-defi
make prepare-forge-artifacts
```

Each external repository retains its own licence and attribution terms. This repository stores only the acquisition metadata and never republishes the corpus content.
