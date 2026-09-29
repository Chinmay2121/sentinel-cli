# UncheckedCallWallet: missing-zero-check

- **Severity:** low
- **Location:** `src/UncheckedCallWallet.sol:11`

## Observation
UncheckedCallWallet.withdraw(address).recipient (src/UncheckedCallWallet.sol#11) lacks a zero-check on :
		- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Evidence
- slither:missing-zero-check: UncheckedCallWallet.withdraw(address).recipient (src/UncheckedCallWallet.sol#11) lacks a zero-check on :
		- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
