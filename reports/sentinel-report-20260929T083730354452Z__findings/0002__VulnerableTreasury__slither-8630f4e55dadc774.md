# VulnerableTreasury: arbitrary-send-eth

- **Severity:** high
- **Location:** `src/VulnerableTreasury.sol:11`

## Observation
VulnerableTreasury.sweep(address) (src/VulnerableTreasury.sol#11-13) sends eth to arbitrary user
	Dangerous calls:
	- recipient.transfer(address(this).balance) (src/VulnerableTreasury.sol#12)


## Evidence
- slither:arbitrary-send-eth: VulnerableTreasury.sweep(address) (src/VulnerableTreasury.sol#11-13) sends eth to arbitrary user
	Dangerous calls:
	- recipient.transfer(address(this).balance) (src/VulnerableTreasury.sol#12)


## Status
Scout candidate; no exploit or patch has been approved yet.
