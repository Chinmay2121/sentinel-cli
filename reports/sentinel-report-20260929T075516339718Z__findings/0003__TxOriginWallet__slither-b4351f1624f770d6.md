# TxOriginWallet: tx-origin

- **Severity:** medium
- **Location:** `src/TxOriginWallet.sol:11`

## Observation
TxOriginWallet.withdraw(address) (src/TxOriginWallet.sol#11-14) uses tx.origin for authorization: require(bool,string)(tx.origin == owner,not owner) (src/TxOriginWallet.sol#12)


## Evidence
- slither:tx-origin: TxOriginWallet.withdraw(address) (src/TxOriginWallet.sol#11-14) uses tx.origin for authorization: require(bool,string)(tx.origin == owner,not owner) (src/TxOriginWallet.sol#12)


## Status
Scout candidate; no exploit or patch has been approved yet.
