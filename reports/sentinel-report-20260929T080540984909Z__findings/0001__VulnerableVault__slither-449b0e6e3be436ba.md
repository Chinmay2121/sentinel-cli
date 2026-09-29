# VulnerableVault: reentrancy-eth

- **Severity:** high
- **Location:** `src/VulnerableVault.sol:11`

## Observation
Reentrancy in VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16):
	External calls:
	- (sent,None) = msg.sender.call{value: amount}() (src/VulnerableVault.sol#13)
	State variables written after the call(s):
	- balances[msg.sender] = 0 (src/VulnerableVault.sol#15)
	VulnerableVault.balances (src/VulnerableVault.sol#5) can be used in cross function reentrancies:
	- VulnerableVault.balances (src/VulnerableVault.sol#5)
	- VulnerableVault.deposit() (src/VulnerableVault.sol#7-9)
	- VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16)


## Evidence
- slither:reentrancy-eth: Reentrancy in VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16):
	External calls:
	- (sent,None) = msg.sender.call{value: amount}() (src/VulnerableVault.sol#13)
	State variables written after the call(s):
	- balances[msg.sender] = 0 (src/VulnerableVault.sol#15)
	VulnerableVault.balances (src/VulnerableVault.sol#5) can be used in cross function reentrancies:
	- VulnerableVault.balances (src/VulnerableVault.sol#5)
	- VulnerableVault.deposit() (src/VulnerableVault.sol#7-9)
	- VulnerableVault.withdraw() (src/VulnerableVault.sol#11-16)


## Status
Scout candidate; no exploit or patch has been approved yet.
