# VulnerableTreasury: missing-zero-check

- **Severity:** low
- **Location:** `src/VulnerableTreasury.sol:11`

## Observation
VulnerableTreasury.sweep(address).recipient (src/VulnerableTreasury.sol#11) lacks a zero-check on :
		- recipient.transfer(address(this).balance) (src/VulnerableTreasury.sol#12)


## Evidence
- slither:missing-zero-check: VulnerableTreasury.sweep(address).recipient (src/VulnerableTreasury.sol#11) lacks a zero-check on :
		- recipient.transfer(address(this).balance) (src/VulnerableTreasury.sol#12)


## Status
Scout candidate; no exploit or patch has been approved yet.
