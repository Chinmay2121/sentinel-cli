# UncheckedCallWallet: reentrancy-eth

- **Severity:** high
- **Location:** `src/UncheckedCallWallet.sol:11`

## Observation
Reentrancy in UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15):
	External calls:
	- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)
	State variables written after the call(s):
	- balances[msg.sender] = 0 (src/UncheckedCallWallet.sol#14)
	UncheckedCallWallet.balances (src/UncheckedCallWallet.sol#5) can be used in cross function reentrancies:
	- UncheckedCallWallet.balances (src/UncheckedCallWallet.sol#5)
	- UncheckedCallWallet.deposit() (src/UncheckedCallWallet.sol#7-9)
	- UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15)


## Evidence
- slither:reentrancy-eth: Reentrancy in UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15):
	External calls:
	- recipient.call{value: amount}() (src/UncheckedCallWallet.sol#13)
	State variables written after the call(s):
	- balances[msg.sender] = 0 (src/UncheckedCallWallet.sol#14)
	UncheckedCallWallet.balances (src/UncheckedCallWallet.sol#5) can be used in cross function reentrancies:
	- UncheckedCallWallet.balances (src/UncheckedCallWallet.sol#5)
	- UncheckedCallWallet.deposit() (src/UncheckedCallWallet.sol#7-9)
	- UncheckedCallWallet.withdraw(address) (src/UncheckedCallWallet.sol#11-15)


## Status
Scout candidate; no exploit or patch has been approved yet.
