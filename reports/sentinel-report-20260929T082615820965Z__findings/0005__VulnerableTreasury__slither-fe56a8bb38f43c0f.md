# VulnerableTreasury: solc-version

- **Severity:** informational
- **Location:** `src/VulnerableTreasury.sol:1`

## Observation
Version constraint ^0.8.20 contains known severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)
	- VerbatimInvalidDeduplication
	- FullInlinerNonExpressionSplitArgumentEvaluationOrder
	- MissingSideEffectsOnSelectorAccess.
It is used by:
	- ^0.8.20 (src/VulnerableTreasury.sol#1)


## Evidence
- slither:solc-version: Version constraint ^0.8.20 contains known severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)
	- VerbatimInvalidDeduplication
	- FullInlinerNonExpressionSplitArgumentEvaluationOrder
	- MissingSideEffectsOnSelectorAccess.
It is used by:
	- ^0.8.20 (src/VulnerableTreasury.sol#1)


## Status
Scout candidate; no exploit or patch has been approved yet.
