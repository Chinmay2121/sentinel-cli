# UncheckedCallWallet: unchecked-low-level-call

- **Severity:** medium
- **Location:** `src/UncheckedCallWallet.sol:13`

## Observation
Demo heuristic: low-level call result is ignored.

## Evidence
- Demo-only lexical pattern; not a Slither or Mythril result

## Status
Selected for Gemini/Forge validation.

Verified patch artifact: `sentinel-report-20260929T083845823044Z__UncheckedCallWallet.patch.sol`
