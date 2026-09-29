# TxOriginWallet: tx-origin-authentication

- **Severity:** high
- **Location:** `src/TxOriginWallet.sol:3`

## Observation
Demo heuristic: authorization uses tx.origin instead of msg.sender.

## Evidence
- Demo-only lexical pattern; not a Slither or Mythril result

## Status
Selected for Gemini/Forge validation.

Verified patch artifact: `sentinel-report-20260929T075516339718Z__TxOriginWallet.patch.sol`
