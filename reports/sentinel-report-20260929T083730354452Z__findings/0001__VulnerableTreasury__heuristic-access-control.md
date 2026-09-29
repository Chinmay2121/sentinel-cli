# VulnerableTreasury: missing-authorization

- **Severity:** critical
- **Location:** `src/VulnerableTreasury.sol:unknown`

## Observation
Demo heuristic: sweep lacks a caller check.

## Evidence
- Demo-only lexical pattern; not a Slither or Mythril result

## Status
Selected for Gemini/Forge validation.

Verified patch artifact: `sentinel-report-20260929T083730354452Z__VulnerableTreasury.patch.sol`
