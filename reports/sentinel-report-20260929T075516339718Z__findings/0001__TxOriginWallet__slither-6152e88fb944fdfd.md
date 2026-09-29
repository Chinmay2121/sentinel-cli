# TxOriginWallet: arbitrary-send-eth

- **Severity:** high
- **Location:** `src/TxOriginWallet.sol:11`

## Observation
TxOriginWallet.withdraw(address) (src/TxOriginWallet.sol#11-14) sends eth to arbitrary user
	Dangerous calls:
	- recipient.transfer(address(this).balance) (src/TxOriginWallet.sol#13)


## Evidence
- slither:arbitrary-send-eth: TxOriginWallet.withdraw(address) (src/TxOriginWallet.sol#11-14) sends eth to arbitrary user
	Dangerous calls:
	- recipient.transfer(address(this).balance) (src/TxOriginWallet.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
