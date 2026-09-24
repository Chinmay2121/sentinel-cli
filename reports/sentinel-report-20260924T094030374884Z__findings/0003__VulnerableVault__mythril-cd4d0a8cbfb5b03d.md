# VulnerableVault: SWC-107

- **Severity:** medium
- **Location:** `src/VulnerableVault.sol:15`

## Observation
State access after external call
Write to persistent state following external call
The contract account state is accessed after an external call to a user defined address. To prevent reentrancy issues, consider accessing the state only before the call, especially if the callee is untrusted. Alternatively, a reentrancy lock can be used to prevent untrusted callees from re-entering the contract in an intermediate state.

## Evidence
- mythril:SWC-107: Write to persistent state following external call
The contract account state is accessed after an external call to a user defined address. To prevent reentrancy issues, consider accessing the state only before the call, especially if the callee is untrusted. Alternatively, a reentrancy lock can be used to prevent untrusted callees from re-entering the contract in an intermediate state.

## Status
Scout candidate; no exploit or patch has been approved yet.
