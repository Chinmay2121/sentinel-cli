# UncheckedCallWallet: low-level-calls

- **Severity:** informational
- **Location:** `src/UncheckedCallWallet.sol:11`

## Observation
Low level call in UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15):
	- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Evidence
- slither:low-level-calls: Low level call in UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15):
	- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
