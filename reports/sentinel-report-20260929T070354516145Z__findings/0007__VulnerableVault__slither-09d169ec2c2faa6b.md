# VulnerableVault: low-level-calls

- **Severity:** informational
- **Location:** `src/VulnerableVault.sol:11`

## Observation
Low level call in VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16):
	- (sent,None) = msg.sender.call{value: amount}() (src/VulnerableVault.sol#13)


## Evidence
- slither:low-level-calls: Low level call in VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16):
	- (sent,None) = msg.sender.call{value: amount}() (src/VulnerableVault.sol#13)


## Status
Scout candidate; no exploit or patch has been approved yet.
