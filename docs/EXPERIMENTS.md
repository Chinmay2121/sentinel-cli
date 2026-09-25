# Sentinel Experiments

Sentinel experiments produce reproducible execution records. They do not turn a project manifest or a fixture into a published performance claim by themselves.

## Experiment Manifest

Create a JSON manifest with a local Foundry project for each case:

```json
{
  "name": "held-out-evaluation",
  "cases": [{
    "id": "case-001",
    "project_path": "../projects/case-001",
    "group": "held_out",
    "vulnerability_class": "reentrancy",
    "ground_truth": "vulnerable"
  }]
}
```

`group` is one of `fixture`, `held_out`, `audit`, or `clean`. `ground_truth` is `vulnerable`, `clean`, or `unknown`. Unknown labels are preserved in the report but excluded from precision, recall, F1, and false-positive-rate denominators.

The checked-in example manifest uses the four reviewed fixtures only. It is an engineering check, not held-out evidence.

## Baselines and Ablations

```bash
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile slither --mock
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile mythril --mock
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile scout-union --mock
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile sentinel-no-red-team --mock
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile sentinel-no-retry --mock
sentinel benchmark datasets/manifests/sentinel-evaluation.example.json --profile sentinel-full --mock
```

Profiles are persisted in each report. `slither`, `mythril`, and `scout-union` collect candidates only. `sentinel-no-red-team` is an explicit confirmation ablation. `sentinel-no-retry` permits one repair attempt. `sentinel-full` uses both analyzers and the configured retry bound.

Each report includes per-case outcome, coverage status, findings, confirmations, verified repairs, retries, duration, per-vulnerability-class counts, configured models, platform, and timeout. Model token or API costs must be added from the provider billing record before they are reported in a paper.

## Stronger Validator Oracles

Place an optional `sentinel-validation.yml` at a Foundry project root:

```yaml
positive_tests:
  - testDepositAndWithdraw
security_tests:
  - testAuthorizationInvariant
require_abi_compatibility: true
require_storage_declaration_compatibility: true
```

Configured test selectors must be Solidity identifiers. Positive and security tests run through Forge and become required Validator gates. The ABI and storage checks compare declared public/external function signatures and top-level storage declarations before and after a patch. They are conservative source checks, not compiler ABI or storage-layout proofs; use compiler-level upgrade checks for production upgradeable contracts.

## Publication Boundary

Do not report aggregate quality metrics until cases have reviewed ground truth, clean controls, comparable tool budgets, and preserved reports. Use fixtures for regression coverage only. Publish runtime, retry, tool availability, model configuration, raw ledgers, and failure categories with any reported result.
