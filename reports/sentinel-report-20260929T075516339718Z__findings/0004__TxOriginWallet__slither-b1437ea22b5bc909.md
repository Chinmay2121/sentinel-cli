# TxOriginWallet: missing-zero-check

- **Severity:** low
- **Location:** `src/TxOriginWallet.sol:11`

## Observation
TxOriginWallet.withdraw(address).recipient (src/TxOriginWallet.sol#11) lacks a zero-check on :
		- recipient.transfer(address(this).balance) (src/TxOriginWallet.sol#13)


## Evidence
- slither:missing-zero-check: TxOriginWallet.withdraw(address).recipient (src/TxOriginWallet.sol#11) lacks a zero-check on :
		- recipient.transfer(address(this).balance) (src/TxOriginWallet.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
