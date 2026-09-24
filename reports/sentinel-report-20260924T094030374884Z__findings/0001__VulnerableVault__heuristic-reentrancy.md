# VulnerableVault: external-call-order

- **Severity:** high
- **Location:** `src/VulnerableVault.sol:13`

## Observation
Demo heuristic: external call before balance update; requires validation.

## Evidence
- Demo-only lexical pattern; not a Slither or Mythril result

## Status
Selected for Gemini/Forge validation.
