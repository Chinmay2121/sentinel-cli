# UncheckedCallWallet: unchecked-lowlevel

- **Severity:** medium
- **Location:** `src/UncheckedCallWallet.sol:11`

## Observation
UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15) ignores return value by recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Evidence
- slither:unchecked-lowlevel: UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15) ignores return value by recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
