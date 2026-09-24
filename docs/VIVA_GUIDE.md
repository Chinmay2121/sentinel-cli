# Viva guide

## Why not accept a static-analysis finding directly?

Static tools can over-approximate. Sentinel keeps tool output as a candidate and requires an executable local Forge test before a reviewed fixture repair proceeds.

## How does the project relate to PoCo?

PoCo generates PoCs from auditor annotations and validates them against developer patches. Sentinel uses that execution-first validation idea, adds Scout evidence, and evaluates a local repair. Sentinel does not reproduce PoCo's PRoof-of-Patch experiment.

## How is reentrancy demonstrated?

The attacker deposits one ether into a vault already holding one ether of victim funds. Its receive function re-enters `withdraw` before the vulnerable vault clears its balance. The PoC asserts that the attacker receives two ether.

## Why does the repair work?

The repair follows checks-effects-interactions: it clears the caller's balance before the external call. A re-entrant invocation then has a zero balance and cannot drain the victim funds.

## How is a patch accepted?

Judge requires three conditions: the patched workspace builds, the original exploit test fails through a normal Forge assertion, and regression tests excluding that exploit pass. Missing tools and timeouts are inconclusive.

## Does Sentinel change customer code?

No. The workflow copies the Foundry project to a temporary workspace. Generated tests and patches stay there; the final report records a diff for manual review.

## What does Scout provide?

Slither JSON contributes detector, impact, confidence, and locations. Mythril JSON contributes SWC classification, severity, locations, and transaction evidence. Sentinel records unavailable or malformed tool output too.

## What is incomplete?

Arbitrary PoC generation, cross-contract reasoning, broad benchmark evaluation, Medusa/Echidna integration, database services, authentication, and production telemetry are future work.
